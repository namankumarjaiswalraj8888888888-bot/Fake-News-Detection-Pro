"""
fact_checker.py
===============
Version 5 — Pipeline orchestrator with URL support and 9-verdict output.

Changes from V4
---------------
- Calls generate_verified_fact() and adds 'verified_fact' key to output.
- make_final_decision() now returns 9 verdicts (via upgraded utils.py).
- 'linguistic_confidence' and 'fact_confidence' keys added to output.
- URL resolve step now logs domain + article length before proceeding.
- Empty-text guard raised from 30 chars to ARTICLE_MIN_LENGTH (config).
- _error_result() updated to carry all V5 confidence keys for safe UI access.
- All search exceptions now produce a structured error message, not a crash.

AI Fake News Detection & Live Verification System — Version 5
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar, Parmeshwar Kumar, Amit Kumar,
              Prince Kumar Chaurasiya, Dhiraj Kumar, MD. Tausim Akhtar
"""

from __future__ import annotations

import logging
import re
import time

from config import TEXT_MAX_LENGTH, ARTICLE_MIN_LENGTH
from utils import (
    clean_text,
    extract_claims,
    extract_keywords,
    extract_primary_claim,
    analyze_linguistic_signals,
    predict_ml,
    make_final_decision,
    generate_verified_fact,
)
from search import (
    search_multiple_queries,
    analyze_search_results,
    build_search_queries,
    extract_article_text,
)

logger = logging.getLogger(__name__)

_URL_RE = re.compile(r"^https?://\S+", re.IGNORECASE)


def _looks_like_url(text: str) -> bool:
    return bool(_URL_RE.match(text.strip()))


# ── URL Resolver ──────────────────────────────────────────────────────────────

def resolve_input(user_input: str) -> tuple[str, dict]:
    """
    If user_input is a URL, fetch and return the article text.
    Otherwise return (user_input, {is_url: False}).

    Returns
    -------
    (text_to_analyse, url_meta)
    url_meta keys: is_url, url, article_title, article_date, domain,
                   fetch_success, fetch_error
    """
    user_input = user_input.strip()
    if not _looks_like_url(user_input):
        return user_input, {"is_url": False}

    logger.info("URL mode — fetching: %s", user_input[:120])
    article = extract_article_text(user_input)

    meta: dict = {
        "is_url":        True,
        "url":           user_input,
        "article_title": article.get("title",   ""),
        "article_date":  article.get("date",    ""),
        "domain":        article.get("domain",  ""),
        "fetch_success": article.get("success", False),
        "fetch_error":   article.get("error"),
    }

    text = article.get("text", "").strip()
    logger.info(
        "URL fetch — domain=%s | length=%d | success=%s",
        meta["domain"], len(text), meta["fetch_success"],
    )

    if not meta["fetch_success"] or len(text) < ARTICLE_MIN_LENGTH:
        error_msg = article.get("error") or "Article text too short or unavailable."
        return "", meta | {"fetch_error": error_msg}

    # Prepend title for better claim / keyword extraction
    if article.get("title"):
        text = article["title"] + ". " + text

    return text, meta


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def check_news(user_input: str) -> dict:
    """
    Full V5 pipeline — 9-verdict fake-news detection.

    Steps
    -----
    0. URL resolution (optional)
    1. Text cleaning
    2. Claim / keyword extraction
    3. Linguistic signal analysis
    4. ML prediction
    5. Build search queries
    6. Live web search + trusted-source evidence analysis
    7. Weighted 9-verdict decision (V5 weights: ML 30 %, Evidence 50 %, Ling 20 %)
    8. Verified Fact block generation

    Parameters
    ----------
    user_input : str
        Raw news text, headline, or news article URL.

    Returns
    -------
    dict — all keys listed at the bottom of this function.
    """
    start_time = time.time()

    # ── Input validation ──────────────────────────────────────────────────────
    if not user_input or not isinstance(user_input, str):
        return _error_result("No input provided.")
    user_input = user_input.strip()
    if len(user_input) < 5:
        return _error_result(
            "Input is too short. Please enter at least 5 characters or a valid URL."
        )

    # ── Step 0: URL resolution ────────────────────────────────────────────────
    text, url_meta = resolve_input(user_input)

    if url_meta.get("is_url") and not text:
        return _error_result(
            url_meta.get("fetch_error") or "Could not extract article text from the URL."
        ) | {"url_meta": url_meta}

    if not text:
        text = user_input

    # Truncate to processing limit
    if len(text) > TEXT_MAX_LENGTH:
        logger.debug("Text truncated from %d to %d chars", len(text), TEXT_MAX_LENGTH)
        text = text[:TEXT_MAX_LENGTH]

    logger.info("check_news — length=%d | url_mode=%s", len(text), url_meta.get("is_url", False))

    # ── Step 1: Clean text ─────────────────────────────────────────────────────
    cleaned = clean_text(text)

    # ── Step 2: Claims + keywords ──────────────────────────────────────────────
    claims        = extract_claims(cleaned)
    primary_claim = extract_primary_claim(cleaned)
    keywords      = extract_keywords(cleaned, top_n=8)

    logger.info("Primary claim: %s", primary_claim[:80])
    logger.info("Top keywords:  %s", keywords[:5])

    # ── Step 3: Linguistic analysis ───────────────────────────────────────────
    linguistic_signals = analyze_linguistic_signals(text)
    logger.info(
        "Linguistics — fake_signals=%d | real_signals=%d | sensationalism=%d",
        linguistic_signals["fake_signal_count"],
        linguistic_signals["real_signal_count"],
        linguistic_signals["sensationalism_score"],
    )

    # ── Step 4: ML prediction ─────────────────────────────────────────────────
    ml_result = predict_ml(cleaned)
    logger.info(
        "ML (%s) — %s @ %.2f conf",
        ml_result.get("model_name", "?"),
        ml_result["label"],
        ml_result["confidence"],
    )

    # ── Step 5: Search query construction ────────────────────────────────────
    search_queries = build_search_queries(primary_claim, keywords)
    logger.info("Search queries (%d): %s", len(search_queries), search_queries[:2])

    # ── Step 6: Live search + evidence analysis ───────────────────────────────
    _empty_evidence: dict = {
        "sources_found":          0,
        "total_results":          0,
        "supporting_sources":     [],
        "contradicting_sources":  [],
        "neutral_sources":        [],
        "supporting_articles":    [],
        "contradicting_articles": [],
        "neutral_articles":       [],
        "evidence_score":         0.0,
        "evidence_confidence":    0,
        "avg_trust_score":        0,
        "articles":               [],
        "all_results":            [],
        "filtered_out":           0,
        "search_performed":       False,
        "search_error":           None,
    }

    try:
        raw_results = search_multiple_queries(search_queries, max_results_per_query=6)
        if raw_results:
            evidence_result = analyze_search_results(raw_results, primary_claim)
            evidence_result["search_performed"] = True
            evidence_result["search_error"]     = None
        else:
            evidence_result = {
                **_empty_evidence,
                "search_performed": True,
                "search_error":     "No results from any source — check network access.",
            }
    except Exception as exc:
        logger.warning("Search step failed: %s", exc)
        evidence_result = {
            **_empty_evidence,
            "search_performed": False,
            "search_error":     str(exc),
        }

    logger.info(
        "Evidence — trusted_sources=%d | score=%.4f | ev_conf=%d%% | filtered=%d",
        evidence_result["sources_found"],
        evidence_result["evidence_score"],
        evidence_result.get("evidence_confidence", 0),
        evidence_result.get("filtered_out", 0),
    )

    # ── Step 7: 9-Verdict decision ────────────────────────────────────────────
    decision = make_final_decision(ml_result, evidence_result, linguistic_signals)

    # ── Step 8: Verified Fact block ───────────────────────────────────────────
    verified_fact = generate_verified_fact(
        verdict=            decision["verdict"],
        primary_claim=      primary_claim,
        evidence_result=    evidence_result,
        linguistic_signals= linguistic_signals,
    )

    elapsed = round(time.time() - start_time, 2)
    logger.info(
        "check_news done — verdict=%s | overall=%d%% | ml=%d%% | ev=%d%% | %.2fs",
        decision["verdict"],
        decision["overall_confidence"],
        decision["ml_confidence"],
        decision["evidence_confidence"],
        elapsed,
    )

    return {
        # ── Input ─────────────────────────────────────────────────────────
        "original_text":       user_input,
        "cleaned_text":        cleaned,
        "claims":              claims,
        "primary_claim":       primary_claim,
        "keywords":            keywords,
        "url_meta":            url_meta,
        # ── ML ────────────────────────────────────────────────────────────
        "ml_result":           ml_result,
        # ── Linguistics ───────────────────────────────────────────────────
        "linguistic_signals":  linguistic_signals,
        # ── Evidence ─────────────────────────────────────────────────────
        "evidence_result":     evidence_result,
        # ── 9-Verdict decision ────────────────────────────────────────────
        "verdict":             decision["verdict"],
        "overall_confidence":  decision["overall_confidence"],
        "ml_confidence":       decision["ml_confidence"],
        "evidence_confidence": decision["evidence_confidence"],
        "linguistic_confidence": decision.get("linguistic_confidence", 0),
        "fact_confidence":     decision.get("fact_confidence", 0),
        "confidence":          decision["overall_confidence"],    # backward compat
        "reasoning":           decision["reasoning"],
        "combined_score":      decision["combined_score"],
        "verdict_meta":        decision["verdict_meta"],
        # ── Verified Fact ─────────────────────────────────────────────────
        "verified_fact":       verified_fact,
        # ── Meta ──────────────────────────────────────────────────────────
        "elapsed_seconds":     elapsed,
        "error":               None,
    }


# ── Error Result ──────────────────────────────────────────────────────────────

def _error_result(message: str) -> dict:
    """Return a fully-typed error dict so the UI never KeyErrors."""
    from constants import VERDICT_META
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
            "ml_confidence": 50, "model_name": "—", "error": message,
        },
        "linguistic_signals":  {},
        "evidence_result": {
            "sources_found": 0, "articles": [], "all_results": [],
            "evidence_score": 0.0, "evidence_confidence": 0,
            "avg_trust_score": 0, "supporting_sources": [],
            "contradicting_sources": [], "neutral_sources": [],
            "supporting_articles": [], "contradicting_articles": [],
            "neutral_articles": [], "filtered_out": 0,
            "search_performed": False, "search_error": message,
        },
        "verdict":             "UNVERIFIED",
        "overall_confidence":  0,
        "ml_confidence":       0,
        "evidence_confidence": 0,
        "linguistic_confidence": 0,
        "fact_confidence":     0,
        "confidence":          0,
        "reasoning":           [message],
        "combined_score":      0.0,
        "verdict_meta":        VERDICT_META["UNVERIFIED"],
        "verified_fact": {
            "type": "insufficient", "summary": message,
            "official_source": "", "official_url": "",
            "publication_date": "", "related_info": [],
            "misconception": "", "correct_fact": "",
            "trusted_sources": [],
        },
        "elapsed_seconds":     0.0,
        "error":               message,
    }
