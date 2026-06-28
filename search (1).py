"""
search.py
=========
Version 3 — Free Real-Time Multi-Source Fact Verification Engine.

Sources (priority order, all free, no API key):
  1. Google News RSS
  2. DuckDuckGo Lite HTML
  3. Official Government / WHO / UN pages
  4. PIB, RBI, ISRO, Election Commission
  5. Reuters, BBC, AP public pages
  6. The Hindu, Indian Express

Features:
  - Automatic fallback chain (RSS → DDG → direct official sites)
  - Source trust-score whitelist
  - Retry logic with exponential back-off
  - In-process LRU cache (TTL 5 min) to avoid duplicate network calls
  - Parallel queries via ThreadPoolExecutor
  - Deduplication by URL
  - Publication-date extraction for freshness scoring
  - URL article-text extraction (for URL-input mode)
  - Graceful error handling — never crashes

AI Fake News Detection & Live Verification System — Version 3
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

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

_REQUEST_TIMEOUT   = 10   # seconds per HTTP call
_MAX_PER_QUERY     = 8    # results kept per search query
_MAX_TOTAL         = 30   # hard cap on all results before dedup
_CACHE_TTL         = 300  # seconds — cache lives 5 minutes
_MAX_RETRIES       = 2    # retry attempts on transient failures
_RETRY_DELAY       = 1.0  # base back-off delay (seconds)
_PARALLEL_WORKERS  = 4    # thread-pool size for parallel queries

# ── Source Trust-Score Whitelist ──────────────────────────────────────────────
# Score range 0–100.  Anything NOT in this table is ignored (score = 0).

TRUSTED_SOURCES: dict[str, tuple[str, int]] = {
    # Government / Official (100)
    "pib.gov.in":              ("PIB — Press Information Bureau", 100),
    "pib.nic.in":              ("PIB — Press Information Bureau", 100),
    "who.int":                 ("World Health Organization",       100),
    "un.org":                  ("United Nations",                  100),
    "mohfw.gov.in":            ("Ministry of Health India",        100),
    "mea.gov.in":              ("Ministry of External Affairs",    100),
    "isro.gov.in":             ("ISRO",                           100),
    "rbi.org.in":              ("Reserve Bank of India",           100),
    "eci.gov.in":              ("Election Commission of India",    100),
    "gov.in":                  ("Government of India",             100),
    "nic.in":                  ("Government of India (NIC)",       100),
    "india.gov.in":            ("India.gov.in — National Portal",  100),
    "sebi.gov.in":             ("SEBI",                           100),
    "icmr.gov.in":             ("ICMR",                           100),
    "mohfw.nic.in":            ("Ministry of Health (NIC)",        100),
    # International wire / broadcast (97–98)
    "reuters.com":             ("Reuters",                         98),
    "apnews.com":              ("Associated Press",                98),
    "bbc.com":                 ("BBC News",                        97),
    "bbc.co.uk":               ("BBC News",                        97),
    "aljazeera.com":           ("Al Jazeera",                      95),
    "theguardian.com":         ("The Guardian",                    95),
    "nytimes.com":             ("The New York Times",              95),
    # Indian trusted press (94–95)
    "thehindu.com":            ("The Hindu",                       95),
    "indianexpress.com":       ("Indian Express",                  94),
    "ndtv.com":                ("NDTV",                            93),
    "hindustantimes.com":      ("Hindustan Times",                 93),
    "theprint.in":             ("The Print",                       92),
    "scroll.in":               ("Scroll.in",                       91),
    "thewire.in":              ("The Wire",                        91),
    "livemint.com":            ("Mint",                            92),
    "business-standard.com":  ("Business Standard",               91),
    "timesofindia.com":        ("Times of India",                  90),
    "economictimes.indiatimes.com": ("Economic Times",            90),
    # Fact-check (97–99)
    "factcheck.org":           ("FactCheck.org",                   99),
    "snopes.com":              ("Snopes",                          97),
    "boomlive.in":             ("Boom Live",                       97),
    "vishvasnews.com":         ("Vishvas News",                    96),
    "altnews.in":              ("AltNews",                         97),
    "factly.in":               ("Factly India",                    96),
    "thequint.com":            ("The Quint",                       90),
    "politifact.com":          ("PolitiFact",                      97),
}

FACT_CHECK_DOMAINS: frozenset[str] = frozenset({
    "factcheck.org", "snopes.com", "boomlive.in",
    "vishvasnews.com", "altnews.in", "factly.in",
    "thequint.com", "politifact.com",
})

CONTRADICTION_KEYWORDS: tuple[str, ...] = (
    "fake", "false", "misinformation", "debunked", "myth", "hoax",
    "misleading", "untrue", "disproven", "fabricated", "rumour", "rumor",
    "fact check", "fact-check", "not true", "no evidence", "unverified",
    "claims false", "claim false", "baseless", "doctored", "manipulated",
)

SUPPORT_KEYWORDS: tuple[str, ...] = (
    "confirmed", "verified", "true", "officially", "announced",
    "launches", "approves", "signs", "publishes", "releases", "declares",
    "study shows", "research finds", "report says", "according to",
    "press release", "statement", "official", "ministry confirms",
)

# ── Simple LRU Cache with TTL ─────────────────────────────────────────────────

class _TTLCache:
    """Thread-safe key→value store with per-entry TTL."""

    def __init__(self, ttl: int = _CACHE_TTL, maxsize: int = 256) -> None:
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
                # Evict oldest entry
                oldest = min(self._store, key=lambda k: self._store[k][1])
                del self._store[oldest]
            self._store[key] = (value, time.monotonic())


_cache = _TTLCache()

# ── Utility: Domain Extraction ────────────────────────────────────────────────

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
    """Return (readable_name, trust_score) for a domain, or ('', 0)."""
    for key, (name, score) in TRUSTED_SOURCES.items():
        if domain == key or domain.endswith("." + key):
            return name, score
    return domain.capitalize(), 0


def _is_fact_check(domain: str) -> bool:
    return any(
        domain == fc or domain.endswith("." + fc) for fc in FACT_CHECK_DOMAINS
    )


# ── Utility: HTTP Fetch with Retry ────────────────────────────────────────────

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; FakeNewsDetectorV3/3.0; "
        "+https://huggingface.co/spaces)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _fetch_url(
    url: str,
    timeout: int = _REQUEST_TIMEOUT,
    retries: int = _MAX_RETRIES,
) -> Optional[str]:
    """Fetch URL text with retry + exponential back-off. Returns None on failure."""
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=_HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                charset = "utf-8"
                ct = resp.headers.get_content_charset()
                if ct:
                    charset = ct
                return resp.read().decode(charset, errors="ignore")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt < retries:
                time.sleep(_RETRY_DELAY * (2 ** attempt))
                logger.debug("Retry %d for %s after: %s", attempt + 1, url, exc)
            else:
                logger.warning("Failed to fetch %s: %s", url, exc)
    return None


# ── Utility: HTML Text Extraction ─────────────────────────────────────────────

class _TextExtractor(HTMLParser):
    """Minimal HTML → plain-text extractor (no external deps)."""

    SKIP_TAGS = frozenset({"script", "style", "noscript", "header", "footer",
                           "nav", "aside", "form", "button", "meta", "link"})

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


def _html_to_text(html_str: str, max_chars: int = 4000) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(html.unescape(html_str))
    except Exception:
        pass
    return " ".join(parser.parts)[:max_chars]


# ── Date Extraction ───────────────────────────────────────────────────────────

_DATE_PATTERNS = [
    re.compile(r'<pubDate>(.*?)</pubDate>',                   re.DOTALL),
    re.compile(r'"datePublished"\s*:\s*"([^"]+)"'),
    re.compile(r'<meta[^>]+property="article:published_time"[^>]+content="([^"]+)"'),
    re.compile(r'<time[^>]+datetime="([^"]+)"'),
    re.compile(r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})\b', re.IGNORECASE),
    re.compile(r'\b(\d{4}-\d{2}-\d{2})\b'),
]


def _extract_date(raw: str) -> str:
    for pat in _DATE_PATTERNS:
        m = pat.search(raw)
        if m:
            d = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            return d[:30]
    return ""


# ── Search Engine 1: Google News RSS ─────────────────────────────────────────

def _google_news_rss(query: str, max_results: int = _MAX_PER_QUERY) -> list[dict]:
    encoded = urllib.parse.quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
    xml = _fetch_url(url)
    if not xml:
        return []

    results: list[dict] = []
    for m in re.finditer(r"<item>(.*?)</item>", xml, re.DOTALL):
        item = m.group(1)

        t = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>",  item, re.DOTALL)
        l = re.search(r"<link>(.*?)</link>",                               item, re.DOTALL)
        d = re.search(r"<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>", item, re.DOTALL)
        pub = re.search(r"<pubDate>(.*?)</pubDate>",                       item, re.DOTALL)

        if t and l:
            snippet = re.sub(r"<[^>]+>", "", d.group(1)).strip() if d else ""
            results.append({
                "title":   re.sub(r"<[^>]+>", "", t.group(1)).strip(),
                "url":     l.group(1).strip(),
                "snippet": snippet[:300],
                "date":    pub.group(1).strip() if pub else "",
                "source":  "google_rss",
            })
        if len(results) >= max_results:
            break
    return results


# ── Search Engine 2: DuckDuckGo Lite ─────────────────────────────────────────

def _duckduckgo_lite(query: str, max_results: int = _MAX_PER_QUERY) -> list[dict]:
    encoded = urllib.parse.quote_plus(query)
    url = f"https://lite.duckduckgo.com/lite/?q={encoded}"
    html_text = _fetch_url(url)
    if not html_text:
        return []

    results: list[dict] = []
    links   = re.findall(r'<a[^>]+class="result-link"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html_text, re.DOTALL | re.IGNORECASE)
    snips   = re.findall(r'<td[^>]+class="result-snippet"[^>]*>(.*?)</td>',               html_text, re.DOTALL | re.IGNORECASE)
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
    """Search PIB Fact Check portal — returns 0-3 results."""
    encoded = urllib.parse.quote_plus(query)
    url = f"https://pib.gov.in/Pressreleaseshare.aspx?PRID=0&Lang=3&q={encoded}"
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


# ── Claim-Based Query Builder ─────────────────────────────────────────────────

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
        queries.append("\"" + " ".join(keywords[:3]) + "\"")

    seen: set[str] = set()
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
    Returns merged results (capped at max_results).
    """
    cache_key = f"q:{query}:{max_results}"
    cached = _cache.get(cache_key)
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

    # Priority 2: DuckDuckGo (supplement / fallback)
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
    max_results_per_query: int = _MAX_PER_QUERY,
) -> list[dict]:
    """
    Run queries in parallel, merge & deduplicate by URL.
    Also appends PIB fact-check results for the first keyword query.
    """
    all_results: list[dict] = []
    seen_urls:   set[str]   = set()

    def _run(q: str) -> list[dict]:
        try:
            return _run_single_query(q, max_results_per_query)
        except Exception as exc:
            logger.warning("Query failed '%s': %s", q[:60], exc)
            return []

    with ThreadPoolExecutor(max_workers=_PARALLEL_WORKERS) as pool:
        futures = {pool.submit(_run, q): q for q in queries[:5]}
        for fut in as_completed(futures):
            for r in fut.result():
                if r["url"] not in seen_urls and len(all_results) < _MAX_TOTAL:
                    seen_urls.add(r["url"])
                    all_results.append(r)

    # Also try PIB fact-check using first query
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


# ── Article Text Extractor (for URL mode) ─────────────────────────────────────

def extract_article_text(url: str) -> dict:
    """
    Fetch a news article URL and extract its main text content.

    Returns
    -------
    dict with keys: text, title, date, domain, success, error
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
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    raw = _fetch_url(url, timeout=15, retries=1)
    if not raw:
        result["error"] = "Could not fetch the article. Check the URL or your network."
        return result

    # Title
    t = re.search(r"<title[^>]*>(.*?)</title>", raw, re.DOTALL | re.IGNORECASE)
    if t:
        result["title"] = re.sub(r"<[^>]+>", "", t.group(1)).strip()[:200]

    # Date
    result["date"] = _extract_date(raw)

    # Body text
    result["text"]    = _html_to_text(raw, max_chars=4000)
    result["success"] = bool(result["text"].strip())
    if not result["success"]:
        result["error"] = "Article text could not be extracted."

    _cache.set(cache_key, result)
    return result


# ── Evidence Classifier ───────────────────────────────────────────────────────

def _classify_result(result: dict, original_query: str) -> str:
    """Return 'supporting' | 'contradicting' | 'neutral'."""
    combined = (result.get("title", "") + " " + result.get("snippet", "")).lower()
    domain   = _extract_domain(result.get("url", ""))

    # Fact-check sites mentioning contradiction words → contradicting
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
    Filter to trusted sources, classify each, and compute weighted evidence score.

    Evidence Score convention
    -------------------------
    Positive  → more contradicting evidence  (FAKE signal)
    Negative  → more supporting evidence     (REAL signal)
    Range: [-1.0, +1.0]

    Trust Score
    -----------
    Weighted average of trust scores of contributing sources (0–100).
    """
    trusted_results: list[dict] = []

    for r in results:
        domain = _extract_domain(r.get("url", ""))
        if _is_trusted(domain):
            name, score = _trust_info(domain)
            r = {**r,                          # shallow copy
                 "source_name":  name,
                 "trust_score":  score,
                 "is_fact_check": _is_fact_check(domain),
                 "domain":       domain,
                 "classification": _classify_result(r, original_query)}
            trusted_results.append(r)

    supporting    = [r for r in trusted_results if r["classification"] == "supporting"]
    contradicting = [r for r in trusted_results if r["classification"] == "contradicting"]
    neutral       = [r for r in trusted_results if r["classification"] == "neutral"]

    total = len(trusted_results)

    if total == 0:
        evidence_score = 0.0
        avg_trust      = 0
    else:
        # Weight each result by its trust score
        con_w = sum(r["trust_score"] for r in contradicting)
        sup_w = sum(r["trust_score"] for r in supporting)
        total_w = sum(r["trust_score"] for r in trusted_results) or 1
        evidence_score = round((con_w - sup_w) / total_w, 4)
        avg_trust      = round(sum(r["trust_score"] for r in trusted_results) / total)

    # Evidence confidence: how strongly the sources agree
    if total == 0:
        evidence_confidence = 0
    else:
        majority = max(len(supporting), len(contradicting), len(neutral))
        evidence_confidence = int(min(95, 40 + (majority / total) * 55))

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
