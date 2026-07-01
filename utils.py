"""
utils.py
========
Version 5 — Text processing, ML prediction, and 9-verdict decision engine.

Bug fixes from V4
-----------------
- WEIGHT_ML was 0.45 — overrode evidence on REAL news.
  V5: WEIGHT_ML=0.30, WEIGHT_EVIDENCE=0.50 (imported from config).
- make_final_decision() now produces 9 verdicts instead of 3.
- Added fact-check site override: if a fact-check site contradicts a claim,
  FACTCHECK_BOOST is added to combined_score regardless of ML output.
- _train_on_the_fly() now uses 4-model comparison (same as train_model.py).
- Reasoning strings now correctly label evidence direction:
    positive ev_score = contradicting sources = FAKE signal.
    negative ev_score = supporting sources    = REAL signal.

New in V5
---------
- generate_verified_fact(): builds a structured "Verified Fact" block from
  evidence — never hallucinates, falls back to "Insufficient evidence".
- compute_linguistic_confidence(): returns 0-100 int for display.
- make_final_decision() returns linguistic_confidence and fact_confidence keys.
- VERDICT_META imported from constants and returned in every decision dict.

AI Fake News Detection & Live Verification System — Version 5
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar, Parmeshwar Kumar, Amit Kumar,
              Prince Kumar Chaurasiya, Dhiraj Kumar, MD. Tausim Akhtar
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
    FACTCHECK_BOOST,
    VERDICT_THRESHOLDS_WITH_EVIDENCE, VERDICT_THRESHOLDS_NO_EVIDENCE,
    CONF_HIGH_FLOOR, CONF_MEDIUM_FLOOR,
    CONF_OVERALL_FLOOR, CONF_OVERALL_CEILING,
    KEYWORDS_TOP_N, CLAIMS_MAX,
)
from constants import (
    FAKE_LINGUISTIC_SIGNALS,
    REAL_LINGUISTIC_SIGNALS,
    FAKE_LINGUISTIC_SIGNALS_COMPILED,
    REAL_LINGUISTIC_SIGNALS_COMPILED,
    SENSATIONALISM_PATTERNS,
    CAPS_SHOUTING_PATTERN,
    STOPWORDS,
    VERDICT_META,
    find_keyword_hits,
)

logger = logging.getLogger(__name__)

# Pre-compile sensationalism patterns once at import time
_SEN_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE) for p in SENSATIONALISM_PATTERNS
]


# ── Text Cleaning ─────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Surface-level cleaning: removes URLs, HTML tags.
    Preserves punctuation for claim/keyword extraction.
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
    Aggressive lowercase + alphanum cleaning for TF-IDF.
    Must match preprocessing used during model training.
    """
    text = str(text).lower()
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s]",      " ", text)
    text = re.sub(r"\s+",              " ", text).strip()
    return text


# ── Claim Extraction ──────────────────────────────────────────────────────────

_OPINION_MARKERS = re.compile(
    r"\b(i think|i believe|in my opinion|personally|some people say|"
    r"rumour has it|allegedly|supposedly|it seems|it appears|"
    r"many believe|some say|could be|might be)\b",
    re.IGNORECASE,
)

_CLAIM_VERBS = re.compile(
    r"\b(is|are|was|were|has|have|had|will|would|launched|confirmed|"
    r"announced|discovered|found|proved|proven|revealed|claims|states|"
    r"shows|demonstrates|causes|prevents|cures|kills|beats|wins|loses|"
    r"signs|passes|approves|bans|arrested|died|born|elected|appointed|"
    r"released|published|reported|declared|established|introduced)\b",
    re.IGNORECASE,
)


def extract_claims(text: str) -> list[str]:
    """Extract verifiable factual claim-sentences; heuristic-ranked."""
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
    """Return the most factual-looking sentence for use as search query."""
    claims = extract_claims(text)
    return claims[0] if claims else clean_text(text)[:200]


def extract_keywords(text: str, top_n: int = KEYWORDS_TOP_N) -> list[str]:
    """Extract the most significant keywords for search queries."""
    text    = text.lower()
    words   = re.findall(r"\b[a-z][a-z0-9]*\b", text)
    filtered = [w for w in words if w not in STOPWORDS and len(w) > 3]

    freq: dict[str, int] = {}
    for w in filtered:
        freq[w] = freq.get(w, 0) + 1

    return sorted(freq, key=lambda x: freq[x], reverse=True)[:top_n]


# ── Linguistic Analysis ───────────────────────────────────────────────────────

def analyze_linguistic_signals(text: str) -> dict:
    """
    Scan raw text for misinformation and credibility markers.
    Returns counts, signal lists, sensationalism score, caps ratio, etc.

    BUG FIX V5.1: sensationalism_score now correctly separates two signals:
      1. Sensational PHRASES (e.g. "shocking", "guaranteed") — matched
         case-insensitively against lowercased text via _SEN_PATTERNS.
      2. ALL-CAPS SHOUTING (e.g. "URGENT", "SHOCKING") — matched
         case-SENSITIVELY against the ORIGINAL-case text via
         CAPS_SHOUTING_PATTERN. Previously this was folded into
         _SEN_PATTERNS as an IGNORECASE [A-Z]{5,} pattern run against
         already-lowercased text, which meant it could never see real
         capitals and instead matched any 5+ letter word — silently
         inflating sensationalism_score on completely normal text.
    """
    t          = text.lower()
    fake_hits  = find_keyword_hits(t, FAKE_LINGUISTIC_SIGNALS_COMPILED)
    real_hits  = find_keyword_hits(t, REAL_LINGUISTIC_SIGNALS_COMPILED)

    phrase_sensationalism = sum(len(p.findall(t)) for p in _SEN_PATTERNS)
    caps_shouting_count    = len(CAPS_SHOUTING_PATTERN.findall(text))   # original case
    sensationalism         = phrase_sensationalism + caps_shouting_count

    caps_ratio     = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    exclamation    = text.count("!")
    question       = text.count("?")
    word_count     = len(text.split())

    return {
        "fake_signal_count":    len(fake_hits),
        "real_signal_count":    len(real_hits),
        "fake_signals_found":   fake_hits[:5],
        "real_signals_found":   real_hits[:5],
        "sensationalism_score": sensationalism,
        "caps_shouting_count":  caps_shouting_count,
        "caps_ratio":           round(caps_ratio, 4),
        "exclamation_count":    exclamation,
        "question_count":       question,
        "word_count":           word_count,
    }


def compute_linguistic_bias(signals: dict) -> float:
    """
    Returns float in [-1.0, +1.0].
    Positive → leaning FAKE.
    Negative → leaning REAL.
    """
    fake_score = (
        signals.get("fake_signal_count",    0) * 0.30
        + signals.get("sensationalism_score", 0) * 0.15
        + signals.get("caps_ratio",           0) * 0.40
        + min(signals.get("exclamation_count", 0), 3) * 0.08
    )
    real_score = signals.get("real_signal_count", 0) * 0.30
    return max(-1.0, min(1.0, round(fake_score - real_score, 4)))


def compute_linguistic_confidence(signals: dict) -> int:
    """
    Returns 0-100 integer representing how confidently linguistic analysis
    leans in one direction.
    """
    fake_n = signals.get("fake_signal_count", 0)
    real_n = signals.get("real_signal_count", 0)
    total  = fake_n + real_n
    if total == 0:
        return 30   # baseline uncertainty
    majority = max(fake_n, real_n)
    # Base: 40 + how dominant the majority signal is, scaled to 90 max
    return int(min(90, 40 + (majority / max(total, 1)) * 50))


# ── Model Loading ─────────────────────────────────────────────────────────────

_MODEL      : Optional[object] = None
_VECTORIZER : Optional[object] = None
_MODEL_NAME : str              = "Unknown"


def _get_model_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def load_model() -> tuple:
    """Load model.pkl and vectorizer.pkl (lazy, module-level cache)."""
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
    """
    Fallback: train and auto-select from 4 classifiers if pkl files missing.
    Mirrors train_model.py logic so the fallback model is production-quality.
    BUG FIX (V4): V4 only trained LogisticRegression here; V5 runs full
    4-model comparison identical to train_model.py.
    """
    try:
        import pandas as pd
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression, PassiveAggressiveClassifier
        from sklearn.model_selection import StratifiedKFold, cross_val_score
        from sklearn.naive_bayes import MultinomialNB
        from sklearn.svm import LinearSVC

        dataset_path = os.path.join(base, "dataset.csv")
        if not os.path.exists(dataset_path):
            raise FileNotFoundError("dataset.csv not found for on-the-fly training")

        df = pd.read_csv(dataset_path).dropna(subset=["text", "label"])
        df["text_clean"]   = df["text"].apply(clean_for_ml)
        df["label_binary"] = (df["label"].str.upper() == "FAKE").astype(int)

        vec = TfidfVectorizer(
            ngram_range=(1, 3), max_features=15_000,
            sublinear_tf=True, min_df=1,
        )
        X = vec.fit_transform(df["text_clean"].values)
        y = df["label_binary"].values

        candidates = [
            ("Logistic Regression",       LogisticRegression(C=2.0, solver="lbfgs", max_iter=1000, class_weight="balanced", random_state=42)),
            ("Linear SVM (Calibrated)",   CalibratedClassifierCV(LinearSVC(C=1.0, class_weight="balanced", max_iter=2000, random_state=42), cv=3)),
            ("Passive Aggressive (Cal.)", CalibratedClassifierCV(PassiveAggressiveClassifier(C=0.5, max_iter=1000, class_weight="balanced", random_state=42), cv=3)),
            ("Multinomial Naive Bayes",   MultinomialNB(alpha=0.1)),
        ]

        cv          = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        best_score  = -1.0
        best_name   = ""
        best_model  = None

        for name, clf in candidates:
            try:
                scores    = cross_val_score(clf, X, y, cv=cv, scoring="accuracy")
                mean_cv   = scores.mean()
                logger.info("  On-the-fly CV %s: %.4f", name, mean_cv)
                if mean_cv > best_score:
                    best_score = mean_cv
                    best_name  = name
                    best_model = clf
            except Exception as exc:
                logger.warning("  %s failed: %s", name, exc)

        if best_model is None:
            raise RuntimeError("All classifiers failed during on-the-fly training")

        best_model.fit(X, y)

        with open(os.path.join(base, MODEL_FILE), "wb") as f:
            pickle.dump(best_model, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open(os.path.join(base, VECTORIZER_FILE), "wb") as f:
            pickle.dump(vec, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open(os.path.join(base, MODEL_NAME_FILE), "w") as f:
            f.write(best_name)

        logger.info("On-the-fly training complete. Best: %s (%.4f)", best_name, best_score)

    except Exception as exc:
        logger.error("On-the-fly training failed: %s", exc)
        raise


# ── ML Prediction ─────────────────────────────────────────────────────────────

def predict_ml(text: str) -> dict:
    """
    Run the best-selected ML model on input text.

    Returns dict:
        label, confidence, prob_real, prob_fake,
        ml_confidence (0-100 int), model_name, error
    """
    try:
        model, vectorizer, model_name = load_model()
        cleaned   = clean_for_ml(text)
        X         = vectorizer.transform([cleaned])
        label_int = int(model.predict(X)[0])

        if hasattr(model, "predict_proba"):
            proba     = model.predict_proba(X)[0]
            prob_fake = float(proba[1])
            prob_real = float(proba[0])
            conf      = float(proba[label_int])
        else:
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


# ── Verdict Mapping ───────────────────────────────────────────────────────────

def _map_verdict(combined: float, ev_sources: int, ev_result: dict, ling_signals: dict) -> str:
    """
    Map combined_score [-1, +1] to one of 9 V5 verdicts.

    With evidence:  uses VERDICT_THRESHOLDS_WITH_EVIDENCE
    Without evidence: uses VERDICT_THRESHOLDS_NO_EVIDENCE (conservative)

    Special: MIXED requires conflicting sources; MISLEADING requires
    high sensationalism even when some evidence exists.
    """
    table = VERDICT_THRESHOLDS_WITH_EVIDENCE if ev_sources > 0 else VERDICT_THRESHOLDS_NO_EVIDENCE

    base_verdict = "UNVERIFIED"
    for verdict, lo, hi in table:
        if lo <= combined < hi:
            base_verdict = verdict
            break

    # Refine MIXED vs MISLEADING when evidence is available
    if ev_sources > 0 and base_verdict in ("MIXED", "MISLEADING"):
        sup_n = len(ev_result.get("supporting_sources",    []))
        con_n = len(ev_result.get("contradicting_sources", []))
        sen   = ling_signals.get("sensationalism_score",    0)

        if sup_n > 0 and con_n > 0:
            base_verdict = "MIXED"
        elif sen >= 4 and sup_n > 0:
            base_verdict = "MISLEADING"     # supported but sensationalist framing
        else:
            base_verdict = "MIXED"

    return base_verdict


# ── V5 Decision Engine ────────────────────────────────────────────────────────

def make_final_decision(
    ml_result:          dict,
    evidence_result:    dict,
    linguistic_signals: dict,
) -> dict:
    """
    V5 weighted decision engine — 9-verdict output.

    Weights (with evidence)
    -----------------------
    ML Prediction  : 30 %   (was 45 % in V4 — reduced to prevent ML override)
    Evidence Score : 50 %   (was 35 % — trusted sources weighted more)
    Linguistic     : 20 %   (unchanged)

    Weights (no evidence found)
    ---------------------------
    ML Prediction  : 55 %
    Linguistic     : 45 %

    Evidence score sign convention (from search.py)
    ------------------------------------------------
    Positive  → more CONTRADICTING sources → FAKE signal
    Negative  → more SUPPORTING sources   → REAL signal

    Fact-check override
    -------------------
    If any fact-check site explicitly contradicts the claim,
    FACTCHECK_BOOST (+0.18) is added to the combined score
    before verdict mapping. This prevents ML from overriding
    a verified debunk result.

    Returns
    -------
    dict with keys:
        verdict, overall_confidence, ml_confidence, evidence_confidence,
        linguistic_confidence, fact_confidence, reasoning (list[str]),
        combined_score, verdict_meta (from constants.VERDICT_META)
    """
    ml_label    = ml_result.get("label",         "UNVERIFIED")
    ml_conf     = ml_result.get("confidence",    0.5)
    ml_conf_pct = ml_result.get("ml_confidence", 50)

    ev_score    = float(evidence_result.get("evidence_score",        0.0))
    ev_sources  = int(evidence_result.get("sources_found",           0))
    ev_conf_pct = int(evidence_result.get("evidence_confidence",     0))
    avg_trust   = int(evidence_result.get("avg_trust_score",         0))

    ling_bias   = compute_linguistic_bias(linguistic_signals)
    ling_conf   = compute_linguistic_confidence(linguistic_signals)

    # ── Adaptive weights ──────────────────────────────────────────────────────
    if ev_sources > 0:
        ml_w, ev_w, li_w = WEIGHT_ML, WEIGHT_EVIDENCE, WEIGHT_LINGUISTIC
    else:
        ml_w, ev_w, li_w = WEIGHT_ML_NO_EV, 0.0, WEIGHT_LINGUISTIC_NO_EV

    # Normalise (guard against floating-point drift)
    total_w = ml_w + ev_w + li_w or 1.0
    ml_w   /= total_w
    ev_w   /= total_w
    li_w   /= total_w

    # ── ML directional score with deadband ───────────────────────────────────
    # Below ML_CONF_GATE: quadratic roll-off so borderline predictions
    # don't dominate when evidence is absent.
    if ml_conf >= ML_CONF_GATE:
        ml_effective = ml_conf
    else:
        ml_effective = ml_conf * (ml_conf / ML_CONF_GATE)

    # FAKE → positive (aligns with ev_score sign), REAL → negative
    ml_score = ml_effective if ml_label == "FAKE" else -ml_effective

    # ── Combined score ────────────────────────────────────────────────────────
    combined = round(
        ml_score  * ml_w
        + ev_score * ev_w
        + ling_bias * li_w,
        4,
    )

    # ── Fact-check override ───────────────────────────────────────────────────
    # If a dedicated fact-check site is in the contradicting set, push the
    # score toward FAKE regardless of what the ML model said.
    fc_articles = [
        a for a in evidence_result.get("articles", [])
        if a.get("is_fact_check") and a.get("classification") == "contradicting"
    ]
    if fc_articles:
        combined = min(1.0, combined + FACTCHECK_BOOST)
        logger.debug(
            "Fact-check override applied (+%.2f): %s",
            FACTCHECK_BOOST,
            [a.get("source_name") for a in fc_articles[:2]],
        )

    combined = max(-1.0, min(1.0, round(combined, 4)))

    # ── Verdict mapping ───────────────────────────────────────────────────────
    verdict = _map_verdict(combined, ev_sources, evidence_result, linguistic_signals)

    # ── Confidence calculations ───────────────────────────────────────────────
    abs_combined = abs(combined)

    # Overall: scales with how far from 0 the combined score is
    raw_conf     = 45 + abs_combined * 50
    overall_conf = int(min(CONF_OVERALL_CEILING, max(CONF_OVERALL_FLOOR, raw_conf)))

    # Fact confidence: blend of evidence confidence and fact-check presence
    fact_boost   = 10 if fc_articles else 0
    fact_conf    = int(min(95, ev_conf_pct + fact_boost))

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
        sup_count = len(evidence_result.get("supporting_sources",    []))
        con_count = len(evidence_result.get("contradicting_sources", []))
        neu_count = len(evidence_result.get("neutral_sources",       []))

        if con_count > 0 and con_count >= sup_count:
            ev_summary = (
                f"{con_count} trusted source(s) contradicted or "
                f"flagged this claim as false or misleading"
            )
        elif sup_count > 0:
            ev_summary = f"{sup_count} trusted source(s) corroborated this claim"
        else:
            ev_summary = (
                f"{neu_count} trusted source(s) referenced this topic "
                f"without a clear stance"
            )
        reasoning.append(
            f"{ev_summary} (avg. trust: {avg_trust}/100)."
        )
    else:
        reasoning.append(
            "Live verification found no results from trusted news sources. "
            "Verdict relies on ML model and linguistic analysis only."
        )

    # 3. Fact-check override notice
    if fc_articles:
        fc_names = ", ".join(a.get("source_name", "") for a in fc_articles[:2])
        reasoning.append(
            f"Dedicated fact-check source(s) {fc_names} explicitly contradict "
            f"this claim — this overrides borderline ML predictions."
        )

    # 4. Linguistic signals
    fake_n = linguistic_signals.get("fake_signal_count", 0)
    real_n = linguistic_signals.get("real_signal_count", 0)

    if fake_n > 0:
        sigs = ", ".join(
            f'"{s}"' for s in linguistic_signals.get("fake_signals_found", [])[:3]
        )
        reasoning.append(
            f"Text contains {fake_n} misinformation/sensationalism "
            f"marker(s): {sigs}."
        )

    if real_n > 0:
        sigs = ", ".join(
            f'"{s}"' for s in linguistic_signals.get("real_signals_found", [])[:3]
        )
        reasoning.append(
            f"Text contains {real_n} credible journalistic "
            f"language marker(s): {sigs}."
        )

    # 5. Named sources
    sup = evidence_result.get("supporting_sources",    [])
    con = evidence_result.get("contradicting_sources", [])
    if sup:
        reasoning.append(f"Corroborating source(s): {', '.join(sup[:3])}.")
    if con:
        reasoning.append(f"Source(s) that contradicted this claim: {', '.join(con[:3])}.")

    # 6. Confidence label
    if overall_conf >= CONF_HIGH_FLOOR:
        conf_label = "High confidence"
    elif overall_conf >= CONF_MEDIUM_FLOOR:
        conf_label = "Moderate confidence"
    else:
        conf_label = "Low confidence"

    reasoning.append(
        f"{conf_label} — combined decision score: {combined:+.3f}."
    )

    return {
        "verdict":              verdict,
        "overall_confidence":   overall_conf,
        "ml_confidence":        ml_conf_pct,
        "evidence_confidence":  ev_conf_pct,
        "linguistic_confidence": ling_conf,
        "fact_confidence":      fact_conf,
        "reasoning":            reasoning,
        "combined_score":       combined,
        "verdict_meta":         VERDICT_META.get(verdict, VERDICT_META["UNVERIFIED"]),
    }


# ── Verified Fact Generator ───────────────────────────────────────────────────

def generate_verified_fact(
    verdict:            str,
    primary_claim:      str,
    evidence_result:    dict,
    linguistic_signals: dict,
) -> dict:
    """
    Build a structured "Verified Fact" block from search evidence.

    NEVER HALLUCINATE — only uses what search.py returned.
    Falls back to "Insufficient evidence" when sources are absent.

    Returns
    -------
    dict with keys:
        type:             'verified' | 'debunked' | 'mixed' | 'insufficient'
        summary:          str  (human-readable summary)
        official_source:  str  (name of best source)
        official_url:     str  (URL of best source)
        publication_date: str
        related_info:     list[str]  (headline snippets)
        misconception:    str  (for FAKE / LIKELY FAKE only)
        correct_fact:     str  (for FAKE / LIKELY FAKE only)
        trusted_sources:  list[str]  (top source names used)
    """
    articles  = evidence_result.get("articles", [])
    ev_sources = evidence_result.get("sources_found", 0)

    sup_articles = [a for a in articles if a.get("classification") == "supporting"]
    con_articles = [a for a in articles if a.get("classification") == "contradicting"]
    fc_articles  = [a for a in con_articles if a.get("is_fact_check")]

    base: dict = {
        "type":             "insufficient",
        "summary":          "",
        "official_source":  "",
        "official_url":     "",
        "publication_date": "",
        "related_info":     [],
        "misconception":    "",
        "correct_fact":     "",
        "trusted_sources":  [],
    }

    if ev_sources == 0:
        base["summary"] = (
            "No trusted evidence available for this claim. "
            "The system cannot confirm or deny it without authoritative sources."
        )
        return base

    v = verdict.upper()

    if v in ("REAL", "LIKELY REAL"):
        base["type"] = "verified"
        ref = sup_articles or articles[:2]
        if ref:
            a = ref[0]
            base["official_source"]  = a.get("source_name", "")
            base["official_url"]     = a.get("url", "")
            base["publication_date"] = a.get("date", "")

            # Build summary from snippets — never invent sentences
            snips = [
                a.get("snippet", "") for a in ref[:3]
                if a.get("snippet") and len(a.get("snippet", "")) > 20
            ]
            if snips:
                base["summary"] = snips[0][:300]
            else:
                base["summary"] = (
                    f"This claim is supported by "
                    f"{a.get('source_name', 'trusted sources')}."
                )

            base["related_info"] = [
                f"{a.get('source_name', '')}: {a.get('title', '')[:100]}"
                for a in ref[:3] if a.get("title")
            ]
        base["trusted_sources"] = [a.get("source_name", "") for a in ref[:3]]

    elif v in ("FAKE", "LIKELY FAKE"):
        base["type"] = "debunked"
        ref = fc_articles or con_articles   # prefer dedicated fact-check sites

        if ref:
            a = ref[0]
            base["official_source"]  = a.get("source_name", "")
            base["official_url"]     = a.get("url", "")
            base["publication_date"] = a.get("date", "")

            snips = [
                a.get("snippet", "") for a in ref[:3]
                if a.get("snippet") and len(a.get("snippet", "")) > 20
            ]
            if snips:
                base["summary"] = snips[0][:300]
            else:
                base["summary"] = (
                    f"This claim has been identified as false or misleading "
                    f"by {a.get('source_name', 'trusted sources')}."
                )

            # Misconception: pull fake linguistic signals
            fake_sigs = linguistic_signals.get("fake_signals_found", [])
            if fake_sigs:
                base["misconception"] = (
                    f"This content uses known misinformation markers: "
                    f"{', '.join(fake_sigs[:3])}."
                )

            # Correct fact: take snippet from a supporting source if available
            if sup_articles:
                snip = sup_articles[0].get("snippet", "")
                if snip:
                    base["correct_fact"] = snip[:250]

            base["related_info"] = [
                f"{a.get('source_name', '')}: {a.get('title', '')[:100]}"
                for a in ref[:3] if a.get("title")
            ]
        base["trusted_sources"] = [a.get("source_name", "") for a in ref[:3]] if ref else []

    elif v in ("PARTIALLY TRUE",):
        base["type"] = "mixed"
        all_ref = (sup_articles + con_articles)[:4]
        if all_ref:
            base["official_source"]  = all_ref[0].get("source_name", "")
            base["official_url"]     = all_ref[0].get("url", "")
            base["publication_date"] = all_ref[0].get("date", "")
            base["summary"] = (
                "This claim contains some factual elements but lacks full accuracy. "
                "Some trusted sources support it while others provide different context."
            )
            base["related_info"] = [
                f"{a.get('source_name', '')}: {a.get('title', '')[:100]}"
                for a in all_ref if a.get("title")
            ]
        base["trusted_sources"] = [a.get("source_name", "") for a in all_ref[:3]]

    else:
        # UNVERIFIED, MIXED, MISLEADING, INSUFFICIENT EVIDENCE
        base["type"]    = "insufficient"
        base["summary"] = (
            f"The available evidence is {v.lower()} or insufficient "
            f"to make a definitive determination. "
            f"Found {ev_sources} trusted source(s) but no clear consensus."
        )
        if articles:
            base["related_info"] = [
                f"{a.get('source_name', '')}: {a.get('title', '')[:100]}"
                for a in articles[:3] if a.get("title")
            ]
            base["trusted_sources"] = [a.get("source_name", "") for a in articles[:3]]

    return base
