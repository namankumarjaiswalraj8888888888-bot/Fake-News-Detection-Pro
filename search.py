"""
search.py
=========
Version 4 — Free Real-Time Multi-Source Fact Verification Engine.

Sources (priority order, all free, no API key required):
  1. Google News RSS
  2. DuckDuckGo Lite HTML
  3. PIB Fact-Check

Bug fixes from V3
-----------------
- Google News RSS returns redirect URLs (news.google.com/rss/...).
  Deduplication by URL was ineffective — the same article appeared
  twice if RSS and DDG both found it. Canonical URL is now extracted
  from the RSS redirect URL before deduplication.
- Content-length guard added to extract_article_text() to reject
  unexpectedly large HTML responses (>500 KB) before parsing.
- TRUSTED_SOURCES and FACT_CHECK_DOMAINS moved to constants.py.

AI Fake News Detection & Live Verification System — Version 4
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar & Parmeshwar
"""

from __future__ import annotations

import html
import logging
import re
import time
import threading
import urllib.parse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from typing import Optional

from config import (
    SEARCH_REQUEST_TIMEOUT, SEARCH_MAX_PER_QUERY, SEARCH_MAX_TOTAL,
    SEARCH_CACHE_TTL, SEARCH_MAX_RETRIES, SEARCH_RETRY_DELAY,
    SEARCH_PARALLEL_WORKERS, ARTICLE_FETCH_TIMEOUT, ARTICLE_FETCH_RETRIES,
    ARTICLE_MAX_CHARS, ARTICLE_MIN_LENGTH,
)
from constants import TRUSTED_SOURCES, FACT_CHECK_DOMAINS, CONTRADICTION_KEYWORDS, SUPPORT_KEYWORDS

logger = logging.getLogger(__name__)

# ── Simple TTL Cache ──────────────────────────────────────────────────────────

class _TTLCache:
    """Thread-safe key→value store with per-entry TTL."""

    def __init__(self, ttl: int = SEARCH_CACHE_TTL, maxsize: int = 256) -> None:
        self._store: dict[str, tuple[object, float]] = {}
        self._ttl   = ttl
        self._max   = maxsize
        self._lock  = threading.Lock()

    def get(self, key: str) -> Optional[object]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, ts = entry
            if time.monotonic() - ts > self._ttl:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: object) -> None:
        with self._lock:
            if len(self._store) >= self._max:
                oldest = min(self._store, key=lambda k: self._store[k][1])
                del self._store[oldest]
            self._store[key] = (value, time.monotonic())


_cache = _TTLCache()

# ── Domain Utilities ──────────────────────────────────────────────────────────

def _extract_domain(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _is_trusted(domain: str) -> bool:
    for key in TRUSTED_SOURCES:
        if domain == key or domain.endswith("." + key):
            return True
    return False


def _trust_info(domain: str) -> tuple[str, int]:
    """Return (readable_name, trust_score) or (domain, 0)."""
    for key, (name, score) in TRUSTED_SOURCES.items():
        if domain == key or domain.endswith("." + key):
            return name, score
    return domain.capitalize(), 0


def _is_fact_check(domain: str) -> bool:
    return any(
        domain == fc or domain.endswith("." + fc) for fc in FACT_CHECK_DOMAINS
    )


def _canonical_url(url: str) -> str:
    """
    Extract the canonical (destination) URL from a Google News RSS redirect.

    Google RSS links look like:
        https://news.google.com/rss/articles/...?oc=5
    The actual article URL is embedded in the path or as a query param.
    If we can't extract it, return the original URL.
    """
    if "news.google.com" not in url:
        return url
    try:
        # Try to extract 'url' query param
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        if "url" in params:
            return params["url"][0]
    except Exception:
        pass
    return url  # fall back to original


# ── HTTP Fetch ────────────────────────────────────────────────────────────────

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; FakeNewsDetectorV4/4.0; "
        "+https://huggingface.co/spaces)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _fetch_url(
    url: str,
    timeout: int = SEARCH_REQUEST_TIMEOUT,
    retries: int = SEARCH_MAX_RETRIES,
    max_bytes: int = 512_000,
) -> Optional[str]:
    """
    Fetch URL text with retry + exponential back-off.
    Enforces a content-size limit to reject unexpectedly large pages.
    Returns None on any failure.
    """
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=_HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                charset = "utf-8"
                ct = resp.headers.get_content_charset()
                if ct:
                    charset = ct
                raw = resp.read(max_bytes)
                return raw.decode(charset, errors="ignore")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt < retries:
                time.sleep(SEARCH_RETRY_DELAY * (2 ** attempt))
                logger.debug("Retry %d for %s: %s", attempt + 1, url[:80], exc)
            else:
                logger.warning("Failed to fetch %s: %s", url[:80], exc)
    return None


# ── HTML Text Extractor ───────────────────────────────────────────────────────

class _TextExtractor(HTMLParser):
    """Minimal HTML → plain-text extractor (no external deps)."""

    SKIP_TAGS = frozenset({
        "script", "style", "noscript", "header", "footer",
        "nav", "aside", "form", "button", "meta", "link",
    })

    def __init__(self) -> None:
        super().__init__()
        self._skip  = False
        self._depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in self.SKIP_TAGS:
            self._skip  = True
            self._depth = 0
        elif self._skip:
            self._depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self._skip:
            if self._depth > 0:
                self._depth -= 1
            else:
                self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            text = data.strip()
            if text:
                self.parts.append(text)


def _html_to_text(html_str: str, max_chars: int = ARTICLE_MAX_CHARS) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(html.unescape(html_str))
    except Exception:
        pass
    return " ".join(parser.parts)[:max_chars]


# ── Date Extraction ───────────────────────────────────────────────────────────

_DATE_PATTERNS = [
    re.compile(r"<pubDate>(.*?)</pubDate>",                       re.DOTALL),
    re.compile(r'"datePublished"\s*:\s*"([^"]+)"'),
    re.compile(r'<meta[^>]+property="article:published_time"[^>]+content="([^"]+)"'),
    re.compile(r'<time[^>]+datetime="([^"]+)"'),
    re.compile(
        r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),
]


def _extract_date(raw: str) -> str:
    for pat in _DATE_PATTERNS:
        m = pat.search(raw)
        if m:
            d = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            return d[:30]
    return ""


# ── Search Engine 1: Google News RSS ─────────────────────────────────────────

def _google_news_rss(query: str, max_results: int = SEARCH_MAX_PER_QUERY) -> list[dict]:
    encoded = urllib.parse.quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
    xml = _fetch_url(url)
    if not xml:
        return []

    results: list[dict] = []
    for m in re.finditer(r"<item>(.*?)</item>", xml, re.DOTALL):
        item = m.group(1)

        t   = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>",   item, re.DOTALL)
        lnk = re.search(r"<link>(.*?)</link>",                                item, re.DOTALL)
        d   = re.search(r"<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>", item, re.DOTALL)
        pub = re.search(r"<pubDate>(.*?)</pubDate>",                          item, re.DOTALL)

        if t and lnk:
            raw_url   = lnk.group(1).strip()
            canon_url = _canonical_url(raw_url)       # ← dedup fix
            snippet   = re.sub(r"<[^>]+>", "", d.group(1)).strip() if d else ""
            results.append({
                "title":     re.sub(r"<[^>]+>", "", t.group(1)).strip(),
                "url":       canon_url,
                "raw_url":   raw_url,
                "snippet":   snippet[:300],
                "date":      pub.group(1).strip() if pub else "",
                "source":    "google_rss",
            })
        if len(results) >= max_results:
            break
    return results


# ── Search Engine 2: DuckDuckGo Lite ─────────────────────────────────────────

def _duckduckgo_lite(query: str, max_results: int = SEARCH_MAX_PER_QUERY) -> list[dict]:
    encoded   = urllib.parse.quote_plus(query)
    url       = f"https://lite.duckduckgo.com/lite/?q={encoded}"
    html_text = _fetch_url(url)
    if not html_text:
        return []

    results: list[dict] = []
    links = re.findall(
        r'<a[^>]+class="result-link"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        html_text, re.DOTALL | re.IGNORECASE,
    )
    snips = re.findall(
        r'<td[^>]+class="result-snippet"[^>]*>(.*?)</td>',
        html_text, re.DOTALL | re.IGNORECASE,
    )
    snip_texts = [re.sub(r"<[^>]+>", "", s).strip() for s in snips]

    for i, (href, title) in enumerate(links[:max_results]):
        clean_title = re.sub(r"<[^>]+>", "", title).strip()
        snippet     = snip_texts[i] if i < len(snip_texts) else ""
        if href.startswith("http"):
            results.append({
                "title":   clean_title,
                "url":     href,
                "snippet": snippet[:300],
                "date":    "",
                "source":  "duckduckgo",
            })
    return results


# ── Search Engine 3: PIB Fact-Check ──────────────────────────────────────────

def _pib_factcheck(query: str) -> list[dict]:
    """Search PIB Fact Check portal — returns 0–3 results."""
    encoded   = urllib.parse.quote_plus(query)
    url       = f"https://pib.gov.in/Pressreleaseshare.aspx?PRID=0&Lang=3&q={encoded}"
    html_text = _fetch_url(url, timeout=8)
    if not html_text:
        return []

    items: list[dict] = []
    for m in re.finditer(
        r'<a[^>]+href="(/PressReleasePage\.aspx[^"]+)"[^>]*>(.*?)</a>',
        html_text, re.DOTALL | re.IGNORECASE,
    ):
        href  = "https://pib.gov.in" + m.group(1)
        title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if len(title) > 15:
            items.append({
                "title":   title,
                "url":     href,
                "snippet": "",
                "date":    "",
                "source":  "pib",
            })
        if len(items) >= 3:
            break
    return items


# ── Query Builder ─────────────────────────────────────────────────────────────

def build_search_queries(text: str, keywords: list[str]) -> list[str]:
    """
    Generate 3–5 targeted queries from text + extracted keywords.
    Includes a dedicated fact-check query to surface debunking content.
    """
    queries: list[str] = []

    short_text = text[:90].strip()
    if len(short_text) > 20:
        queries.append(short_text)

    if keywords:
        queries.append(" ".join(keywords[:5]))
        queries.append(" ".join(keywords[:4]) + " fact check")

    if len(keywords) >= 3:
        queries.append(" ".join(keywords[:3]) + " India")

    if keywords:
        queries.append('"' + " ".join(keywords[:3]) + '"')

    seen:   set[str]  = set()
    unique: list[str] = []
    for q in queries:
        if q not in seen and len(q) > 5:
            seen.add(q)
            unique.append(q)
    return unique[:5]


# ── Parallel Multi-Query Search ───────────────────────────────────────────────

def _run_single_query(query: str, max_results: int) -> list[dict]:
    """
    Try sources in priority order for ONE query.
    Results are cached by query string.
    """
    cache_key = f"q:{query}:{max_results}"
    cached    = _cache.get(cache_key)
    if cached is not None:
        logger.debug("Cache hit: %s", query[:60])
        return cached  # type: ignore[return-value]

    results: list[dict] = []

    # Priority 1: Google News RSS
    try:
        rss = _google_news_rss(query, max_results)
        results.extend(rss)
        logger.debug("RSS returned %d for: %s", len(rss), query[:60])
    except Exception as exc:
        logger.warning("RSS error for '%s': %s", query[:60], exc)

    # Priority 2: DuckDuckGo (supplement or fallback)
    if len(results) < 3:
        try:
            ddg = _duckduckgo_lite(query, max_results)
            results.extend(ddg)
            logger.debug("DDG returned %d for: %s", len(ddg), query[:60])
        except Exception as exc:
            logger.warning("DDG error for '%s': %s", query[:60], exc)

    _cache.set(cache_key, results[:max_results])
    return results[:max_results]


def search_multiple_queries(
    queries: list[str],
    max_results_per_query: int = SEARCH_MAX_PER_QUERY,
) -> list[dict]:
    """
    Run queries in parallel, merge, and deduplicate by canonical URL.
    Also appends PIB fact-check results for the first query.
    """
    all_results: list[dict] = []
    seen_urls:   set[str]   = set()

    def _run(q: str) -> list[dict]:
        try:
            return _run_single_query(q, max_results_per_query)
        except Exception as exc:
            logger.warning("Query failed '%s': %s", q[:60], exc)
            return []

    with ThreadPoolExecutor(max_workers=SEARCH_PARALLEL_WORKERS) as pool:
        futures = {pool.submit(_run, q): q for q in queries[:5]}
        for fut in as_completed(futures):
            for r in fut.result():
                canon = r.get("url", "")
                if canon not in seen_urls and len(all_results) < SEARCH_MAX_TOTAL:
                    seen_urls.add(canon)
                    all_results.append(r)

    # Also try PIB fact-check for the first query
    if queries:
        try:
            pib_results = _pib_factcheck(queries[0])
            for r in pib_results:
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    all_results.append(r)
        except Exception as exc:
            logger.warning("PIB fact-check error: %s", exc)

    logger.info("Total raw results after dedup: %d", len(all_results))
    return all_results


# ── Article Text Extractor (URL mode) ────────────────────────────────────────

def extract_article_text(url: str) -> dict:
    """
    Fetch a news article URL and extract its main text content.

    Returns
    -------
    dict: text, title, date, domain, success, error
    """
    result = {
        "text":    "",
        "title":   "",
        "date":    "",
        "domain":  _extract_domain(url),
        "success": False,
        "error":   None,
    }

    cache_key = f"article:{url}"
    cached    = _cache.get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    raw = _fetch_url(
        url,
        timeout=ARTICLE_FETCH_TIMEOUT,
        retries=ARTICLE_FETCH_RETRIES,
        max_bytes=500_000,          # content-length guard
    )
    if not raw:
        result["error"] = "Could not fetch the article. Check the URL or network."
        return result

    # Title
    t = re.search(r"<title[^>]*>(.*?)</title>", raw, re.DOTALL | re.IGNORECASE)
    if t:
        result["title"] = re.sub(r"<[^>]+>", "", t.group(1)).strip()[:200]

    result["date"] = _extract_date(raw)
    result["text"] = _html_to_text(raw, max_chars=ARTICLE_MAX_CHARS)

    if len(result["text"].strip()) < ARTICLE_MIN_LENGTH:
        result["error"] = "Article text could not be extracted (page may require JavaScript)."
    else:
        result["success"] = True

    _cache.set(cache_key, result)
    return result


# ── Evidence Classifier ───────────────────────────────────────────────────────

def _classify_result(result: dict, original_query: str) -> str:
    """Return 'supporting' | 'contradicting' | 'neutral'."""
    combined = (result.get("title", "") + " " + result.get("snippet", "")).lower()
    domain   = _extract_domain(result.get("url", ""))

    # Fact-check sites: any contradiction keyword → contradicting
    if _is_fact_check(domain):
        for kw in CONTRADICTION_KEYWORDS:
            if kw in combined:
                return "contradicting"
        return "neutral"

    for kw in CONTRADICTION_KEYWORDS:
        if kw in combined:
            return "contradicting"

    for kw in SUPPORT_KEYWORDS:
        if kw in combined:
            q_words = set(re.findall(r"\b\w{4,}\b", original_query.lower()))
            r_words = set(re.findall(r"\b\w{4,}\b", combined))
            if len(q_words & r_words) >= 2:
                return "supporting"

    return "neutral"


# ── Main Analysis Function ────────────────────────────────────────────────────

def analyze_search_results(results: list[dict], original_query: str) -> dict:
    """
    Filter to trusted sources, classify each, and compute trust-weighted
    evidence score.

    Evidence score convention
    -------------------------
    Positive  → more CONTRADICTING evidence (FAKE signal)
    Negative  → more SUPPORTING evidence    (REAL signal)
    Range:  [-1.0, +1.0]
    """
    trusted_results: list[dict] = []

    for r in results:
        domain = _extract_domain(r.get("url", ""))
        if _is_trusted(domain):
            name, score = _trust_info(domain)
            enriched = {
                **r,
                "source_name":    name,
                "trust_score":    score,
                "is_fact_check":  _is_fact_check(domain),
                "domain":         domain,
                "classification": _classify_result(r, original_query),
            }
            trusted_results.append(enriched)

    supporting    = [r for r in trusted_results if r["classification"] == "supporting"]
    contradicting = [r for r in trusted_results if r["classification"] == "contradicting"]
    neutral       = [r for r in trusted_results if r["classification"] == "neutral"]
    total         = len(trusted_results)

    if total == 0:
        evidence_score = 0.0
        avg_trust      = 0
    else:
        con_w   = sum(r["trust_score"] for r in contradicting)
        sup_w   = sum(r["trust_score"] for r in supporting)
        total_w = sum(r["trust_score"] for r in trusted_results) or 1
        evidence_score = round((con_w - sup_w) / total_w, 4)
        avg_trust      = round(sum(r["trust_score"] for r in trusted_results) / total)

    if total == 0:
        evidence_confidence = 0
    else:
        majority            = max(len(supporting), len(contradicting), len(neutral))
        evidence_confidence = int(
            min(95, CONF_EV_BASE + (majority / total) * CONF_EV_WEIGHT)
        )

    return {
        "sources_found":          total,
        "total_results":          len(results),
        "supporting_sources":     [r["source_name"] for r in supporting],
        "contradicting_sources":  [r["source_name"] for r in contradicting],
        "neutral_sources":        [r["source_name"] for r in neutral],
        "supporting_articles":    supporting,
        "contradicting_articles": contradicting,
        "neutral_articles":       neutral,
        "evidence_score":         evidence_score,
        "evidence_confidence":    evidence_confidence,
        "avg_trust_score":        avg_trust,
        "articles":               trusted_results[:8],
        "all_results":            results[:12],
    }
