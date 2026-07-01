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
APP_VERSION    = "5.1"
APP_TAGLINE    = "9-Verdict System · Live Evidence · ML Classification · Verified Facts"
INSTITUTION    = "Government Polytechnic West Champaran"
DEPARTMENT     = "Department of Computer Science & Engineering"
BOARD          = "SBTE Bihar · Diploma Engineering · Session 2025–2028"
INTERNSHIP     = "AI & ML Internship 2026"
COPYRIGHT_YEAR = "2026"

DEVELOPERS: list[dict] = [
    {
        "id":     "naman-kumar",
        "name":   "Naman Kumar",
        "role":   "Full Stack AI Developer · UI/UX Designer",
        "badge":  "Project Lead",
        "icon":   "compass",
        "bio": (
            "Project lead and primary architect of the AI Fake News Detection "
            "& Live Verification System. Naman designed the end-to-end "
            "verification pipeline — from the live-evidence search layer "
            "through the ML classifier to the 9-verdict scoring engine — and "
            "led the UI/UX direction for the full forensic-dossier interface, "
            "including the bilingual (English/Hindi) experience and the "
            "dark/light theming system. Drawn to projects that sit at the "
            "intersection of applied machine learning and interface design: "
            "building tools that don't just compute an answer, but make the "
            "reasoning behind it legible to the person using it."
        ),
        "skills": [
            "Python", "Gradio", "scikit-learn", "System Architecture",
            "UI/UX Design", "REST APIs", "Git/GitHub", "Product Thinking",
        ],
        "contributions": [
            "Designed the 9-verdict decision engine and confidence-weighting system",
            "Built the live multi-source evidence verification pipeline",
            "Led the full UI/UX redesign, including bilingual and dark/light theming",
            "Coordinated the team and owns the project roadmap",
        ],
        "quote": "A verdict only earns trust if you can see how it was reached.",
    },
    {
        "id":     "parmeshwar-kumar",
        "name":   "Parmeshwar Kumar",
        "role":   "Backend Developer · API Integration",
        "badge":  "Backend",
        "icon":   "server",
        "bio": (
            "Backend developer responsible for the live evidence-search "
            "integration layer — wiring together multiple news and "
            "fact-check sources into a single reliable pipeline, with "
            "retry handling and graceful degradation when sources are "
            "unavailable. Focused on making the system resilient under "
            "real-world network conditions, not just in the happy path."
        ),
        "skills": [
            "Python", "REST APIs", "HTTP/Networking", "Error Handling",
            "Caching", "Concurrency",
        ],
        "contributions": [
            "Integrated live search across multiple news and fact-check sources",
            "Implemented retry logic and timeout handling for external requests",
            "Built the source caching layer to reduce redundant lookups",
        ],
        "quote": "A system is only as trustworthy as how it fails.",
    },
    {
        "id":     "amit-kumar",
        "name":   "Amit Kumar",
        "role":   "ML Engineer · Dataset & Model Training",
        "badge":  "ML / AI",
        "icon":   "flask",
        "bio": (
            "ML engineer who built and trained the text-classification "
            "model at the core of the system — from dataset preparation "
            "and feature engineering (TF-IDF vectorization) through to "
            "model selection and evaluation. Focused on keeping the "
            "classifier interpretable enough that its confidence scores "
            "mean something, rather than chasing accuracy alone."
        ),
        "skills": [
            "scikit-learn", "Pandas", "NumPy", "TF-IDF / NLP",
            "Model Evaluation", "Feature Engineering",
        ],
        "contributions": [
            "Trained and tuned the Multinomial Naive Bayes classifier",
            "Built the TF-IDF vectorization pipeline",
            "Ran model evaluation and selection across candidate algorithms",
        ],
        "quote": "A confidence score is a promise. We tested it to keep that promise honest.",
    },
    {
        "id":     "prince-kumar-chaurasiya",
        "name":   "Prince Kumar Chaurasiya",
        "role":   "Research & Documentation Lead",
        "badge":  "Research",
        "icon":   "book-open",
        "bio": (
            "Led research into misinformation patterns and credibility "
            "signals that shaped the system's linguistic-analysis rules, "
            "and authored the project's technical documentation — keeping "
            "the team's design decisions, trade-offs, and verdict "
            "definitions clearly recorded for review and future "
            "maintenance."
        ),
        "skills": [
            "Technical Writing", "Research", "Misinformation Studies",
            "Documentation", "Requirements Analysis",
        ],
        "contributions": [
            "Researched linguistic credibility and misinformation markers",
            "Authored the project's technical and user documentation",
            "Defined the 9-verdict taxonomy used by the scoring engine",
        ],
        "quote": "Good documentation is how a project keeps its promises after launch.",
    },
    {
        "id":     "dhiraj-kumar",
        "name":   "Dhiraj Kumar",
        "role":   "QA Engineer · Performance Testing",
        "badge":  "QA",
        "icon":   "shield-check",
        "bio": (
            "QA engineer responsible for testing the verification pipeline "
            "end-to-end — covering edge cases in claim text, malformed "
            "inputs, and network failure scenarios — and for performance "
            "testing under load to keep response times predictable."
        ),
        "skills": [
            "Manual & Exploratory Testing", "Edge Case Analysis",
            "Performance Testing", "Bug Triage",
        ],
        "contributions": [
            "Tested the verification pipeline across edge cases and malformed inputs",
            "Ran performance testing on the search and scoring pipeline",
            "Triaged and tracked bugs across development cycles",
        ],
        "quote": "If it isn't tested against the weird input, it isn't tested.",
    },
    {
        "id":     "md-tausim-akhtar",
        "name":   "MD. Tausim Akhtar",
        "role":   "AI Research Contributor",
        "badge":  "Research",
        "icon":   "lightbulb",
        "bio": (
            "Contributed research into evidence-weighting approaches and "
            "supported evaluation of the decision-scoring logic, helping "
            "validate how ML confidence, live evidence, and linguistic "
            "signals should be balanced in the final verdict."
        ),
        "skills": [
            "AI Research", "Data Analysis", "Evaluation Design",
        ],
        "contributions": [
            "Researched evidence-weighting strategies for the scoring engine",
            "Supported evaluation of verdict accuracy across sample cases",
        ],
        "quote": "Weighing evidence well matters more than weighing it fast.",
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
