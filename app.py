"""
app.py
======
Version 4 — Professional Gradio UI for AI Fake News Detection System.

Features
--------
- Dark / Light mode with system preference detection
- Fully responsive (mobile-first)
- Animated confidence meters (CSS keyframe, no flash-to-full bug)
- Professional source cards with trust badges
- Keyword highlighting
- Export: PDF, TXT, JSON
- Session history with statistics panel
- Loading state with step-by-step progress indicator
- URL mode banner
- Professional team footer
- All text sanitised before HTML injection (XSS-safe)

AI Fake News Detection & Live Verification System — Version 4
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar & Parmeshwar
"""

from __future__ import annotations

import html
import logging
import os

import gradio as gr

from config import (
    APP_TITLE, APP_VERSION, INSTITUTION, DEVELOPERS,
    SERVER_HOST, SERVER_PORT, SERVER_SHARE, SERVER_SHOW_ERROR,
)
from constants import SAMPLE_NEWS
from fact_checker import check_news
from export import export_pdf, export_txt, export_json, format_report_text
from history import VerificationHistory
from styles import CSS, THEME_JS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── HTML Safety ───────────────────────────────────────────────────────────────

def _h(text: object) -> str:
    """Escape for safe HTML injection."""
    return html.escape(str(text))


# ══════════════════════════════════════════════════════════════════════════════
# HTML RENDERERS
# ══════════════════════════════════════════════════════════════════════════════

def _render_empty_state() -> str:
    return """
    <div class="fnd-empty">
      <span class="fnd-empty-icon">🔍</span>
      <h3>Ready to verify</h3>
      <p>Enter a news headline, article text, or paste a news URL above, then click
         <strong>Verify News</strong> to start the analysis.</p>
    </div>
    """


def _render_loading() -> str:
    return """
    <div class="fnd-loading active" id="fnd-loading-indicator">
      <div class="fnd-spinner"></div>
      <div class="fnd-loading-label">Analysing…</div>
      <div class="fnd-loading-sub">Running ML model + live web verification</div>
      <div class="fnd-steps">
        <div class="fnd-step done">
          <span class="fnd-step-dot"></span> Input validated
        </div>
        <div class="fnd-step done">
          <span class="fnd-step-dot"></span> ML prediction
        </div>
        <div class="fnd-step active">
          <span class="fnd-step-dot"></span> Live web search
        </div>
        <div class="fnd-step">
          <span class="fnd-step-dot"></span> Evidence analysis
        </div>
        <div class="fnd-step">
          <span class="fnd-step-dot"></span> Final verdict
        </div>
      </div>
    </div>
    """


def _confidence_bar(label: str, pct: int, cls: str, icon: str = "") -> str:
    safe_pct = max(0, min(100, pct))
    return f"""
    <div class="fnd-conf-row">
      <div class="fnd-conf-header">
        <span class="fnd-conf-label">{icon} {_h(label)}</span>
        <span class="fnd-conf-pct">{safe_pct}%</span>
      </div>
      <div class="fnd-conf-track">
        <div class="fnd-conf-fill {cls}"
             style="--target-width:{safe_pct}%;width:{safe_pct}%"></div>
      </div>
    </div>
    """


def _render_verdict(result: dict) -> str:
    verdict  = result.get("verdict", "UNVERIFIED")
    overall  = result.get("overall_confidence", 0)
    ml_conf  = result.get("ml_confidence",      0)
    ev_conf  = result.get("evidence_confidence", 0)
    elapsed  = result.get("elapsed_seconds",     0)
    model    = _h(result.get("ml_result", {}).get("model_name", "—"))
    sources  = result.get("evidence_result", {}).get("sources_found", 0)
    url_meta = result.get("url_meta", {})

    VERDICT_CONFIG = {
        "REAL": {
            "icon":   "✅",
            "label":  "REAL",
            "sub":    "This news appears credible based on ML analysis and trusted sources.",
            "cls":    "fnd-verdict-real",
            "bar_cls": "real",
        },
        "FAKE": {
            "icon":   "❌",
            "label":  "FAKE",
            "sub":    "This content shows strong indicators of misinformation.",
            "cls":    "fnd-verdict-fake",
            "bar_cls": "fake",
        },
        "UNVERIFIED": {
            "icon":   "⚠️",
            "label":  "UNVERIFIED",
            "sub":    "Insufficient evidence for a definitive verdict. Verify manually.",
            "cls":    "fnd-verdict-unv",
            "bar_cls": "unv",
        },
    }
    cfg = VERDICT_CONFIG.get(verdict, VERDICT_CONFIG["UNVERIFIED"])

    # URL banner
    url_banner = ""
    if url_meta.get("is_url") and url_meta.get("fetch_success"):
        domain = _h(url_meta.get("domain", ""))
        title  = _h(url_meta.get("article_title", "")[:80])
        date   = _h(url_meta.get("article_date", ""))
        url_banner = f"""
        <div class="fnd-url-banner">
          🌐 Analysed from URL &nbsp;·&nbsp;
          <span class="fnd-url-domain">{domain}</span>
          {f'&nbsp;·&nbsp; {title}' if title else ''}
          {f'&nbsp;·&nbsp; <em>{date}</em>' if date else ''}
        </div>
        """

    # Confidence bars
    bars = (
        _confidence_bar("Overall Confidence", overall, cfg["bar_cls"],      "🎯")
        + _confidence_bar(f"ML Model [{model}]", ml_conf, cfg["bar_cls"],   "🤖")
        + _confidence_bar(f"Evidence [{sources} source(s)]", ev_conf, cfg["bar_cls"], "📡")
    )

    meta_line = f"""
    <div style="font-size:0.78rem;color:var(--text-muted);margin-top:var(--space-3);
                display:flex;gap:1rem;flex-wrap:wrap;">
      <span>⏱ {elapsed}s</span>
      <span>🤖 {model}</span>
      <span>📰 {sources} source(s) found</span>
    </div>
    """

    return f"""
    {url_banner}
    <div class="fnd-card {cfg['cls']}">
      <span class="fnd-verdict-icon">{cfg['icon']}</span>
      <div class="fnd-verdict-label {cfg['bar_cls']}">{cfg['label']}</div>
      <div class="fnd-verdict-sub">{cfg['sub']}</div>
      <div class="fnd-conf-block">{bars}</div>
      {meta_line}
    </div>
    """


def _render_reasoning(result: dict) -> str:
    reasons = result.get("reasoning", [])
    if not reasons:
        return "<p style='color:var(--text-muted);font-size:0.88rem;'>No reasoning available.</p>"

    items = "\n".join(
        f"<li>{_h(r)}</li>"
        for r in reasons
    )
    return f"""
    <div class="fnd-card">
      <div class="fnd-card-title">💡 AI Reasoning</div>
      <ul class="fnd-reasoning">{items}</ul>
    </div>
    """


def _render_keywords(result: dict) -> str:
    kws = result.get("keywords", [])
    if not kws:
        return ""
    badges = "".join(f'<span class="fnd-kw">{_h(k)}</span>' for k in kws)
    return f"""
    <div class="fnd-card" style="margin-top:var(--space-4);">
      <div class="fnd-card-title">🔑 Detected Keywords</div>
      <div class="fnd-kw-wrap">{badges}</div>
    </div>
    """


def _render_sources(result: dict) -> str:
    ev        = result.get("evidence_result", {})
    articles  = ev.get("articles", [])
    s_found   = ev.get("sources_found", 0)

    if not articles:
        search_err = ev.get("search_error", "")
        return f"""
        <div class="fnd-empty">
          <span class="fnd-empty-icon">📡</span>
          <h3>No trusted sources found</h3>
          <p>{"Search error: " + _h(search_err) if search_err else
             "No results matched our trusted source whitelist. "
             "The verdict relies on ML model and linguistic analysis."}</p>
        </div>
        """

    cards = []
    for a in articles:
        cls_raw = a.get("classification", "neutral")
        cls_map = {"supporting": "supporting", "contradicting": "contradicting"}
        cls     = cls_map.get(cls_raw, "neutral")
        name    = _h(a.get("source_name", a.get("domain", "Source")))
        trust   = int(a.get("trust_score", 0))
        title   = _h(a.get("title",   "")[:140])
        snippet = _h(a.get("snippet", "")[:200])
        url     = _h(a.get("url",     ""))
        date    = _h(a.get("date",    ""))
        is_fc   = a.get("is_fact_check", False)

        # Classification badge
        badge_map = {
            "supporting":    ('<span class="fnd-badge fnd-badge-sup">✅ Supporting</span>', "Supporting"),
            "contradicting": ('<span class="fnd-badge fnd-badge-con">❌ Contradicts</span>', "Contradicts"),
        }
        cls_badge, _ = badge_map.get(cls, ('<span class="fnd-badge fnd-badge-neu">⚠️ Neutral</span>', "Neutral"))

        fc_badge = '<span class="fnd-badge fnd-badge-fc">✓ Fact-Check</span>' if is_fc else ""

        # Trust score styling
        trust_cls = "trust-high" if trust >= 90 else ("trust-mid" if trust >= 70 else "trust-low")
        trust_html = f"""
        <span class="fnd-trust-score {trust_cls}">
          <span class="fnd-trust-dot"></span> {trust}/100
        </span>
        """

        snippet_html = (
            f'<div class="fnd-source-snippet">{snippet}…</div>' if snippet else ""
        )
        date_html = (
            f'<span class="fnd-source-date">📅 {date}</span>' if date else ""
        )

        cards.append(f"""
        <div class="fnd-source-card {cls}">
          <div class="fnd-source-header">
            <div class="fnd-source-name">{name}</div>
            <div class="fnd-source-badges">
              {cls_badge}{fc_badge}{trust_html}
            </div>
          </div>
          <div class="fnd-source-title">{title}</div>
          {snippet_html}
          <div class="fnd-source-meta">
            <a class="fnd-source-link" href="{url}" target="_blank"
               rel="noopener noreferrer">🔗 View article</a>
            {date_html}
          </div>
        </div>
        """)

    summary_badges = []
    sup_n = len([a for a in articles if a.get("classification") == "supporting"])
    con_n = len([a for a in articles if a.get("classification") == "contradicting"])
    neu_n = s_found - sup_n - con_n
    if sup_n: summary_badges.append(f'<span class="fnd-badge fnd-badge-sup">✅ {sup_n} Supporting</span>')
    if con_n: summary_badges.append(f'<span class="fnd-badge fnd-badge-con">❌ {con_n} Contradicting</span>')
    if neu_n: summary_badges.append(f'<span class="fnd-badge fnd-badge-neu">⚠️ {neu_n} Neutral</span>')

    return f"""
    <div class="fnd-card-title" style="margin-bottom:var(--space-3);">
      📡 Evidence from {s_found} Trusted Source(s)
      &nbsp; {'&nbsp;'.join(summary_badges)}
    </div>
    {''.join(cards)}
    """


def _render_copy_report(result: dict) -> str:
    text = format_report_text(result, result.get("original_text", ""))
    safe = _h(text)
    return f"""
    <div class="fnd-card">
      <div class="fnd-card-title">📋 Formatted Report</div>
      <pre style="font-family:var(--font-mono);font-size:0.78rem;
                  color:var(--text-secondary);white-space:pre-wrap;
                  word-break:break-word;
                  background:var(--bg-code);padding:var(--space-4);
                  border-radius:var(--radius-md);max-height:400px;overflow-y:auto;
                  border:1px solid var(--border-subtle);">{safe}</pre>
    </div>
    """


def _hero_html() -> str:
    return f"""
    <div class="fnd-hero">
      <div class="fnd-hero-badge">🔍 AI-Powered · Free · No Paid APIs</div>
      <h1>AI Fake News Detection<br>&amp; Live Verification System</h1>
      <p>Multi-source evidence gathering · Machine learning classification ·
         Trust-weighted scoring · Real-time web verification</p>
      <div class="fnd-hero-pills">
        <span class="fnd-hero-pill">🤖 ML Classifier</span>
        <span class="fnd-hero-pill">📡 Live Web Search</span>
        <span class="fnd-hero-pill">✅ 40+ Trusted Sources</span>
        <span class="fnd-hero-pill">🌐 URL Mode</span>
        <span class="fnd-hero-pill">📊 Confidence Scoring</span>
        <span class="fnd-hero-pill">📥 Export Reports</span>
      </div>
    </div>
    """


def _footer_html() -> str:
    team_cards = ""
    for dev in DEVELOPERS:
        team_cards += f"""
        <div class="fnd-team-card">
          <div class="fnd-avatar">{_h(dev['avatar'])}</div>
          <div class="fnd-team-name">{_h(dev['name'])}</div>
          <div class="fnd-team-role">{_h(dev['role'])}</div>
          <span class="fnd-team-badge">{_h(dev['badge'])}</span>
        </div>
        """

    return f"""
    <div class="fnd-footer">
      <span class="fnd-footer-logo">🔍 FakeNewsDetect</span>
      <h2>Meet the Team</h2>
      <p class="fnd-footer-sub">{_h(INSTITUTION)} · AI &amp; ML Internship 2026</p>
      <div class="fnd-team-grid">{team_cards}</div>
      <div class="fnd-footer-pills">
        <span class="fnd-footer-pill">🏛 {_h(INSTITUTION)}</span>
        <span class="fnd-footer-pill">🎓 SBTE Bihar · Diploma Engineering</span>
        <span class="fnd-footer-pill">📅 Session 2025–2028</span>
        <span class="fnd-footer-pill">🚀 Version {_h(APP_VERSION)}</span>
        <span class="fnd-footer-pill">📜 MIT License</span>
        <span class="fnd-footer-pill">✅ 100% Free APIs</span>
      </div>
      <div class="fnd-footer-bottom">
        <div class="fnd-footer-info">
          Department of Computer Science &amp; Engineering ·
          AI &amp; ML Internship 2026<br>
          &copy; 2026 All rights reserved ·
          For educational and research purposes only
        </div>
      </div>
    </div>
    """


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CHECK FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def run_check(
    news_input: str,
    history_state: VerificationHistory,
) -> tuple:
    """
    Main Gradio event handler.
    Returns: (verdict_html, reasoning_html, sources_html, keywords_html,
              copy_html, history_html, stats_html,
              pdf_path, txt_path, json_path,
              history_state)
    """
    # Input validation
    if not news_input or not news_input.strip():
        err = '<div class="fnd-error">⚠️ Please enter a news headline, article text, or URL.</div>'
        empty = _render_empty_state()
        return (err, empty, empty, empty, empty,
                history_state.render_history_html(),
                history_state.render_stats_html(),
                None, None, None, history_state)

    logger.info("run_check — input length: %d", len(news_input))

    try:
        result = check_news(news_input)
    except Exception as exc:
        logger.exception("check_news raised: %s", exc)
        err_html = f'<div class="fnd-error">❌ Analysis error: {_h(str(exc))}</div>'
        empty    = _render_empty_state()
        return (err_html, empty, empty, empty, empty,
                history_state.render_history_html(),
                history_state.render_stats_html(),
                None, None, None, history_state)

    # Error from pipeline
    if result.get("error"):
        err_html = f'<div class="fnd-error">⚠️ {_h(result["error"])}</div>'
        empty    = _render_empty_state()
        return (err_html, empty, empty, empty, empty,
                history_state.render_history_html(),
                history_state.render_stats_html(),
                None, None, None, history_state)

    # Render output sections
    verdict_html   = _render_verdict(result)
    reasoning_html = _render_reasoning(result)
    sources_html   = _render_sources(result)
    keywords_html  = _render_keywords(result)
    copy_html      = _render_copy_report(result)

    # Add to session history
    history_state.add(result, news_input)

    # Generate export files
    pdf_path  = None
    txt_path  = None
    json_path = None
    try:
        txt_path  = export_txt(result, news_input)
        json_path = export_json(result, news_input)
        pdf_path  = export_pdf(result, news_input)
    except Exception as exc:
        logger.warning("Export generation failed: %s", exc)

    return (
        verdict_html,
        reasoning_html,
        sources_html,
        keywords_html,
        copy_html,
        history_state.render_history_html(),
        history_state.render_stats_html(),
        pdf_path,
        txt_path,
        json_path,
        history_state,
    )


def load_sample(sample_label: str) -> str:
    return SAMPLE_NEWS.get(sample_label, "")


def clear_history_fn(history_state: VerificationHistory) -> tuple:
    history_state.clear()
    return (
        history_state.render_history_html(),
        history_state.render_stats_html(),
        history_state,
    )


# ══════════════════════════════════════════════════════════════════════════════
# GRADIO LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

def build_ui() -> gr.Blocks:
    with gr.Blocks(
        title=f"{APP_TITLE} v{APP_VERSION}",
        css=CSS,
        theme=gr.themes.Base(
            font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
        ),
    ) as demo:

        # ── Theme toggle JS ───────────────────────────────────────────────────
        gr.HTML(f"""
        <script>
          {THEME_JS}
          document.addEventListener('DOMContentLoaded', initTheme);
        </script>
        """)

        # Session history state (one per browser session)
        history_state = gr.State(VerificationHistory)

        # ── Theme toggle bar ──────────────────────────────────────────────────
        gr.HTML("""
        <div class="fnd-theme-bar">
          <button class="fnd-theme-toggle"
                  id="fnd-theme-btn"
                  onclick="toggleTheme()"
                  title="Toggle dark / light mode">
            🌙 Dark Mode
          </button>
        </div>
        """)

        # ── Hero ──────────────────────────────────────────────────────────────
        gr.HTML(_hero_html())

        # ════════════════════════════════════════════════════════════════════
        # MAIN TABS
        # ════════════════════════════════════════════════════════════════════
        with gr.Tabs():

            # ── TAB 1: VERIFY ─────────────────────────────────────────────
            with gr.TabItem("🔍 Verify News", id="verify"):
                with gr.Row(equal_height=False):

                    # ── LEFT COLUMN — Input ───────────────────────────────
                    with gr.Column(scale=5, min_width=300, elem_classes=["fnd-input-wrap"]):
                        gr.HTML('<div class="fnd-card-title">📝 Enter News to Verify</div>')

                        news_input = gr.Textbox(
                            label="News Headline / Article Text / URL",
                            placeholder=(
                                "Paste a news headline, article text, or a URL "
                                "(e.g. https://www.thehindu.com/...)"
                            ),
                            lines=6,
                            max_lines=20,
                            show_copy_button=True,
                            elem_classes=["fnd-input-wrap"],
                        )

                        sample_dropdown = gr.Dropdown(
                            label="Try a sample",
                            choices=list(SAMPLE_NEWS.keys()),
                            value=None,
                            interactive=True,
                            elem_classes=["fnd-sample"],
                            info="Select a sample to auto-fill the input",
                        )

                        with gr.Row():
                            verify_btn = gr.Button(
                                "🔍 Verify News",
                                variant="primary",
                                size="lg",
                                elem_classes=["fnd-btn-primary"],
                            )
                            clear_btn = gr.ClearButton(
                                components=[news_input],
                                value="🗑 Clear",
                                size="sm",
                                elem_classes=["fnd-btn-secondary"],
                            )

                        gr.HTML("""
                        <div class="fnd-disclaimer">
                          ⚠️ <strong>Disclaimer:</strong> This tool is for educational and
                          research purposes only. Always cross-reference with authoritative
                          sources. Never use as the sole basis for any decision.
                        </div>
                        """)

                    # ── RIGHT COLUMN — Results ────────────────────────────
                    with gr.Column(scale=7, min_width=320):
                        with gr.Tabs():

                            # VERDICT tab
                            with gr.TabItem("🎯 Verdict"):
                                verdict_html = gr.HTML(value=_render_empty_state())

                            # REASONING tab
                            with gr.TabItem("💡 Reasoning"):
                                reasoning_html = gr.HTML(value=_render_empty_state())

                            # SOURCES tab
                            with gr.TabItem("📡 Sources"):
                                sources_html = gr.HTML(value=_render_empty_state())

                            # KEYWORDS tab
                            with gr.TabItem("🔑 Keywords"):
                                keywords_html = gr.HTML(value=_render_empty_state())

                            # REPORT tab
                            with gr.TabItem("📋 Report"):
                                copy_html = gr.HTML(value=_render_empty_state())

                            # EXPORT tab
                            with gr.TabItem("📥 Export"):
                                gr.HTML("""
                                <div class="fnd-card" style="margin-bottom:var(--space-4);">
                                  <div class="fnd-card-title">📥 Download Verification Report</div>
                                  <p style="font-size:0.85rem;color:var(--text-secondary);
                                            margin-bottom:var(--space-4);">
                                    Run a verification first, then download the report
                                    in your preferred format.
                                  </p>
                                </div>
                                """)
                                with gr.Row():
                                    pdf_download  = gr.File(
                                        label="📄 PDF Report",
                                        interactive=False,
                                        visible=True,
                                    )
                                    txt_download  = gr.File(
                                        label="📝 Text Report",
                                        interactive=False,
                                        visible=True,
                                    )
                                    json_download = gr.File(
                                        label="🗂 JSON Report",
                                        interactive=False,
                                        visible=True,
                                    )

            # ── TAB 2: HISTORY ────────────────────────────────────────────
            with gr.TabItem("📋 History", id="history"):
                with gr.Row():
                    with gr.Column():
                        gr.HTML('<div class="fnd-card-title">📋 Recent Analyses (This Session)</div>')
                        history_html = gr.HTML(
                            value='<div class="hist-empty">'
                                  '<span class="hist-empty-icon">📋</span>'
                                  '<p>No checks yet in this session.</p>'
                                  '</div>',
                        )
                        clear_history_btn = gr.Button(
                            "🗑 Clear History",
                            size="sm",
                            variant="secondary",
                            elem_classes=["fnd-btn-secondary"],
                        )

                    with gr.Column():
                        gr.HTML('<div class="fnd-card-title">📊 Session Statistics</div>')
                        stats_html = gr.HTML(
                            value='<div class="stats-empty">'
                                  '<p>Run at least one check to see statistics.</p>'
                                  '</div>',
                        )

            # ── TAB 3: HOW IT WORKS ───────────────────────────────────────
            with gr.TabItem("ℹ️ How It Works", id="howto"):
                gr.HTML("""
                <div style="max-width:780px;margin:0 auto;padding:var(--space-4) 0;">

                  <div class="fnd-card" style="margin-bottom:var(--space-4);">
                    <div class="fnd-card-title">🏗 Architecture</div>
                    <p style="font-size:0.88rem;color:var(--text-secondary);
                               line-height:1.8;margin-bottom:var(--space-4);">
                      The system combines machine learning with live evidence gathering
                      from trusted news publishers — with zero paid APIs required.
                    </p>
                    <div style="font-family:var(--font-mono);font-size:0.78rem;
                                color:var(--text-secondary);
                                background:var(--bg-code);padding:var(--space-4);
                                border-radius:var(--radius-md);
                                border:1px solid var(--border-subtle);
                                white-space:pre;overflow-x:auto;">
User Input (Text or URL)
        ↓
URL? → Fetch article text
        ↓
Text Cleaning &amp; Preprocessing
        ↓
Factual Claim Extraction (primary claim)
        ↓
Keyword Mining (top 8 keywords)
        ↓
Linguistic Signal Analysis
        ↓
Parallel Live Search (ThreadPoolExecutor)
  ├── Google News RSS   (Priority 1)
  ├── DuckDuckGo Lite   (Priority 2 / fallback)
  └── PIB Fact-Check    (supplementary)
        ↓
Trust-Weighted Evidence Scoring
        ↓
Best ML Model Prediction (TF-IDF + auto-selected classifier)
        ↓
Weighted Decision Fusion
  ML 45% + Evidence 35% + Linguistics 20%
        ↓
REAL / FAKE / UNVERIFIED + Confidence Scores
                    </div>
                  </div>

                  <div class="fnd-card" style="margin-bottom:var(--space-4);">
                    <div class="fnd-card-title">🏅 Trusted Sources</div>
                    <div style="font-size:0.85rem;color:var(--text-secondary);
                                line-height:1.9;">
                      <strong style="color:var(--text-primary);">40+ whitelisted domains</strong>
                      including Reuters (98), AP (98), BBC (97), The Hindu (95),
                      PIB (100), WHO (100), ISRO (100), RBI (100),
                      FactCheck.org (99), AltNews (97), NDTV (93) and more.
                      <br><br>
                      Sources not in the whitelist are ignored — the system never
                      bases verdicts on unknown websites.
                    </div>
                  </div>

                  <div class="fnd-card" style="margin-bottom:var(--space-4);">
                    <div class="fnd-card-title">📊 Confidence Score Breakdown</div>
                    <div style="font-size:0.85rem;color:var(--text-secondary);line-height:1.9;">
                      <strong style="color:var(--text-primary);">ML Confidence (45%)</strong>
                      — The ML model's prediction probability using TF-IDF features.<br>
                      <strong style="color:var(--text-primary);">Evidence Confidence (35%)</strong>
                      — Agreement strength among trusted news sources found online.<br>
                      <strong style="color:var(--text-primary);">Linguistic Analysis (20%)</strong>
                      — Presence of misinformation markers and credibility signals.<br><br>
                      When no evidence is found, weights shift to ML 45% + Linguistics 55%.
                    </div>
                  </div>

                  <div class="fnd-card">
                    <div class="fnd-card-title">⚠️ Limitations</div>
                    <div style="font-size:0.85rem;color:var(--text-secondary);line-height:1.9;">
                      • Paywalled or JavaScript-rendered articles may not extract correctly.<br>
                      • The ML model's accuracy depends on the training dataset size.<br>
                      • Very recent breaking news may have no trusted-source coverage yet.<br>
                      • The system is for <em>research and education only</em> — not a legal authority.<br>
                      • Always verify with multiple sources before making any decision.
                    </div>
                  </div>

                </div>
                """)

        # ── Footer ─────────────────────────────────────────────────────────
        gr.HTML(_footer_html())

        # ════════════════════════════════════════════════════════════════════
        # EVENT WIRING
        # ════════════════════════════════════════════════════════════════════

        outputs = [
            verdict_html,
            reasoning_html,
            sources_html,
            keywords_html,
            copy_html,
            history_html,
            stats_html,
            pdf_download,
            txt_download,
            json_download,
            history_state,
        ]

        verify_btn.click(
            fn=run_check,
            inputs=[news_input, history_state],
            outputs=outputs,
            api_name="verify",
        )

        news_input.submit(
            fn=run_check,
            inputs=[news_input, history_state],
            outputs=outputs,
        )

        sample_dropdown.change(
            fn=load_sample,
            inputs=[sample_dropdown],
            outputs=[news_input],
        )

        clear_history_btn.click(
            fn=clear_history_fn,
            inputs=[history_state],
            outputs=[history_html, stats_html, history_state],
        )

    return demo


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("=" * 62)
    logger.info("  %s v%s", APP_TITLE, APP_VERSION)
    logger.info("  %s", INSTITUTION)
    logger.info("  AI & ML Internship 2026")
    logger.info("=" * 62)

    demo = build_ui()
    demo.launch(
        server_name=SERVER_HOST,
        server_port=SERVER_PORT,
        share=SERVER_SHARE,
        show_error=SERVER_SHOW_ERROR,
        favicon_path=None,
    )
