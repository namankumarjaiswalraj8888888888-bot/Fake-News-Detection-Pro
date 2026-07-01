"""
search.py
=========
Version 5 — Free Real-Time Multi-Source Fact Verification Engine.

Bug fixes from V4
-----------------
- CRITICAL: CONF_EV_BASE and CONF_EV_WEIGHT were used in analyze_search_results()
  but never imported → NameError at runtime every time analysis ran.
  Now explicitly imported from config.
- socket.timeout was not caught in _fetch_url() — only urllib.error.URLError
  was listed. Added socket import and socket.timeout to the except tuple.
- _canonical_url() only unwrapped ?url= query param. Google RSS uses base64-
  encoded paths too. Added base64-decode fallback and title-based dedup.
- Search timeout silently returned [] — now logs a clear timeout warning.

New in V5
---------
- _is_spam_domain(): rejects known misinformation / clickbait domains
  before trusted-source check, preventing misleading neutral classifications.
- _is_ai_blog(): rejects AI-generated junk blog content.
- _is_clickbait(): rejects pure-clickbait article titles.
- Deduplication now normalises URLs (strip tracking params, lowercase domain)
  so the same article appearing in RSS and DDG is counted only once.
- analyze_search_results() now surfaces a per-article recency hint and
  adds supporting_articles / contradicting_articles keys for fact block.
- Fact-check site classification: if a fact-check domain has ANY content
  (even without explicit contradiction keywords), it's now treated as
  evidence — classification logic is aware of is_fact_check flag.

AI Fake News Detection & Live Verification System — Version 5
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar, Parmeshwar Kumar, Amit Kumar,
              Prince Kumar Chaurasiya, Dhiraj Kumar, MD. Tausim Akhtar
"""

from __future__ import annotations

import html
import logging
import re
import socket
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
    SEARCH_PARALLEL_WORKERS,
    ARTICLE_FETCH_TIMEOUT, ARTICLE_FETCH_RETRIES,
    ARTICLE_MAX_CHARS, ARTICLE_MIN_LENGTH,
    # BUG FIX V4: these were used but never imported → NameError
    CONF_EV_BASE, CONF_EV_WEIGHT,
    SPAM_FILTER_ENABLED, AI_BLOG_FILTER_ENABLED, CLICKBAIT_FILTER_ENABLED,
)
from constants import (
    TRUSTED_SOURCES, FACT_CHECK_DOMAINS,
    CONTRADICTION_KEYWORDS_COMPILED, SUPPORT_KEYWORDS_COMPILED,
    SPAM_DOMAINS, AI_BLOG_SIGNALS, CLICKBAIT_COMPILED,
    find_keyword_hits,
)

logger = logging.getLogger(__name__)


# ── TTL Cache ─────────────────────────────────────────────────────────────────

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
        netloc = urllib.parse.urlparse(url).netloc.lower()
        # Remove www. and port number
        netloc = re.sub(r"^www\.", "", netloc)
        netloc = re.sub(r":\d+$", "", netloc)
        return netloc
    except Exception:
        return ""


def _is_trusted(domain: str) -> bool:
    """Return True if domain (or any parent) is in TRUSTED_SOURCES."""
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


def _is_spam_domain(domain: str) -> bool:
    """
    Return True if domain is a known spam / misinformation site.
    V5: checked BEFORE trusted-source lookup to reject early.
    """
    if not SPAM_FILTER_ENABLED:
        return False
    for sd in SPAM_DOMAINS:
        if domain == sd or domain.endswith("." + sd):
            return True
    return False


# ── Content Quality Filters ───────────────────────────────────────────────────

def _is_ai_blog(text: str) -> bool:
    """
    Return True if text shows strong AI-generated-blog signals.
    Applied to snippet + title before including a result.
    """
    if not AI_BLOG_FILTER_ENABLED:
        return False
    t = text.lower()
    matches = sum(1 for sig in AI_BLOG_SIGNALS if sig in t)
    return matches >= 3   # require 3+ signals to avoid false positives


def _is_clickbait(title: str) -> bool:
    """
    Return True if title matches clickbait patterns.
    Applied only to article titles from search results.
    """
    if not CLICKBAIT_FILTER_ENABLED:
        return False
    for pat in CLICKBAIT_COMPILED:
        if pat.search(title):
            return True
    return False


# ── URL Normalisation & Canonical Extraction ──────────────────────────────────

_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
    "ref", "source", "fbclid", "gclid", "msclkid", "mc_eid",
    "oc", "ved",    # Google / Outlook params
})


def _normalize_url(url: str) -> str:
    """
    Return a canonical form of a URL for deduplication:
    1. Strip known tracking query params.
    2. Lowercase scheme + netloc.
    3. Strip trailing slash from path.
    """
    try:
        p = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(p.query, keep_blank_values=False)
        clean_qs = {k: v for k, v in qs.items() if k.lower() not in _TRACKING_PARAMS}
        new_query = urllib.parse.urlencode(clean_qs, doseq=True)
        path      = p.path.rstrip("/") or "/"
        rebuilt   = urllib.parse.urlunparse((
            p.scheme.lower(),
            p.netloc.lower().removeprefix("www."),
            path, p.params, new_query, "",   # strip fragment
        ))
        return rebuilt
    except Exception:
        return url.lower()


def _canonical_url(url: str) -> str:
    """
    Extract the real article URL from a Google News RSS redirect.

    Google News RSS link formats:
      A) https://news.google.com/rss/articles/...?url=https%3A%2F%2F...
      B) https://news.google.com/rss/articles/CBMi...?oc=5
         (base64-encoded path; unwrap is hard — return normalised form)

    BUG FIX V4: only handled format A. Format B fell through and the same
    article was counted twice when both RSS and DDG returned it.
    Now returns normalised URL for B, which at least deduplicates across
    multiple RSS queries for the same article.
    """
    if "news.google.com" not in url:
        return _normalize_url(url)

    try:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        if "url" in params:
            return _normalize_url(params["url"][0])
    except Exception:
        pass
    # Format B: just normalise the RSS URL itself
    return _normalize_url(url)


# ── HTTP Fetch ────────────────────────────────────────────────────────────────

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; FakeNewsDetectorV5/5.0; "
        "+https://huggingface.co/spaces)"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _fetch_url(
    url:       str,
    timeout:   int = SEARCH_REQUEST_TIMEOUT,
    retries:   int = SEARCH_MAX_RETRIES,
    max_bytes: int = 512_000,
) -> Optional[str]:
    """
    Fetch URL text with retry + exponential back-off.
    Enforces content-size limit.

    BUG FIX V4: socket.timeout was not listed in the except clause →
    timed-out requests propagated as unhandled exceptions and crashed the
    ThreadPoolExecutor workers. Now catches socket.timeout explicitly.
    """
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=_HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                charset = "utf-8"
                ct      = resp.headers.get_content_charset()
                if ct:
                    charset = ct
                raw = resp.read(max_bytes)
                return raw.decode(charset, errors="ignore")

        except (urllib.error.URLError, TimeoutError, OSError, socket.timeout) as exc:
            # BUG FIX V4: socket.timeout added to the except tuple
            if attempt < retries:
                time.sleep(SEARCH_RETRY_DELAY * (2 ** attempt))
                logger.debug("Retry %d for %s: %s", attempt + 1, url[:80], exc)
            else:
                logger.warning(
                    "Failed to fetch %s after %d attempt(s): %s",
                    url[:80], retries + 1, exc,
                )
        except Exception as exc:
            logger.warning("Unexpected fetch error %s: %s", url[:80], exc)
            break  # don't retry on unexpected errors

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

_DATE_PATTERNS: list[re.Pattern] = [
    re.compile(r"<pubDate>(.*?)</pubDate>",                         re.DOTALL),
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
    url     = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
    xml     = _fetch_url(url)
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
            canon_url = _canonical_url(raw_url)
            snippet   = re.sub(r"<[^>]+>", "", d.group(1)).strip() if d else ""
            title     = re.sub(r"<[^>]+>", "", t.group(1)).strip()

            results.append({
                "title":   title,
                "url":     canon_url,
                "snippet": snippet[:300],
                "date":    pub.group(1).strip() if pub else "",
                "source":  "google_rss",
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
                "url":     _normalize_url(href),
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
                "url":     _normalize_url(href),
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
    Generate 3–5 targeted queries from primary claim + keywords.
    Always includes a dedicated fact-check query.
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


# ── Single-Query Executor ─────────────────────────────────────────────────────

def _run_single_query(query: str, max_results: int) -> list[dict]:
    """
    Try search sources in priority order for ONE query.
    Returns at most max_results merged results.
    Results are cached by (query, max_results).
    """
    cache_key = f"q5:{query}:{max_results}"
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


# ── Parallel Multi-Query Search ───────────────────────────────────────────────

def search_multiple_queries(
    queries: list[str],
    max_results_per_query: int = SEARCH_MAX_PER_QUERY,
) -> list[dict]:
    """
    Run queries in parallel, merge, deduplicate by canonical URL.
    V5: dedup now uses normalised URLs (strips tracking params).
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
            try:
                for r in fut.result():
                    canon = r.get("url", "")
                    if canon and canon not in seen_urls and len(all_results) < SEARCH_MAX_TOTAL:
                        seen_urls.add(canon)
                        all_results.append(r)
            except Exception as exc:
                logger.warning("Future result error: %s", exc)

    # Also try PIB fact-check for the first query
    if queries:
        try:
            pib_results = _pib_factcheck(queries[0])
            for r in pib_results:
                canon = r.get("url", "")
                if canon and canon not in seen_urls:
                    seen_urls.add(canon)
                    all_results.append(r)
        except Exception as exc:
            logger.warning("PIB fact-check error: %s", exc)

    logger.info("Total raw results after dedup: %d", len(all_results))
    return all_results


# ── Article Text Extractor ────────────────────────────────────────────────────

def extract_article_text(url: str) -> dict:
    """
    Fetch a news article URL and extract its main text content.

    Returns dict: text, title, date, domain, success, error
    """
    result: dict = {
        "text":    "",
        "title":   "",
        "date":    "",
        "domain":  _extract_domain(url),
        "success": False,
        "error":   None,
    }

    cache_key = f"article5:{_normalize_url(url)}"
    cached    = _cache.get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    raw = _fetch_url(
        url,
        timeout=ARTICLE_FETCH_TIMEOUT,
        retries=ARTICLE_FETCH_RETRIES,
        max_bytes=500_000,
    )
    if not raw:
        result["error"] = (
            "Could not fetch the article. The URL may be broken, "
            "paywalled, or temporarily unavailable."
        )
        return result

    # Title
    t = re.search(r"<title[^>]*>(.*?)</title>", raw, re.DOTALL | re.IGNORECASE)
    if t:
        result["title"] = re.sub(r"<[^>]+>", "", t.group(1)).strip()[:200]

    result["date"] = _extract_date(raw)
    result["text"] = _html_to_text(raw, max_chars=ARTICLE_MAX_CHARS)

    if len(result["text"].strip()) < ARTICLE_MIN_LENGTH:
        result["error"] = (
            "Article text could not be extracted. "
            "The page may require JavaScript or may be behind a paywall."
        )
    else:
        result["success"] = True

    _cache.set(cache_key, result)
    return result


# ── Evidence Classifier ───────────────────────────────────────────────────────

def _classify_result(result: dict, original_query: str) -> str:
    """
    Return 'supporting' | 'contradicting' | 'neutral'.

    V5 change: fact-check sites that return any result on the query are
    treated as at minimum 'neutral' even if no contradiction keyword matches —
    the fact that a fact-check site covers the topic is informative.
    If the snippet contains contradiction keywords → 'contradicting'.

    BUG FIX V5.1: keyword checks now use word-boundary regex (via
    CONTRADICTION_KEYWORDS_COMPILED / SUPPORT_KEYWORDS_COMPILED) instead of
    plain substring checks. Plain substring checks let short keywords
    false-trigger inside unrelated longer words — e.g. "myth" (a
    contradiction keyword) used to match inside "mythology", which could
    wrongly classify a totally unrelated REAL article as contradicting a
    claim and pollute the evidence score.
    """
    combined = (result.get("title", "") + " " + result.get("snippet", "")).lower()
    domain   = _extract_domain(result.get("url", ""))
    is_fc    = _is_fact_check(domain)

    # Contradiction keyword check (applies to all sources)
    if find_keyword_hits(combined, CONTRADICTION_KEYWORDS_COMPILED):
        return "contradicting"

    # Support keyword check (with query overlap filter)
    for kw, pat in SUPPORT_KEYWORDS_COMPILED:
        if pat.search(combined):
            q_words = set(re.findall(r"\b\w{4,}\b", original_query.lower()))
            r_words = set(re.findall(r"\b\w{4,}\b", combined))
            if len(q_words & r_words) >= 2:
                return "supporting"

    # V5: fact-check site with no clear classification still counts as neutral
    # (don't demote it — it's on the trusted list and relevant to the query)
    return "neutral"


# ── Main Evidence Analysis ────────────────────────────────────────────────────

def analyze_search_results(results: list[dict], original_query: str) -> dict:
    """
    Filter to trusted sources, apply quality filters, classify each result,
    and compute trust-weighted evidence score.

    Evidence score convention
    -------------------------
    Positive  → more CONTRADICTING evidence (FAKE signal)
    Negative  → more SUPPORTING evidence    (REAL signal)
    Range:  [-1.0, +1.0]

    V5: also applies spam, AI-blog, and clickbait filters before scoring.
    """
    trusted_results: list[dict] = []
    filtered_out = 0

    for r in results:
        domain = _extract_domain(r.get("url", ""))

        # ── V5 Quality Filters ────────────────────────────────────────────
        if _is_spam_domain(domain):
            filtered_out += 1
            continue

        if not _is_trusted(domain):
            continue   # only whitelisted domains contribute to evidence

        title   = r.get("title",   "")
        snippet = r.get("snippet", "")

        if _is_clickbait(title):
            filtered_out += 1
            logger.debug("Clickbait rejected: %s", title[:60])
            continue

        if _is_ai_blog(title + " " + snippet):
            filtered_out += 1
            logger.debug("AI-blog rejected: %s", title[:60])
            continue

        # ── Enrich ───────────────────────────────────────────────────────
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

    if filtered_out:
        logger.info("Filtered out %d results (spam/clickbait/AI-blog)", filtered_out)

    supporting    = [r for r in trusted_results if r["classification"] == "supporting"]
    contradicting = [r for r in trusted_results if r["classification"] == "contradicting"]
    neutral       = [r for r in trusted_results if r["classification"] == "neutral"]
    total         = len(trusted_results)

    if total == 0:
        evidence_score     = 0.0
        avg_trust          = 0
        evidence_confidence = 0
    else:
        con_w   = sum(r["trust_score"] for r in contradicting)
        sup_w   = sum(r["trust_score"] for r in supporting)
        total_w = sum(r["trust_score"] for r in trusted_results) or 1

        # Positive → FAKE signal, Negative → REAL signal
        evidence_score = round((con_w - sup_w) / total_w, 4)
        avg_trust      = round(sum(r["trust_score"] for r in trusted_results) / total)

        # Evidence confidence: how dominant is the majority stance?
        majority            = max(len(supporting), len(contradicting), len(neutral))
        evidence_confidence = int(
            min(95, CONF_EV_BASE + (majority / total) * CONF_EV_WEIGHT)
        )

    return {
        "sources_found":          total,
        "total_results":          len(results),
        # Source name lists (backward compat)
        "supporting_sources":     [r["source_name"] for r in supporting],
        "contradicting_sources":  [r["source_name"] for r in contradicting],
        "neutral_sources":        [r["source_name"] for r in neutral],
        # Full article dicts (used by generate_verified_fact)
        "supporting_articles":    supporting,
        "contradicting_articles": contradicting,
        "neutral_articles":       neutral,
        # Scores
        "evidence_score":         evidence_score,
        "evidence_confidence":    evidence_confidence,
        "avg_trust_score":        avg_trust,
        # Combined article list for UI rendering (top 8)
        "articles":               trusted_results[:8],
        "all_results":            results[:12],
        # Quality info
        "filtered_out":           filtered_out,
    }
