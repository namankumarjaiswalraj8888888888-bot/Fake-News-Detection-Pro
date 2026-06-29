"""
export.py
=========
Version 4 — Export verification results as PDF, TXT, or JSON.

Uses only stdlib + fpdf2 (pure-Python PDF, no system dependencies).
fpdf2 is optional — if missing, PDF export gracefully falls back to TXT.

AI Fake News Detection & Live Verification System — Version 4
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar & Parmeshwar
"""

from __future__ import annotations

import json
import os
import tempfile
import textwrap
from datetime import datetime
from typing import Optional

from config import (
    APP_TITLE, APP_VERSION, INSTITUTION, DEVELOPERS,
    EXPORT_PDF_FONT,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _verdict_label(verdict: str) -> str:
    return {"REAL": "✅ REAL", "FAKE": "❌ FAKE"}.get(verdict, "⚠️ UNVERIFIED")


def _safe_text(text: str, max_chars: int = 300) -> str:
    """Truncate and strip non-printable characters for safe embedding."""
    return "".join(c if c.isprintable() or c in "\n\t" else " " for c in text[:max_chars])


def _dev_names() -> str:
    return ", ".join(d["name"] for d in DEVELOPERS[:2])


# ── TXT Export ────────────────────────────────────────────────────────────────

def export_txt(result: dict, query_text: str = "") -> str:
    """
    Write a plain-text verification report to a temp file.
    Returns the file path.
    """
    verdict  = result.get("verdict", "UNVERIFIED")
    overall  = result.get("overall_confidence", 0)
    ml_conf  = result.get("ml_confidence", 0)
    ev_conf  = result.get("evidence_confidence", 0)
    elapsed  = result.get("elapsed_seconds", 0)
    ml_name  = result.get("ml_result", {}).get("model_name", "—")
    keywords = result.get("keywords", [])
    reasoning = result.get("reasoning", [])
    articles  = result.get("evidence_result", {}).get("articles", [])
    sources   = result.get("evidence_result", {}).get("sources_found", 0)

    sep  = "=" * 70
    sep2 = "-" * 70
    lines: list[str] = [
        sep,
        f"  {APP_TITLE}",
        f"  Version {APP_VERSION}  |  {INSTITUTION}",
        f"  Developed by: {_dev_names()}",
        sep,
        "",
        f"  Verification Report — {_timestamp()}",
        f"  Analysis time: {elapsed}s",
        "",
        sep2,
        "  QUERY",
        sep2,
        textwrap.fill(_safe_text(query_text or result.get("original_text", ""), 500),
                      width=70, initial_indent="  ", subsequent_indent="  "),
        "",
        sep2,
        "  VERDICT",
        sep2,
        f"  {_verdict_label(verdict)}",
        f"  Overall Confidence  : {overall}%",
        f"  ML Model Confidence : {ml_conf}%   [{ml_name}]",
        f"  Evidence Confidence : {ev_conf}%   [{sources} trusted source(s) found]",
        "",
        sep2,
        "  AI REASONING",
        sep2,
    ]

    for i, r in enumerate(reasoning, 1):
        lines.append(f"  {i}. {_safe_text(r, 400)}")

    if keywords:
        lines += ["", sep2, "  KEYWORDS DETECTED", sep2,
                  "  " + ", ".join(keywords)]

    if articles:
        lines += ["", sep2, "  EVIDENCE SOURCES", sep2]
        for a in articles[:6]:
            cls  = a.get("classification", "neutral").upper()
            name = a.get("source_name", a.get("domain", "Unknown"))
            ts   = a.get("trust_score", 0)
            titl = _safe_text(a.get("title", ""), 120)
            url  = a.get("url", "")
            lines += [
                f"  [{cls}] {name}  (Trust: {ts}/100)",
                f"  Title  : {titl}",
                f"  URL    : {url}",
                "",
            ]

    lines += [
        sep,
        "  DISCLAIMER",
        sep2,
        "  This tool is an AI assistant for educational and research purposes.",
        "  Always cross-reference with multiple authoritative sources.",
        "  The system never claims 100% certainty.",
        "",
        f"  © {APP_TITLE} — {INSTITUTION}",
        sep,
    ]

    fd, path = tempfile.mkstemp(suffix=".txt", prefix="fakenews_report_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


# ── JSON Export ───────────────────────────────────────────────────────────────

def export_json(result: dict, query_text: str = "") -> str:
    """
    Write the full verification result as pretty-printed JSON to a temp file.
    Returns the file path.
    """
    payload = {
        "report_meta": {
            "app":       APP_TITLE,
            "version":   APP_VERSION,
            "timestamp": _timestamp(),
            "developers": _dev_names(),
            "institution": INSTITUTION,
        },
        "query":        query_text or result.get("original_text", ""),
        "verdict":      result.get("verdict", "UNVERIFIED"),
        "confidence": {
            "overall":  result.get("overall_confidence", 0),
            "ml":       result.get("ml_confidence",      0),
            "evidence": result.get("evidence_confidence", 0),
        },
        "ml": {
            "model":      result.get("ml_result", {}).get("model_name", "—"),
            "label":      result.get("ml_result", {}).get("label", "—"),
            "prob_real":  result.get("ml_result", {}).get("prob_real", 0),
            "prob_fake":  result.get("ml_result", {}).get("prob_fake", 0),
        },
        "keywords":     result.get("keywords", []),
        "reasoning":    result.get("reasoning", []),
        "evidence": {
            "sources_found":         result.get("evidence_result", {}).get("sources_found", 0),
            "avg_trust_score":       result.get("evidence_result", {}).get("avg_trust_score", 0),
            "supporting_sources":    result.get("evidence_result", {}).get("supporting_sources", []),
            "contradicting_sources": result.get("evidence_result", {}).get("contradicting_sources", []),
            "neutral_sources":       result.get("evidence_result", {}).get("neutral_sources", []),
            "articles": [
                {
                    "title":          a.get("title", ""),
                    "url":            a.get("url", ""),
                    "source_name":    a.get("source_name", ""),
                    "trust_score":    a.get("trust_score", 0),
                    "classification": a.get("classification", "neutral"),
                    "date":           a.get("date", ""),
                }
                for a in result.get("evidence_result", {}).get("articles", [])[:8]
            ],
        },
        "linguistic": {
            "fake_signals": result.get("linguistic_signals", {}).get("fake_signal_count", 0),
            "real_signals": result.get("linguistic_signals", {}).get("real_signal_count", 0),
            "sensationalism_score": result.get("linguistic_signals", {}).get("sensationalism_score", 0),
            "caps_ratio":   result.get("linguistic_signals", {}).get("caps_ratio", 0),
        },
        "elapsed_seconds": result.get("elapsed_seconds", 0),
    }

    fd, path = tempfile.mkstemp(suffix=".json", prefix="fakenews_report_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


# ── PDF Export ────────────────────────────────────────────────────────────────

def export_pdf(result: dict, query_text: str = "") -> Optional[str]:
    """
    Write a formatted PDF report. Returns file path or None if fpdf2 missing.
    Falls back to TXT export if fpdf2 is not installed.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        return export_txt(result, query_text)

    verdict  = result.get("verdict", "UNVERIFIED")
    overall  = result.get("overall_confidence", 0)
    ml_conf  = result.get("ml_confidence", 0)
    ev_conf  = result.get("evidence_confidence", 0)
    elapsed  = result.get("elapsed_seconds", 0)
    ml_name  = result.get("ml_result", {}).get("model_name", "—")
    keywords = result.get("keywords", [])
    reasoning = result.get("reasoning", [])
    articles  = result.get("evidence_result", {}).get("articles", [])
    sources   = result.get("evidence_result", {}).get("sources_found", 0)

    VERDICT_COLORS = {
        "REAL":       (34, 197, 94),
        "FAKE":       (239, 68, 68),
        "UNVERIFIED": (234, 179, 8),
    }
    color = VERDICT_COLORS.get(verdict, (107, 114, 128))

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    F = EXPORT_PDF_FONT

    # Header band
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 32, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(F, "B", 14)
    pdf.set_xy(10, 8)
    pdf.cell(0, 7, APP_TITLE, ln=True)
    pdf.set_font(F, "", 9)
    pdf.set_x(10)
    pdf.cell(0, 5, f"Version {APP_VERSION}  |  {INSTITUTION}  |  {_timestamp()}", ln=True)
    pdf.set_x(10)
    pdf.cell(0, 5, f"Developed by: {_dev_names()}", ln=True)
    pdf.set_text_color(0, 0, 0)

    pdf.ln(6)

    def section(title: str) -> None:
        pdf.set_font(F, "B", 10)
        pdf.set_fill_color(241, 245, 249)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 7, f"  {title}", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)

    def body(text: str, indent: int = 8) -> None:
        pdf.set_font(F, "", 9)
        pdf.set_x(indent)
        pdf.multi_cell(0, 5, _safe_text(text, 500))

    # Query
    section("QUERY")
    body(query_text or result.get("original_text", ""))
    pdf.ln(3)

    # Verdict box
    section("VERDICT")
    pdf.set_fill_color(*color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(F, "B", 16)
    pdf.set_x(8)
    label = {"REAL": "REAL — Likely Credible",
             "FAKE": "FAKE — Likely Misinformation"}.get(verdict, "UNVERIFIED")
    pdf.cell(0, 12, f"  {label}", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    pdf.set_font(F, "", 9)
    for label_, val in [
        (f"Overall Confidence", f"{overall}%"),
        (f"ML Confidence [{ml_name}]", f"{ml_conf}%"),
        (f"Evidence Confidence [{sources} sources]", f"{ev_conf}%"),
        (f"Analysis Time", f"{elapsed}s"),
    ]:
        pdf.set_x(8)
        pdf.set_font(F, "B", 9)
        pdf.cell(80, 5, label_, border=0)
        pdf.set_font(F, "", 9)
        pdf.cell(0, 5, val, ln=True)
    pdf.ln(3)

    # Reasoning
    section("AI REASONING")
    for i, r in enumerate(reasoning, 1):
        body(f"{i}. {r}")
    pdf.ln(3)

    # Keywords
    if keywords:
        section("KEYWORDS DETECTED")
        body(", ".join(keywords))
        pdf.ln(3)

    # Evidence sources
    if articles:
        section("EVIDENCE SOURCES")
        for a in articles[:6]:
            cls  = a.get("classification", "neutral").upper()
            name = a.get("source_name", "Unknown")
            ts   = a.get("trust_score", 0)
            titl = a.get("title", "")[:100]
            url  = a.get("url", "")[:100]

            cls_color = {
                "SUPPORTING":    (34, 197, 94),
                "CONTRADICTING": (239, 68, 68),
            }.get(cls, (107, 114, 128))

            pdf.set_x(8)
            pdf.set_fill_color(*cls_color)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font(F, "B", 8)
            pdf.cell(28, 5, f" {cls}", fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font(F, "", 9)
            pdf.cell(0, 5, f"  {name}  (Trust: {ts}/100)", ln=True)
            body(titl)
            pdf.set_x(8)
            pdf.set_font(F, "I", 8)
            pdf.set_text_color(59, 130, 246)
            pdf.cell(0, 5, url, ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(1)
        pdf.ln(2)

    # Footer
    pdf.set_fill_color(241, 245, 249)
    pdf.rect(0, pdf.get_y(), 210, 20, "F")
    pdf.set_font(F, "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.set_x(8)
    pdf.multi_cell(
        0, 4,
        "DISCLAIMER: This tool is for educational and research purposes only. "
        "Always cross-reference with multiple authoritative sources. "
        f"© {APP_TITLE} — {INSTITUTION}",
    )

    fd, path = tempfile.mkstemp(suffix=".pdf", prefix="fakenews_report_")
    os.close(fd)
    pdf.output(path)
    return path


# ── Formatted Report String (for Copy button) ────────────────────────────────

def format_report_text(result: dict, query_text: str = "") -> str:
    """Return a clean multi-line report string for clipboard copying."""
    verdict  = result.get("verdict", "UNVERIFIED")
    overall  = result.get("overall_confidence", 0)
    ml_conf  = result.get("ml_confidence", 0)
    ev_conf  = result.get("evidence_confidence", 0)
    ml_name  = result.get("ml_result", {}).get("model_name", "—")
    elapsed  = result.get("elapsed_seconds", 0)
    keywords = result.get("keywords", [])
    reasoning = result.get("reasoning", [])
    sources  = result.get("evidence_result", {}).get("sources_found", 0)
    articles = result.get("evidence_result", {}).get("articles", [])

    lines = [
        f"{'='*60}",
        f"AI FAKE NEWS DETECTION REPORT — {_timestamp()}",
        f"{'='*60}",
        f"",
        f"QUERY: {_safe_text(query_text or result.get('original_text',''), 200)}",
        f"",
        f"VERDICT: {_verdict_label(verdict)}",
        f"Overall Confidence  : {overall}%",
        f"ML Confidence       : {ml_conf}%  [{ml_name}]",
        f"Evidence Confidence : {ev_conf}%  [{sources} source(s)]",
        f"Analysis Time       : {elapsed}s",
        f"",
        f"{'─'*60}",
        f"AI REASONING:",
        f"{'─'*60}",
    ]
    for i, r in enumerate(reasoning, 1):
        lines.append(f"{i}. {r}")

    if keywords:
        lines += ["", f"KEYWORDS: {', '.join(keywords)}"]

    if articles:
        lines += ["", f"{'─'*60}", "EVIDENCE SOURCES:", f"{'─'*60}"]
        for a in articles[:5]:
            cls  = a.get("classification", "neutral").upper()
            name = a.get("source_name", "")
            ts   = a.get("trust_score", 0)
            titl = a.get("title", "")[:100]
            url  = a.get("url", "")
            lines += [f"[{cls}] {name} (Trust: {ts}/100)", f"  {titl}", f"  {url}", ""]

    lines += [
        f"{'='*60}",
        f"Developed by: {_dev_names()} | {INSTITUTION}",
        f"{'='*60}",
    ]
    return "\n".join(lines)
