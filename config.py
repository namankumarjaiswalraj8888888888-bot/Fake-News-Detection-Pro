"""
config.py
=========
Central configuration for AI Fake News Detection & Live Verification System.

All tunable parameters live here. Change this file to adjust behaviour
without touching pipeline or UI code.

AI Fake News Detection & Live Verification System — Version 4
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar & Parmeshwar
"""

from __future__ import annotations


# ── Application Metadata ──────────────────────────────────────────────────────

APP_TITLE      = "AI Fake News Detection & Live Verification"
APP_VERSION    = "4.0"
APP_TAGLINE    = "Multi-source · Machine Learning · Evidence-based analysis"
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

SEARCH_REQUEST_TIMEOUT   : int   = 10      # seconds per HTTP call
SEARCH_MAX_PER_QUERY     : int   = 8       # results kept per query
SEARCH_MAX_TOTAL         : int   = 30      # hard cap before dedup
SEARCH_CACHE_TTL         : int   = 300     # 5 minutes
SEARCH_MAX_RETRIES       : int   = 2
SEARCH_RETRY_DELAY       : float = 1.0     # base back-off (seconds)
SEARCH_PARALLEL_WORKERS  : int   = 4
SEARCH_MAX_QUERIES       : int   = 5       # max queries per check


# ── Text Processing ───────────────────────────────────────────────────────────

TEXT_MAX_LENGTH          : int   = 5000    # truncate input at this length
TEXT_MIN_LENGTH          : int   = 5       # reject shorter inputs
KEYWORDS_TOP_N           : int   = 8       # keywords extracted per article
CLAIMS_MAX               : int   = 5       # max factual claims extracted


# ── ML Model ─────────────────────────────────────────────────────────────────

MODEL_FILE               : str   = "model.pkl"
VECTORIZER_FILE          : str   = "vectorizer.pkl"
MODEL_NAME_FILE          : str   = "model_name.txt"
ML_CONF_FLOOR            : int   = 30      # min ML confidence reported (%)
ML_CONF_CEILING          : int   = 97      # max ML confidence reported (%)
ML_CONF_GATE             : float = 0.60    # min prob before full directional weight


# ── Decision Engine Weights ───────────────────────────────────────────────────

WEIGHT_ML                : float = 0.45
WEIGHT_EVIDENCE          : float = 0.35
WEIGHT_LINGUISTIC        : float = 0.20

# When no evidence is available:
WEIGHT_ML_NO_EV          : float = 0.45
WEIGHT_LINGUISTIC_NO_EV  : float = 0.55

# Verdict thresholds (combined_score)
FAKE_THRESHOLD           : float = 0.22    # score ≥ this → FAKE
REAL_THRESHOLD           : float = -0.15   # score ≤ this → REAL


# ── Confidence Calibration ────────────────────────────────────────────────────

CONF_HIGH_FLOOR          : int   = 80      # ≥ this → "High confidence"
CONF_MEDIUM_FLOOR        : int   = 60      # ≥ this → "Moderate confidence"
CONF_OVERALL_FLOOR       : int   = 30
CONF_OVERALL_CEILING     : int   = 97
CONF_EV_BASE             : int   = 40      # base evidence confidence
CONF_EV_WEIGHT           : float = 55.0    # evidence confidence scaling


# ── Article Extractor ─────────────────────────────────────────────────────────

ARTICLE_FETCH_TIMEOUT    : int   = 15
ARTICLE_FETCH_RETRIES    : int   = 1
ARTICLE_MAX_CHARS        : int   = 4000
ARTICLE_MIN_LENGTH       : int   = 30      # reject shorter extracted text


# ── Export ────────────────────────────────────────────────────────────────────

EXPORT_PDF_FONT          : str   = "Helvetica"
EXPORT_MAX_HISTORY       : int   = 20      # keep last N checks in session


# ── Gradio Server ─────────────────────────────────────────────────────────────

SERVER_HOST              : str   = "0.0.0.0"
SERVER_PORT              : int   = 7860
SERVER_SHARE             : bool  = False
SERVER_SHOW_ERROR        : bool  = True
