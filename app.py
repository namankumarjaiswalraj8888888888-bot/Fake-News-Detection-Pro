"""
app.py
======
Version 5.1 — Gradio UI for the AI Fake News Detection & Live Verification System.

New in 5.1
----------
- Forensic-dossier UI redesign (Source Serif 4 · Inter · JetBrains Mono)
- Dark / light mode: @media prefers-color-scheme auto + manual toggle
- English / Hindi language toggle (both langs pre-rendered, JS visibility swap)
- SVG evidence-gauge with animated sweep needle
- Interactive team profile modals (click name → full biodata popup)
- word-boundary keyword-matching bugs fixed in utils.py / search.py
- Sensationalism regex bug fixed in constants.py / utils.py
- model.pkl + vectorizer.pkl verified and wired

AI Fake News Detection & Live Verification System — Version 5.1
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
    APP_TITLE, APP_VERSION, APP_TAGLINE,
    INSTITUTION, BOARD, INTERNSHIP,
    DEVELOPERS,
    SERVER_HOST, SERVER_PORT, SERVER_SHARE, SERVER_SHOW_ERROR,
)
from constants import SAMPLE_NEWS, VERDICT_META
from styles   import get_css
from fact_checker import check_news
from export   import export_txt, export_json, export_pdf, report_filename
from history  import history as _history
from i18n_strings import (
    STATIC_UI, VERDICT_LABELS_HI, VERDICT_DESCRIPTIONS_HI,
    EVIDENCE_LABELS_HI, TEAM_HI,
)

logger = logging.getLogger(__name__)

# ── Singleton to hold the last result for export ──────────────────────────────
_last_result: dict | None = None


# ── Tiny helpers ──────────────────────────────────────────────────────────────
def _esc(s: object) -> str:
    return html.escape(str(s)) if s else ""


def _si(key: str, lang_attr: str = "") -> str:
    """Return both EN and HI versions of a static UI string as pre-rendered spans."""
    entry = STATIC_UI.get(key, {"en": key, "hi": key})
    return (
        f'<span class="en">{_esc(entry["en"])}</span>'
        f'<span class="hi">{_esc(entry["hi"])}</span>'
    )


# ── Verdict CSS class map ──────────────────────────────────────────────────────
_VERDICT_CSS: dict[str, str] = {
    "REAL":                  "fnd-v-real",
    "LIKELY REAL":           "fnd-v-lreal",
    "PARTIALLY TRUE":        "fnd-v-partial",
    "UNVERIFIED":            "fnd-v-unv",
    "INSUFFICIENT EVIDENCE": "fnd-v-insuff",
    "MIXED":                 "fnd-v-mixed",
    "MISLEADING":            "fnd-v-mislead",
    "LIKELY FAKE":           "fnd-v-lfake",
    "FAKE":                  "fnd-v-fake",
}

# ── Lucide-style inline SVG icons ─────────────────────────────────────────────
_ICONS: dict[str, str] = {
    "compass": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>',
    "server":  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>',
    "flask":   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3h6"/><path d="M10 3v5l-3.5 6a4 4 0 0 0 3.5 6h4a4 4 0 0 0 3.5-6L14 8V3"/><path d="M6.5 14.5h11"/></svg>',
    "book-open": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>',
    "shield-check": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>',
    "lightbulb": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21h6"/><path d="M12 3a6 6 0 0 1 6 6c0 2.2-1.2 4.2-3 5.4V18H9v-3.6A6 6 0 0 1 6 9a6 6 0 0 1 6-6z"/></svg>',
    "magnify": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "moon":    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
    "sun":     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
}


def _icon(name: str, cls: str = "") -> str:
    svg = _ICONS.get(name, "")
    if cls:
        svg = svg.replace("<svg ", f'<svg class="{_esc(cls)}" ', 1)
    return svg


# ── SVG Evidence Gauge ────────────────────────────────────────────────────────
def _gauge_svg(combined_score: float, verdict_css: str) -> str:
    """
    Semicircular gauge: REAL (left, green) → centre (amber) → FAKE (right, red).
    combined_score in [-1, +1]; maps to needle angle -90° (left) … +90° (right).
    The needle animates on reveal via a data-score attribute + inline JS.
    """
    # Clamp to [-1, 1]
    score = max(-1.0, min(1.0, combined_score))
    # Map [-1, 1] → [-90, 90] degrees (0 deg = straight up = centre)
    angle = score * 90
    return f"""
<div class="fnd-gauge-wrap">
  <svg class="fnd-gauge-svg" viewBox="0 0 200 110" width="200" height="110"
       data-score="{score:.4f}" aria-label="Evidence gauge">
    <!-- Track arc (180° semicircle) -->
    <defs>
      <linearGradient id="gauge-grad" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%"   stop-color="var(--verify)"  stop-opacity=".85"/>
        <stop offset="45%"  stop-color="var(--amber)"   stop-opacity=".75"/>
        <stop offset="100%" stop-color="var(--flag)"    stop-opacity=".85"/>
      </linearGradient>
    </defs>
    <!-- Background track -->
    <path d="M 16 100 A 84 84 0 0 1 184 100"
          fill="none" stroke="var(--line)" stroke-width="10"
          stroke-linecap="round"/>
    <!-- Colored track -->
    <path d="M 16 100 A 84 84 0 0 1 184 100"
          fill="none" stroke="url(#gauge-grad)" stroke-width="10"
          stroke-linecap="round" opacity=".6"/>
    <!-- Tick marks -->
    <g stroke="var(--line-strong)" stroke-width="1.5" opacity=".7">
      <line x1="100" y1="18" x2="100" y2="26"/>
      <line x1="20"  y1="98" x2="28"  y2="95"/>
      <line x1="180" y1="98" x2="172" y2="95"/>
      <line x1="43"  y1="38" x2="49"  y2="44"/>
      <line x1="157" y1="38" x2="151" y2="44"/>
    </g>
    <!-- Labels -->
    <text x="10"  y="110" font-size="9" fill="var(--verify)"
          font-family="var(--font-mono)" text-anchor="middle">REAL</text>
    <text x="100" y="14"  font-size="8" fill="var(--amber)"
          font-family="var(--font-mono)" text-anchor="middle">?</text>
    <text x="190" y="110" font-size="9" fill="var(--flag)"
          font-family="var(--font-mono)" text-anchor="middle">FAKE</text>
    <!-- Needle (animated via JS on load) -->
    <g class="fnd-gauge-needle" id="gauge-needle"
       style="transform: rotate({angle:.1f}deg); transform-origin: 100px 100px;">
      <line x1="100" y1="100" x2="100" y2="26"
            stroke="var(--ink)" stroke-width="2.5" stroke-linecap="round"/>
      <circle cx="100" cy="100" r="5" fill="var(--ink)"/>
      <circle cx="100" cy="100" r="2.5" fill="var(--paper-raised)"/>
    </g>
  </svg>
  <div style="font-family:var(--font-mono);font-size:.68rem;color:var(--ink-soft);margin-top:2px">
    score: <span style="color:var(--ink)">{combined_score:+.4f}</span>
  </div>
</div>"""


# ── Confidence bar ─────────────────────────────────────────────────────────────
def _conf_bar(label_en: str, label_hi: str, pct: int,
              extra_cls: str = "", i18n_key: str = "") -> str:
    fill_cls = f"fnd-conf-fill {extra_cls}".strip()
    return f"""
<div class="fnd-conf-row">
  <div class="fnd-conf-label">
    <span class="en">{_esc(label_en)}</span>
    <span class="hi">{_esc(label_hi)}</span>
  </div>
  <div class="fnd-conf-track">
    <div class="{fill_cls}" style="width:{pct}%" aria-valuenow="{pct}"></div>
  </div>
  <div class="fnd-conf-pct">{pct}%</div>
</div>"""


# ── Verdict HTML ──────────────────────────────────────────────────────────────
def _verdict_html(result: dict) -> str:
    verdict    = result.get("verdict", "UNVERIFIED")
    css_cls    = _VERDICT_CSS.get(verdict, "fnd-v-unv")
    meta       = VERDICT_META.get(verdict, {})
    icon       = meta.get("icon", "❓")
    desc_en    = meta.get("description", "")
    desc_hi    = VERDICT_DESCRIPTIONS_HI.get(verdict, desc_en)
    verdict_hi = VERDICT_LABELS_HI.get(verdict, verdict)

    overall_conf = result.get("overall_confidence", 0)
    ml_conf      = result.get("ml_confidence", 0)
    ev_conf      = result.get("evidence_confidence", 0)
    ling_conf    = result.get("linguistic_confidence", 0)
    combined     = result.get("combined_score", 0.0)
    model_name   = result.get("model_name", "")
    elapsed      = result.get("elapsed_seconds", 0)
    claim_short  = (result.get("claim", "") or "")[:120]

    gauge = _gauge_svg(combined, css_cls)

    conf_bars = (
        _conf_bar("Overall Confidence", "समग्र विश्वसनीयता",   overall_conf, "fnd-conf-fill-overall") +
        _conf_bar("ML Model",          "एमएल मॉडल",            ml_conf) +
        _conf_bar("Evidence",          "साक्ष्य",               ev_conf) +
        _conf_bar("Linguistic",        "भाषाई",                 ling_conf)
    )

    claim_block = ""
    if claim_short:
        claim_block = f'<div class="fnd-verdict-claim">{_esc(claim_short)}{"…" if len(result.get("claim",""))>120 else ""}</div>'

    return f"""
<div class="fnd-verdict-wrap {css_cls}">
  <div class="fnd-verdict-header">
    <span class="en">VERIFICATION VERDICT</span>
    <span class="hi">सत्यापन निर्णय</span>
  </div>
  <div class="fnd-verdict-stamp">
    <div class="fnd-verdict-icon" aria-hidden="true">{icon}</div>
    <div class="fnd-verdict-text-block">
      <div class="fnd-verdict-word">
        <span class="en">{_esc(verdict)}</span>
        <span class="fnd-verdict-word-hi hi">{_esc(verdict_hi)}</span>
      </div>
      <div class="fnd-verdict-desc">
        <span class="en">{_esc(desc_en)}</span>
        <span class="hi">{_esc(desc_hi)}</span>
      </div>
    </div>
  </div>
  {claim_block}
  {gauge}
  <div class="fnd-conf-section">
    <div class="fnd-conf-title">
      <span class="en">CONFIDENCE BREAKDOWN</span>
      <span class="hi">विश्वसनीयता विवरण</span>
    </div>
    {conf_bars}
  </div>
  <div class="fnd-verdict-meta">
    Model: {_esc(model_name)} &nbsp;|&nbsp;
    <span class="en">Verified in</span><span class="hi">जाँच में लगा समय</span>
    {elapsed:.2f}s
  </div>
</div>"""


# ── Verified Fact HTML ────────────────────────────────────────────────────────
def _fact_html(vf: dict, verdict_css: str) -> str:
    if not vf:
        return ""
    status   = vf.get("status", "INSUFFICIENT EVIDENCE")
    detail   = vf.get("detail", "")
    status_hi = VERDICT_LABELS_HI.get(status, status)
    return f"""
<div class="fnd-fact-wrap {verdict_css}">
  <div class="fnd-section-title">
    <span class="en">🔎 VERIFIED FACT</span>
    <span class="hi">🔎 सत्यापित तथ्य</span>
  </div>
  <div class="fnd-fact-verdict-tag">
    <span class="en">{_esc(status)}</span>
    <span class="hi">{_esc(status_hi)}</span>
  </div>
  <div class="fnd-fact-text">{_esc(detail)}</div>
</div>"""


# ── Source card HTML ──────────────────────────────────────────────────────────
def _src_card(article: dict) -> str:
    cls_map  = {"supporting": "sup", "contradicting": "con", "neutral": "neu"}
    ctype    = article.get("classification", "neutral")
    tab_cls  = f"fnd-src-tab fnd-src-tab-{cls_map.get(ctype, 'neu')}"
    label_en = ctype.upper()
    label_hi = EVIDENCE_LABELS_HI.get(ctype, ctype).upper()
    domain   = _esc(article.get("domain", article.get("url", "")[:40]))
    title    = _esc(article.get("title", ""))
    snippet  = _esc((article.get("snippet") or "")[:140])
    url      = _esc(article.get("url", "#"))
    trust    = article.get("trust_score", 0)
    return f"""
<div class="fnd-src-card">
  <div class="{tab_cls}">
    <span class="en">{label_en}</span>
    <span class="hi">{label_hi}</span>
  </div>
  <div class="fnd-src-domain">{domain}</div>
  <div class="fnd-src-title">{title}</div>
  {"" if not snippet else f'<div class="fnd-src-snippet">{snippet}…</div>'}
  {"" if url == "#" else f'<a class="fnd-src-link" href="{url}" target="_blank" rel="noopener">↗ <span class="en">Read more</span><span class="hi">पढ़ें</span></a>'}
</div>"""


# ── Sources HTML ──────────────────────────────────────────────────────────────
def _sources_html(evidence_result: dict, verdict_css: str) -> str:
    articles = evidence_result.get("articles", [])
    n        = evidence_result.get("sources_found", 0)
    if not articles:
        no_src_en = STATIC_UI["result.no_sources"]["en"]
        no_src_hi = STATIC_UI["result.no_sources"]["hi"]
        return f"""
<div class="fnd-sources-wrap {verdict_css}">
  <div class="fnd-section-title">
    <span class="en">📡 SOURCES</span><span class="hi">📡 स्रोत</span>
  </div>
  <div class="fnd-no-sources">
    <span class="en">{_esc(no_src_en)}</span>
    <span class="hi">{_esc(no_src_hi)}</span>
  </div>
</div>"""

    cards = "".join(_src_card(a) for a in articles[:6])
    return f"""
<div class="fnd-sources-wrap {verdict_css}">
  <div class="fnd-section-title">
    <span class="en">📡 SOURCES ({n})</span>
    <span class="hi">📡 स्रोत ({n})</span>
  </div>
  <div class="fnd-sources-grid">{cards}</div>
</div>"""


# ── Reasoning HTML ────────────────────────────────────────────────────────────
def _reasoning_html(reasoning: list[str], verdict_css: str) -> str:
    if not reasoning:
        return ""
    items = "".join(f"<li>{_esc(r)}</li>" for r in reasoning)
    return f"""
<div class="fnd-reasoning-wrap {verdict_css}">
  <div class="fnd-section-title">
    <span class="en">🧠 REASONING</span><span class="hi">🧠 तर्क</span>
  </div>
  <ol class="fnd-reasoning-list">{items}</ol>
</div>"""


# ── Full result HTML ──────────────────────────────────────────────────────────
def build_result_html(result: dict) -> str:
    if not result:
        return _placeholder_html()
    verdict    = result.get("verdict", "UNVERIFIED")
    css_cls    = _VERDICT_CSS.get(verdict, "fnd-v-unv")
    ev_result  = result.get("evidence_result", {})
    vf         = result.get("verified_fact", {})
    reasoning  = result.get("reasoning", [])

    return (
        _verdict_html(result) +
        _fact_html(vf, css_cls) +
        _sources_html(ev_result, css_cls) +
        _reasoning_html(reasoning, css_cls)
    )


# ── Placeholder HTML ──────────────────────────────────────────────────────────
def _placeholder_html() -> str:
    return f"""
<div class="fnd-placeholder">
  {_icon("magnify")}
  <div>
    <span class="en">{STATIC_UI["result.placeholder"]["en"]}</span>
    <span class="hi">{STATIC_UI["result.placeholder"]["hi"]}</span>
  </div>
</div>"""


# ── Loading HTML ──────────────────────────────────────────────────────────────
def _loading_html() -> str:
    return """
<div class="fnd-loading">
  <div class="fnd-shimmer-line" style="width:60%"></div>
  <div class="fnd-shimmer-line" style="width:85%"></div>
  <div class="fnd-shimmer-line" style="width:45%"></div>
  <div class="fnd-shimmer-line" style="width:70%;margin-top:18px"></div>
  <div class="fnd-shimmer-line" style="width:90%"></div>
</div>"""


# ── History HTML ──────────────────────────────────────────────────────────────
def _history_html(entries: list[dict]) -> str:
    if not entries:
        return '<div style="font-size:.82rem;color:var(--ink-soft);padding:8px 0;font-style:italic">No verifications yet.</div>'
    rows = ""
    for e in entries[:100]:
        v       = e.get("verdict", "?")
        css_cls = _VERDICT_CSS.get(v, "fnd-v-unv")
        v_hi    = VERDICT_LABELS_HI.get(v, v)
        claim   = _esc((e.get("claim", "") or "")[:60])
        conf    = e.get("overall_confidence", 0)
        ts      = _esc(e.get("timestamp", ""))
        rows += f"""
<div style="display:flex;align-items:center;gap:10px;padding:8px 0;
     border-bottom:1px solid var(--line);font-size:.8rem;">
  <span class="{css_cls}" style="color:var(--verdict-color,var(--ink));
        font-weight:600;min-width:100px;font-size:.75rem;">
    <span class="en">{_esc(v)}</span><span class="hi">{_esc(v_hi)}</span>
  </span>
  <span style="flex:1;color:var(--ink-mid)">{claim}{"…" if len(e.get("claim",""))>60 else ""}</span>
  <span style="font-family:var(--font-mono);color:var(--ink-soft);font-size:.68rem">{conf}%</span>
  <span style="color:var(--ink-soft);font-size:.68rem">{ts}</span>
</div>"""
    return f'<div style="margin-top:6px">{rows}</div>'


# ── Error HTML ────────────────────────────────────────────────────────────────
def _error_html(msg: str) -> str:
    return f"""
<div class="fnd-fact-wrap fnd-v-fake" style="border-left:3px solid var(--flag)">
  <div class="fnd-section-title">⚠ Error</div>
  <div class="fnd-fact-text">{_esc(msg)}</div>
</div>"""


# ── Team section HTML ─────────────────────────────────────────────────────────
def _team_html() -> str:
    cards = ""
    for dev in DEVELOPERS:
        dev_id   = dev["id"]
        icon_svg = _icon(dev.get("icon", "compass"))
        hi_data  = TEAM_HI.get(dev_id, {})
        role_hi  = hi_data.get("role", dev["role"])
        badge_hi = hi_data.get("badge", dev["badge"])
        cards += f"""
<div class="fnd-team-card" data-id="{_esc(dev_id)}"
     onclick="fndOpenModal('{_esc(dev_id)}')"
     role="button" tabindex="0" aria-label="View {_esc(dev['name'])} profile"
     onkeydown="if(event.key==='Enter')fndOpenModal('{_esc(dev_id)}')">
  <div class="fnd-team-icon">{icon_svg}</div>
  <div class="fnd-member-name">{_esc(dev['name'])}</div>
  <div class="fnd-member-role">
    <span class="en">{_esc(dev['role'])}</span>
    <span class="hi">{_esc(role_hi)}</span>
  </div>
  <span class="fnd-member-badge">
    <span class="en">{_esc(dev['badge'])}</span>
    <span class="hi">{_esc(badge_hi)}</span>
  </span>
</div>"""

    return f"""
<div class="fnd-team-section">
  <div class="fnd-team-hdr">
    <div class="fnd-team-title">
      <span class="en">{STATIC_UI["team.title"]["en"]}</span>
      <span class="hi">{STATIC_UI["team.title"]["hi"]}</span>
    </div>
  </div>
  <div class="fnd-team-sub">{_esc(INSTITUTION)} · {_esc(BOARD)} · {_esc(INTERNSHIP)}</div>
  <div class="fnd-team-hint">
    <span class="en">{STATIC_UI["team.tap_hint"]["en"]}</span>
    <span class="hi">{STATIC_UI["team.tap_hint"]["hi"]}</span>
  </div>
  <div class="fnd-team-grid">{cards}</div>
  <div class="fnd-institution">
    AI &amp; Machine Learning Internship Project 2026 &nbsp;·&nbsp;
    Diploma Engineering &nbsp;·&nbsp; Computer Science &amp; Engineering<br>
    <strong>Version {APP_VERSION}</strong>
  </div>
</div>
{_modal_backdrop_html()}"""


def _modal_backdrop_html() -> str:
    """Pre-render ALL team member modals into hidden divs, shown by JS."""
    modals = ""
    for dev in DEVELOPERS:
        dev_id  = dev["id"]
        hi_data = TEAM_HI.get(dev_id, {})

        # Skills (both langs)
        skills_en  = "".join(f'<span class="fnd-skill-tag en">{_esc(s)}</span>'
                              for s in dev.get("skills", []))
        skills_hi  = "".join(f'<span class="fnd-skill-tag hi">{_esc(s)}</span>'
                              for s in hi_data.get("skills", dev.get("skills", [])))

        # Contributions (both langs)
        contrib_en = "".join(f'<li class="en">{_esc(c)}</li>'
                              for c in dev.get("contributions", []))
        contrib_hi = "".join(f'<li class="hi">{_esc(c)}</li>'
                              for c in hi_data.get("contributions", dev.get("contributions", [])))

        # Quote (both langs)
        quote_en   = _esc(dev.get("quote", ""))
        quote_hi   = _esc(hi_data.get("quote", dev.get("quote", "")))

        bio_en     = _esc(dev.get("bio", ""))
        bio_hi     = _esc(hi_data.get("bio", dev.get("bio", "")))

        role_en    = _esc(dev["role"])
        role_hi    = _esc(hi_data.get("role", dev["role"]))
        badge_en   = _esc(dev["badge"])
        badge_hi   = _esc(hi_data.get("badge", dev["badge"]))

        icon_svg   = _icon(dev.get("icon", "compass"))

        close_en   = STATIC_UI["team.modal.close"]["en"]
        close_hi   = STATIC_UI["team.modal.close"]["hi"]
        skills_label_en = STATIC_UI["team.modal.skills"]["en"]
        skills_label_hi = STATIC_UI["team.modal.skills"]["hi"]
        contrib_label_en = STATIC_UI["team.modal.contributions"]["en"]
        contrib_label_hi = STATIC_UI["team.modal.contributions"]["hi"]

        modals += f"""
<div class="fnd-modal" id="modal-{_esc(dev_id)}" role="dialog"
     aria-labelledby="modal-name-{_esc(dev_id)}" aria-modal="true"
     style="display:none">
  <button class="fnd-modal-close" onclick="fndCloseModal()"
          aria-label="Close">✕</button>
  <div class="fnd-modal-head">
    <div class="fnd-modal-icon">{icon_svg}</div>
    <div>
      <div class="fnd-modal-name" id="modal-name-{_esc(dev_id)}">{_esc(dev['name'])}</div>
      <div class="fnd-modal-role">
        <span class="en">{role_en}</span><span class="hi">{role_hi}</span>
      </div>
      <span class="fnd-modal-badge">
        <span class="en">{badge_en}</span><span class="hi">{badge_hi}</span>
      </span>
    </div>
  </div>
  <div class="fnd-modal-body">
    <div class="fnd-modal-bio">
      <span class="en">{bio_en}</span>
      <span class="hi">{bio_hi}</span>
    </div>
    <div class="fnd-modal-section-title">
      <span class="en">{_esc(skills_label_en)}</span>
      <span class="hi">{_esc(skills_label_hi)}</span>
    </div>
    <div class="fnd-modal-skills">{skills_en}{skills_hi}</div>
    <div class="fnd-modal-section-title">
      <span class="en">{_esc(contrib_label_en)}</span>
      <span class="hi">{_esc(contrib_label_hi)}</span>
    </div>
    <ul class="fnd-modal-contrib">{contrib_en}{contrib_hi}</ul>
    {"" if not quote_en else f'''
    <div class="fnd-modal-quote">
      <span class="en">{quote_en}</span>
      <span class="hi">{quote_hi}</span>
    </div>'''}
  </div>
</div>"""

    return f'<div class="fnd-modal-backdrop" id="fnd-modal-backdrop" onclick="fndBackdropClick(event)">{modals}</div>'


# ── Plain text summary (for Quick Copy) ───────────────────────────────────────
def _build_plain_summary(result: dict) -> str:
    if not result:
        return ""
    v   = result.get("verdict", "?")
    c   = (result.get("claim", "") or "")[:120]
    oc  = result.get("overall_confidence", 0)
    mlc = result.get("ml_confidence", 0)
    evc = result.get("evidence_confidence", 0)
    lc  = result.get("linguistic_confidence", 0)
    mn  = result.get("model_name", "")
    el  = result.get("elapsed_seconds", 0)
    n   = result.get("evidence_result", {}).get("sources_found", 0)
    return (
        f"VERDICT: {v}\n"
        f"Claim  : {c}\n"
        f"Overall Confidence : {oc}%\n"
        f"ML Confidence      : {mlc}% ({mn})\n"
        f"Evidence Confidence: {evc}% ({n} sources)\n"
        f"Linguistic         : {lc}%\n"
        f"Time: {el:.2f}s"
    )


# ── Event handlers ────────────────────────────────────────────────────────────
def run_check(text: str):
    global _last_result
    if not text or len(text.strip()) < 5:
        err = _error_html("Please enter at least 5 characters of news text or a URL.")
        return err, "", gr.update(), _history_html(_history.all())

    result       = check_news(text.strip())
    _last_result = result

    if result.get("error") and not result.get("verdict"):
        return (
            _error_html(result["error"]),
            "",
            gr.update(),
            _history_html(_history.all()),
        )

    _history.add(result)
    return (
        build_result_html(result),
        _build_plain_summary(result),
        gr.update(value=""),
        _history_html(_history.all()),
    )


def clear_all():
    global _last_result
    _last_result = None
    return gr.update(value=""), _placeholder_html(), "", _history_html(_history.all())


def load_sample(name: str) -> gr.update:
    return gr.update(value=SAMPLE_NEWS.get(name, ""))


def search_history(query: str):
    entries = _history.search(query) if query.strip() else _history.all()
    return _history_html(entries)


def clear_history():
    _history.clear()
    return _history_html([])


def export_history_json():
    entries = _history.all()
    if not entries:
        return None
    path = os.path.join(tempfile.gettempdir(), "fnd_history.json")
    import json
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    return path


def download_txt():
    if not _last_result:
        return None
    path = os.path.join(tempfile.gettempdir(), report_filename(_last_result, "txt"))
    content = export_txt(_last_result)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def download_json():
    if not _last_result:
        return None
    path = os.path.join(tempfile.gettempdir(), report_filename(_last_result, "json"))
    content = export_json(_last_result)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def download_pdf():
    if not _last_result:
        return None
    path = os.path.join(tempfile.gettempdir(), report_filename(_last_result, "pdf"))
    data = export_pdf(_last_result)
    if data is None:
        return None
    with open(path, "wb") as f:
        f.write(data)
    return path


# ── Client-side JS (injected once into <head>) ────────────────────────────────
_HEAD_JS = """
<script>
// ── Theme toggle ──────────────────────────────────────────────────────────────
(function(){
  var root = null;
  function getRoot() {
    if (!root) root = document.getElementById('fnd-root') || document.querySelector('.gradio-container') || document.body;
    return root;
  }
  var stored = localStorage.getItem('fnd-theme');
  if (stored) { document.addEventListener('DOMContentLoaded', function(){ getRoot().setAttribute('data-theme', stored); updateThemeBtn(stored); }); }

  window.fndToggleTheme = function() {
    var r = getRoot();
    var cur = r.getAttribute('data-theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    var next = cur === 'dark' ? 'light' : 'dark';
    r.setAttribute('data-theme', next);
    localStorage.setItem('fnd-theme', next);
    updateThemeBtn(next);
  };
  function updateThemeBtn(theme) {
    var btn = document.getElementById('fnd-theme-btn');
    if (!btn) return;
    var moonEN = btn.querySelector('.moon-en'), moonHI = btn.querySelector('.moon-hi');
    var sunEN  = btn.querySelector('.sun-en'),  sunHI  = btn.querySelector('.sun-hi');
    if (theme === 'dark') {
      if (moonEN) moonEN.style.display = 'none';
      if (moonHI) moonHI.style.display = 'none';
      if (sunEN)  sunEN.style.display  = 'flex';
      if (sunHI)  sunHI.style.display  = 'flex';
    } else {
      if (moonEN) moonEN.style.display = 'flex';
      if (moonHI) moonHI.style.display = 'flex';
      if (sunEN)  sunEN.style.display  = 'none';
      if (sunHI)  sunHI.style.display  = 'none';
    }
  }
})();

// ── Language toggle ───────────────────────────────────────────────────────────
(function(){
  var root = null;
  function getRoot() {
    if (!root) root = document.getElementById('fnd-root') || document.querySelector('.gradio-container') || document.body;
    return root;
  }

  // Auto-detect browser language on first load
  document.addEventListener('DOMContentLoaded', function(){
    root = document.getElementById('fnd-root') || document.querySelector('.gradio-container') || document.body;
    var stored = localStorage.getItem('fnd-lang');
    if (stored) {
      root.setAttribute('data-lang', stored);
    } else {
      var lang = (navigator.language || navigator.userLanguage || 'en').toLowerCase();
      var detected = (lang.startsWith('hi') || lang.startsWith('mr') || lang.startsWith('ne')) ? 'hi' : 'en';
      root.setAttribute('data-lang', detected);
    }
    updateLangBtn(root.getAttribute('data-lang'));
  });

  window.fndToggleLang = function() {
    var r = getRoot();
    var cur = r.getAttribute('data-lang') || 'en';
    var next = cur === 'en' ? 'hi' : 'en';
    r.setAttribute('data-lang', next);
    localStorage.setItem('fnd-lang', next);
    updateLangBtn(next);
  };

  function updateLangBtn(lang) {
    var btn = document.getElementById('fnd-lang-btn');
    if (!btn) return;
    var enSpan = btn.querySelector('.lang-en');
    var hiSpan = btn.querySelector('.lang-hi');
    if (lang === 'hi') {
      if (enSpan) enSpan.textContent = 'EN';
      if (hiSpan) hiSpan.textContent = '• हिं';
      btn.title = 'Switch to English';
    } else {
      if (enSpan) enSpan.textContent = 'EN •';
      if (hiSpan) hiSpan.textContent = 'हिं';
      btn.title = 'हिंदी में बदलें';
    }
  }
})();

// ── Team member modal ─────────────────────────────────────────────────────────
window.fndOpenModal = function(devId) {
  var backdrop = document.getElementById('fnd-modal-backdrop');
  if (!backdrop) return;
  // Hide all modals first
  backdrop.querySelectorAll('.fnd-modal').forEach(function(m){ m.style.display = 'none'; });
  var modal = document.getElementById('modal-' + devId);
  if (!modal) return;
  modal.style.display = 'block';
  backdrop.classList.add('open');
  document.body.style.overflow = 'hidden';
  // Focus the close button for accessibility
  var closeBtn = modal.querySelector('.fnd-modal-close');
  if (closeBtn) setTimeout(function(){ closeBtn.focus(); }, 100);
};

window.fndCloseModal = function() {
  var backdrop = document.getElementById('fnd-modal-backdrop');
  if (!backdrop) return;
  backdrop.classList.remove('open');
  document.body.style.overflow = '';
};

window.fndBackdropClick = function(e) {
  if (e.target === document.getElementById('fnd-modal-backdrop')) fndCloseModal();
};

// Close modal on Escape key
document.addEventListener('keydown', function(e){
  if (e.key === 'Escape') fndCloseModal();
});

// ── Animate confidence bars on result render ──────────────────────────────────
// Gradio re-renders gr.HTML() in place; MutationObserver triggers on each update.
(function(){
  var observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(m) {
      m.addedNodes.forEach(function(node) {
        if (node.nodeType !== 1) return;
        var fills = node.querySelectorAll ? node.querySelectorAll('.fnd-conf-fill') : [];
        fills.forEach(function(fill) {
          var target = fill.style.width;
          fill.style.width = '0%';
          requestAnimationFrame(function(){
            setTimeout(function(){ fill.style.width = target; }, 60);
          });
        });
      });
    });
  });
  document.addEventListener('DOMContentLoaded', function(){
    var container = document.querySelector('.gradio-container') || document.body;
    observer.observe(container, { childList: true, subtree: true });
  });
})();
</script>
"""


# ── Gradio App ────────────────────────────────────────────────────────────────
def create_app() -> gr.Blocks:
    sample_names = list(SAMPLE_NEWS.keys())

    with gr.Blocks(
        title=f"{APP_TITLE} V{APP_VERSION}",
        css=get_css(),
        head=_HEAD_JS,
        theme=gr.themes.Base(),
        elem_id="fnd-root",
    ) as app:

        # NOTE: We no longer inject an unclosed <div class="fnd-root"> wrapper.
        # Instead, gr.Blocks(elem_id="fnd-root") makes Gradio add id="fnd-root"
        # directly on the .gradio-container element, so our CSS/JS targets it
        # without any extra wrapper div causing blank space at top.

        # ── Header ────────────────────────────────────────────────────────────
        gr.HTML(f"""
<header class="fnd-header">
  <div class="fnd-wordmark">
    <div class="fnd-wordmark-icon">{_icon("magnify")}</div>
    <div>
      <div class="fnd-wordmark-text">
        <span class="en">AI Fake News Detection</span>
        <span class="hi">एआई फेक न्यूज़ डिटेक्शन</span>
      </div>
      <div class="fnd-wordmark-sub">
        <span class="en">{APP_TAGLINE}</span>
        <span class="hi">9-निर्णय · लाइव साक्ष्य · एमएल · सत्यापन</span>
      </div>
    </div>
  </div>
  <div class="fnd-header-controls">
    <button id="fnd-lang-btn" class="fnd-lang-toggle"
            onclick="fndToggleLang()" title="हिंदी में बदलें / Switch to English">
      <span class="lang-en">EN •</span>&nbsp;<span class="lang-hi">हिं</span>
    </button>
    <button id="fnd-theme-btn" class="fnd-theme-toggle"
            onclick="fndToggleTheme()" title="Toggle dark / light mode">
      <span class="moon-en" style="display:flex;align-items:center;gap:4px">{_icon("moon")}&nbsp;Dark</span>
      <span class="moon-hi" style="display:none;align-items:center;gap:4px">{_icon("moon")}&nbsp;डार्क</span>
      <span class="sun-en"  style="display:none;align-items:center;gap:4px">{_icon("sun")}&nbsp;Light</span>
      <span class="sun-hi"  style="display:none;align-items:center;gap:4px">{_icon("sun")}&nbsp;लाइट</span>
    </button>
    <span class="fnd-version-pill">v{APP_VERSION}</span>
  </div>
</header>""")

        # ── Main row ──────────────────────────────────────────────────────────
        with gr.Row(equal_height=False):

            # Left panel — input
            with gr.Column(scale=5, min_width=300):
                gr.HTML('<div class="fnd-panel">')
                gr.HTML(f'<div class="fnd-panel-label"><span class="en">Claim to verify</span><span class="hi">जाँचने का दावा</span></div>')

                news_input = gr.Textbox(
                    placeholder="Paste news headline, article text, or a URL…\nMinimum 5 characters.",
                    lines=6, max_lines=14,
                    label="", show_label=False,
                )

                # Sample buttons
                gr.HTML(f'<div class="fnd-samples-label"><span class="en">Try a sample →</span><span class="hi">उदाहरण आज़माएँ →</span></div>')
                gr.HTML('<div class="fnd-samples-wrap">')
                with gr.Row():
                    sample_btns = [
                        gr.Button(name, size="sm", elem_classes=["fnd-sample-btn"])
                        for name in sample_names
                    ]
                gr.HTML("</div>")

                gr.HTML('<div class="fnd-btn-row">')
                clear_btn   = gr.Button("Clear",  size="sm",  elem_classes=["fnd-btn-clear"])
                analyze_btn = gr.Button("Verify →", size="lg", elem_classes=["fnd-btn-analyze"])
                gr.HTML("</div>")

                gr.HTML("</div>")  # /fnd-panel

                # Export accordion
                with gr.Accordion("Export Report", open=False):
                    gr.HTML(f"""
<div style="padding:6px 0 4px;font-size:.82rem;color:var(--ink-soft)">
  <span class="en">Run a verification first, then download the report.</span>
  <span class="hi">पहले जाँच पूरी करें, फिर रिपोर्ट डाउनलोड करें।</span>
</div>""")
                    gr.HTML('<div class="fnd-export-row">')
                    txt_btn  = gr.Button("TXT",  size="sm", elem_classes=["fnd-export-btn"])
                    json_btn = gr.Button("JSON", size="sm", elem_classes=["fnd-export-btn"])
                    pdf_btn  = gr.Button("PDF",  size="sm", elem_classes=["fnd-export-btn"])
                    gr.HTML("</div>")
                    txt_file   = gr.File(label="TXT",  visible=False, interactive=False)
                    json_file  = gr.File(label="JSON", visible=False, interactive=False)
                    pdf_file   = gr.File(label="PDF",  visible=False, interactive=False)
                    plain_text = gr.Textbox(
                        label="Quick Copy", lines=6,
                        interactive=False, show_copy_button=True,
                    )

                # History accordion
                with gr.Accordion("Verification History", open=False):
                    gr.HTML('<div style="font-size:.78rem;color:var(--ink-soft);padding:4px 0 8px">Last 100 verifications (this session)</div>')
                    hist_search = gr.Textbox(placeholder="Search history…", label="", show_label=False)
                    with gr.Row():
                        hist_search_btn = gr.Button("Search",     size="sm")
                        hist_clear_btn  = gr.Button("Clear All",  size="sm", variant="stop")
                        hist_export_btn = gr.Button("Export JSON", size="sm")
                    hist_display     = gr.HTML(_history_html(_history.all()))
                    hist_export_file = gr.File(label="History JSON", visible=False, interactive=False)

            # Right panel — results
            with gr.Column(scale=7, min_width=340):
                result_html = gr.HTML(value=_placeholder_html(), label="")

        # ── Team section ──────────────────────────────────────────────────────
        gr.HTML(_team_html())

        # ── Event wiring ──────────────────────────────────────────────────────
        analyze_btn.click(
            fn=run_check, inputs=[news_input],
            outputs=[result_html, plain_text, news_input, hist_display],
            show_progress="minimal",
        ).then(fn=lambda: gr.update(visible=False), outputs=[txt_file])

        for btn, name in zip(sample_btns, sample_names):
            btn.click(fn=lambda n=name: load_sample(n), outputs=[news_input])

        clear_btn.click(
            fn=clear_all,
            outputs=[news_input, result_html, plain_text, hist_display],
        )

        txt_btn.click(fn=download_txt, outputs=[txt_file]
            ).then(fn=lambda: gr.update(visible=True), outputs=[txt_file])
        json_btn.click(fn=download_json, outputs=[json_file]
            ).then(fn=lambda: gr.update(visible=True), outputs=[json_file])
        pdf_btn.click(fn=download_pdf, outputs=[pdf_file]
            ).then(fn=lambda: gr.update(visible=True), outputs=[pdf_file])

        hist_search_btn.click(fn=search_history, inputs=[hist_search], outputs=[hist_display])
        hist_clear_btn.click(fn=clear_history, outputs=[hist_display])
        hist_export_btn.click(fn=export_history_json, outputs=[hist_export_file]
            ).then(fn=lambda: gr.update(visible=True), outputs=[hist_export_file])

    return app


# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> None:
    app = create_app()
    app.launch(
        server_name=SERVER_HOST,
        server_port=SERVER_PORT,
        share=SERVER_SHARE,
        show_error=SERVER_SHOW_ERROR,
        favicon_path=None,
    )


if __name__ == "__main__":
    main()
