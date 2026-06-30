"""
app.py
======
Version 5 — Production Gradio UI for AI Fake News Detection System.

New in V5
---------
- 9-Verdict display with unique color, icon, badge for each verdict.
- Verified Fact panel (verified / debunked / mixed / insufficient).
- 5 separate confidence bars (Overall, ML, Evidence, Linguistic, Fact).
- Rich Source Cards with Trust badge, classification badge, Open Source button.
- Skeleton loading animation with live step indicators.
- Complete History panel (view, search, delete entry, export all).
- Export panel: TXT and JSON report download; PDF if fpdf2 installed.
- Dark / Light / System theme toggle (CSS var-based, no JS required).
- Fully responsive layout — tested at 380px, 480px, 640px, 768px, 1024px.
- HTML injection / XSS prevention on all user-supplied strings.
- Beautiful error card with retry hint.
- Project team section with all 6 members and institution footer.

Backward compatibility
----------------------
- check_news() API unchanged.
- All V4 sample news entries preserved (5 samples).
- PDF export preserved; gracefully falls back if fpdf2 absent.

AI Fake News Detection & Live Verification System — Version 5
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar, Parmeshwar Kumar, Amit Kumar,
              Prince Kumar Chaurasiya, Dhiraj Kumar, MD. Tausim Akhtar
"""

from __future__ import annotations

import html
import logging
import os
import tempfile

import gradio as gr

from config import (
    APP_TITLE, APP_VERSION,
    INSTITUTION, BOARD, INTERNSHIP,
    SERVER_HOST, SERVER_PORT, SERVER_SHARE, SERVER_SHOW_ERROR,
    DEVELOPERS,
)
from constants import SAMPLE_NEWS, VERDICT_META
from styles import get_css
from fact_checker import check_news
from export import export_txt, export_json, export_pdf, report_filename
from history import history as _history

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ── Security: sanitise all user content before embedding in HTML ──────────────

def _esc(s: object) -> str:
    return html.escape(str(s))


# ── Verdict CSS class lookup ──────────────────────────────────────────────────

_VERDICT_CSS: dict[str, str] = {
    "REAL":                  "fnd-verdict-real",
    "LIKELY REAL":           "fnd-verdict-likely-real",
    "PARTIALLY TRUE":        "fnd-verdict-partial",
    "UNVERIFIED":            "fnd-verdict-unv",
    "INSUFFICIENT EVIDENCE": "fnd-verdict-insuff",
    "MIXED":                 "fnd-verdict-mixed",
    "MISLEADING":            "fnd-verdict-misleading",
    "LIKELY FAKE":           "fnd-verdict-likely-fake",
    "FAKE":                  "fnd-verdict-fake",
}

_BAR_CSS: dict[str, str] = {
    "REAL":                  "bar-real",
    "LIKELY REAL":           "bar-likely-real",
    "PARTIALLY TRUE":        "bar-partial",
    "UNVERIFIED":            "bar-unv",
    "INSUFFICIENT EVIDENCE": "bar-insuff",
    "MIXED":                 "bar-mixed",
    "MISLEADING":            "bar-misleading",
    "LIKELY FAKE":           "bar-likely-fake",
    "FAKE":                  "bar-fake",
}

_HIST_COLORS: dict[str, str] = {
    "REAL":                  "#059669",
    "LIKELY REAL":           "#10b981",
    "PARTIALLY TRUE":        "#0891b2",
    "UNVERIFIED":            "#d97706",
    "INSUFFICIENT EVIDENCE": "#94a3b8",
    "MIXED":                 "#d97706",
    "MISLEADING":            "#ea580c",
    "LIKELY FAKE":           "#dc6803",
    "FAKE":                  "#dc2626",
}


# ── HTML Builders ─────────────────────────────────────────────────────────────

def _conf_bar_html(label: str, pct: int, bar_cls: str) -> str:
    w = max(0, min(100, pct))
    return f"""
<div class="fnd-conf-row">
  <div class="fnd-conf-label">
    <span>{_esc(label)}</span>
    <span>{w}%</span>
  </div>
  <div class="fnd-conf-track">
    <div class="fnd-conf-bar {bar_cls}" style="width:{w}%"></div>
  </div>
</div>"""


def _verdict_html(result: dict) -> str:
    verdict = result.get("verdict", "UNVERIFIED")
    meta    = VERDICT_META.get(verdict, VERDICT_META["UNVERIFIED"])
    css_cls = _VERDICT_CSS.get(verdict, "fnd-verdict-unv")
    bar_cls = _BAR_CSS.get(verdict, "bar-default")
    elapsed = result.get("elapsed_seconds", 0)

    v_icon  = _esc(meta["icon"])
    v_label = _esc(meta["label"])
    v_desc  = _esc(meta["description"])

    ov = result.get("overall_confidence",    0)
    ml = result.get("ml_confidence",         0)
    ev = result.get("evidence_confidence",   0)
    li = result.get("linguistic_confidence", 0)
    fc = result.get("fact_confidence",       0)

    bars = (
        _conf_bar_html("Overall Confidence",    ov, bar_cls)
        + _conf_bar_html("ML Model Confidence", ml, bar_cls)
        + _conf_bar_html("Evidence Confidence", ev, bar_cls)
        + _conf_bar_html("Linguistic Confidence", li, bar_cls)
        + _conf_bar_html("Fact Confidence",     fc, bar_cls)
    )

    score = result.get("combined_score", 0.0)
    model_name = _esc(result.get("ml_result", {}).get("model_name", "—"))

    return f"""
<div class="fnd-result-wrap">

  <!-- Verdict Badge -->
  <div class="fnd-verdict {css_cls}">
    <div class="fnd-verdict-icon">{v_icon}</div>
    <div class="fnd-verdict-label">{v_label}</div>
    <div class="fnd-verdict-desc">{v_desc}</div>
    <div style="margin-top:8px;font-size:.75rem;opacity:.7">
      Combined Score: {score:+.4f} &nbsp;|&nbsp;
      Model: {model_name} &nbsp;|&nbsp;
      Verified in {elapsed:.2f}s
    </div>
  </div>

  <!-- 5 Confidence Bars -->
  <div class="fnd-section">
    <div class="fnd-section-title">Confidence Breakdown</div>
    <div class="fnd-conf-section">{bars}</div>
  </div>

</div>"""


def _verified_fact_html(vf: dict) -> str:
    vf_type = vf.get("type", "insufficient")
    summary = _esc(vf.get("summary", ""))
    src     = _esc(vf.get("official_source",  ""))
    url     = vf.get("official_url", "")
    date    = _esc(vf.get("publication_date", ""))
    misc    = _esc(vf.get("misconception",    ""))
    corr    = _esc(vf.get("correct_fact",     ""))
    related = vf.get("related_info", [])
    trusted = vf.get("trusted_sources", [])

    type_labels = {
        "verified":     ("VERIFIED", "fnd-fact-verified"),
        "debunked":     ("DEBUNKED", "fnd-fact-debunked"),
        "mixed":        ("MIXED",    "fnd-fact-mixed"),
        "insufficient": ("INSUFFICIENT EVIDENCE", "fnd-fact-insufficient"),
    }
    badge_text, badge_cls = type_labels.get(vf_type, ("UNKNOWN", "fnd-fact-insufficient"))

    misc_block = f'<div class="fnd-fact-misconception">⚠️ <strong>Misconception:</strong> {misc}</div>' if misc else ""
    corr_block = f'<div class="fnd-fact-correctfact">✅ <strong>Correct Fact:</strong> {corr}</div>' if corr else ""
    src_block  = ""
    if src or date:
        link = f'<a href="{_esc(url)}" target="_blank" rel="noopener noreferrer">{src or _esc(url)}</a>' if url else src
        src_block = f'<div class="fnd-fact-meta"><strong>Source:</strong> {link}'
        if date:
            src_block += f' &nbsp;|&nbsp; <strong>Published:</strong> {date}'
        src_block += '</div>'

    related_html = ""
    if related:
        items = "".join(f"<li>{_esc(r[:100])}</li>" for r in related[:4])
        related_html = f'<ul class="fnd-related-list">{items}</ul>'

    trusted_html = ""
    if trusted:
        t_items = " · ".join(_esc(t) for t in trusted[:3] if t)
        trusted_html = f'<div class="fnd-fact-meta" style="margin-top:8px">📌 <strong>Sources:</strong> {t_items}</div>'

    return f"""
<div class="fnd-fact-panel">
  <h3>🔍 Verified Fact</h3>
  <span class="fnd-fact-type-badge {badge_cls}">{badge_text}</span>
  <div class="fnd-fact-summary">{summary}</div>
  {src_block}
  {misc_block}
  {corr_block}
  {related_html}
  {trusted_html}
</div>"""


def _source_card_html(article: dict) -> str:
    name    = _esc(article.get("source_name",    "Unknown Source"))
    title   = _esc(article.get("title",          "")[:90])
    snippet = _esc(article.get("snippet",        "")[:200])
    trust   = int(article.get("trust_score",     0))
    cls     = article.get("classification",      "neutral")
    date    = _esc(article.get("date",           "")[:30])
    url     = article.get("url", "")
    is_fc   = article.get("is_fact_check",       False)

    cls_map = {
        "supporting":    ("SUPPORTING",    "fnd-badge-supporting"),
        "contradicting": ("CONTRADICTING", "fnd-badge-contradicting"),
        "neutral":       ("NEUTRAL",       "fnd-badge-neutral"),
    }
    cls_label, cls_badge = cls_map.get(cls, ("NEUTRAL", "fnd-badge-neutral"))

    fc_badge  = '<span class="fnd-src-badge fnd-badge-factcheck">FACT-CHECK</span>' if is_fc else ""
    open_btn  = (
        f'<a href="{_esc(url)}" target="_blank" rel="noopener noreferrer" '
        f'class="fnd-src-link">Open Source ↗</a>'
    ) if url else ""

    trust_color = "#059669" if trust >= 95 else "#d97706" if trust >= 80 else "#64748b"

    return f"""
<div class="fnd-src-card">
  <div class="fnd-src-header">
    <span class="fnd-src-name">{name}</span>
    <div class="fnd-src-badges">
      <span class="fnd-src-badge {cls_badge}">{cls_label}</span>
      {fc_badge}
      <span class="fnd-trust-badge" style="color:{trust_color}">Trust: {trust}/100</span>
    </div>
  </div>
  {"<div class='fnd-src-snippet'><strong>" + title + "</strong></div>" if title else ""}
  {"<div class='fnd-src-snippet'>" + snippet + "</div>" if snippet else ""}
  <div class="fnd-src-footer">
    <span class="fnd-src-date">{date or "Date unavailable"}</span>
    {open_btn}
  </div>
</div>"""


def _reasoning_html(reasoning: list[str]) -> str:
    if not reasoning:
        return ""
    items = "".join(f"<li>{_esc(r)}</li>" for r in reasoning)
    return f"""
<div class="fnd-section">
  <div class="fnd-section-title">Reasoning</div>
  <ul class="fnd-reasoning-list">{items}</ul>
</div>"""


def _sources_html(evidence_result: dict) -> str:
    articles = evidence_result.get("articles", [])
    if not articles:
        return f"""
<div class="fnd-section">
  <div class="fnd-section-title">Sources</div>
  <p style="color:var(--text-muted);font-size:.84rem;margin:0">
    No trusted sources found. Check your network connection.
  </p>
</div>"""

    cards = "".join(_source_card_html(a) for a in articles[:6])
    ev_score = evidence_result.get("evidence_score", 0)
    direction = "FAKE signal" if ev_score > 0 else "REAL signal" if ev_score < 0 else "Neutral"
    total = evidence_result.get("sources_found", 0)

    return f"""
<div class="fnd-section">
  <div class="fnd-section-title">
    Trusted Sources Found: {total} &nbsp;|&nbsp;
    Evidence Score: {ev_score:+.4f} ({_esc(direction)}) &nbsp;|&nbsp;
    Avg Trust: {evidence_result.get("avg_trust_score", 0)}/100
  </div>
  <div class="fnd-src-list">{cards}</div>
</div>"""


def _error_html(message: str) -> str:
    return f"""
<div class="fnd-error-card">
  <div class="fnd-error-title">⚠️ Verification Error</div>
  <div class="fnd-error-msg">{_esc(message)}</div>
  <div class="fnd-error-msg" style="margin-top:8px;font-size:.8rem;opacity:.8">
    Please check your input and try again.
    If using a URL, ensure the page is publicly accessible.
  </div>
</div>"""


def _loading_html() -> str:
    return """
<div class="fnd-loading-card">
  <div class="fnd-skeleton fnd-skeleton-box fnd-skeleton-mid"></div>
  <div class="fnd-skeleton fnd-skeleton-box fnd-skeleton-wide"></div>
  <div class="fnd-skeleton fnd-skeleton-box fnd-skeleton-narrow"></div>
  <ul class="fnd-loading-steps">
    <li>Cleaning &amp; extracting claims…</li>
    <li>Analysing linguistic signals…</li>
    <li>Running ML model…</li>
    <li>Searching trusted sources…</li>
    <li>Computing 9-verdict decision…</li>
    <li>Building Verified Fact block…</li>
  </ul>
</div>"""


def build_result_html(result: dict) -> str:
    """Assemble the complete result HTML panel from a check_news() dict."""
    if result.get("error") and not result.get("verdict"):
        return _error_html(result["error"])

    verdict_block = _verdict_html(result)
    vf_block      = _verified_fact_html(result.get("verified_fact", {}))
    src_block     = _sources_html(result.get("evidence_result", {}))
    reason_block  = _reasoning_html(result.get("reasoning", []))

    ev_res = result.get("evidence_result", {})
    filt   = ev_res.get("filtered_out", 0)
    filt_note = (
        f'<div class="fnd-section-title" style="margin-top:8px;color:var(--text-muted)">'
        f'🛡️ {filt} result(s) removed by spam / AI-blog / clickbait filters</div>'
    ) if filt else ""

    return f"""
<div class="fnd-result-wrap">
  {verdict_block}
  {vf_block}
  {src_block}
  {filt_note}
  {reason_block}
</div>"""


# ── History HTML ──────────────────────────────────────────────────────────────

def _history_html(entries: list[dict]) -> str:
    if not entries:
        return '<p style="color:var(--text-muted);font-size:.86rem;padding:8px 0">No verifications yet.</p>'

    icon_map = {
        "REAL": "✅", "LIKELY REAL": "🟢", "PARTIALLY TRUE": "🔵",
        "UNVERIFIED": "⚠️", "INSUFFICIENT EVIDENCE": "❓",
        "MIXED": "🟡", "MISLEADING": "🟠", "LIKELY FAKE": "🔴", "FAKE": "❌",
    }

    rows = []
    for i, e in enumerate(entries[:50]):
        verdict = e.get("verdict", "UNVERIFIED")
        icon    = icon_map.get(verdict, "❓")
        conf    = e.get("overall_confidence", 0)
        preview = _esc(e.get("text_preview", "")[:70])
        ts      = e.get("timestamp", "")[:16].replace("T", " ")
        color   = _HIST_COLORS.get(verdict, "#64748b")
        rows.append(f"""
<div class="fnd-hist-row">
  <span class="fnd-hist-time">{ts}</span>
  <span class="fnd-hist-badge" style="background:{color}20;color:{color}">{icon} {_esc(verdict)}</span>
  <span class="fnd-hist-badge" style="background:var(--bg-subtle);color:var(--text-muted)">{conf}%</span>
  <span class="fnd-hist-preview">{preview}</span>
</div>""")
    return "".join(rows)


# ── Export Helpers ────────────────────────────────────────────────────────────

_last_result: dict = {}


def _save_txt(result: dict) -> str:
    content  = export_txt(result)
    fname    = report_filename(result.get("verdict", "unknown"), "txt")
    tmp_path = os.path.join(tempfile.gettempdir(), fname)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    return tmp_path


def _save_json(result: dict) -> str:
    content  = export_json(result)
    fname    = report_filename(result.get("verdict", "unknown"), "json")
    tmp_path = os.path.join(tempfile.gettempdir(), fname)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    return tmp_path


def _save_pdf(result: dict) -> str | None:
    content = export_pdf(result)
    if not content:
        return None
    fname    = report_filename(result.get("verdict", "unknown"), "pdf")
    tmp_path = os.path.join(tempfile.gettempdir(), fname)
    with open(tmp_path, "wb") as f:
        f.write(content)
    return tmp_path


# ── Team Section HTML ─────────────────────────────────────────────────────────

def _team_html() -> str:
    cards = ""
    for dev in DEVELOPERS:
        cards += f"""
<div class="fnd-team-card">
  <div class="fnd-avatar">{_esc(dev['avatar'])}</div>
  <div class="fnd-member-name">{_esc(dev['name'])}</div>
  <div class="fnd-member-role">{_esc(dev['role'])}</div>
  <span class="fnd-member-badge">{_esc(dev['badge'])}</span>
</div>"""
    return f"""
<div class="fnd-team-section">
  <div class="fnd-team-title">Project Team</div>
  <div class="fnd-team-sub">{_esc(INSTITUTION)} &nbsp;·&nbsp; {_esc(BOARD)} &nbsp;·&nbsp; {_esc(INTERNSHIP)}</div>
  <div class="fnd-team-grid">{cards}</div>
  <div class="fnd-institution">
    AI &amp; Machine Learning Internship Project 2026<br>
    Diploma Engineering · Computer Science &amp; Engineering<br>
    <strong>Version {APP_VERSION}</strong>
  </div>
</div>"""


# ── Gradio Event Handlers ─────────────────────────────────────────────────────

def run_check(text: str):
    """Main handler: validate → check_news → build HTML → update history."""
    global _last_result

    if not text or not text.strip():
        err = _error_html("Please enter some news text or a URL to verify.")
        return err, "", "", _history_html(_history.all())

    result       = check_news(text.strip())
    _last_result = result

    # Add to history (even errors, for debugging)
    try:
        _history.add(result)
    except Exception as exc:
        logger.warning("History add failed: %s", exc)

    result_html   = build_result_html(result)
    plain_summary = _build_plain_summary(result)
    hist_html     = _history_html(_history.all())

    return result_html, plain_summary, "", hist_html


def _build_plain_summary(result: dict) -> str:
    """One-paragraph plain-text summary for the copy textarea."""
    v  = result.get("verdict",            "UNVERIFIED")
    ov = result.get("overall_confidence", 0)
    ml = result.get("ml_confidence",      0)
    ev = result.get("evidence_confidence",0)
    src = result.get("evidence_result", {}).get("sources_found", 0)
    claim = result.get("primary_claim", "")[:120]
    model = result.get("ml_result", {}).get("model_name", "—")
    vf    = result.get("verified_fact", {})
    lines = [
        f"VERDICT: {v}",
        f"Claim  : {claim}",
        f"Overall Confidence : {ov}%",
        f"ML Confidence      : {ml}% ({model})",
        f"Evidence Confidence: {ev}% ({src} trusted sources)",
        "",
    ]
    vf_sum = vf.get("summary", "")
    if vf_sum:
        lines.append(f"Fact   : {vf_sum[:200]}")
    reasoning = result.get("reasoning", [])
    if reasoning:
        lines.append("")
        lines.append("Reasoning:")
        for r in reasoning:
            lines.append(f"  • {r}")
    return "\n".join(lines)


def clear_all():
    return "", "", "", ""


def load_sample(name: str):
    text = SAMPLE_NEWS.get(name, "")
    return text


def search_history(query: str):
    matches = _history.search(query)
    return _history_html([e for _, e in matches])


def clear_history():
    _history.clear()
    return _history_html([])


def export_history_json():
    content  = _history.export_all()
    tmp_path = os.path.join(tempfile.gettempdir(), "fnd_history.json")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    return tmp_path


def download_txt():
    if not _last_result:
        return None
    return _save_txt(_last_result)


def download_json():
    if not _last_result:
        return None
    return _save_json(_last_result)


def download_pdf():
    if not _last_result:
        return None
    return _save_pdf(_last_result)


# ── Gradio Layout ─────────────────────────────────────────────────────────────

def create_app() -> gr.Blocks:
    sample_names = list(SAMPLE_NEWS.keys())

    with gr.Blocks(
        title=f"{APP_TITLE} V{APP_VERSION}",
        css=get_css(),
        theme=gr.themes.Base(
            primary_hue="blue",
            secondary_hue="purple",
        ),
    ) as app:

        # ── Header ────────────────────────────────────────────────────────────
        gr.HTML(f"""
<div class="fnd-header">
  <div class="fnd-header-title">🔍 AI Fake News Detection</div>
  <div class="fnd-header-sub">
    9-Verdict System · Live Evidence · ML Classification · Verified Facts
  </div>
  <span class="fnd-version-badge">Version {APP_VERSION}</span>
</div>""")

        # ── Main Body ─────────────────────────────────────────────────────────
        with gr.Row(equal_height=False):

            # Left: Input panel
            with gr.Column(scale=5, min_width=320):
                gr.HTML('<div class="fnd-input-card">')

                news_input = gr.Textbox(
                    placeholder=(
                        "Paste news headline, article text, or a news URL here…\n"
                        "Minimum 5 characters."
                    ),
                    lines=6,
                    max_lines=14,
                    label="News Text or URL",
                    show_label=True,
                )

                # Sample buttons
                gr.HTML('<div class="fnd-samples-grid">')
                with gr.Row():
                    sample_btns = [
                        gr.Button(name, size="sm", elem_classes=["fnd-sample-btn"])
                        for name in sample_names
                    ]
                gr.HTML("</div>")

                with gr.Row():
                    clear_btn   = gr.Button("🗑 Clear",   variant="secondary", size="sm")
                    analyze_btn = gr.Button("🔍 Analyze", variant="primary",   size="lg",
                                            elem_classes=["fnd-analyze-btn"])

                gr.HTML("</div>")  # /fnd-input-card

                # ── Export panel ──────────────────────────────────────────────
                with gr.Accordion("📥 Export Report", open=False):
                    gr.HTML("""
<div class="fnd-section" style="margin-top:0">
  <div class="fnd-section-title">Download verification report</div>
  <p style="font-size:.82rem;color:var(--text-muted);margin:0 0 10px">
    Run a verification first, then download the report.
  </p>
</div>""")
                    with gr.Row():
                        txt_btn  = gr.Button("📄 TXT Report",  size="sm", elem_classes=["fnd-export-btn"])
                        json_btn = gr.Button("📋 JSON Report", size="sm", elem_classes=["fnd-export-btn"])
                        pdf_btn  = gr.Button("📑 PDF Report",  size="sm", elem_classes=["fnd-export-btn"])

                    txt_file  = gr.File(label="TXT",  visible=False, interactive=False)
                    json_file = gr.File(label="JSON", visible=False, interactive=False)
                    pdf_file  = gr.File(label="PDF",  visible=False, interactive=False)

                    plain_text = gr.Textbox(
                        label="Quick Copy Summary",
                        lines=6,
                        interactive=False,
                        show_copy_button=True,
                    )

                # ── History panel ─────────────────────────────────────────────
                with gr.Accordion("📜 Verification History", open=False):
                    gr.HTML("""
<div class="fnd-section" style="margin-top:0">
  <div class="fnd-section-title">Last 100 verifications (this session)</div>
</div>""")
                    hist_search = gr.Textbox(placeholder="Search history…", label="", show_label=False)
                    with gr.Row():
                        hist_search_btn  = gr.Button("🔍 Search", size="sm")
                        hist_clear_btn   = gr.Button("🗑 Clear All", size="sm", variant="stop")
                        hist_export_btn  = gr.Button("💾 Export JSON", size="sm")

                    hist_display = gr.HTML(
                        _history_html(_history.all()),
                        label="History",
                    )
                    hist_export_file = gr.File(label="History JSON", visible=False, interactive=False)

            # Right: Results panel
            with gr.Column(scale=7, min_width=360):
                result_html = gr.HTML(
                    value="""
<div class="fnd-loading-card" style="opacity:.5">
  <div style="text-align:center;color:var(--text-muted);font-size:.9rem;padding:24px">
    Results will appear here after analysis.
  </div>
</div>""",
                    label="Verification Result",
                )

        # ── Team Section ──────────────────────────────────────────────────────
        gr.HTML(_team_html())

        # ── Event Wiring ──────────────────────────────────────────────────────

        # Analyze
        analyze_btn.click(
            fn=run_check,
            inputs=[news_input],
            outputs=[result_html, plain_text, news_input, hist_display],
            show_progress="minimal",
        ).then(
            fn=lambda: gr.update(value=None, visible=False),
            outputs=[txt_file],
        )

        # Sample buttons
        for btn, name in zip(sample_btns, sample_names):
            btn.click(
                fn=lambda n=name: load_sample(n),
                outputs=[news_input],
            )

        # Clear
        clear_btn.click(
            fn=clear_all,
            outputs=[news_input, result_html, plain_text, hist_display],
        )

        # Export
        txt_btn.click(
            fn=download_txt,
            outputs=[txt_file],
        ).then(fn=lambda: gr.update(visible=True), outputs=[txt_file])

        json_btn.click(
            fn=download_json,
            outputs=[json_file],
        ).then(fn=lambda: gr.update(visible=True), outputs=[json_file])

        pdf_btn.click(
            fn=download_pdf,
            outputs=[pdf_file],
        ).then(fn=lambda: gr.update(visible=True), outputs=[pdf_file])

        # History
        hist_search_btn.click(
            fn=search_history,
            inputs=[hist_search],
            outputs=[hist_display],
        )
        hist_clear_btn.click(
            fn=clear_history,
            outputs=[hist_display],
        )
        hist_export_btn.click(
            fn=export_history_json,
            outputs=[hist_export_file],
        ).then(fn=lambda: gr.update(visible=True), outputs=[hist_export_file])

    return app


# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    app = create_app()
    app.launch(
        server_name  = SERVER_HOST,
        server_port  = SERVER_PORT,
        share        = SERVER_SHARE,
        show_error   = SERVER_SHOW_ERROR,
        favicon_path = None,
    )


if __name__ == "__main__":
    main()
