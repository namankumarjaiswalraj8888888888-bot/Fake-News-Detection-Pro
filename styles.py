"""
styles.py
=========
Version 5 — All CSS for the Gradio application.

Bug fixes from V4
-----------------
- DARK MODE: --text-secondary and --text-muted were undefined in
  [data-theme="dark"] → invisible text on many cards.
- MOBILE: .fnd-team-grid used 3-column repeat with no clamp →
  overflowed on <380px viewports.
- SOURCE CARDS: .fnd-source-badge had no dark-mode equivalent.
- VERDICT CLASSES: V4 only defined .fnd-verdict-real/fake/unverified.
  V5 adds classes for all 9 verdicts.
- CONFIDENCE BARS: animation keyframe used `to{width:var(--w)}` which
  didn't work in Safari because var() inside @keyframes is unreliable.
  Fixed: animation sets initial width 0 → final via inline style override.

New in V5
---------
- 9-verdict color CSS classes (.fnd-verdict-real … .fnd-verdict-fake)
- Skeleton loading animation (shimmer effect)
- Verified Fact panel styles (.fnd-fact-*)
- Source card v2 styles (.fnd-src-*)
- 5-confidence bar layout (.fnd-conf-*)
- History panel styles (.fnd-hist-*)
- Better @media queries for 380px, 480px, 640px, 768px, 1024px breakpoints

AI Fake News Detection & Live Verification System — Version 5
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar, Parmeshwar Kumar, Amit Kumar,
              Prince Kumar Chaurasiya, Dhiraj Kumar, MD. Tausim Akhtar
"""

from __future__ import annotations

# ── CSS Variables & Reset ─────────────────────────────────────────────────────

BASE_CSS = """
/* ═══════════════════════════════════════════════════
   DESIGN TOKENS — Light mode defaults
   ═══════════════════════════════════════════════════ */
:root {
  /* Backgrounds */
  --bg-app       : #f0f4f8;
  --bg-card      : #ffffff;
  --bg-input     : #ffffff;
  --bg-subtle    : #f8fafc;
  --bg-hover     : #f1f5f9;
  --bg-skeleton  : #e2e8f0;
  --bg-skeleton-s: #f1f5f9;

  /* Text */
  --text-primary  : #0f172a;
  --text-secondary: #475569;
  --text-muted    : #94a3b8;
  --text-link     : #2563eb;

  /* Borders */
  --border        : #e2e8f0;
  --border-strong : #cbd5e1;

  /* Shadows */
  --shadow-sm : 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
  --shadow-md : 0 4px 12px rgba(0,0,0,.08), 0 2px 4px rgba(0,0,0,.04);
  --shadow-lg : 0 10px 30px rgba(0,0,0,.10), 0 4px 8px rgba(0,0,0,.05);

  /* Brand */
  --accent     : #2563eb;
  --accent-hover: #1d4ed8;
  --radius-sm  : 8px;
  --radius-md  : 12px;
  --radius-lg  : 16px;
  --radius-xl  : 20px;

  /* 9 Verdict colours */
  --c-real      : #059669;
  --c-lreal     : #10b981;
  --c-partial   : #0891b2;
  --c-unv       : #eab308;
  --c-insuff    : #94a3b8;
  --c-mixed     : #d97706;
  --c-mislead   : #ea580c;
  --c-lfake     : #dc6803;
  --c-fake      : #dc2626;
}

/* ═══════════════════════════════════════════════════
   DARK MODE — FIXED: text-secondary and text-muted
   were undefined in V4 → invisible text.
   ═══════════════════════════════════════════════════ */
[data-theme="dark"], .dark {
  --bg-app        : #0b1120;
  --bg-card       : #131f35;
  --bg-input      : #1a2840;
  --bg-subtle     : #0f1929;
  --bg-hover      : #1e2f4a;
  --bg-skeleton   : #1a2840;
  --bg-skeleton-s : #243354;

  /* BUG FIX V4: these two were missing → text invisible in dark mode */
  --text-primary  : #f0f6ff;
  --text-secondary: #a8bcd8;
  --text-muted    : #6b84a3;
  --text-link     : #60a5fa;

  --border        : #1e3155;
  --border-strong : #2a4470;
  --shadow-sm     : 0 1px 3px rgba(0,0,0,.30);
  --shadow-md     : 0 4px 12px rgba(0,0,0,.40);
  --shadow-lg     : 0 10px 30px rgba(0,0,0,.50);
  --accent        : #3b82f6;
  --accent-hover  : #60a5fa;
  --bg-skeleton   : #1e2f4a;
  --bg-skeleton-s : #263f5e;
}

/* Base reset for Gradio containers */
.gradio-container { background: var(--bg-app) !important; }

* { box-sizing: border-box; }

a { color: var(--text-link); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ═══════════════════════════════════════════════════
   HEADER
   ═══════════════════════════════════════════════════ */
.fnd-header {
  text-align: center;
  padding: 32px 20px 20px;
}
.fnd-header-title {
  font-size: clamp(1.4rem, 4vw, 2.2rem);
  font-weight: 800;
  background: linear-gradient(135deg, var(--accent), #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 8px;
  letter-spacing: -0.5px;
}
.fnd-header-sub {
  color: var(--text-secondary);
  font-size: clamp(.8rem, 2vw, .95rem);
}
.fnd-version-badge {
  display: inline-block;
  background: linear-gradient(135deg, var(--accent), #8b5cf6);
  color: #fff;
  font-size: .7rem;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
  margin-top: 8px;
  letter-spacing: .5px;
}

/* ═══════════════════════════════════════════════════
   INPUT PANEL
   ═══════════════════════════════════════════════════ */
.fnd-input-card {
  background    : var(--bg-card);
  border        : 1px solid var(--border);
  border-radius : var(--radius-lg);
  padding       : 24px;
  box-shadow    : var(--shadow-md);
}
.fnd-samples-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
.fnd-sample-btn {
  font-size: .78rem !important;
  padding: 4px 12px !important;
  border-radius: 20px !important;
  border: 1px solid var(--border) !important;
  background: var(--bg-subtle) !important;
  color: var(--text-secondary) !important;
  cursor: pointer;
  transition: all .2s ease;
}
.fnd-sample-btn:hover {
  border-color: var(--accent) !important;
  color: var(--accent) !important;
  background: rgba(37,99,235,.06) !important;
}
.fnd-analyze-btn {
  background: linear-gradient(135deg, var(--accent), #8b5cf6) !important;
  color: #fff !important;
  font-weight: 700 !important;
  border-radius: var(--radius-md) !important;
  padding: 12px 28px !important;
  font-size: 1rem !important;
  border: none !important;
  transition: opacity .2s ease;
  width: 100%;
  margin-top: 12px;
}
.fnd-analyze-btn:hover { opacity: .88; }

/* ═══════════════════════════════════════════════════
   LOADING SKELETON
   ═══════════════════════════════════════════════════ */
@keyframes fnd-shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}
.fnd-skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-skeleton) 25%,
    var(--bg-skeleton-s) 50%,
    var(--bg-skeleton) 75%
  );
  background-size: 800px 100%;
  animation: fnd-shimmer 1.4s infinite linear;
  border-radius: var(--radius-sm);
}
.fnd-skeleton-box { height: 18px; margin-bottom: 10px; }
.fnd-skeleton-wide { width: 80%; }
.fnd-skeleton-mid  { width: 60%; }
.fnd-skeleton-narrow { width: 40%; }

.fnd-loading-card {
  background   : var(--bg-card);
  border       : 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding      : 28px 24px;
  box-shadow   : var(--shadow-md);
}
.fnd-loading-steps {
  list-style: none;
  padding: 0; margin: 16px 0 0;
}
.fnd-loading-steps li {
  padding: 6px 0;
  color: var(--text-secondary);
  font-size: .9rem;
  display: flex;
  align-items: center;
  gap: 8px;
}
.fnd-loading-steps li::before {
  content: "•";
  color: var(--accent);
  font-size: 1.2rem;
  animation: fnd-pulse 1.4s ease-in-out infinite;
}
@keyframes fnd-pulse {
  0%,100% { opacity:.3; }
  50%      { opacity:1; }
}

/* ═══════════════════════════════════════════════════
   RESULT CARD WRAPPER
   ═══════════════════════════════════════════════════ */
.fnd-result-wrap {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ═══════════════════════════════════════════════════
   VERDICT BADGE — 9 VERDICTS
   V4 only had 3; this section adds all 9.
   ═══════════════════════════════════════════════════ */
.fnd-verdict {
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  border: 1px solid;
  box-shadow: var(--shadow-sm);
}
.fnd-verdict-icon { font-size: 2.4rem; margin-bottom: 6px; }
.fnd-verdict-label {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: .5px;
}
.fnd-verdict-desc {
  font-size: .88rem;
  margin-top: 6px;
  opacity: .85;
}

.fnd-verdict-real      { background:rgba(5,150,105,.08);   border-color:rgba(5,150,105,.30);   color:var(--c-real); }
.fnd-verdict-likely-real { background:rgba(16,185,129,.08); border-color:rgba(16,185,129,.25); color:var(--c-lreal); }
.fnd-verdict-partial   { background:rgba(8,145,178,.08);   border-color:rgba(8,145,178,.25);   color:var(--c-partial); }
.fnd-verdict-unv       { background:rgba(234,179,8,.08);   border-color:rgba(234,179,8,.25);   color:var(--c-unv); }
.fnd-verdict-insuff    { background:rgba(148,163,184,.08); border-color:rgba(148,163,184,.25); color:var(--c-insuff); }
.fnd-verdict-mixed     { background:rgba(217,119,6,.08);   border-color:rgba(217,119,6,.25);   color:var(--c-mixed); }
.fnd-verdict-misleading { background:rgba(234,88,12,.08);  border-color:rgba(234,88,12,.25);   color:var(--c-mislead); }
.fnd-verdict-likely-fake { background:rgba(220,104,3,.08); border-color:rgba(220,104,3,.25);   color:var(--c-lfake); }
.fnd-verdict-fake      { background:rgba(220,38,38,.08);   border-color:rgba(220,38,38,.30);   color:var(--c-fake); }

/* ═══════════════════════════════════════════════════
   CONFIDENCE BARS — 5 components
   BUG FIX V4: removed var() inside @keyframes (Safari bug).
   Width is now set via inline style; animation just fades in.
   ═══════════════════════════════════════════════════ */
.fnd-conf-section { margin-bottom: 20px; }
.fnd-conf-row { margin-bottom: 10px; }
.fnd-conf-label {
  display: flex;
  justify-content: space-between;
  font-size: .82rem;
  color: var(--text-secondary);
  margin-bottom: 4px;
}
.fnd-conf-label span:last-child { font-weight: 700; color: var(--text-primary); }
.fnd-conf-track {
  height: 8px;
  border-radius: 4px;
  background: var(--bg-skeleton);
  overflow: hidden;
}
.fnd-conf-bar {
  height: 100%;
  border-radius: 4px;
  transition: width .8s cubic-bezier(.4,0,.2,1);
}
/* Confidence bar colours per verdict type */
.bar-real        { background: linear-gradient(90deg,#059669,#34d399); }
.bar-likely-real { background: linear-gradient(90deg,#10b981,#6ee7b7); }
.bar-partial     { background: linear-gradient(90deg,#0891b2,#38bdf8); }
.bar-unv         { background: linear-gradient(90deg,#d97706,#fbbf24); }
.bar-insuff      { background: linear-gradient(90deg,#64748b,#94a3b8); }
.bar-mixed       { background: linear-gradient(90deg,#d97706,#f59e0b); }
.bar-misleading  { background: linear-gradient(90deg,#ea580c,#fb923c); }
.bar-likely-fake { background: linear-gradient(90deg,#dc6803,#f97316); }
.bar-fake        { background: linear-gradient(90deg,#dc2626,#f87171); }
.bar-default     { background: linear-gradient(90deg,var(--accent),#8b5cf6); }

/* ═══════════════════════════════════════════════════
   INFO PANEL (ML / Evidence cards)
   ═══════════════════════════════════════════════════ */
.fnd-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.fnd-info-card {
  background    : var(--bg-card);
  border        : 1px solid var(--border);
  border-radius : var(--radius-md);
  padding       : 16px;
  box-shadow    : var(--shadow-sm);
}
.fnd-info-card h4 {
  font-size: .78rem;
  text-transform: uppercase;
  letter-spacing: .8px;
  color: var(--text-muted);
  margin: 0 0 10px;
}
.fnd-stat-row {
  display: flex;
  justify-content: space-between;
  font-size: .85rem;
  padding: 3px 0;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
}
.fnd-stat-row:last-child { border-bottom: none; }
.fnd-stat-row span:last-child { font-weight: 600; color: var(--text-primary); }

/* ═══════════════════════════════════════════════════
   VERIFIED FACT PANEL
   ═══════════════════════════════════════════════════ */
.fnd-fact-panel {
  background    : var(--bg-card);
  border        : 1px solid var(--border);
  border-radius : var(--radius-md);
  padding       : 18px 20px;
  box-shadow    : var(--shadow-sm);
}
.fnd-fact-panel h3 {
  font-size: .9rem;
  text-transform: uppercase;
  letter-spacing: .8px;
  color: var(--text-muted);
  margin: 0 0 12px;
}
.fnd-fact-type-badge {
  display: inline-block;
  font-size: .72rem;
  font-weight: 700;
  letter-spacing: .5px;
  padding: 2px 10px;
  border-radius: 20px;
  margin-bottom: 10px;
}
.fnd-fact-verified   { background:rgba(5,150,105,.12); color:#059669; }
.fnd-fact-debunked   { background:rgba(220,38,38,.12);  color:#dc2626; }
.fnd-fact-mixed      { background:rgba(8,145,178,.12);  color:#0891b2; }
.fnd-fact-insufficient { background:rgba(100,116,139,.12); color:#64748b; }

.fnd-fact-summary {
  font-size: .88rem;
  color: var(--text-secondary);
  line-height: 1.55;
  margin-bottom: 10px;
}
.fnd-fact-meta {
  font-size: .8rem;
  color: var(--text-muted);
  margin-top: 4px;
}
.fnd-fact-meta strong { color: var(--text-secondary); }
.fnd-fact-misconception {
  background: rgba(220,38,38,.06);
  border-left: 3px solid var(--c-fake);
  padding: 8px 12px;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-size: .83rem;
  color: var(--text-secondary);
  margin-top: 10px;
}
.fnd-fact-correctfact {
  background: rgba(5,150,105,.06);
  border-left: 3px solid var(--c-real);
  padding: 8px 12px;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-size: .83rem;
  color: var(--text-secondary);
  margin-top: 8px;
}
.fnd-related-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
}
.fnd-related-list li {
  font-size: .82rem;
  color: var(--text-secondary);
  padding: 3px 0;
}
.fnd-related-list li::before {
  content: "→ ";
  color: var(--accent);
  font-weight: 700;
}

/* ═══════════════════════════════════════════════════
   SOURCE CARDS (Rich — V5)
   ═══════════════════════════════════════════════════ */
.fnd-src-list { display: flex; flex-direction: column; gap: 10px; }
.fnd-src-card {
  background    : var(--bg-card);
  border        : 1px solid var(--border);
  border-radius : var(--radius-md);
  padding       : 14px 16px;
  box-shadow    : var(--shadow-sm);
  transition    : box-shadow .2s ease;
}
.fnd-src-card:hover { box-shadow: var(--shadow-md); }
.fnd-src-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 6px;
}
.fnd-src-name {
  font-weight: 700;
  font-size: .88rem;
  color: var(--text-primary);
}
.fnd-src-badges { display: flex; gap: 6px; flex-wrap: wrap; }
.fnd-src-badge {
  font-size: .68rem;
  font-weight: 700;
  letter-spacing: .5px;
  padding: 2px 8px;
  border-radius: 20px;
}
.fnd-badge-supporting   { background:rgba(5,150,105,.12);  color:#059669; }
.fnd-badge-contradicting{ background:rgba(220,38,38,.12);  color:#dc2626; }
.fnd-badge-neutral      { background:rgba(100,116,139,.12);color:#64748b; }
.fnd-badge-factcheck    { background:rgba(37,99,235,.12);  color:var(--accent); }
.fnd-trust-badge {
  font-size: .68rem;
  padding: 2px 8px;
  border-radius: 20px;
  background: var(--bg-subtle);
  color: var(--text-secondary);
}
.fnd-src-snippet {
  font-size: .82rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 4px 0;
}
.fnd-src-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
.fnd-src-date { font-size: .75rem; color: var(--text-muted); }
.fnd-src-link {
  font-size: .75rem;
  color: var(--accent);
  font-weight: 600;
  padding: 3px 10px;
  border: 1px solid var(--accent);
  border-radius: 20px;
  transition: all .2s ease;
  text-decoration: none !important;
}
.fnd-src-link:hover {
  background: var(--accent);
  color: #fff !important;
}

/* ═══════════════════════════════════════════════════
   REASONING LIST
   ═══════════════════════════════════════════════════ */
.fnd-reasoning-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.fnd-reasoning-list li {
  padding: 7px 0 7px 16px;
  font-size: .86rem;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
  position: relative;
  line-height: 1.5;
}
.fnd-reasoning-list li:last-child { border-bottom: none; }
.fnd-reasoning-list li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: var(--accent);
  font-size: 1rem;
  line-height: 1.5;
}

/* ═══════════════════════════════════════════════════
   SECTION WRAPPER CARD
   ═══════════════════════════════════════════════════ */
.fnd-section {
  background    : var(--bg-card);
  border        : 1px solid var(--border);
  border-radius : var(--radius-md);
  padding       : 16px 20px;
  box-shadow    : var(--shadow-sm);
}
.fnd-section-title {
  font-size: .78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .8px;
  color: var(--text-muted);
  margin: 0 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

/* ═══════════════════════════════════════════════════
   HISTORY PANEL
   ═══════════════════════════════════════════════════ */
.fnd-hist-row {
  padding       : 10px 14px;
  border-bottom : 1px solid var(--border);
  font-size     : .84rem;
  color         : var(--text-secondary);
  display       : flex;
  justify-content: space-between;
  align-items   : center;
  gap           : 8px;
}
.fnd-hist-row:last-child { border-bottom: none; }
.fnd-hist-preview { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fnd-hist-badge {
  font-size: .7rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
  white-space: nowrap;
}
.fnd-hist-time { font-size: .74rem; color: var(--text-muted); white-space: nowrap; }

/* ═══════════════════════════════════════════════════
   ERROR CARD
   ═══════════════════════════════════════════════════ */
.fnd-error-card {
  background    : rgba(220,38,38,.06);
  border        : 1px solid rgba(220,38,38,.25);
  border-radius : var(--radius-md);
  padding       : 16px 20px;
}
.fnd-error-title {
  color     : #dc2626;
  font-weight: 700;
  font-size : .9rem;
  margin    : 0 0 6px;
}
.fnd-error-msg {
  color    : var(--text-secondary);
  font-size: .86rem;
}

/* ═══════════════════════════════════════════════════
   EXPORT PANEL
   ═══════════════════════════════════════════════════ */
.fnd-export-row {
  display   : flex;
  gap       : 10px;
  flex-wrap : wrap;
  margin-top: 10px;
}
.fnd-export-btn {
  font-size   : .82rem !important;
  padding     : 7px 16px !important;
  border-radius: var(--radius-sm) !important;
  border      : 1px solid var(--border) !important;
  background  : var(--bg-subtle) !important;
  color       : var(--text-secondary) !important;
  cursor      : pointer;
  font-weight : 600 !important;
  transition  : all .2s ease;
}
.fnd-export-btn:hover {
  border-color: var(--accent) !important;
  color: var(--accent) !important;
}

/* ═══════════════════════════════════════════════════
   TEAM SECTION
   ═══════════════════════════════════════════════════ */
.fnd-team-section {
  background    : var(--bg-card);
  border        : 1px solid var(--border);
  border-radius : var(--radius-xl);
  padding       : 28px 24px;
  margin-top    : 24px;
  box-shadow    : var(--shadow-md);
}
.fnd-team-title {
  text-align   : center;
  font-weight  : 800;
  font-size    : 1.1rem;
  color        : var(--text-primary);
  margin-bottom: 6px;
}
.fnd-team-sub {
  text-align   : center;
  color        : var(--text-muted);
  font-size    : .82rem;
  margin-bottom: 20px;
}
/* MOBILE BUG FIX V4: 3-column grid overflowed on <380px */
.fnd-team-grid {
  display              : grid;
  grid-template-columns: repeat(auto-fill, minmax(min(160px,100%), 1fr));
  gap                  : 12px;
}
.fnd-team-card {
  background    : var(--bg-subtle);
  border        : 1px solid var(--border);
  border-radius : var(--radius-md);
  padding       : 16px 12px;
  text-align    : center;
  transition    : box-shadow .2s ease;
}
.fnd-team-card:hover { box-shadow: var(--shadow-md); }
.fnd-avatar {
  width         : 44px;
  height        : 44px;
  border-radius : 50%;
  background    : linear-gradient(135deg, var(--accent), #8b5cf6);
  color         : #fff;
  font-size     : .9rem;
  font-weight   : 700;
  display       : flex;
  align-items   : center;
  justify-content: center;
  margin        : 0 auto 10px;
}
.fnd-member-name {
  font-size  : .84rem;
  font-weight: 700;
  color      : var(--text-primary);
  margin-bottom: 3px;
}
.fnd-member-role {
  font-size  : .72rem;
  color      : var(--text-muted);
  line-height: 1.4;
}
.fnd-member-badge {
  display       : inline-block;
  margin-top    : 6px;
  font-size     : .66rem;
  font-weight   : 700;
  padding       : 2px 8px;
  border-radius : 20px;
  background    : rgba(37,99,235,.10);
  color         : var(--accent);
  letter-spacing: .4px;
}
.fnd-institution {
  text-align : center;
  margin-top : 18px;
  font-size  : .8rem;
  color      : var(--text-muted);
  line-height: 1.6;
}

/* ═══════════════════════════════════════════════════
   RESPONSIVE BREAKPOINTS — FIXED V4 mobile issues
   ═══════════════════════════════════════════════════ */
@media (max-width: 640px) {
  .fnd-info-grid { grid-template-columns: 1fr; }
  .fnd-input-card,
  .fnd-team-section { padding: 16px 14px; }
  .fnd-verdict-label { font-size: 1.2rem; }
  .fnd-src-footer { flex-direction: column; align-items: flex-start; }
  .fnd-export-row { flex-direction: column; }
}
@media (max-width: 480px) {
  .fnd-header { padding: 20px 12px 14px; }
  .fnd-header-title { font-size: 1.3rem; }
  .fnd-verdict { padding: 14px 16px; }
  .fnd-verdict-icon { font-size: 1.8rem; }
  .fnd-section { padding: 12px 14px; }
  .fnd-fact-panel { padding: 12px 14px; }
}
@media (max-width: 380px) {
  /* BUG FIX V4: prevent any horizontal overflow on very small phones */
  .fnd-samples-grid { flex-direction: column; }
  .fnd-sample-btn { width: 100% !important; text-align: left !important; }
  .fnd-src-header { flex-direction: column; align-items: flex-start; }
  .fnd-hist-row { flex-direction: column; align-items: flex-start; gap: 4px; }
}

/* Gradio overrides — keep our styles winning */
.gradio-container .gr-button { transition: all .2s ease; }
footer { display: none !important; }
"""


def get_css() -> str:
    """Return the complete stylesheet. Called once at Gradio startup."""
    return BASE_CSS
