"""
utils.py
========
Version 4 — Text processing, claim extraction, ML prediction,
             separate confidence scores, and weighted final decision engine.

Bug fixes from V3
-----------------
- Evidence direction label was INVERTED: positive evidence_score means
  MORE contradicting sources (FAKE signal), negative means supporting (REAL).
  The reasoning string now correctly reflects this.
- ML confidence gate now uses quadratic roll-off (was linear in some code paths).
- Keyword extraction uses shared STOPWORDS from constants.py (no duplication).
- clean_text() and clean_for_ml() are clearly separated and documented.

AI Fake News Detection & Live Verification System — Version 4
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar & Parmeshwar
"""

from __future__ import annotations

import logging
import os
import pickle
import re
from typing import Optional

from config import (
    MODEL_FILE, VECTORIZER_FILE, MODEL_NAME_FILE,
    ML_CONF_FLOOR, ML_CONF_CEILING, ML_CONF_GATE,
    WEIGHT_ML, WEIGHT_EVIDENCE, WEIGHT_LINGUISTIC,
    WEIGHT_ML_NO_EV, WEIGHT_LINGUISTIC_NO_EV,
    FAKE_THRESHOLD, REAL_THRESHOLD,
    CONF_HIGH_FLOOR, CONF_MEDIUM_FLOOR,
    CONF_OVERALL_FLOOR, CONF_OVERALL_CEILING,
    CONF_EV_BASE, CONF_EV_WEIGHT,
    KEYWORDS_TOP_N, CLAIMS_MAX,
)
from constants import (
    FAKE_LINGUISTIC_SIGNALS,
    REAL_LINGUISTIC_SIGNALS,
    SENSATIONALISM_PATTERNS,
    STOPWORDS,
)

logger = logging.getLogger(__name__)


# ── Text Cleaning ─────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Surface-level cleaning.
    Removes URLs and HTML tags but preserves punctuation for claim extraction.
    """
    if not text or not isinstance(text, str):
        return ""
    text = text.strip()
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"<[^>]+>",          " ", text)
    text = re.sub(r"[^\w\s.!?,'-]",    " ", text)
    text = re.sub(r"\s+",              " ", text).strip()
    return text


def clean_for_ml(text: str) -> str:
    """
    Aggressive lowercase + alphanum cleaning for the TF-IDF vectorizer.
    Must match the preprocessing used during model training.
    """
    text = str(text).lower()
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s]",      " ", text)
    text = re.sub(r"\s+",              " ", text).strip()
    return text


# ── Claim Extraction ──────────────────────────────────────────────────────────

# Opinion / hedging markers — sentences with these are deprioritised
_OPINION_MARKERS = re.compile(
    r"\b(i think|i believe|in my opinion|personally|some people say|"
    r"rumour has it|allegedly|supposedly|it seems|it appears|"
    r"many believe|some say|could be|might be)\b",
    re.IGNORECASE,
)

# Verbs that carry factual claims
_CLAIM_VERBS = re.compile(
    r"\b(is|are|was|were|has|have|had|will|would|launched|confirmed|"
    r"announced|discovered|found|proved|proven|revealed|claims|states|"
    r"shows|demonstrates|causes|prevents|cures|kills|beats|wins|loses|"
    r"signs|passes|approves|bans|arrested|died|born|elected|appointed|"
    r"released|published|reported|declared|established|introduced)\b",
    re.IGNORECASE,
)


def extract_claims(text: str) -> list[str]:
    """
    Split text into verifiable factual claim-sentences.
    Heuristic: prefer sentences with a claim verb and no opinion markers.
    Returns up to CLAIMS_MAX candidates, best first.
    """
    cleaned   = clean_text(text)
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
    return result[:CLAIMS_MAX]


def extract_primary_claim(text: str) -> str:
    """Return the single most factual-looking sentence for use as search query."""
    claims = extract_claims(text)
    return claims[0] if claims else clean_text(text)[:200]


def extract_keywords(text: str, top_n: int = KEYWORDS_TOP_N) -> list[str]:
    """Extract the most significant keywords for search queries."""
    text  = text.lower()
    words = re.findall(r"\b[a-z][a-z0-9]*\b", text)
    filtered = [w for w in words if w not in STOPWORDS and len(w) > 3]

    freq: dict[str, int] = {}
    for w in filtered:
        freq[w] = freq.get(w, 0) + 1

    return sorted(freq, key=lambda x: freq[x], reverse=True)[:top_n]


# ── Linguistic Analysis ───────────────────────────────────────────────────────

def analyze_linguistic_signals(text: str) -> dict:
    """
    Scan the raw (not ML-cleaned) text for misinformation and credibility markers.

    Returns a dict with counts, found signals, sensationalism score,
    caps ratio, punctuation counts, and word count.
    """
    t = text.lower()
    fake_hits = [kw for kw in FAKE_LINGUISTIC_SIGNALS if kw in t]
    real_hits = [kw for kw in REAL_LINGUISTIC_SIGNALS if kw in t]

    sensationalism = 0
    for pat in SENSATIONALISM_PATTERNS:
        sensationalism += len(re.findall(pat, t, re.IGNORECASE))

    caps_ratio  = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    exclamation = text.count("!")
    question    = text.count("?")
    word_count  = len(text.split())

    return {
        "fake_signal_count":    len(fake_hits),
        "real_signal_count":    len(real_hits),
        "fake_signals_found":   fake_hits[:5],
        "real_signals_found":   real_hits[:5],
        "sensationalism_score": sensationalism,
        "caps_ratio":           round(caps_ratio, 4),
        "exclamation_count":    exclamation,
        "question_count":       question,
        "word_count":           word_count,
    }


def compute_linguistic_bias(signals: dict) -> float:
    """
    Returns float in [-1.0, 1.0].
    Positive → leaning FAKE.
    Negative → leaning REAL.
    """
    fake_score = (
        signals["fake_signal_count"]    * 0.30
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
    model_path = os.path.join(base, MODEL_FILE)
    vec_path   = os.path.join(base, VECTORIZER_FILE)
    name_path  = os.path.join(base, MODEL_NAME_FILE)

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
    """Fallback: train a basic model if pkl files are missing."""
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

        vec = TfidfVectorizer(
            ngram_range=(1, 3), max_features=15_000,
            sublinear_tf=True, min_df=1,
        )
        mdl = LogisticRegression(
            C=2.0, solver="lbfgs", max_iter=1000,
            class_weight="balanced", random_state=42,
        )
        X = vec.fit_transform(df["text_clean"].values)
        mdl.fit(X, df["label_binary"].values)

        with open(os.path.join(base, MODEL_FILE), "wb") as f:
            pickle.dump(mdl, f)
        with open(os.path.join(base, VECTORIZER_FILE), "wb") as f:
            pickle.dump(vec, f)
        with open(os.path.join(base, MODEL_NAME_FILE), "w") as f:
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
    dict with: label, confidence (float 0-1), prob_real, prob_fake,
               ml_confidence (int 0-100), model_name, error
    """
    try:
        model, vectorizer, model_name = load_model()
        cleaned   = clean_for_ml(text)
        X         = vectorizer.transform([cleaned])
        label_int = int(model.predict(X)[0])

        if hasattr(model, "predict_proba"):
            proba     = model.predict_proba(X)[0]   # [P(REAL), P(FAKE)]
            prob_fake = float(proba[1])
            prob_real = float(proba[0])
            conf      = float(proba[label_int])
        else:
            # LinearSVC / PAC fallback: sigmoid on decision_function
            df_val    = model.decision_function(X)[0]
            prob_fake = float(1 / (1 + 2.718 ** -float(df_val)))
            prob_real = 1.0 - prob_fake
            conf      = prob_fake if label_int == 1 else prob_real

        label = "FAKE" if label_int == 1 else "REAL"
        return {
            "label":         label,
            "confidence":    round(conf, 4),
            "prob_real":     round(prob_real, 4),
            "prob_fake":     round(prob_fake, 4),
            "ml_confidence": int(min(ML_CONF_CEILING, max(ML_CONF_FLOOR, conf * 100))),
            "model_name":    model_name,
            "error":         None,
        }

    except Exception as exc:
        logger.error("ML prediction failed: %s", exc)
        return {
            "label":         "UNVERIFIED",
            "confidence":    0.5,
            "prob_real":     0.5,
            "prob_fake":     0.5,
            "ml_confidence": 50,
            "model_name":    "Unknown",
            "error":         str(exc),
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
    ML prediction       : 45 %   (raises to 45% of normalised total when no evidence)
    Evidence (sources)  : 35 %   (0 % when no trusted sources found)
    Linguistic signals  : 20 %   (raises to 55 % when no evidence)

    Evidence score convention (from search.py)
    ------------------------------------------
    Positive  → more CONTRADICTING sources → FAKE signal
    Negative  → more SUPPORTING sources   → REAL signal

    Returns
    -------
    dict: verdict, ml_confidence, evidence_confidence, overall_confidence,
          reasoning (list[str]), combined_score
    """
    ml_label    = ml_result.get("label",         "UNVERIFIED")
    ml_conf     = ml_result.get("confidence",    0.5)
    ml_conf_pct = ml_result.get("ml_confidence", 50)

    ev_score    = float(evidence_result.get("evidence_score",        0.0))
    ev_sources  = int(evidence_result.get("sources_found",           0))
    ev_conf_pct = int(evidence_result.get("evidence_confidence",     0))
    avg_trust   = int(evidence_result.get("avg_trust_score",         0))

    ling_bias   = compute_linguistic_bias(linguistic_signals)

    # ── Adaptive weights ──────────────────────────────────────────────────────
    if ev_sources > 0:
        ml_w  = WEIGHT_ML
        ev_w  = WEIGHT_EVIDENCE
        li_w  = WEIGHT_LINGUISTIC
    else:
        ml_w  = WEIGHT_ML_NO_EV
        ev_w  = 0.0
        li_w  = WEIGHT_LINGUISTIC_NO_EV

    # Normalise (in case of floating-point drift)
    total_w = ml_w + ev_w + li_w
    ml_w   /= total_w
    ev_w   /= total_w
    li_w   /= total_w

    # ── ML directional score ──────────────────────────────────────────────────
    # Gate: below ML_CONF_GATE, quadratic roll-off so borderline predictions
    # don't dominate when evidence is absent.
    if ml_conf >= ML_CONF_GATE:
        ml_effective = ml_conf
    else:
        ml_effective = ml_conf * (ml_conf / ML_CONF_GATE)

    # FAKE → positive pole, REAL → negative pole (aligns with ev_score sign)
    ml_score = ml_effective if ml_label == "FAKE" else -ml_effective

    combined = round(
        ml_score  * ml_w
        + ev_score * ev_w
        + ling_bias * li_w,
        4,
    )

    # ── Asymmetric verdict thresholds ─────────────────────────────────────────
    # FAKE requires stronger evidence to reduce false positives.
    if combined >= FAKE_THRESHOLD:
        verdict  = "FAKE"
        raw_conf = 50 + combined * 45
    elif combined <= REAL_THRESHOLD:
        verdict  = "REAL"
        raw_conf = 50 + abs(combined) * 45
    else:
        verdict  = "UNVERIFIED"
        raw_conf = 40 + abs(combined) * 20

    overall_conf = int(min(CONF_OVERALL_CEILING, max(CONF_OVERALL_FLOOR, raw_conf)))

    # ── Reasoning generation ──────────────────────────────────────────────────
    reasoning: list[str] = []
    model_name = ml_result.get("model_name", "ML Model")

    # 1. ML statement
    reasoning.append(
        f"{model_name} classified this as {ml_label} "
        f"with {ml_conf_pct}% model confidence."
    )

    # 2. Evidence statement
    # IMPORTANT: positive ev_score = contradicting sources = FAKE signal
    #            negative ev_score = supporting sources    = REAL signal
    if ev_sources > 0:
        sup_count  = len(evidence_result.get("supporting_sources", []))
        con_count  = len(evidence_result.get("contradicting_sources", []))
        neu_count  = len(evidence_result.get("neutral_sources", []))

        if con_count > 0 and con_count >= sup_count:
            ev_summary = (
                f"{con_count} trusted source(s) contradicted or flagged this claim "
                f"as false/misleading"
            )
        elif sup_count > 0:
            ev_summary = (
                f"{sup_count} trusted source(s) corroborated this claim"
            )
        else:
            ev_summary = (
                f"{neu_count} trusted source(s) referenced this topic "
                f"without a clear supporting or contradicting position"
            )

        reasoning.append(
            f"{ev_summary} (avg. trust score: {avg_trust}/100)."
        )
    else:
        reasoning.append(
            "Live verification found no results from trusted news sources. "
            "Verdict relies on the ML model and linguistic analysis only."
        )

    # 3. Linguistic signals
    if linguistic_signals.get("fake_signal_count", 0) > 0:
        sigs = ", ".join(
            f'"{s}"' for s in linguistic_signals.get("fake_signals_found", [])[:3]
        )
        reasoning.append(
            f"Text contains {linguistic_signals['fake_signal_count']} "
            f"misinformation/sensationalism marker(s): {sigs}."
        )

    if linguistic_signals.get("real_signal_count", 0) > 0:
        sigs = ", ".join(
            f'"{s}"' for s in linguistic_signals.get("real_signals_found", [])[:3]
        )
        reasoning.append(
            f"Text contains {linguistic_signals['real_signal_count']} "
            f"credible journalistic language marker(s): {sigs}."
        )

    # 4. Specific sources
    sup = evidence_result.get("supporting_sources", [])
    con = evidence_result.get("contradicting_sources", [])

    if sup:
        reasoning.append(
            f"Corroborating sources: {', '.join(sup[:3])}."
        )
    if con:
        reasoning.append(
            f"Sources that contradicted this claim: {', '.join(con[:3])}."
        )

    # 5. Confidence label
    if overall_conf >= CONF_HIGH_FLOOR:
        conf_label = "High confidence"
    elif overall_conf >= CONF_MEDIUM_FLOOR:
        conf_label = "Moderate confidence"
    else:
        conf_label = "Low confidence"

    reasoning.append(
        f"{conf_label} verdict — combined decision score: {combined:+.3f}."
    )

    return {
        "verdict":             verdict,
        "overall_confidence":  overall_conf,
        "ml_confidence":       ml_conf_pct,
        "evidence_confidence": ev_conf_pct,
        "reasoning":           reasoning,
        "combined_score":      combined,
    }
