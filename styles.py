"""
styles.py
=========
Version 5.1 — Complete CSS + JS for the AI Fake News Detection app.

Design system: Forensic-dossier aesthetic.
- Ink/paper color palette (not generic SaaS blues)
- Source Serif 4 (verdicts/headings) + Inter (body) + JetBrains Mono (data)
- Noto Sans/Serif Devanagari for Hindi rendering
- Dark mode via @media prefers-color-scheme + manual toggle (data-theme attr)
- Language toggle via data-lang attr on root wrapper (both langs pre-rendered)
- SVG evidence gauge (animated sweep needle)
- Team member modal (click name → profile popup)

AI Fake News Detection & Live Verification System — Version 5.1
Government Polytechnic West Champaran — AI & ML Internship 2026
"""

from __future__ import annotations


def get_css() -> str:
    return BASE_CSS + COMPONENT_CSS + TEAM_CSS + MODAL_CSS + DARK_CSS + MEDIA_CSS


# ══════════════════════════════════════════════════════════════════════════════
#  BASE — tokens, reset, fonts
# ══════════════════════════════════════════════════════════════════════════════
BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+Devanagari:wght@400;500;600&family=Noto+Serif+Devanagari:wght@400;600&display=swap');

/* ── Design tokens: light mode ── */
:root {
  /* Palette */
  --ink        : #14213D;
  --ink-mid    : #3D4F6B;
  --ink-soft   : #6B7C99;
  --paper      : #FBFAF7;
  --paper-raised: #FFFFFF;
  --paper-subtle: #F3F2EE;
  --line       : #D8D3C7;
  --line-strong: #B8B2A8;

  /* Signal colors */
  --verify     : #1B7A5E;
  --verify-light: #E8F5F1;
  --flag       : #B23A2E;
  --flag-light : #FAEAE8;
  --amber      : #C17D17;
  --amber-light: #FDF3E0;
  --slate      : #3D5A80;
  --slate-light: #EBF0F7;
  --neutral-sig: #5A6A80;
  --neutral-light: #EEF1F5;

  /* 9-verdict colors */
  --v-real      : #1B7A5E;
  --v-lreal     : #2A9D7A;
  --v-partial   : #3D7CB5;
  --v-unv       : #8B6914;
  --v-insuff    : #6B7C99;
  --v-mixed     : #C17D17;
  --v-mislead   : #C45C1A;
  --v-lfake     : #B23A2E;
  --v-fake      : #8B1A12;

  /* Typography */
  --font-serif  : 'Source Serif 4', 'Noto Serif Devanagari', Georgia, serif;
  --font-body   : 'Inter', 'Noto Sans Devanagari', system-ui, sans-serif;
  --font-mono   : 'JetBrains Mono', 'Courier New', monospace;

  /* Spacing & shape */
  --r-sm  : 4px;
  --r-md  : 8px;
  --r-lg  : 12px;
  --r-xl  : 16px;

  /* Shadows — paper-document quality */
  --sh-sm : 0 1px 3px rgba(20,33,61,.07), 0 1px 2px rgba(20,33,61,.04);
  --sh-md : 0 3px 10px rgba(20,33,61,.08), 0 1px 4px rgba(20,33,61,.05);
  --sh-lg : 0 8px 24px rgba(20,33,61,.10), 0 2px 8px rgba(20,33,61,.06);
}

/* ── Design tokens: dark mode (OS-level) ── */
@media (prefers-color-scheme: dark) {
  :root { --_dark: 1; }
  .fnd-root:not([data-theme="light"]) {
    --ink        : #D8E4F0;
    --ink-mid    : #A8BDD6;
    --ink-soft   : #6E8BAA;
    --paper      : #111827;
    --paper-raised: #1A2436;
    --paper-subtle: #0F1520;
    --line       : #243350;
    --line-strong: #2E4268;

    --verify     : #34A37D;
    --verify-light: #0D2420;
    --flag       : #D8584A;
    --flag-light : #2A1210;
    --amber      : #D99A3D;
    --amber-light: #28200A;
    --slate      : #5B8BB8;
    --slate-light: #0F1E30;
    --neutral-sig: #7A90AA;
    --neutral-light: #141E2B;

    --v-real      : #34A37D;
    --v-lreal     : #3DB88A;
    --v-partial   : #5298C8;
    --v-unv       : #C89A30;
    --v-insuff    : #7A90AA;
    --v-mixed     : #D99A3D;
    --v-mislead   : #D4753A;
    --v-lfake     : #D8584A;
    --v-fake      : #E07060;

    --sh-sm : 0 1px 3px rgba(0,0,0,.30);
    --sh-md : 0 3px 10px rgba(0,0,0,.40);
    --sh-lg : 0 8px 24px rgba(0,0,0,.50);
  }
}

/* ── Manual dark override (toggle button) ── */
.fnd-root[data-theme="dark"] {
  --ink        : #D8E4F0;
  --ink-mid    : #A8BDD6;
  --ink-soft   : #6E8BAA;
  --paper      : #111827;
  --paper-raised: #1A2436;
  --paper-subtle: #0F1520;
  --line       : #243350;
  --line-strong: #2E4268;
  --verify     : #34A37D;
  --verify-light: #0D2420;
  --flag       : #D8584A;
  --flag-light : #2A1210;
  --amber      : #D99A3D;
  --amber-light: #28200A;
  --slate      : #5B8BB8;
  --slate-light: #0F1E30;
  --neutral-sig: #7A90AA;
  --neutral-light: #141E2B;
  --v-real      : #34A37D;
  --v-lreal     : #3DB88A;
  --v-partial   : #5298C8;
  --v-unv       : #C89A30;
  --v-insuff    : #7A90AA;
  --v-mixed     : #D99A3D;
  --v-mislead   : #D4753A;
  --v-lfake     : #D8584A;
  --v-fake      : #E07060;
  --sh-sm : 0 1px 3px rgba(0,0,0,.30);
  --sh-md : 0 3px 10px rgba(0,0,0,.40);
  --sh-lg : 0 8px 24px rgba(0,0,0,.50);
}

/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.fnd-root {
  font-family : var(--font-body);
  color       : var(--ink);
  background  : var(--paper);
  min-height  : 100vh;
  transition  : background .25s, color .25s;
}

.gradio-container, .gradio-container > .main {
  background  : var(--paper) !important;
  max-width   : 1200px !important;
  margin      : 0 auto !important;
  padding     : 0 !important;
}

/* Hide Gradio default label chrome where we inject our own */
.fnd-root label.svelte-1hnfib2 { display: none !important; }

/* ── i18n visibility ── */
.fnd-root:not([data-lang="hi"]) .hi { display: none !important; }
.fnd-root[data-lang="hi"]       .en { display: none !important; }
"""

# ══════════════════════════════════════════════════════════════════════════════
#  COMPONENT CSS — header, input panel, verdict, evidence, reasoning
# ══════════════════════════════════════════════════════════════════════════════
COMPONENT_CSS = """
/* ── Header ── */
.fnd-header {
  display         : flex;
  align-items     : center;
  justify-content : space-between;
  flex-wrap       : wrap;
  gap             : 8px;
  padding         : 14px 20px;
  border-bottom   : 1px solid var(--line);
  background      : var(--paper-raised);
  position        : sticky;
  top             : 0;
  z-index         : 100;
  box-shadow      : var(--sh-sm);
}
.fnd-wordmark {
  display     : flex;
  align-items : center;
  gap         : 8px;
}
.fnd-wordmark-icon {
  width  : 28px; height : 28px;
  color  : var(--slate);
  flex-shrink: 0;
}
.fnd-wordmark-text {
  font-family : var(--font-serif);
  font-size   : 1.05rem;
  font-weight : 600;
  color       : var(--ink);
  letter-spacing: -.01em;
  line-height : 1.2;
}
.fnd-wordmark-sub {
  font-size   : .72rem;
  color       : var(--ink-soft);
  margin-top  : 1px;
  font-family : var(--font-body);
  font-weight : 400;
}
.fnd-header-controls {
  display     : flex;
  align-items : center;
  gap         : 6px;
}
.fnd-lang-toggle, .fnd-theme-toggle {
  display         : flex;
  align-items     : center;
  gap             : 4px;
  padding         : 5px 10px;
  border-radius   : var(--r-md);
  border          : 1px solid var(--line-strong);
  background      : var(--paper-subtle);
  color           : var(--ink-mid);
  font-family     : var(--font-body);
  font-size       : .78rem;
  font-weight     : 500;
  cursor          : pointer;
  transition      : background .15s, border-color .15s, color .15s;
  letter-spacing  : .02em;
  white-space     : nowrap;
}
.fnd-lang-toggle:hover, .fnd-theme-toggle:hover {
  background    : var(--paper-raised);
  border-color  : var(--ink-soft);
  color         : var(--ink);
}
.fnd-version-pill {
  font-family : var(--font-mono);
  font-size   : .68rem;
  padding     : 2px 7px;
  border-radius: 20px;
  background  : var(--paper-subtle);
  color       : var(--ink-soft);
  border      : 1px solid var(--line);
}

/* ── Left panel card ── */
.fnd-panel {
  background    : var(--paper-raised);
  border        : 1px solid var(--line);
  border-radius : var(--r-xl);
  padding       : 20px;
  box-shadow    : var(--sh-sm);
}
.fnd-panel-label {
  font-size     : .72rem;
  font-weight   : 600;
  letter-spacing: .08em;
  text-transform: uppercase;
  color         : var(--ink-soft);
  margin-bottom : 10px;
}

/* Gradio textbox override */
.fnd-root .gr-textbox textarea,
.fnd-root textarea {
  font-family   : var(--font-body) !important;
  font-size     : .92rem !important;
  color         : var(--ink) !important;
  background    : var(--paper-subtle) !important;
  border        : 1px solid var(--line) !important;
  border-radius : var(--r-lg) !important;
  padding       : 12px 14px !important;
  resize        : vertical;
  transition    : border-color .15s;
  line-height   : 1.6;
}
.fnd-root .gr-textbox textarea:focus,
.fnd-root textarea:focus {
  border-color  : var(--slate) !important;
  outline       : none !important;
  box-shadow    : 0 0 0 3px color-mix(in srgb, var(--slate) 15%, transparent) !important;
}

/* Sample buttons */
.fnd-samples-label {
  font-size   : .72rem;
  color       : var(--ink-soft);
  margin      : 14px 0 6px;
  font-weight : 500;
}
.fnd-samples-wrap {
  display     : flex;
  flex-wrap   : wrap;
  gap         : 6px;
  margin-bottom: 14px;
}
.fnd-sample-btn {
  font-size     : .75rem !important;
  padding       : 5px 11px !important;
  border-radius : 20px !important;
  border        : 1px solid var(--line-strong) !important;
  background    : var(--paper-subtle) !important;
  color         : var(--ink-mid) !important;
  font-family   : var(--font-body) !important;
  cursor        : pointer;
  transition    : all .15s;
  white-space   : nowrap;
}
.fnd-sample-btn:hover {
  background    : var(--slate-light) !important;
  border-color  : var(--slate) !important;
  color         : var(--slate) !important;
}

/* Action buttons */
.fnd-btn-row {
  display : flex; gap : 8px; margin-top : 4px;
}
.fnd-btn-clear {
  flex         : 0 0 auto;
  padding      : 9px 16px !important;
  border-radius: var(--r-lg) !important;
  border       : 1px solid var(--line-strong) !important;
  background   : transparent !important;
  color        : var(--ink-mid) !important;
  font-family  : var(--font-body) !important;
  font-size    : .85rem !important;
  cursor       : pointer;
  transition   : all .15s;
}
.fnd-btn-clear:hover {
  background   : var(--paper-subtle) !important;
  color        : var(--ink) !important;
}
.fnd-btn-analyze {
  flex         : 1;
  padding      : 10px 20px !important;
  border-radius: var(--r-lg) !important;
  border       : none !important;
  background   : var(--ink) !important;
  color        : var(--paper) !important;
  font-family  : var(--font-body) !important;
  font-size    : .92rem !important;
  font-weight  : 600 !important;
  cursor       : pointer;
  transition   : background .15s, transform .1s;
  letter-spacing: .01em;
}
.fnd-btn-analyze:hover  { background: var(--ink-mid) !important; }
.fnd-btn-analyze:active { transform: scale(.98); }

/* Accordion overrides */
.fnd-root details summary {
  font-family  : var(--font-body);
  font-size    : .85rem;
  font-weight  : 600;
  color        : var(--ink-mid);
  padding      : 10px 0;
  cursor       : pointer;
  list-style   : none;
  border-top   : 1px solid var(--line);
  margin-top   : 12px;
  user-select  : none;
}
.fnd-root details summary::-webkit-details-marker { display: none; }

/* Export buttons */
.fnd-export-row {
  display    : flex; flex-wrap : wrap; gap : 6px; margin : 10px 0;
}
.fnd-export-btn {
  flex         : 1; min-width : 90px;
  padding      : 7px 12px !important;
  border-radius: var(--r-md) !important;
  border       : 1px solid var(--line-strong) !important;
  background   : var(--paper-subtle) !important;
  color        : var(--ink-mid) !important;
  font-size    : .78rem !important;
  font-family  : var(--font-body) !important;
  cursor       : pointer;
  transition   : all .15s;
}
.fnd-export-btn:hover {
  background   : var(--slate-light) !important;
  border-color : var(--slate) !important;
  color        : var(--slate) !important;
}

/* ─────────────────────────────────────────────
   RESULT PANEL — verdict, gauge, bars, cards
   ───────────────────────────────────────────── */

/* Placeholder state */
.fnd-placeholder {
  display         : flex;
  flex-direction  : column;
  align-items     : center;
  justify-content : center;
  gap             : 12px;
  min-height      : 260px;
  border          : 1px dashed var(--line-strong);
  border-radius   : var(--r-xl);
  color           : var(--ink-soft);
  font-size       : .9rem;
  text-align      : center;
  padding         : 32px;
  background      : var(--paper-subtle);
}
.fnd-placeholder svg { opacity: .35; }

/* Verdict stamp */
.fnd-verdict-wrap {
  background    : var(--paper-raised);
  border        : 1px solid var(--line);
  border-radius : var(--r-xl);
  padding       : 24px 24px 20px;
  box-shadow    : var(--sh-md);
  margin-bottom : 14px;
}
.fnd-verdict-header {
  font-size     : .68rem;
  font-weight   : 700;
  letter-spacing: .12em;
  text-transform: uppercase;
  color         : var(--ink-soft);
  margin-bottom : 10px;
}
.fnd-verdict-stamp {
  display       : flex;
  align-items   : flex-start;
  gap           : 14px;
  margin-bottom : 16px;
}
.fnd-verdict-icon {
  font-size : 2.2rem;
  line-height: 1;
  flex-shrink: 0;
}
.fnd-verdict-text-block { flex: 1; min-width: 0; }
.fnd-verdict-word {
  font-family   : var(--font-serif);
  font-size     : 1.7rem;
  font-weight   : 700;
  line-height   : 1.1;
  letter-spacing: -.02em;
  color         : var(--verdict-color, var(--ink));
}
.fnd-verdict-word-hi {
  font-family   : var(--font-serif);
  font-size     : 1.5rem;
  font-weight   : 600;
  line-height   : 1.15;
  color         : var(--verdict-color, var(--ink));
  display       : block;
}
.fnd-verdict-desc {
  font-size    : .84rem;
  color        : var(--ink-mid);
  margin-top   : 6px;
  line-height  : 1.5;
}
.fnd-verdict-meta {
  font-family  : var(--font-mono);
  font-size    : .68rem;
  color        : var(--ink-soft);
  margin-top   : 8px;
}
.fnd-verdict-claim {
  font-size    : .82rem;
  color        : var(--ink-mid);
  font-style   : italic;
  border-left  : 2px solid var(--line-strong);
  padding-left : 10px;
  margin-top   : 10px;
  line-height  : 1.5;
}

/* Verdict color classes */
.fnd-v-real      { --verdict-color: var(--v-real); }
.fnd-v-lreal     { --verdict-color: var(--v-lreal); }
.fnd-v-partial   { --verdict-color: var(--v-partial); }
.fnd-v-unv       { --verdict-color: var(--v-unv); }
.fnd-v-insuff    { --verdict-color: var(--v-insuff); }
.fnd-v-mixed     { --verdict-color: var(--v-mixed); }
.fnd-v-mislead   { --verdict-color: var(--v-mislead); }
.fnd-v-lfake     { --verdict-color: var(--v-lfake); }
.fnd-v-fake      { --verdict-color: var(--v-fake); }

/* ── SVG Gauge ── */
.fnd-gauge-wrap {
  display         : flex;
  flex-direction  : column;
  align-items     : center;
  margin          : 4px 0 12px;
}
.fnd-gauge-svg { overflow: visible; }
.fnd-gauge-needle {
  transform-origin : 100px 100px;
  transition        : transform 1.2s cubic-bezier(.34,1.56,.64,1);
}

/* ── Confidence bars ── */
.fnd-conf-section {
  margin-top : 4px;
}
.fnd-conf-title {
  font-size     : .68rem;
  font-weight   : 700;
  letter-spacing: .10em;
  text-transform: uppercase;
  color         : var(--ink-soft);
  margin-bottom : 10px;
}
.fnd-conf-row {
  display       : flex;
  align-items   : center;
  gap           : 8px;
  margin-bottom : 8px;
}
.fnd-conf-label {
  font-size   : .78rem;
  color       : var(--ink-mid);
  min-width   : 148px;
  flex-shrink : 0;
}
.fnd-conf-track {
  flex          : 1;
  height        : 5px;
  background    : var(--line);
  border-radius : 10px;
  overflow      : hidden;
}
.fnd-conf-fill {
  height        : 100%;
  border-radius : 10px;
  background    : var(--slate);
  width         : 0;
  transition    : width 1s cubic-bezier(.4,0,.2,1);
}
.fnd-conf-fill-overall { background: var(--verdict-color, var(--slate)); }
.fnd-conf-pct {
  font-family  : var(--font-mono);
  font-size    : .75rem;
  color        : var(--ink);
  min-width    : 34px;
  text-align   : right;
}

/* ── Verified Fact panel ── */
.fnd-fact-wrap {
  background    : var(--paper-raised);
  border        : 1px solid var(--line);
  border-radius : var(--r-xl);
  padding       : 18px 20px;
  box-shadow    : var(--sh-sm);
  margin-bottom : 14px;
}
.fnd-section-title {
  font-size     : .68rem;
  font-weight   : 700;
  letter-spacing: .10em;
  text-transform: uppercase;
  color         : var(--ink-soft);
  margin-bottom : 10px;
  display       : flex;
  align-items   : center;
  gap           : 6px;
}
.fnd-section-title::before {
  content       : '';
  display       : inline-block;
  width         : 6px; height : 6px;
  border-radius : 50%;
  background    : var(--verdict-color, var(--slate));
  flex-shrink   : 0;
}
.fnd-fact-verdict-tag {
  display       : inline-block;
  font-size     : .7rem;
  font-weight   : 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  padding       : 2px 8px;
  border-radius : 4px;
  background    : color-mix(in srgb, var(--verdict-color, var(--slate)) 12%, transparent);
  color         : var(--verdict-color, var(--slate));
  margin-bottom : 8px;
  border        : 1px solid color-mix(in srgb, var(--verdict-color, var(--slate)) 30%, transparent);
}
.fnd-fact-text {
  font-size     : .85rem;
  color         : var(--ink-mid);
  line-height   : 1.55;
}

/* ── Sources section ── */
.fnd-sources-wrap {
  background    : var(--paper-raised);
  border        : 1px solid var(--line);
  border-radius : var(--r-xl);
  padding       : 18px 20px;
  box-shadow    : var(--sh-sm);
  margin-bottom : 14px;
}
.fnd-sources-grid {
  display       : grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap           : 10px;
  margin-top    : 10px;
}
.fnd-src-card {
  border        : 1px solid var(--line);
  border-radius : var(--r-lg);
  padding       : 12px 14px;
  background    : var(--paper-subtle);
  position      : relative;
  overflow      : hidden;
  transition    : box-shadow .15s;
}
.fnd-src-card:hover { box-shadow: var(--sh-sm); }
.fnd-src-tab {
  position      : absolute;
  top           : 0; right : 0;
  font-size     : .62rem;
  font-weight   : 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  padding       : 2px 8px;
  border-radius : 0 var(--r-lg) 0 var(--r-md);
}
.fnd-src-tab-sup { background: var(--verify-light); color: var(--verify); }
.fnd-src-tab-con { background: var(--flag-light);   color: var(--flag);   }
.fnd-src-tab-neu { background: var(--neutral-light); color: var(--neutral-sig); }
.fnd-src-domain {
  font-family   : var(--font-mono);
  font-size     : .68rem;
  color         : var(--ink-soft);
  margin-bottom : 4px;
  margin-top    : 2px;
}
.fnd-src-title {
  font-size     : .82rem;
  font-weight   : 500;
  color         : var(--ink);
  line-height   : 1.4;
  margin-bottom : 6px;
}
.fnd-src-snippet {
  font-size     : .75rem;
  color         : var(--ink-mid);
  line-height   : 1.5;
}
.fnd-src-link {
  display       : inline-block;
  font-size     : .72rem;
  color         : var(--slate);
  margin-top    : 6px;
  text-decoration: none;
  font-weight   : 500;
}
.fnd-src-link:hover { text-decoration: underline; }
.fnd-no-sources {
  font-size    : .84rem;
  color        : var(--ink-soft);
  font-style   : italic;
  padding      : 8px 0;
}

/* ── Reasoning transcript ── */
.fnd-reasoning-wrap {
  background    : var(--paper-raised);
  border        : 1px solid var(--line);
  border-radius : var(--r-xl);
  padding       : 18px 20px;
  box-shadow    : var(--sh-sm);
  margin-bottom : 14px;
}
.fnd-reasoning-list {
  list-style    : none;
  padding       : 0;
  border-left   : 2px solid var(--line-strong);
  margin-top    : 10px;
  padding-left  : 16px;
}
.fnd-reasoning-list li {
  font-size     : .84rem;
  color         : var(--ink-mid);
  line-height   : 1.6;
  padding       : 5px 0;
  border-bottom : 1px solid var(--line);
  counter-increment: reasoning;
  position      : relative;
}
.fnd-reasoning-list li:last-child { border-bottom: none; }
.fnd-reasoning-list li::before {
  content       : counter(reasoning);
  position      : absolute;
  left          : -28px;
  top           : 8px;
  font-family   : var(--font-mono);
  font-size     : .62rem;
  color         : var(--ink-soft);
  background    : var(--paper-raised);
  width         : 18px; height : 18px;
  border-radius : 50%;
  border        : 1px solid var(--line);
  display       : flex;
  align-items   : center;
  justify-content: center;
}
.fnd-reasoning-wrap { counter-reset: reasoning; }

/* ── Loading shimmer ── */
.fnd-loading {
  background    : var(--paper-raised);
  border        : 1px solid var(--line);
  border-radius : var(--r-xl);
  padding       : 24px;
  box-shadow    : var(--sh-sm);
}
.fnd-shimmer-line {
  height        : 14px;
  border-radius : 4px;
  background    : linear-gradient(90deg,
    var(--paper-subtle) 25%,
    var(--line) 50%,
    var(--paper-subtle) 75%);
  background-size: 200% 100%;
  animation     : fnd-shimmer 1.4s infinite;
  margin-bottom : 10px;
}
@keyframes fnd-shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  TEAM CSS
# ══════════════════════════════════════════════════════════════════════════════
TEAM_CSS = """
/* ── Team section ── */
.fnd-team-section {
  margin        : 32px 0 0;
  padding       : 28px 24px;
  background    : var(--paper-raised);
  border-top    : 1px solid var(--line);
  border-radius : var(--r-xl) var(--r-xl) 0 0;
}
.fnd-team-hdr {
  display       : flex;
  align-items   : baseline;
  gap           : 10px;
  margin-bottom : 4px;
}
.fnd-team-title {
  font-family   : var(--font-serif);
  font-size     : 1.15rem;
  font-weight   : 600;
  color         : var(--ink);
  letter-spacing: -.01em;
}
.fnd-team-sub {
  font-size     : .78rem;
  color         : var(--ink-soft);
  margin-bottom : 20px;
  line-height   : 1.5;
}
.fnd-team-hint {
  font-size     : .72rem;
  color         : var(--ink-soft);
  margin-bottom : 14px;
  font-style    : italic;
}
.fnd-team-grid {
  display               : grid;
  grid-template-columns : repeat(auto-fill, minmax(170px, 1fr));
  gap                   : 12px;
  margin-bottom         : 24px;
}
.fnd-team-card {
  display       : flex;
  flex-direction: column;
  align-items   : center;
  text-align    : center;
  padding       : 20px 14px 16px;
  border        : 1px solid var(--line);
  border-radius : var(--r-xl);
  background    : var(--paper-subtle);
  cursor        : pointer;
  transition    : all .2s;
  position      : relative;
  overflow      : hidden;
}
.fnd-team-card::after {
  content       : '';
  position      : absolute;
  inset         : 0;
  border-radius : var(--r-xl);
  border        : 2px solid transparent;
  transition    : border-color .2s;
  pointer-events: none;
}
.fnd-team-card:hover { box-shadow: var(--sh-md); transform: translateY(-2px); }
.fnd-team-card:hover::after { border-color: var(--slate); }
.fnd-team-icon {
  width         : 52px; height : 52px;
  border-radius : 50%;
  background    : var(--slate-light);
  display       : flex;
  align-items   : center;
  justify-content: center;
  margin-bottom : 12px;
  color         : var(--slate);
  flex-shrink   : 0;
}
.fnd-team-icon svg { width: 24px; height: 24px; }
/* Lead member: bigger icon, accent border */
.fnd-team-card[data-id="naman-kumar"] .fnd-team-icon {
  width         : 60px; height : 60px;
  background    : color-mix(in srgb, var(--slate) 15%, var(--paper-raised));
}
.fnd-team-card[data-id="naman-kumar"] { border-color: color-mix(in srgb, var(--slate) 40%, transparent); }
.fnd-member-name {
  font-size     : .88rem;
  font-weight   : 600;
  color         : var(--ink);
  margin-bottom : 3px;
  line-height   : 1.3;
}
.fnd-member-role {
  font-size     : .72rem;
  color         : var(--ink-soft);
  line-height   : 1.4;
  margin-bottom : 8px;
}
.fnd-member-badge {
  font-size     : .65rem;
  font-weight   : 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  padding       : 2px 8px;
  border-radius : 20px;
  background    : var(--slate-light);
  color         : var(--slate);
  border        : 1px solid color-mix(in srgb, var(--slate) 25%, transparent);
}
.fnd-institution {
  font-size   : .76rem;
  color       : var(--ink-soft);
  text-align  : center;
  line-height : 1.7;
  border-top  : 1px solid var(--line);
  padding-top : 18px;
}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  MODAL CSS — team member profile popup
# ══════════════════════════════════════════════════════════════════════════════
MODAL_CSS = """
/* ── Modal backdrop ── */
.fnd-modal-backdrop {
  display         : none;
  position        : fixed;
  inset           : 0;
  background      : rgba(10,16,28,.55);
  backdrop-filter : blur(4px);
  z-index         : 9000;
  align-items     : center;
  justify-content : center;
  padding         : 16px;
}
.fnd-modal-backdrop.open { display: flex; animation: fnd-fade-in .2s ease; }
@keyframes fnd-fade-in { from { opacity: 0; } to { opacity: 1; } }

.fnd-modal {
  background    : var(--paper-raised);
  border        : 1px solid var(--line);
  border-radius : var(--r-xl);
  box-shadow    : var(--sh-lg);
  max-width     : 520px;
  width         : 100%;
  max-height    : 88vh;
  overflow-y    : auto;
  animation     : fnd-slide-up .25s cubic-bezier(.34,1.56,.64,1);
  position      : relative;
}
@keyframes fnd-slide-up {
  from { transform: translateY(24px); opacity: 0; }
  to   { transform: translateY(0);    opacity: 1; }
}
.fnd-modal-close {
  position      : absolute;
  top           : 14px; right : 14px;
  width         : 28px; height : 28px;
  border-radius : 50%;
  border        : 1px solid var(--line);
  background    : var(--paper-subtle);
  color         : var(--ink-soft);
  font-size     : 1rem;
  cursor        : pointer;
  display       : flex;
  align-items   : center;
  justify-content: center;
  transition    : all .15s;
  line-height   : 1;
  z-index       : 1;
}
.fnd-modal-close:hover { background: var(--flag-light); color: var(--flag); }

.fnd-modal-head {
  padding       : 24px 24px 16px;
  display       : flex;
  align-items   : flex-start;
  gap           : 16px;
  border-bottom : 1px solid var(--line);
}
.fnd-modal-icon {
  width         : 56px; height : 56px;
  border-radius : 50%;
  background    : var(--slate-light);
  display       : flex;
  align-items   : center;
  justify-content: center;
  color         : var(--slate);
  flex-shrink   : 0;
}
.fnd-modal-icon svg { width: 26px; height: 26px; }
.fnd-modal-name {
  font-family   : var(--font-serif);
  font-size     : 1.2rem;
  font-weight   : 700;
  color         : var(--ink);
  line-height   : 1.2;
  margin-bottom : 4px;
}
.fnd-modal-role {
  font-size     : .8rem;
  color         : var(--ink-mid);
  margin-bottom : 6px;
  line-height   : 1.4;
}
.fnd-modal-badge {
  font-size     : .65rem;
  font-weight   : 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  padding       : 2px 8px;
  border-radius : 20px;
  background    : var(--slate-light);
  color         : var(--slate);
  border        : 1px solid color-mix(in srgb, var(--slate) 25%, transparent);
}
.fnd-modal-body { padding: 20px 24px 24px; }
.fnd-modal-bio {
  font-size    : .87rem;
  color        : var(--ink-mid);
  line-height  : 1.65;
  margin-bottom: 18px;
}
.fnd-modal-section-title {
  font-size     : .68rem;
  font-weight   : 700;
  letter-spacing: .10em;
  text-transform: uppercase;
  color         : var(--ink-soft);
  margin-bottom : 8px;
  margin-top    : 16px;
}
.fnd-modal-section-title:first-child { margin-top: 0; }
.fnd-modal-skills {
  display   : flex;
  flex-wrap : wrap;
  gap       : 6px;
  margin-bottom: 4px;
}
.fnd-skill-tag {
  font-size     : .72rem;
  font-weight   : 500;
  padding       : 3px 10px;
  border-radius : 20px;
  background    : var(--paper-subtle);
  color         : var(--ink-mid);
  border        : 1px solid var(--line);
}
.fnd-modal-contrib {
  list-style    : none;
  padding       : 0;
}
.fnd-modal-contrib li {
  font-size    : .83rem;
  color        : var(--ink-mid);
  line-height  : 1.55;
  padding      : 6px 0;
  border-bottom: 1px solid var(--line);
  padding-left : 14px;
  position     : relative;
}
.fnd-modal-contrib li:last-child { border-bottom: none; }
.fnd-modal-contrib li::before {
  content   : '→';
  position  : absolute;
  left      : 0;
  color     : var(--slate);
  font-size : .78rem;
}
.fnd-modal-quote {
  font-family  : var(--font-serif);
  font-size    : .9rem;
  font-style   : italic;
  color        : var(--ink-mid);
  border-left  : 3px solid var(--slate);
  padding-left : 14px;
  margin-top   : 18px;
  line-height  : 1.6;
}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  DARK-MODE explicit overrides where CSS vars aren't enough
# ══════════════════════════════════════════════════════════════════════════════
DARK_CSS = """
.fnd-root[data-theme="dark"] .gradio-container,
.fnd-root[data-theme="dark"] .gradio-container > .main {
  background: var(--paper) !important;
}
.fnd-root[data-theme="dark"] textarea,
.fnd-root[data-theme="dark"] input[type="text"] {
  background: var(--paper-subtle) !important;
  color: var(--ink) !important;
  border-color: var(--line) !important;
}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  RESPONSIVE
# ══════════════════════════════════════════════════════════════════════════════
MEDIA_CSS = """
@media (max-width: 640px) {
  .fnd-header        { padding: 10px 14px; }
  .fnd-wordmark-sub  { display: none; }
  .fnd-version-pill  { display: none; }
  .fnd-team-grid     { grid-template-columns: repeat(2, 1fr); }
  .fnd-sources-grid  { grid-template-columns: 1fr; }
  .fnd-conf-label    { min-width: 120px; font-size: .72rem; }
  .fnd-verdict-word  { font-size: 1.35rem; }
  .fnd-team-section  { padding: 20px 14px; }
  .fnd-modal         { border-radius: var(--r-lg); }
}
@media (max-width: 400px) {
  .fnd-team-grid     { grid-template-columns: 1fr 1fr; }
  .fnd-lang-toggle span.label-text { display: none; }
}
"""
