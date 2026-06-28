"""
utils.py
========
Version 3 — Text processing, claim extraction, multi-model ML prediction,
             separate confidence scores, and weighted final decision engine.

Changes from V2
---------------
- Claim extraction now uses NLP heuristics to identify the core factual claim
- predict_ml() returns ml_confidence, prob_real, prob_fake as before PLUS
  a separate ml_confidence integer (0-100)
- make_final_decision() produces ml_confidence, evidence_confidence, and
  overall_confidence as separate scores
- compute_linguistic_bias() is made more granular

AI Fake News Detection & Live Verification System — Version 3
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar & Parmeshwar
"""

from __future__ import annotations

import logging
import os
import pickle
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ── Keyword Banks ─────────────────────────────────────────────────────────────

FAKE_LINGUISTIC_SIGNALS: list[str] = [
    "secret", "hidden", "suppressed", "conspiracy", "government hiding",
    "they don't want you to know", "100 percent guaranteed", "miracle cure",
    "shocking truth", "leaked documents", "aliens confirmed", "illuminati",
    "deep state", "anonymous sources", "unnamed sources", "confirms insider",
    "mainstream media won't tell", "doctors hate this", "one weird trick",
    "banned by", "censored by", "share before deleted", "wake up sheeple",
    "pharma lobby", "big pharma hiding", "suppressed by government",
    "secret treaty", "microchip", "tracking device", "mind control",
    "hollow earth", "moon landing fake", "flat earth proven",
    "share immediately", "forward this", "before it gets deleted",
    "what they don't want", "cover-up", "shadow government",
]

REAL_LINGUISTIC_SIGNALS: list[str] = [
    "according to", "reported by", "study shows", "research indicates",
    "official statement", "government announces", "ministry confirms",
    "data shows", "statistics reveal", "survey finds", "trial results",
    "peer-reviewed", "published in", "clinical trial", "press release",
    "official spokesperson", "verified by", "confirmed by", "sources say",
    "as per report", "audit reveals", "commission recommends",
    "parliament passed", "supreme court", "high court", "rbi announces",
    "isro confirms", "who statement", "un report",
]

SENSATIONALISM_PATTERNS: list[str] = [
    r"\b(shocking|explosive|bombshell|unbelievable|mind-blowing|terrifying)\b",
    r"\b(100\s*%|guaranteed|completely|absolutely)\b",
    r"!!+",
    r"\b(urgent|breaking|alert|must\s+read|viral)\b",
    r"[A-Z]{5,}",
    r"\b(secret|hidden|suppressed|leaked|banned)\b",
]

# ── Text Cleaning ─────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Surface-level cleaning — preserves punctuation for claim extraction."""
    if not text or not isinstance(text, str):
        return ""
    text = text.strip()
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"<[^>]+>",          " ", text)
    text = re.sub(r"[^\w\s.!?,'-]",    " ", text)
    text = re.sub(r"\s+",              " ", text).strip()
    return text


def clean_for_ml(text: str) -> str:
    """Aggressive lowercase+alphanum cleaning for ML vectorizer."""
    text = str(text).lower()
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s]",      " ", text)
    text = re.sub(r"\s+",              " ", text).strip()
    return text


# ── Claim Extraction ──────────────────────────────────────────────────────────

# Patterns that signal opinion/emotion rather than factual claims
_OPINION_MARKERS = re.compile(
    r"\b(i think|i believe|in my opinion|personally|some people say|"
    r"rumour has it|allegedly|supposedly|it seems|it appears)\b",
    re.IGNORECASE,
)

# Entity-bearing sentence patterns that carry a factual claim
_CLAIM_VERBS = re.compile(
    r"\b(is|are|was|were|has|have|had|will|would|launched|confirmed|"
    r"announced|discovered|found|proved|proven|revealed|claims|states|"
    r"shows|demonstrates|causes|prevents|cures|kills|beats|wins|loses|"
    r"signs|passes|approves|bans|arrested|died|born|elected|appointed)\b",
    re.IGNORECASE,
)


def extract_claims(text: str) -> list[str]:
    """
    Split text into verifiable factual claim-sentences.
    Heuristic: prefer sentences that contain a claim verb and lack opinion markers.
    Returns up to 5 candidates, best candidates first.
    """
    cleaned = clean_text(text)
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)

    factual: list[str] = []
    opinion: list[str] = []

    for s in sentences:
        s = s.strip()
        if len(s) < 20:
            continue
        if _OPINION_MARKERS.search(s):
            opinion.append(s)
        elif _CLAIM_VERBS.search(s):
            factual.append(s)
        else:
            opinion.append(s)

    result = factual + opinion
    if not result and len(cleaned) > 10:
        result = [cleaned]
    return result[:5]


def extract_primary_claim(text: str) -> str:
    """
    Return a single string representing the core factual claim.
    Used as the primary query for search.
    """
    claims = extract_claims(text)
    return claims[0] if claims else clean_text(text)[:200]


def extract_keywords(text: str, top_n: int = 8) -> list[str]:
    """Extract most significant keywords for search queries."""
    text = text.lower()
    stopwords: set[str] = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "has", "have", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "this", "that", "these", "those",
        "it", "its", "as", "if", "then", "than", "so", "not", "no", "also",
        "according", "says", "said", "report", "reports", "reported",
        "very", "just", "even", "only", "more", "most", "some", "any",
        "which", "who", "what", "when", "where", "how", "they", "them",
        "their", "we", "our", "you", "your", "he", "she", "his", "her",
    }
    words = re.findall(r"\b[a-z][a-z0-9]*\b", text)
    filtered = [w for w in words if w not in stopwords and len(w) > 3]
    freq: dict[str, int] = {}
    for w in filtered:
        freq[w] = freq.get(w, 0) + 1
    return sorted(freq, key=lambda x: freq[x], reverse=True)[:top_n]


# ── Linguistic Analysis ───────────────────────────────────────────────────────

def analyze_linguistic_signals(text: str) -> dict:
    t = text.lower()
    fake_hits = [kw for kw in FAKE_LINGUISTIC_SIGNALS if kw in t]
    real_hits = [kw for kw in REAL_LINGUISTIC_SIGNALS if kw in t]

    sensationalism = 0
    for pat in SENSATIONALISM_PATTERNS:
        sensationalism += len(re.findall(pat, t, re.IGNORECASE))

    caps_ratio    = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    exclamation   = text.count("!")
    question      = text.count("?")
    word_count    = len(text.split())

    return {
        "fake_signal_count":   len(fake_hits),
        "real_signal_count":   len(real_hits),
        "fake_signals_found":  fake_hits[:5],
        "real_signals_found":  real_hits[:5],
        "sensationalism_score": sensationalism,
        "caps_ratio":          round(caps_ratio, 4),
        "exclamation_count":   exclamation,
        "question_count":      question,
        "word_count":          word_count,
    }


def compute_linguistic_bias(signals: dict) -> float:
    """
    Returns float in [-1.0, 1.0].
    Positive → leaning FAKE.  Negative → leaning REAL.
    """
    fake_score = (
        signals["fake_signal_count"]   * 0.30
        + signals["sensationalism_score"] * 0.15
        + signals["caps_ratio"]           * 0.40
        + min(signals["exclamation_count"], 3) * 0.08
    )
    real_score = signals["real_signal_count"] * 0.30
    return max(-1.0, min(1.0, round(fake_score - real_score, 4)))


# ── Model Loading & Prediction ────────────────────────────────────────────────

_MODEL      : Optional[object] = None
_VECTORIZER : Optional[object] = None
_MODEL_NAME : str = "Unknown"


def _get_model_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def load_model() -> tuple:
    """Load model.pkl and vectorizer.pkl (lazy, cached in module globals)."""
    global _MODEL, _VECTORIZER, _MODEL_NAME
    if _MODEL is not None and _VECTORIZER is not None:
        return _MODEL, _VECTORIZER, _MODEL_NAME

    base       = _get_model_dir()
    model_path = os.path.join(base, "model.pkl")
    vec_path   = os.path.join(base, "vectorizer.pkl")
    name_path  = os.path.join(base, "model_name.txt")

    if not os.path.exists(model_path) or not os.path.exists(vec_path):
        logger.warning("Model files missing — training on the fly …")
        _train_on_the_fly(base)

    with open(model_path, "rb") as f:
        _MODEL = pickle.load(f)
    with open(vec_path, "rb") as f:
        _VECTORIZER = pickle.load(f)
    if os.path.exists(name_path):
        with open(name_path) as f:
            _MODEL_NAME = f.read().strip()

    logger.info("Model '%s' loaded from %s", _MODEL_NAME, base)
    return _MODEL, _VECTORIZER, _MODEL_NAME


def _train_on_the_fly(base: str) -> None:
    """Fallback: train with best-model selection if pkl files are missing."""
    try:
        import pandas as pd
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression

        dataset_path = os.path.join(base, "dataset.csv")
        if not os.path.exists(dataset_path):
            raise FileNotFoundError("dataset.csv not found")

        df = pd.read_csv(dataset_path).dropna(subset=["text", "label"])
        df["text_clean"]   = df["text"].apply(clean_for_ml)
        df["label_binary"] = (df["label"].str.upper() == "FAKE").astype(int)

        vec = TfidfVectorizer(ngram_range=(1, 3), max_features=15000,
                              sublinear_tf=True, min_df=1)
        mdl = LogisticRegression(C=2.0, solver="lbfgs", max_iter=1000,
                                 class_weight="balanced", random_state=42)
        X   = vec.fit_transform(df["text_clean"].values)
        mdl.fit(X, df["label_binary"].values)

        with open(os.path.join(base, "model.pkl"), "wb") as f:
            pickle.dump(mdl, f)
        with open(os.path.join(base, "vectorizer.pkl"), "wb") as f:
            pickle.dump(vec, f)
        with open(os.path.join(base, "model_name.txt"), "w") as f:
            f.write("Logistic Regression (fallback)")
        logger.info("On-the-fly training complete.")
    except Exception as exc:
        logger.error("On-the-fly training failed: %s", exc)
        raise


def predict_ml(text: str) -> dict:
    """
    Run the best-selected ML model on input text.

    Returns
    -------
    dict:  label, confidence (float 0-1), prob_real, prob_fake,
           ml_confidence (int 0-100), model_name, error
    """
    try:
        model, vectorizer, model_name = load_model()
        cleaned   = clean_for_ml(text)
        X         = vectorizer.transform([cleaned])
        label_int = model.predict(X)[0]

        # Models that support predict_proba
        if hasattr(model, "predict_proba"):
            proba     = model.predict_proba(X)[0]   # [P(REAL), P(FAKE)]
            prob_fake = float(proba[1])
            prob_real = float(proba[0])
            conf      = float(proba[label_int])
        else:
            # LinearSVC / PassiveAggressive: use decision_function for confidence
            df_val    = model.decision_function(X)[0]
            prob_fake = float(1 / (1 + 2.718 ** -df_val))   # sigmoid
            prob_real = 1.0 - prob_fake
            conf      = prob_fake if label_int == 1 else prob_real

        label = "FAKE" if label_int == 1 else "REAL"
        return {
            "label":          label,
            "confidence":     round(conf, 4),
            "prob_real":      round(prob_real, 4),
            "prob_fake":      round(prob_fake, 4),
            "ml_confidence":  int(min(97, max(30, conf * 100))),
            "model_name":     model_name,
            "error":          None,
        }
    except Exception as exc:
        logger.error("ML prediction failed: %s", exc)
        return {
            "label":          "UNVERIFIED",
            "confidence":     0.5,
            "prob_real":      0.5,
            "prob_fake":      0.5,
            "ml_confidence":  50,
            "model_name":     "Unknown",
            "error":          str(exc),
        }


# ── Final Decision Engine ─────────────────────────────────────────────────────

def make_final_decision(
    ml_result:          dict,
    evidence_result:    dict,
    linguistic_signals: dict,
) -> dict:
    """
    Combine ML + evidence + linguistics into a final verdict.

    Decision weights
    ----------------
    ML prediction      : 45 %
    Evidence (sources) : 35 %  (0 % if no sources found)
    Linguistic signals : 20 %  (raised to 55 % if no sources)

    Returns
    -------
    dict: verdict, ml_confidence, evidence_confidence, overall_confidence,
          reasoning, combined_score
    """
    ml_label    = ml_result.get("label",         "UNVERIFIED")
    ml_conf     = ml_result.get("confidence",    0.5)
    ml_conf_pct = ml_result.get("ml_confidence", 50)

    ev_score    = evidence_result.get("evidence_score",        0.0)
    ev_sources  = evidence_result.get("sources_found",         0)
    ev_conf_pct = evidence_result.get("evidence_confidence",   0)
    avg_trust   = evidence_result.get("avg_trust_score",       0)

    ling_bias   = compute_linguistic_bias(linguistic_signals)

    # ── Weights ────────────────────────────────────────────────────────────────
    ml_w  = 0.45
    ev_w  = 0.35 if ev_sources > 0 else 0.0
    li_w  = 0.20 if ev_sources > 0 else 0.55
    total_w = ml_w + ev_w + li_w
    ml_w  /= total_w
    ev_w  /= total_w
    li_w  /= total_w

    # ML score: FAKE=+1 pole, REAL=-1 pole
    # Apply a deadband: ML confidence must exceed 0.60 to contribute
    # its full directional weight; below that it is scaled back so
    # a borderline ML prediction (0.50–0.60) does not dominate when
    # no corroborating evidence is available.
    ML_CONF_GATE = 0.60   # min confidence before full ML directional weight
    ml_effective = ml_conf if ml_conf >= ML_CONF_GATE else (
        ml_conf * (ml_conf / ML_CONF_GATE)  # quadratic roll-off below gate
    )
    ml_score = ml_effective if ml_label == "FAKE" else -ml_effective

    combined = round(
        ml_score  * ml_w
        + ev_score * ev_w
        + ling_bias * li_w,
        4,
    )

    # ── Verdict thresholds ─────────────────────────────────────────────────────
    # Thresholds are asymmetric: FAKE requires stronger evidence than REAL
    # because false positives (calling real news fake) are more harmful.
    FAKE_THRESH = 0.22
    REAL_THRESH = -0.15

    if combined >= FAKE_THRESH:
        verdict      = "FAKE"
        raw_conf     = 50 + combined * 45
    elif combined <= REAL_THRESH:
        verdict      = "REAL"
        raw_conf     = 50 + abs(combined) * 45
    else:
        verdict      = "UNVERIFIED"
        raw_conf     = 40 + abs(combined) * 20

    overall_conf = int(min(97, max(30, raw_conf)))

    # ── Reasoning ──────────────────────────────────────────────────────────────
    reasoning: list[str] = []

    model_name = ml_result.get("model_name", "ML Model")
    reasoning.append(
        f"{model_name} predicted {ml_label} with "
        f"{ml_conf_pct}% ML confidence."
    )

    if ev_sources > 0:
        ev_dir = "supporting" if ev_score < 0 else "contradicting"
        reasoning.append(
            f"Found {ev_sources} trusted source(s) providing {ev_dir} evidence "
            f"(average trust score: {avg_trust}/100)."
        )
    else:
        reasoning.append(
            "Live verification could not retrieve results from trusted news sources. "
            "Verdict relies on ML model and linguistic analysis."
        )

    if linguistic_signals.get("fake_signal_count", 0) > 0:
        sigs = ", ".join(f'"{s}"' for s in linguistic_signals.get("fake_signals_found", [])[:3])
        reasoning.append(
            f"Text contains {linguistic_signals['fake_signal_count']} "
            f"misinformation/sensationalism markers: {sigs}."
        )

    if linguistic_signals.get("real_signal_count", 0) > 0:
        sigs = ", ".join(f'"{s}"' for s in linguistic_signals.get("real_signals_found", [])[:3])
        reasoning.append(
            f"Text contains {linguistic_signals['real_signal_count']} "
            f"credible/journalistic language markers: {sigs}."
        )

    sup = evidence_result.get("supporting_sources", [])
    con = evidence_result.get("contradicting_sources", [])

    if sup:
        reasoning.append(
            f"Corroborating sources: {', '.join(sup[:3])}."
        )
    if con:
        reasoning.append(
            f"Contradicting sources flagged this claim: {', '.join(con[:3])}."
        )

    if overall_conf >= 80:
        confidence_label = "High confidence"
    elif overall_conf >= 60:
        confidence_label = "Moderate confidence"
    else:
        confidence_label = "Low confidence"

    reasoning.append(
        f"{confidence_label} verdict — combined decision score: {combined:+.3f}."
    )

    return {
        "verdict":              verdict,
        "overall_confidence":   overall_conf,
        "ml_confidence":        ml_conf_pct,
        "evidence_confidence":  ev_conf_pct,
        "reasoning":            reasoning,
        "combined_score":       combined,
    }
