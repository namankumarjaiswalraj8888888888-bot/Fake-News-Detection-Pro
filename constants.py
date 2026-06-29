"""
constants.py
============
All static data: trusted source whitelist, sample news, keyword banks,
sensationalism patterns, contradiction / support keywords, and fact-check
domain list.

Moved out of utils.py and search.py so both modules share one source of
truth and nothing is duplicated.

AI Fake News Detection & Live Verification System — Version 4
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar & Parmeshwar
"""

from __future__ import annotations

# ── Sample News ───────────────────────────────────────────────────────────────

SAMPLE_NEWS: dict[str, str] = {
    "✅ Real — ISRO Mission": (
        "ISRO successfully tests reusable launch vehicle for future space missions. "
        "The Indian Space Research Organisation conducted the landmark test from the "
        "Satish Dhawan Space Centre in Sriharikota. The mission paves the way for "
        "cost-effective launches in the coming decade, according to an official ISRO "
        "press release issued today."
    ),
    "❌ Fake — Microchip Vaccine": (
        "SHOCKING: Bill Gates admits he put microchips in COVID-19 vaccines to track "
        "the population worldwide! Secret documents LEAKED from WHO confirm global "
        "surveillance plan. Share before this is DELETED by mainstream media! "
        "The deep state and pharma lobby are suppressing this truth."
    ),
    "⚠️ Ambiguous — Miracle Cure": (
        "Scientists say drinking turmeric water every morning for 30 days completely "
        "reverses diabetes and cancer. This ancient remedy was suppressed by the pharma "
        "lobby for decades. 100% guaranteed results with no side effects whatsoever."
    ),
    "✅ Real — RBI Policy": (
        "Reserve Bank of India raises repo rate by 25 basis points to 6.75 percent "
        "to control inflation. The Monetary Policy Committee voted 5–1 in favour of "
        "the rate hike, according to an official RBI press release. Governor Shaktikanta "
        "Das announced the decision after the three-day MPC meeting."
    ),
    "❌ Fake — WhatsApp Hoax": (
        "URGENT: WhatsApp will start charging Rs 10 per message from next Monday! "
        "Forward this to all your contacts immediately to activate your free lifetime "
        "subscription before the deadline. Government has approved this new policy! "
        "Share before deleted!"
    ),
}

# ── Linguistic Signal Banks ───────────────────────────────────────────────────

FAKE_LINGUISTIC_SIGNALS: list[str] = [
    "secret", "hidden", "suppressed", "conspiracy", "government hiding",
    "they don't want you to know", "100 percent guaranteed", "100% guaranteed",
    "miracle cure", "shocking truth", "leaked documents", "aliens confirmed",
    "illuminati", "deep state", "anonymous sources", "unnamed sources",
    "confirms insider", "mainstream media won't tell", "doctors hate this",
    "one weird trick", "banned by", "censored by", "share before deleted",
    "wake up sheeple", "pharma lobby", "big pharma hiding",
    "suppressed by government", "secret treaty", "microchip", "tracking device",
    "mind control", "hollow earth", "moon landing fake", "flat earth proven",
    "share immediately", "forward this", "before it gets deleted",
    "what they don't want", "cover-up", "shadow government",
    "elites don't want", "they are hiding", "urgent forward",
]

REAL_LINGUISTIC_SIGNALS: list[str] = [
    "according to", "reported by", "study shows", "research indicates",
    "official statement", "government announces", "ministry confirms",
    "data shows", "statistics reveal", "survey finds", "trial results",
    "peer-reviewed", "published in", "clinical trial", "press release",
    "official spokesperson", "verified by", "confirmed by", "sources say",
    "as per report", "audit reveals", "commission recommends",
    "parliament passed", "supreme court", "high court", "rbi announces",
    "isro confirms", "who statement", "un report", "official data",
    "government data", "ministry of", "department of", "official release",
]

SENSATIONALISM_PATTERNS: list[str] = [
    r"\b(shocking|explosive|bombshell|unbelievable|mind-blowing|terrifying)\b",
    r"\b(100\s*%|guaranteed|completely|absolutely)\b",
    r"!!+",
    r"\b(urgent|breaking|alert|must\s+read|viral)\b",
    r"[A-Z]{5,}",
    r"\b(secret|hidden|suppressed|leaked|banned)\b",
    r"\b(they|government|elites?)\s+(are\s+)?(hiding|suppressing|don't\s+want)\b",
]

# ── Evidence Keywords ─────────────────────────────────────────────────────────

CONTRADICTION_KEYWORDS: tuple[str, ...] = (
    "fake", "false", "misinformation", "debunked", "myth", "hoax",
    "misleading", "untrue", "disproven", "fabricated", "rumour", "rumor",
    "fact check", "fact-check", "not true", "no evidence", "unverified",
    "claims false", "claim false", "baseless", "doctored", "manipulated",
    "no proof", "lacks evidence", "disputed", "misleads", "incorrect",
    "inaccurate", "wrong claim",
)

SUPPORT_KEYWORDS: tuple[str, ...] = (
    "confirmed", "verified", "true", "officially", "announced",
    "launches", "approves", "signs", "publishes", "releases", "declares",
    "study shows", "research finds", "report says", "according to",
    "press release", "statement", "official", "ministry confirms",
    "government confirms", "rbi confirms", "isro confirms",
)

# ── Trusted Source Whitelist ──────────────────────────────────────────────────
# Format: domain → (readable_name, trust_score_0_to_100)

TRUSTED_SOURCES: dict[str, tuple[str, int]] = {
    # Government / Official (100)
    "pib.gov.in":                     ("PIB — Press Information Bureau",    100),
    "pib.nic.in":                     ("PIB — Press Information Bureau",    100),
    "who.int":                        ("World Health Organization",          100),
    "un.org":                         ("United Nations",                     100),
    "mohfw.gov.in":                   ("Ministry of Health India",           100),
    "mea.gov.in":                     ("Ministry of External Affairs",       100),
    "isro.gov.in":                    ("ISRO",                               100),
    "rbi.org.in":                     ("Reserve Bank of India",              100),
    "eci.gov.in":                     ("Election Commission of India",       100),
    "gov.in":                         ("Government of India",                100),
    "nic.in":                         ("Government of India (NIC)",          100),
    "india.gov.in":                   ("India.gov.in — National Portal",     100),
    "sebi.gov.in":                    ("SEBI",                               100),
    "icmr.gov.in":                    ("ICMR",                               100),
    "mohfw.nic.in":                   ("Ministry of Health (NIC)",           100),
    "pfizer.com":                     ("Pfizer Inc.",                         85),
    "fda.gov":                        ("US Food and Drug Administration",    100),
    "cdc.gov":                        ("US Centers for Disease Control",     100),
    # International wire / broadcast (95–98)
    "reuters.com":                    ("Reuters",                             98),
    "apnews.com":                     ("Associated Press",                    98),
    "bbc.com":                        ("BBC News",                            97),
    "bbc.co.uk":                      ("BBC News",                            97),
    "aljazeera.com":                  ("Al Jazeera",                          95),
    "theguardian.com":                ("The Guardian",                        95),
    "nytimes.com":                    ("The New York Times",                  95),
    "washingtonpost.com":             ("The Washington Post",                 94),
    # Indian trusted press (90–95)
    "thehindu.com":                   ("The Hindu",                           95),
    "indianexpress.com":              ("Indian Express",                      94),
    "ndtv.com":                       ("NDTV",                                93),
    "hindustantimes.com":             ("Hindustan Times",                     93),
    "theprint.in":                    ("The Print",                           92),
    "scroll.in":                      ("Scroll.in",                           91),
    "thewire.in":                     ("The Wire",                            91),
    "livemint.com":                   ("Mint",                                92),
    "business-standard.com":          ("Business Standard",                   91),
    "timesofindia.com":               ("Times of India",                      90),
    "economictimes.indiatimes.com":   ("Economic Times",                      90),
    "theweek.in":                     ("The Week India",                      88),
    "outlookindia.com":               ("Outlook India",                       88),
    "tribuneindia.com":               ("The Tribune India",                   87),
    # International business / science (88–93)
    "ft.com":                         ("Financial Times",                     93),
    "bloomberg.com":                  ("Bloomberg",                           92),
    "nature.com":                     ("Nature",                              95),
    "science.org":                    ("Science Magazine",                    95),
    "thelancet.com":                  ("The Lancet",                          95),
    "bmj.com":                        ("BMJ",                                 95),
    # Fact-check sites (96–99)
    "factcheck.org":                  ("FactCheck.org",                       99),
    "snopes.com":                     ("Snopes",                              97),
    "boomlive.in":                    ("Boom Live",                           97),
    "vishvasnews.com":                ("Vishvas News",                        96),
    "altnews.in":                     ("AltNews",                             97),
    "factly.in":                      ("Factly India",                        96),
    "thequint.com":                   ("The Quint",                           90),
    "politifact.com":                 ("PolitiFact",                          97),
    "fullfact.org":                   ("Full Fact",                           97),
    "africa-check.org":               ("Africa Check",                        95),
}

FACT_CHECK_DOMAINS: frozenset[str] = frozenset({
    "factcheck.org", "snopes.com", "boomlive.in",
    "vishvasnews.com", "altnews.in", "factly.in",
    "thequint.com", "politifact.com", "fullfact.org",
    "africa-check.org",
})

# ── Stopwords for keyword extraction ─────────────────────────────────────────

STOPWORDS: frozenset[str] = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "has", "have", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "this", "that", "these", "those",
    "it", "its", "as", "if", "then", "than", "so", "not", "no", "also",
    "according", "says", "said", "report", "reports", "reported",
    "very", "just", "even", "only", "more", "most", "some", "any",
    "which", "who", "what", "when", "where", "how", "they", "them",
    "their", "we", "our", "you", "your", "he", "she", "his", "her",
    "after", "before", "during", "since", "while", "about", "over",
    "under", "between", "among", "through", "against", "into", "onto",
    "upon", "now", "then", "here", "there", "all", "each", "every",
    "both", "few", "many", "much", "other", "another", "such", "own",
    "same", "too", "very", "can", "cannot", "one", "two", "three",
})
