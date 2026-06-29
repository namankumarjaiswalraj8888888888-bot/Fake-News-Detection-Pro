"""
fact_checker.py
===============
Version 4 — Pipeline orchestrator with URL support and richer output.

Changes from V3
---------------
- All config values imported from config.py
- Content-length guard delegates to search.py (already handled there)
- Better error messages for URL failures
- Logging improved for production debugging

AI Fake News Detection & Live Verification System — Version 4
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar & Parmeshwar
"""

from __future__ import annotations

import logging
import re
import time

from config import TEXT_MAX_LENGTH, TEXT_MIN_LENGTH
from utils import (
    clean_text,
    extract_claims,
    extract_keywords,
    extract_primary_claim,
    analyze_linguistic_signals,
    predict_ml,
    make_final_decision,
)
from search import (
    search_multiple_queries,
    analyze_search_results,
    build_search_queries,
    extract_article_text,
)

logger = logging.getLogger(__name__)

_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)


def _looks_like_url(text: str) -> bool:
    return bool(_URL_RE.match(text.strip()))


# ── URL Resolution ────────────────────────────────────────────────────────────

def resolve_input(user_input: str) -> tuple[str, dict]:
    """
    If user_input is a URL, fetch and return the article text + metadata.
    Otherwise return (user_input, {is_url: False}).
    """
    user_input = user_input.strip()
    if not _looks_like_url(user_input):
        return user_input, {"is_url": False}

    logger.info("URL mode — fetching: %s", user_input[:100])
    article = extract_article_text(user_input)

    meta = {
        "is_url":        True,
        "url":           user_input,
        "article_title": article.get("title", ""),
        "article_date":  article.get("date",  ""),
        "domain":        article.get("domain", ""),
        "fetch_success": article.get("success", False),
        "fetch_error":   article.get("error"),
    }

    if not article["success"] or len(article.get("text", "").strip()) < 30:
        error_msg = (
            article.get("error")
            or "Article text too short to analyse. "
               "The page may be paywalled or require JavaScript."
        )
        return "", meta | {"error": error_msg}

    text = article["text"]
    if article.get("title"):
        text = article["title"] + ". " + text
    return text, meta


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def check_news(user_input: str) -> dict:
    """
    Full V4 fake-news detection pipeline.

    Parameters
    ----------
    user_input : str
        Raw news text, headline, or a URL to a news article.

    Returns
    -------
    dict — see keys below
    """
    start_time = time.time()

    # ── Input validation ──────────────────────────────────────────────────────
    if not user_input or not isinstance(user_input, str):
        return _error_result("No input provided.")
    user_input = user_input.strip()
    if len(user_input) < TEXT_MIN_LENGTH:
        return _error_result(
            f"Input is too short (minimum {TEXT_MIN_LENGTH} characters). "
            "Please enter a news headline, article text, or a valid URL."
        )

    # ── Step 0: URL resolution ────────────────────────────────────────────────
    text, url_meta = resolve_input(user_input)

    if url_meta.get("is_url") and not text:
        return (
            _error_result(url_meta.get("error") or "Could not extract article text from the URL.")
            | {"url_meta": url_meta}
        )

    if not text:
        text = user_input

    if len(text) > TEXT_MAX_LENGTH:
        text = text[:TEXT_MAX_LENGTH]

    logger.info(
        "check_news — length=%d | url=%s",
        len(text), url_meta.get("is_url", False),
    )

    # ── Step 1: Clean text ────────────────────────────────────────────────────
    cleaned = clean_text(text)

    # ── Step 2: Extract claims, primary claim, keywords ───────────────────────
    claims        = extract_claims(cleaned)
    primary_claim = extract_primary_claim(cleaned)
    keywords      = extract_keywords(cleaned)

    logger.info("Primary claim: %s", primary_claim[:80])
    logger.info("Keywords: %s", keywords[:5])

    # ── Step 3: Linguistic analysis ───────────────────────────────────────────
    linguistic_signals = analyze_linguistic_signals(text)
    logger.info(
        "Linguistic — fake: %d | real: %d",
        linguistic_signals["fake_signal_count"],
        linguistic_signals["real_signal_count"],
    )

    # ── Step 4: ML prediction ─────────────────────────────────────────────────
    ml_result = predict_ml(cleaned)
    logger.info(
        "ML (%s) — %s @ %.2f",
        ml_result.get("model_name", "?"),
        ml_result["label"],
        ml_result["confidence"],
    )

    # ── Step 5: Build search queries ──────────────────────────────────────────
    search_queries = build_search_queries(primary_claim, keywords)
    logger.info("Search queries: %s", search_queries[:3])

    # ── Step 6: Live web search & evidence analysis ───────────────────────────
    _empty_evidence: dict = {
        "sources_found":         0,
        "total_results":         0,
        "supporting_sources":    [],
        "contradicting_sources": [],
        "neutral_sources":       [],
        "evidence_score":        0.0,
        "evidence_confidence":   0,
        "avg_trust_score":       0,
        "articles":              [],
        "all_results":           [],
        "search_performed":      False,
        "search_error":          None,
    }

    try:
        raw_results = search_multiple_queries(search_queries, max_results_per_query=6)
        if raw_results:
            evidence_result = analyze_search_results(raw_results, primary_claim)
            evidence_result["search_performed"] = True
        else:
            evidence_result = {
                **_empty_evidence,
                "search_performed": True,
                "search_error":     "No results returned from any search source.",
            }
    except Exception as exc:
        logger.warning("Search step failed: %s", exc)
        evidence_result = {**_empty_evidence, "search_error": str(exc)}

    logger.info(
        "Evidence — sources: %d | score: %.4f | ev_conf: %d%%",
        evidence_result["sources_found"],
        evidence_result["evidence_score"],
        evidence_result.get("evidence_confidence", 0),
    )

    # ── Step 7: Final decision ─────────────────────────────────────────────────
    decision = make_final_decision(ml_result, evidence_result, linguistic_signals)

    elapsed = round(time.time() - start_time, 2)
    logger.info(
        "Decision — %s | overall: %d%% | ml: %d%% | ev: %d%% (%.2fs)",
        decision["verdict"],
        decision["overall_confidence"],
        decision["ml_confidence"],
        decision["evidence_confidence"],
        elapsed,
    )

    return {
        # Input
        "original_text":       user_input,
        "cleaned_text":        cleaned,
        "claims":              claims,
        "primary_claim":       primary_claim,
        "keywords":            keywords,
        "url_meta":            url_meta,
        # ML
        "ml_result":           ml_result,
        # Linguistics
        "linguistic_signals":  linguistic_signals,
        # Evidence
        "evidence_result":     evidence_result,
        # Final verdict
        "verdict":             decision["verdict"],
        "overall_confidence":  decision["overall_confidence"],
        "ml_confidence":       decision["ml_confidence"],
        "evidence_confidence": decision["evidence_confidence"],
        "confidence":          decision["overall_confidence"],   # backward compat
        "reasoning":           decision["reasoning"],
        "combined_score":      decision["combined_score"],
        # Meta
        "elapsed_seconds":     elapsed,
        "error":               None,
    }


# ── Error Result Template ─────────────────────────────────────────────────────

def _error_result(message: str) -> dict:
    return {
        "original_text":       "",
        "cleaned_text":        "",
        "claims":              [],
        "primary_claim":       "",
        "keywords":            [],
        "url_meta":            {"is_url": False},
        "ml_result": {
            "label": "UNVERIFIED", "confidence": 0.5,
            "prob_real": 0.5, "prob_fake": 0.5,
            "ml_confidence": 50, "model_name": "—",
        },
        "linguistic_signals":  {},
        "evidence_result": {
            "sources_found": 0, "articles": [], "all_results": [],
            "evidence_score": 0.0, "evidence_confidence": 0, "avg_trust_score": 0,
        },
        "verdict":             "UNVERIFIED",
        "overall_confidence":  0,
        "ml_confidence":       0,
        "evidence_confidence": 0,
        "confidence":          0,
        "reasoning":           [message],
        "combined_score":      0.0,
        "elapsed_seconds":     0.0,
        "error":               message,
    }
