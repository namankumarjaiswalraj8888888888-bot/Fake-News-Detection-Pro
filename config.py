"""
config.py
=========
Version 5 — Central configuration for AI Fake News Detection System.

Changes from V4
---------------
- APP_VERSION bumped to 5.0
- WEIGHT_ML reduced 0.45 → 0.30 (was overriding evidence on REAL news)
- WEIGHT_EVIDENCE raised 0.35 → 0.50 (trusted sources > ML alone)
- WEIGHT_LINGUISTIC kept 0.20
- WEIGHT_ML_NO_EV / WEIGHT_LINGUISTIC_NO_EV kept (already correct)
- FAKE_THRESHOLD / REAL_THRESHOLD replaced by 9-verdict table (see below)
- EXPORT_MAX_HISTORY raised 20 → 100
- CONF_EV_BASE / CONF_EV_WEIGHT moved here from search.py inline use
  (search.py V4 used them without importing — NameError fixed)
- Added V5 9-VERDICT_THRESHOLDS dict for make_final_decision()
- Added FACTCHECK_BOOST (additive boost when fact-check site says FAKE)
- Added SPAM_FILTER_ENABLED flag

AI Fake News Detection & Live Verification System — Version 5
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar, Parmeshwar Kumar, Amit Kumar,
              Prince Kumar Chaurasiya, Dhiraj Kumar, MD. Tausim Akhtar
"""

from __future__ import annotations


# ── Application Metadata ──────────────────────────────────────────────────────

APP_TITLE      = "AI Fake News Detection & Live Verification"
APP_VERSION    = "5.0"
APP_TAGLINE    = "9-Verdict System · Multi-source Evidence · ML Classification"
INSTITUTION    = "Government Polytechnic West Champaran"
DEPARTMENT     = "Department of Computer Science & Engineering"
BOARD          = "SBTE Bihar · Diploma Engineering · Session 2025–2028"
INTERNSHIP     = "AI & ML Internship 2026"
COPYRIGHT_YEAR = "2026"

DEVELOPERS: list[dict] = [
    {
        "name":   "Naman Kumar",
        "role":   "Full Stack AI Developer · UI/UX Designer",
        "badge":  "Project Lead",
        "avatar": "NK",
    },
    {
        "name":   "Parmeshwar Kumar",
        "role":   "Backend Developer · API Integration",
        "badge":  "Backend",
        "avatar": "PK",
    },
    {
        "name":   "Amit Kumar",
        "role":   "ML Engineer · Dataset & Model Training",
        "badge":  "ML / AI",
        "avatar": "AK",
    },
    {
        "name":   "Prince Kumar Chaurasiya",
        "role":   "Research & Documentation Lead",
        "badge":  "Research",
        "avatar": "PC",
    },
    {
        "name":   "Dhiraj Kumar",
        "role":   "QA Engineer · Performance Testing",
        "badge":  "QA",
        "avatar": "DK",
    },
    {
        "name":   "MD. Tausim Akhtar",
        "role":   "AI Research Contributor",
        "badge":  "Research",
        "avatar": "MT",
    },
]


# ── Search Configuration ──────────────────────────────────────────────────────

SEARCH_REQUEST_TIMEOUT   : int   = 10
SEARCH_MAX_PER_QUERY     : int   = 8
SEARCH_MAX_TOTAL         : int   = 40
SEARCH_CACHE_TTL         : int   = 300     # 5 minutes
SEARCH_MAX_RETRIES       : int   = 2
SEARCH_RETRY_DELAY       : float = 1.0
SEARCH_PARALLEL_WORKERS  : int   = 4
SEARCH_MAX_QUERIES       : int   = 5


# ── Text Processing ───────────────────────────────────────────────────────────

TEXT_MAX_LENGTH          : int   = 5000
TEXT_MIN_LENGTH          : int   = 5
KEYWORDS_TOP_N           : int   = 8
CLAIMS_MAX               : int   = 5


# ── ML Model ─────────────────────────────────────────────────────────────────

MODEL_FILE               : str   = "model.pkl"
VECTORIZER_FILE          : str   = "vectorizer.pkl"
MODEL_NAME_FILE          : str   = "model_name.txt"
ML_CONF_FLOOR            : int   = 30
ML_CONF_CEILING          : int   = 97
ML_CONF_GATE             : float = 0.60    # quadratic roll-off below this


# ── Decision Engine Weights (V5) ──────────────────────────────────────────────
# BUG FIX: V4 had WEIGHT_ML=0.45 which overrode evidence on REAL news.
# V5 reduces ML weight and trusts trusted-source evidence more.

WEIGHT_ML                : float = 0.30    # was 0.45 in V4
WEIGHT_EVIDENCE          : float = 0.50    # was 0.35 in V4
WEIGHT_LINGUISTIC        : float = 0.20    # unchanged
# Sum = 1.00 ✓

# No-evidence fallback weights (when ev_sources == 0)
WEIGHT_ML_NO_EV          : float = 0.55
WEIGHT_LINGUISTIC_NO_EV  : float = 0.45
# Sum = 1.00 ✓

# Additive boost when a fact-check site explicitly says FAKE
FACTCHECK_BOOST          : float = 0.18

# V5 Nine-Verdict Thresholds
# combined_score ∈ [-1.0, +1.0]
# Positive → FAKE signal; Negative → REAL signal
#
# Format: { verdict: (lower_inclusive, upper_exclusive) }
# Two tables: one when evidence exists, one when it doesn't.

VERDICT_THRESHOLDS_WITH_EVIDENCE: list[tuple[str, float, float]] = [
    # verdict,             lower,  upper
    ("REAL",              -2.0,  -0.50),
    ("LIKELY REAL",       -0.50, -0.22),
    ("PARTIALLY TRUE",    -0.22, -0.08),
    ("UNVERIFIED",        -0.08,  0.08),
    ("MIXED",              0.08,  0.20),
    ("MISLEADING",         0.20,  0.36),
    ("LIKELY FAKE",        0.36,  0.58),
    ("FAKE",               0.58,  2.0),
]

VERDICT_THRESHOLDS_NO_EVIDENCE: list[tuple[str, float, float]] = [
    ("LIKELY REAL",            -2.0,  -0.38),
    ("INSUFFICIENT EVIDENCE",  -0.38,  0.10),
    ("LIKELY FAKE",             0.10,  2.0),
]


# ── Confidence Calibration ────────────────────────────────────────────────────

CONF_HIGH_FLOOR          : int   = 80
CONF_MEDIUM_FLOOR        : int   = 60
CONF_OVERALL_FLOOR       : int   = 30
CONF_OVERALL_CEILING     : int   = 97
# BUG FIX: CONF_EV_BASE / CONF_EV_WEIGHT were used in search.py but never
# imported there — caused NameError at runtime. Now centrally defined and
# explicitly imported by search.py.
CONF_EV_BASE             : int   = 40
CONF_EV_WEIGHT           : float = 55.0


# ── Article Extractor ─────────────────────────────────────────────────────────

ARTICLE_FETCH_TIMEOUT    : int   = 15
ARTICLE_FETCH_RETRIES    : int   = 1
ARTICLE_MAX_CHARS        : int   = 4000
ARTICLE_MIN_LENGTH       : int   = 30


# ── Feature Flags ─────────────────────────────────────────────────────────────

SPAM_FILTER_ENABLED      : bool  = True    # block known spam/misinformation domains
AI_BLOG_FILTER_ENABLED   : bool  = True    # skip AI-generated blog posts
CLICKBAIT_FILTER_ENABLED : bool  = True    # skip pure-clickbait titles


# ── Export & History ──────────────────────────────────────────────────────────

EXPORT_PDF_FONT          : str   = "Helvetica"
EXPORT_MAX_HISTORY       : int   = 100     # was 20 in V4


# ── Gradio Server ─────────────────────────────────────────────────────────────

SERVER_HOST              : str   = "0.0.0.0"
SERVER_PORT              : int   = 7860
SERVER_SHARE             : bool  = False
SERVER_SHOW_ERROR        : bool  = True
