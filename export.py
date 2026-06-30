"""
export.py
=========
Version 5 — Professional forensic verification report generator.

Changes from V4
---------------
- Report now includes all 5 V5 confidence components:
    Overall / ML / Evidence / Linguistic / Fact Confidence.
- Added 'Verified Fact' section to every export.
- Added 'Related Facts' section from verified_fact.related_info.
- _verdict_label() and _verdict_icon() now cover all 9 V5 verdicts
  (V4 only handled 3 → would KeyError on new verdicts).
- TXT export redesigned to look like a professional forensic audit report.
- JSON export includes verdict_meta dict for downstream consumers.
- PDF export (fpdf2) uses section headers and indented bullet layout.

AI Fake News Detection & Live Verification System — Version 5
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar, Parmeshwar Kumar, Amit Kumar,
              Prince Kumar Chaurasiya, Dhiraj Kumar, MD. Tausim Akhtar
"""

from __future__ import annotations

import io
import json
import logging
import re
from datetime import datetime

from config import APP_VERSION, INSTITUTION, BOARD, INTERNSHIP, DEVELOPERS

logger = logging.getLogger(__name__)

_DIVIDER  = "═" * 54
_THIN_DIV = "─" * 54


# ── Verdict Helpers ───────────────────────────────────────────────────────────

_VERDICT_ICONS: dict[str, str] = {
    "REAL":                 "✅",
    "LIKELY REAL":          "🟢",
    "PARTIALLY TRUE":       "🔵",
    "UNVERIFIED":           "⚠️",
    "INSUFFICIENT EVIDENCE":"❓",
    "MIXED":                "🟡",
    "MISLEADING":           "🟠",
    "LIKELY FAKE":          "🔴",
    "FAKE":                 "❌",
}

_VERDICT_LABELS: dict[str, str] = {
    "REAL":                 "REAL NEWS",
    "LIKELY REAL":          "LIKELY REAL",
    "PARTIALLY TRUE":       "PARTIALLY TRUE",
    "UNVERIFIED":           "UNVERIFIED",
    "INSUFFICIENT EVIDENCE":"INSUFFICIENT EVIDENCE",
    "MIXED":                "MIXED",
    "MISLEADING":           "MISLEADING",
    "LIKELY FAKE":          "LIKELY FAKE",
    "FAKE":                 "FAKE NEWS",
}


def _verdict_icon(verdict: str) -> str:
    return _VERDICT_ICONS.get(verdict.upper(), "❓")


def _verdict_label(verdict: str) -> str:
    return _VERDICT_LABELS.get(verdict.upper(), verdict.upper())


# ── ASCII Confidence Bar ──────────────────────────────────────────────────────

def _conf_bar(pct: int, width: int = 20) -> str:
    filled = max(0, min(width, round(pct / 100 * width)))
    return "█" * filled + "░" * (width - filled) + f"  {pct}%"


# ── TXT Export ────────────────────────────────────────────────────────────────

def export_txt(result: dict) -> str:
    """
    Generate a professional forensic verification report as plain text.
    Designed to look like an audit report — safe to print or share.
    """
    verdict       = result.get("verdict",       "UNVERIFIED")
    v_meta        = result.get("verdict_meta",  {})
    v_icon        = _verdict_icon(verdict)
    v_label       = _verdict_label(verdict)
    v_desc        = v_meta.get("description", "")
    ml_res        = result.get("ml_result",     {})
    ev_res        = result.get("evidence_result", {})
    ling          = result.get("linguistic_signals", {})
    vf            = result.get("verified_fact", {})
    url_meta      = result.get("url_meta",      {})
    ts            = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    elapsed       = result.get("elapsed_seconds", 0)

    lines: list[str] = []

    def ln(s: str = "") -> None:
        lines.append(s)

    ln(_DIVIDER)
    ln(f"  {APP_VERSION} — AI FAKE NEWS DETECTION REPORT")
    ln(_DIVIDER)
    ln(f"  Institution : {INSTITUTION}")
    ln(f"  Programme   : {BOARD}")
    ln(f"  Internship  : {INTERNSHIP}")
    ln(f"  Generated   : {ts}")
    ln(f"  Duration    : {elapsed:.2f} s")
    ln()

    # ── Query ─────────────────────────────────────────────────────────────────
    ln(f"  {_THIN_DIV}")
    ln("  QUERY")
    ln(f"  {_THIN_DIV}")
    if url_meta.get("is_url"):
        ln(f"  URL          : {url_meta.get('url', '')[:80]}")
        ln(f"  Domain       : {url_meta.get('domain', '')}")
        ln(f"  Article      : {url_meta.get('article_title', '')[:70]}")
        ln(f"  Date         : {url_meta.get('article_date', 'Unknown')}")
    else:
        raw = result.get("original_text", "")
        ln(f"  Input        : {raw[:140]}")
    ln(f"  Claim        : {result.get('primary_claim', '')[:140]}")
    kw = ", ".join(result.get("keywords", [])[:6])
    ln(f"  Keywords     : {kw}")
    ln()

    # ── Verdict ───────────────────────────────────────────────────────────────
    ln(f"  {_THIN_DIV}")
    ln("  VERDICT")
    ln(f"  {_THIN_DIV}")
    ln(f"  {v_icon}  {v_label}")
    if v_desc:
        ln(f"      {v_desc}")
    ln(f"  Score        : {result.get('combined_score', 0):+.4f}")
    ln()

    # ── Confidence ────────────────────────────────────────────────────────────
    ln(f"  {_THIN_DIV}")
    ln("  CONFIDENCE SCORES")
    ln(f"  {_THIN_DIV}")
    ln(f"  Overall     {_conf_bar(result.get('overall_confidence',    0))}")
    ln(f"  ML Model    {_conf_bar(result.get('ml_confidence',         0))}")
    ln(f"  Evidence    {_conf_bar(result.get('evidence_confidence',   0))}")
    ln(f"  Linguistic  {_conf_bar(result.get('linguistic_confidence', 0))}")
    ln(f"  Fact        {_conf_bar(result.get('fact_confidence',       0))}")
    ln()

    # ── ML Analysis ───────────────────────────────────────────────────────────
    ln(f"  {_THIN_DIV}")
    ln("  ML ANALYSIS")
    ln(f"  {_THIN_DIV}")
    ln(f"  Model        : {ml_res.get('model_name', '—')}")
    ln(f"  Prediction   : {ml_res.get('label', '—')}")
    ln(f"  Prob Real    : {ml_res.get('prob_real', 0)*100:.1f}%")
    ln(f"  Prob Fake    : {ml_res.get('prob_fake', 0)*100:.1f}%")
    ln()

    # ── Verified Fact ─────────────────────────────────────────────────────────
    ln(f"  {_THIN_DIV}")
    ln("  VERIFIED FACT")
    ln(f"  {_THIN_DIV}")
    vf_type    = vf.get("type",   "insufficient").upper()
    vf_summary = vf.get("summary", "")
    ln(f"  Status       : {vf_type}")
    if vf_summary:
        ln(f"  Summary      : {vf_summary[:200]}")
    if vf.get("official_source"):
        ln(f"  Source       : {vf.get('official_source', '')}")
    if vf.get("official_url"):
        ln(f"  Reference    : {vf.get('official_url', '')[:80]}")
    if vf.get("publication_date"):
        ln(f"  Published    : {vf.get('publication_date', '')}")
    if vf.get("misconception"):
        ln(f"  Misconception: {vf.get('misconception', '')[:200]}")
    if vf.get("correct_fact"):
        ln(f"  Correct Fact : {vf.get('correct_fact', '')[:200]}")
    ln()

    # ── Evidence ──────────────────────────────────────────────────────────────
    ln(f"  {_THIN_DIV}")
    ln("  EVIDENCE SUMMARY")
    ln(f"  {_THIN_DIV}")
    ln(f"  Trusted Sources  : {ev_res.get('sources_found', 0)}")
    ln(f"  Evidence Score   : {ev_res.get('evidence_score', 0):+.4f}")
    ln(f"  Avg Trust Score  : {ev_res.get('avg_trust_score', 0)}/100")

    sup = ev_res.get("supporting_sources",    [])
    con = ev_res.get("contradicting_sources", [])
    neu = ev_res.get("neutral_sources",       [])
    if sup:
        ln(f"  Supporting       : {', '.join(sup[:4])}")
    if con:
        ln(f"  Contradicting    : {', '.join(con[:4])}")
    if neu:
        ln(f"  Neutral          : {', '.join(neu[:4])}")
    ln()

    # ── Source Details ────────────────────────────────────────────────────────
    articles = ev_res.get("articles", [])
    if articles:
        ln(f"  {_THIN_DIV}")
        ln("  SOURCE DETAILS")
        ln(f"  {_THIN_DIV}")
        for i, a in enumerate(articles[:6], 1):
            cls = a.get("classification", "neutral").upper()
            ln(f"  [{i}] {a.get('source_name','?')} | Trust: {a.get('trust_score',0)}/100 | [{cls}]")
            title = a.get("title",   "")
            url   = a.get("url",     "")
            date  = a.get("date",    "")
            if title:
                ln(f"      {title[:72]}")
            if url:
                ln(f"      {url[:80]}")
            if date:
                ln(f"      Published: {date[:30]}")
            ln()

    # ── Reasoning ─────────────────────────────────────────────────────────────
    reasoning = result.get("reasoning", [])
    if reasoning:
        ln(f"  {_THIN_DIV}")
        ln("  REASONING")
        ln(f"  {_THIN_DIV}")
        for item in reasoning:
            for chunk in _wrap(item, 72):
                ln(f"  • {chunk}")
        ln()

    # ── Related Facts ─────────────────────────────────────────────────────────
    related = vf.get("related_info", [])
    if related:
        ln(f"  {_THIN_DIV}")
        ln("  RELATED FACTS")
        ln(f"  {_THIN_DIV}")
        for r in related[:4]:
            ln(f"  → {r[:80]}")
        ln()

    # ── Linguistic Analysis ───────────────────────────────────────────────────
    ln(f"  {_THIN_DIV}")
    ln("  LINGUISTIC ANALYSIS")
    ln(f"  {_THIN_DIV}")
    ln(f"  Word Count          : {ling.get('word_count',           0)}")
    ln(f"  Fake Signal Count   : {ling.get('fake_signal_count',    0)}")
    ln(f"  Real Signal Count   : {ling.get('real_signal_count',    0)}")
    ln(f"  Sensationalism Score: {ling.get('sensationalism_score', 0)}")
    ln(f"  Caps Ratio          : {ling.get('caps_ratio', 0)*100:.1f}%")
    ln(f"  Exclamation Marks   : {ling.get('exclamation_count',    0)}")
    ln()

    # ── Team & Footer ─────────────────────────────────────────────────────────
    ln(f"  {_THIN_DIV}")
    ln("  PROJECT TEAM")
    ln(f"  {_THIN_DIV}")
    for dev in DEVELOPERS:
        ln(f"  {dev['name']:<26} — {dev['role']}")
    ln()
    ln(f"  {INSTITUTION}")
    ln(f"  {BOARD}")
    ln(f"  {INTERNSHIP}")
    ln()
    ln(_DIVIDER)
    ln("  DISCLAIMER")
    ln(_DIVIDER)
    ln("  This report is produced by an AI system for research and")
    ln("  educational purposes. Always verify with authoritative")
    ln("  sources before making any decisions based on this report.")
    ln(_DIVIDER)

    return "\n".join(lines)


def _wrap(text: str, width: int) -> list[str]:
    words   = text.split()
    lines:  list[str] = []
    current = ""
    for w in words:
        if current and len(current) + 1 + len(w) > width:
            lines.append(current)
            current = w
        else:
            current = (current + " " + w).strip()
    if current:
        lines.append(current)
    return lines or [""]


# ── JSON Export ───────────────────────────────────────────────────────────────

def export_json(result: dict) -> str:
    """
    Return result as formatted JSON.
    Non-serialisable objects (numpy arrays etc.) are converted to strings.
    """
    def _safe(obj: object) -> object:
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        if isinstance(obj, dict):
            return {k: _safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_safe(x) for x in obj]
        return str(obj)

    payload = {
        "report_version":   APP_VERSION,
        "generated_at":     datetime.now().isoformat(),
        "institution":      INSTITUTION,
        "result":           _safe(result),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


# ── PDF Export (fpdf2) ────────────────────────────────────────────────────────

def export_pdf(result: dict) -> Optional[bytes]:  # type: ignore[name-defined]
    """
    Generate a PDF forensic report using fpdf2.
    Returns bytes on success, None if fpdf2 is not installed.
    """
    try:
        from fpdf import FPDF  # type: ignore[import]
    except ImportError:
        logger.warning("fpdf2 not installed — PDF export unavailable.")
        return None

    try:
        verdict  = result.get("verdict", "UNVERIFIED")
        v_label  = _verdict_label(verdict)
        v_icon   = _verdict_icon(verdict)
        ml_res   = result.get("ml_result",       {})
        ev_res   = result.get("evidence_result", {})
        vf       = result.get("verified_fact",   {})
        ts       = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

        # Strip emojis for PDF (PDF basic fonts don't support Unicode emoji)
        def _strip_emoji(s: str) -> str:
            return re.sub(r"[^\x00-\x7F]", "", s).strip()

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # ── Header ────────────────────────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 8, "AI Fake News Detection Report — V5", ln=True, align="C")
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 5, f"{INSTITUTION}  |  {BOARD}", ln=True, align="C")
        pdf.cell(0, 5, f"Generated: {ts}", ln=True, align="C")
        pdf.ln(3)
        pdf.set_draw_color(100, 100, 100)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        def _section(title: str) -> None:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 6, f"  {title}", ln=True, fill=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.ln(1)

        def _row(label: str, value: str) -> None:
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(45, 5, f"  {label}:", ln=False)
            pdf.set_font("Helvetica", "", 9)
            value_clean = _strip_emoji(str(value))[:90]
            pdf.multi_cell(0, 5, value_clean)

        def _bullet(text: str) -> None:
            pdf.set_font("Helvetica", "", 9)
            clean = _strip_emoji(text)[:110]
            pdf.cell(5, 5, "", ln=False)
            pdf.multi_cell(0, 5, f"* {clean}")

        # ── Verdict ───────────────────────────────────────────────────────────
        _section("VERDICT")
        _row("Result",   v_label)
        _row("Score",    f"{result.get('combined_score', 0):+.4f}")
        _row("Description", result.get("verdict_meta", {}).get("description", ""))
        pdf.ln(2)

        # ── Confidence ────────────────────────────────────────────────────────
        _section("CONFIDENCE SCORES")
        for label, key in [
            ("Overall",    "overall_confidence"),
            ("ML Model",   "ml_confidence"),
            ("Evidence",   "evidence_confidence"),
            ("Linguistic", "linguistic_confidence"),
            ("Fact",       "fact_confidence"),
        ]:
            pct = result.get(key, 0)
            _row(label, f"{pct}%")
        pdf.ln(2)

        # ── Claim ─────────────────────────────────────────────────────────────
        _section("CLAIM")
        _row("Claim", result.get("primary_claim", "")[:120])
        pdf.ln(2)

        # ── ML ────────────────────────────────────────────────────────────────
        _section("ML ANALYSIS")
        _row("Model",      ml_res.get("model_name", "—"))
        _row("Prediction", ml_res.get("label",      "—"))
        _row("Prob Real",  f"{ml_res.get('prob_real', 0)*100:.1f}%")
        _row("Prob Fake",  f"{ml_res.get('prob_fake', 0)*100:.1f}%")
        pdf.ln(2)

        # ── Verified Fact ─────────────────────────────────────────────────────
        _section("VERIFIED FACT")
        _row("Status",    vf.get("type", "insufficient").upper())
        _row("Summary",   vf.get("summary", "")[:200])
        if vf.get("official_source"):
            _row("Source", vf.get("official_source", ""))
        if vf.get("official_url"):
            _row("URL",    vf.get("official_url", "")[:80])
        pdf.ln(2)

        # ── Evidence ─────────────────────────────────────────────────────────
        _section("EVIDENCE")
        _row("Trusted Sources",  str(ev_res.get("sources_found", 0)))
        _row("Evidence Score",   f"{ev_res.get('evidence_score', 0):+.4f}")
        _row("Avg Trust",        f"{ev_res.get('avg_trust_score', 0)}/100")
        sup = ", ".join(ev_res.get("supporting_sources",    [])[:3])
        con = ", ".join(ev_res.get("contradicting_sources", [])[:3])
        if sup:
            _row("Supporting",   sup)
        if con:
            _row("Contradicting", con)
        pdf.ln(2)

        # ── Reasoning ────────────────────────────────────────────────────────
        _section("REASONING")
        for item in result.get("reasoning", []):
            _bullet(item)
        pdf.ln(2)

        # ── Footer ────────────────────────────────────────────────────────────
        pdf.set_font("Helvetica", "I", 7)
        pdf.cell(0, 4,
            "This report is produced by an AI system for research/educational "
            "purposes only. Verify with authoritative sources before any decision.",
            ln=True, align="C",
        )

        return bytes(pdf.output())

    except Exception as exc:
        logger.error("PDF export failed: %s", exc)
        return None


# ── Filename Helpers ──────────────────────────────────────────────────────────

def report_filename(verdict: str, ext: str) -> str:
    """Generate a safe, timestamped filename for the report."""
    ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe  = re.sub(r"[^a-zA-Z0-9_]", "_", verdict.lower())
    return f"fnd_report_{safe}_{ts}.{ext}"
