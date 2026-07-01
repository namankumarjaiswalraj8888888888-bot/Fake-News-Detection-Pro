"""
constants.py
============
Version 5 — Centralised static data for the entire project.

Changes from V4
---------------
- Added VERDICT_META: 9-verdict definitions with color, icon, description
- Added SPAM_DOMAINS: 30+ known misinformation / clickbait domains
- Added AI_BLOG_SIGNALS: patterns that identify AI-generated junk content
- Added CLICKBAIT_PATTERNS: regex patterns for clickbait title detection
- Extended TRUSTED_SOURCES with 12 more high-quality domains
- Extended FAKE_LINGUISTIC_SIGNALS and REAL_LINGUISTIC_SIGNALS
- Added SAMPLE_NEWS entry for URL mode demonstration

AI Fake News Detection & Live Verification System — Version 5
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar, Parmeshwar Kumar, Amit Kumar,
              Prince Kumar Chaurasiya, Dhiraj Kumar, MD. Tausim Akhtar
"""

from __future__ import annotations

import re


# ── Keyword Matching Helper ───────────────────────────────────────────────────
# BUG FIX V5.1: every keyword/phrase list below (FAKE_LINGUISTIC_SIGNALS,
# REAL_LINGUISTIC_SIGNALS, CONTRADICTION_KEYWORDS, SUPPORT_KEYWORDS) used to be
# matched with plain substring checks (`if kw in text`). This meant short
# keywords could silently false-trigger inside unrelated longer words —
# e.g. "myth" (a contradiction keyword) matches inside "mythology" or
# "myth-busting", and "isro" (a real-news signal) matches inside "misrouted".
# A genuinely unrelated article about Indian mythology could get wrongly
# classified as contradicting a claim, polluting the evidence score.
#
# Fix: every keyword is now wrapped in \b...\b word-boundary regex, so it only
# matches whole words/phrases, never as a substring of something longer.
# Multi-word phrases (e.g. "share before deleted") still work correctly since
# \b applies at the start of the first word and the end of the last word.
def compile_keyword_patterns(keywords) -> list[tuple[str, re.Pattern]]:
    """
    Compile a list of keyword/phrase strings into (keyword, word-boundary
    regex pattern) pairs, case-insensitive. Returned patterns should be
    matched with `pattern.search(text)`, not `keyword in text`.
    """
    return [
        (kw, re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE))
        for kw in keywords
    ]


def find_keyword_hits(text: str, compiled_patterns: list[tuple[str, re.Pattern]]) -> list[str]:
    """Return the list of original keyword strings whose pattern matched text."""
    return [kw for kw, pat in compiled_patterns if pat.search(text)]


# ── Nine-Verdict Metadata ─────────────────────────────────────────────────────
# Used by utils.py (decision engine) and app.py (HTML renderer).

VERDICT_META: dict[str, dict] = {
    "REAL": {
        "icon":        "✅",
        "label":       "REAL NEWS",
        "color":       "#059669",
        "bg":          "rgba(5,150,105,0.08)",
        "border":      "rgba(5,150,105,0.30)",
        "bar_cls":     "real",
        "description": "Verified by multiple trusted sources and ML model.",
        "css_class":   "fnd-verdict-real",
    },
    "LIKELY REAL": {
        "icon":        "🟢",
        "label":       "LIKELY REAL",
        "color":       "#10b981",
        "bg":          "rgba(16,185,129,0.08)",
        "border":      "rgba(16,185,129,0.25)",
        "bar_cls":     "likely-real",
        "description": "Strong indicators of genuine news; minor evidence gaps.",
        "css_class":   "fnd-verdict-likely-real",
    },
    "PARTIALLY TRUE": {
        "icon":        "🔵",
        "label":       "PARTIALLY TRUE",
        "color":       "#0891b2",
        "bg":          "rgba(8,145,178,0.08)",
        "border":      "rgba(8,145,178,0.25)",
        "bar_cls":     "partial",
        "description": "Contains factual elements but also inaccuracies or missing context.",
        "css_class":   "fnd-verdict-partial",
    },
    "UNVERIFIED": {
        "icon":        "⚠️",
        "label":       "UNVERIFIED",
        "color":       "#eab308",
        "bg":          "rgba(234,179,8,0.08)",
        "border":      "rgba(234,179,8,0.25)",
        "bar_cls":     "unv",
        "description": "Insufficient evidence for a definitive verdict. Verify manually.",
        "css_class":   "fnd-verdict-unv",
    },
    "INSUFFICIENT EVIDENCE": {
        "icon":        "❓",
        "label":       "INSUFFICIENT EVIDENCE",
        "color":       "#94a3b8",
        "bg":          "rgba(148,163,184,0.08)",
        "border":      "rgba(148,163,184,0.25)",
        "bar_cls":     "insuff",
        "description": "No trusted sources found. Cannot verify or refute this claim.",
        "css_class":   "fnd-verdict-insuff",
    },
    "MIXED": {
        "icon":        "🟡",
        "label":       "MIXED",
        "color":       "#d97706",
        "bg":          "rgba(217,119,6,0.08)",
        "border":      "rgba(217,119,6,0.25)",
        "bar_cls":     "mixed",
        "description": "Conflicting evidence found. Contains both true and false elements.",
        "css_class":   "fnd-verdict-mixed",
    },
    "MISLEADING": {
        "icon":        "🟠",
        "label":       "MISLEADING",
        "color":       "#ea580c",
        "bg":          "rgba(234,88,12,0.08)",
        "border":      "rgba(234,88,12,0.25)",
        "bar_cls":     "misleading",
        "description": "Technically factual but framed to create false impressions.",
        "css_class":   "fnd-verdict-misleading",
    },
    "LIKELY FAKE": {
        "icon":        "🔴",
        "label":       "LIKELY FAKE",
        "color":       "#dc6803",
        "bg":          "rgba(220,104,3,0.08)",
        "border":      "rgba(220,104,3,0.25)",
        "bar_cls":     "likely-fake",
        "description": "Strong indicators of misinformation. Treat with high suspicion.",
        "css_class":   "fnd-verdict-likely-fake",
    },
    "FAKE": {
        "icon":        "❌",
        "label":       "FAKE NEWS",
        "color":       "#dc2626",
        "bg":          "rgba(220,38,38,0.08)",
        "border":      "rgba(220,38,38,0.30)",
        "bar_cls":     "fake",
        "description": "Identified as false or fabricated by trusted sources and ML.",
        "css_class":   "fnd-verdict-fake",
    },
}


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
    # Conspiracy markers
    "secret", "hidden", "suppressed", "conspiracy", "government hiding",
    "they don't want you to know", "deep state", "shadow government",
    "illuminati", "new world order", "cover-up", "coverup",
    # Medical misinformation
    "100 percent guaranteed", "100% guaranteed", "miracle cure",
    "doctors hate this", "one weird trick", "pharma lobby", "big pharma hiding",
    "suppressed by government", "ancient remedy", "no side effects",
    "cures cancer", "cures diabetes", "reverses diabetes",
    # Urgency / sharing manipulation
    "share before deleted", "share immediately", "forward this",
    "before it gets deleted", "before they delete", "act now",
    "urgent forward", "must share", "share now",
    # Sourcing red flags
    "leaked documents", "anonymous sources", "unnamed sources",
    "confirms insider", "mainstream media won't tell",
    "banned by", "censored by", "suppressed by",
    "wake up sheeple", "wake up people",
    # Pseudoscience
    "aliens confirmed", "microchip", "tracking device", "mind control",
    "hollow earth", "moon landing fake", "flat earth proven",
    # Conspiracy amplifiers
    "elites don't want", "they are hiding", "what they don't want",
    "explosive revelation", "bombshell truth",
]

REAL_LINGUISTIC_SIGNALS: list[str] = [
    # Attribution
    "according to", "reported by", "as per", "citing",
    # Official sourcing
    "official statement", "government announces", "ministry confirms",
    "parliament passed", "supreme court", "high court",
    "rbi announces", "isro confirms", "who statement", "un report",
    "press release", "official spokesperson", "official release",
    "ministry of", "department of",
    # Evidence-based language
    "study shows", "research indicates", "data shows", "statistics reveal",
    "survey finds", "trial results", "peer-reviewed", "published in",
    "clinical trial", "audit reveals", "commission recommends",
    # Verification markers
    "verified by", "confirmed by", "fact-checked", "investigation found",
    "evidence suggests", "analysis shows",
    # Named institutional sources
    "reserve bank of india", "election commission", "supreme court of india",
    "ministry of health", "isro", "nasa", "who confirmed",
]

# Pre-compiled word-boundary patterns — see compile_keyword_patterns() docstring
# above for why plain substring matching (`kw in text`) was unsafe.
FAKE_LINGUISTIC_SIGNALS_COMPILED = compile_keyword_patterns(FAKE_LINGUISTIC_SIGNALS)
REAL_LINGUISTIC_SIGNALS_COMPILED = compile_keyword_patterns(REAL_LINGUISTIC_SIGNALS)

SENSATIONALISM_PATTERNS: list[str] = [
    r"\b(shocking|explosive|bombshell|unbelievable|mind-blowing|terrifying)\b",
    r"\b(100\s*%|guaranteed|completely|absolutely)\b",
    r"!!+",
    r"\b(urgent|breaking|alert|must\s+read|viral)\b",
    r"\b(secret|hidden|suppressed|leaked|banned)\b",
    r"\b(they|government|elites?)\s+(are\s+)?(hiding|suppressing|don't\s+want)\b",
    r"\b(share|forward)\s+(before|now|immediately)\b",
]

# Compiled regex for performance — these are matched case-insensitively against
# already-lowercased text (so "SHOCKING" and "shocking" both match the same way).
_SENSATIONALISM_COMPILED: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE) for p in SENSATIONALISM_PATTERNS
]

# ── ALL-CAPS "Shouting" Detection ─────────────────────────────────────────────
# BUG FIX V5.1: this used to live inside SENSATIONALISM_PATTERNS as r"[A-Z]{5,}"
# compiled with re.IGNORECASE — but analyze_linguistic_signals() in utils.py
# evaluates patterns against text.lower(), so an IGNORECASE [A-Z]{5,} pattern
# could never see real uppercase letters and instead matched ANY word of 5+
# letters (case-insensitively), wrongly flagging ordinary text like
# "successfully", "missions", "government" as "sensationalism".
#
# Fix: keep caps-detection as its own pattern, compiled WITHOUT IGNORECASE,
# and always run it against the ORIGINAL-CASE text (never lowercased).
# A real run of 5+ consecutive uppercase letters (e.g. "URGENT", "SHOCKING")
# is a genuine shouting signal; a long lowercase word is not.
CAPS_SHOUTING_PATTERN: re.Pattern = re.compile(r"\b[A-Z]{5,}\b")


# ── Clickbait Patterns ────────────────────────────────────────────────────────
# Applied to article titles before including in evidence.

CLICKBAIT_PATTERNS_RAW: list[str] = [
    r"you won.t believe",
    r"what happened next",
    r"this one (trick|thing|hack)",
    r"doctors (hate|don.t want)",
    r"(share|forward) before (they|it gets?) delet",
    r"mainstream media (won.t|doesn.t)",
    r"they don.t want you to know",
    r"wake up sheeple",
    r"^\s*#\w+(\s+#\w+){3,}",     # hashtag spam as "article title"
]

CLICKBAIT_COMPILED: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE) for p in CLICKBAIT_PATTERNS_RAW
]


# ── AI-Blog Detection Signals ─────────────────────────────────────────────────
# These phrases often appear in low-quality AI-generated listicles.

AI_BLOG_SIGNALS: list[str] = [
    "in this article, we will",
    "let's explore",
    "as an ai language model",
    "i am an ai",
    "as of my knowledge cutoff",
    "table of contents",
    "frequently asked questions",
    "in conclusion,",
    "in this blog post",
    "in summary,",
    "to summarize,",
    "key takeaways",
    "final thoughts",
]


# ── Spam / Misinformation Domain Blocklist ────────────────────────────────────
# URLs from these domains are rejected before any trusted-source check.

SPAM_DOMAINS: frozenset[str] = frozenset({
    # Known satire / parody sites
    "theonion.com", "clickhole.com", "babylonbee.com",
    # Known fake-news factories
    "worldnewsdailyreport.com", "empirenews.net", "nationalreport.net",
    "huzlers.com", "abcnews.com.co", "cbsnews.com.co",
    "usatoday.com.co", "nbc.com.co", "newslo.com",
    "newswatch33.com", "politicops.com",
    # Health / pseudoscience misinformation
    "naturalnews.com",
    # Conspiracy / extreme bias
    "infowars.com", "zerohedge.com", "beforeitsnews.com",
    "whatdoesitmean.com", "yournewswire.com", "newspunch.com",
    "neonnettle.com", "thegatewaypundit.com",
    # State-controlled / heavily biased
    "rt.com", "sputniknews.com",
    # Clickbait farms
    "buzzfeed.com",   # allowed for pop culture; blocked here for news
})


# ── Trusted Source Whitelist ──────────────────────────────────────────────────
# Format: domain → (readable_name, trust_score_0_to_100)

TRUSTED_SOURCES: dict[str, tuple[str, int]] = {
    # ── Indian Government / Official (100) ──────────────────────────────────
    "pib.gov.in":                     ("PIB — Press Information Bureau",    100),
    "pib.nic.in":                     ("PIB — Press Information Bureau",    100),
    "mohfw.gov.in":                   ("Ministry of Health India",           100),
    "mohfw.nic.in":                   ("Ministry of Health (NIC)",           100),
    "mea.gov.in":                     ("Ministry of External Affairs",       100),
    "isro.gov.in":                    ("ISRO",                               100),
    "rbi.org.in":                     ("Reserve Bank of India",              100),
    "eci.gov.in":                     ("Election Commission of India",       100),
    "sebi.gov.in":                    ("SEBI",                               100),
    "icmr.gov.in":                    ("ICMR",                               100),
    "gov.in":                         ("Government of India",                100),
    "nic.in":                         ("Government of India (NIC)",          100),
    "india.gov.in":                   ("India.gov.in — National Portal",     100),
    "mha.gov.in":                     ("Ministry of Home Affairs",           100),
    "pmindia.gov.in":                 ("Prime Minister's Office",            100),
    "rajyasabha.nic.in":              ("Rajya Sabha",                        100),
    "loksabha.nic.in":                ("Lok Sabha",                          100),
    "supremecourtofindia.nic.in":     ("Supreme Court of India",             100),
    "dst.gov.in":                     ("Dept. of Science & Technology",      100),
    "meity.gov.in":                   ("MeitY",                              100),
    # ── International Bodies (100) ──────────────────────────────────────────
    "who.int":                        ("World Health Organization",          100),
    "un.org":                         ("United Nations",                     100),
    "nasa.gov":                       ("NASA",                               100),
    "cdc.gov":                        ("US CDC",                             100),
    "fda.gov":                        ("US FDA",                             100),
    "nih.gov":                        ("US NIH",                             100),
    "iaea.org":                       ("IAEA",                               100),
    "worldbank.org":                  ("World Bank",                          98),
    "imf.org":                        ("IMF",                                 98),
    "oecd.org":                       ("OECD",                                97),
    # ── Wire Services (98) ──────────────────────────────────────────────────
    "reuters.com":                    ("Reuters",                             98),
    "apnews.com":                     ("Associated Press",                    98),
    "afp.com":                        ("Agence France-Presse",                97),
    # ── International Broadcast (94–97) ─────────────────────────────────────
    "bbc.com":                        ("BBC News",                            97),
    "bbc.co.uk":                      ("BBC News",                            97),
    "aljazeera.com":                  ("Al Jazeera",                          95),
    "theguardian.com":                ("The Guardian",                        95),
    "nytimes.com":                    ("The New York Times",                  95),
    "washingtonpost.com":             ("The Washington Post",                 94),
    "bloomberg.com":                  ("Bloomberg",                           94),
    "ft.com":                         ("Financial Times",                     94),
    "economist.com":                  ("The Economist",                       95),
    # ── Academic / Scientific (95–97) ───────────────────────────────────────
    "science.org":                    ("Science Magazine",                    96),
    "nature.com":                     ("Nature",                              97),
    "thelancet.com":                  ("The Lancet",                          97),
    "nejm.org":                       ("New England Journal of Medicine",     97),
    "bmj.com":                        ("BMJ",                                 95),
    # ── Indian Trusted Press (90–95) ────────────────────────────────────────
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
    "telegraphindia.com":             ("The Telegraph India",                 91),
    "deccanherald.com":               ("Deccan Herald",                       90),
    # ── Fact-Check Sites (96–99) ────────────────────────────────────────────
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
    "chequeado.com":                  ("Chequeado",                           95),
    # ── Pharmaceutical / Medical ─────────────────────────────────────────────
    "fda.gov":                        ("US Food and Drug Administration",    100),
}

FACT_CHECK_DOMAINS: frozenset[str] = frozenset({
    "factcheck.org", "snopes.com", "boomlive.in",
    "vishvasnews.com", "altnews.in", "factly.in",
    "thequint.com", "politifact.com", "fullfact.org",
    "africa-check.org", "chequeado.com",
})


# ── Evidence Keywords ─────────────────────────────────────────────────────────

CONTRADICTION_KEYWORDS: tuple[str, ...] = (
    "fake", "false", "misinformation", "debunked", "myth", "hoax",
    "misleading", "untrue", "disproven", "fabricated", "rumour", "rumor",
    "fact check", "fact-check", "not true", "no evidence", "unverified",
    "claims false", "claim false", "baseless", "doctored", "manipulated",
    "no proof", "lacks evidence", "disputed", "misleads", "incorrect",
    "inaccurate", "wrong claim", "satire", "parody", "fictional",
    "out of context", "misrepresented", "debunk",
)

SUPPORT_KEYWORDS: tuple[str, ...] = (
    "confirmed", "verified", "true", "officially", "announced",
    "launches", "approves", "signs", "publishes", "releases", "declares",
    "study shows", "research finds", "report says", "according to",
    "press release", "statement", "official", "ministry confirms",
    "government confirms", "rbi confirms", "isro confirms",
    "authenticated", "legitimate", "accurate",
)

# Pre-compiled word-boundary patterns — see compile_keyword_patterns() docstring
# near the top of this file for why plain substring matching (`kw in text`)
# was unsafe (e.g. "myth" matching inside "mythology").
CONTRADICTION_KEYWORDS_COMPILED = compile_keyword_patterns(CONTRADICTION_KEYWORDS)
SUPPORT_KEYWORDS_COMPILED       = compile_keyword_patterns(SUPPORT_KEYWORDS)


# ── Stopwords ────────────────────────────────────────────────────────────────

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
