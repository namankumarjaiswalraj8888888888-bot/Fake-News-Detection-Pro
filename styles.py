"""
styles.py
=========
Version 4 — Complete CSS string for the Gradio UI.

Design decisions
----------------
- CSS custom properties (variables) for every color — one place to theme.
- True dark / light mode via data-theme attribute on <html>.
- System preference auto-detection via prefers-color-scheme.
- Mobile-first breakpoints (320px → 768px → 1200px).
- Glassmorphism cards: backdrop-filter blur, translucent backgrounds.
- Confidence bars animate from 0 → target width via CSS keyframe (avoids
  the flash-to-full-width bug in V3 where transition ran on initial render).
- No Gradio-version-specific class names (no .svelte-*, no .gradio-container).
  All overrides target standard HTML elements or our own .fnd-* classes.
- Reduced motion respected via @media (prefers-reduced-motion: reduce).

AI Fake News Detection & Live Verification System — Version 4
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar & Parmeshwar
"""

CSS = """
/* ═══════════════════════════════════════════════════════════════════════════
   1. DESIGN TOKENS
═══════════════════════════════════════════════════════════════════════════ */

:root {
  /* Brand */
  --brand-primary:   #6366f1;
  --brand-secondary: #8b5cf6;
  --brand-accent:    #06b6d4;
  --brand-gradient:  linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%);

  /* Verdict */
  --real-color:      #22c55e;
  --real-bg:         #f0fdf4;
  --real-border:     #86efac;
  --fake-color:      #ef4444;
  --fake-bg:         #fef2f2;
  --fake-border:     #fca5a5;
  --unv-color:       #eab308;
  --unv-bg:          #fefce8;
  --unv-border:      #fde047;

  /* Source classification */
  --sup-color:       #10b981;
  --con-color:       #f43f5e;
  --neu-color:       #64748b;

  /* Typography */
  --font-sans: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;

  /* Spacing scale */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-12: 3rem;

  /* Border radius */
  --radius-sm:  6px;
  --radius-md:  12px;
  --radius-lg:  18px;
  --radius-xl:  24px;
  --radius-full: 9999px;

  /* Transitions */
  --ease-out:    cubic-bezier(0.16, 1, 0.3, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);

  /* Shadows */
  --shadow-sm:  0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
  --shadow-md:  0 4px 16px rgba(0,0,0,0.10), 0 2px 6px rgba(0,0,0,0.08);
  --shadow-lg:  0 10px 40px rgba(0,0,0,0.14), 0 4px 12px rgba(0,0,0,0.08);
  --shadow-xl:  0 20px 60px rgba(0,0,0,0.18);
  --glow:       0 0 24px rgba(99,102,241,0.25);
}

/* ── Light theme (default) ─────────────────────────────────────────────── */
:root,
html[data-theme="light"] {
  --bg-page:         #f1f5f9;
  --bg-hero:         linear-gradient(160deg, #0f172a 0%, #1e1b4b 50%, #0c1445 100%);
  --bg-card:         rgba(255,255,255,0.85);
  --bg-card-hover:   rgba(255,255,255,0.95);
  --bg-input:        #ffffff;
  --bg-subtle:       #f8fafc;
  --bg-code:         #f1f5f9;
  --border-color:    rgba(99,102,241,0.15);
  --border-subtle:   #e2e8f0;
  --text-primary:    #0f172a;
  --text-secondary:  #475569;
  --text-muted:      #94a3b8;
  --text-hero:       #ffffff;
  --glass-bg:        rgba(255,255,255,0.70);
  --glass-border:    rgba(255,255,255,0.50);
  --glass-blur:      blur(20px) saturate(180%);
  --input-border:    #c7d2fe;
  --input-focus:     #6366f1;
  --tag-bg:          #ede9fe;
  --tag-color:       #5b21b6;
  --btn-text:        #ffffff;
  --stat-bg:         rgba(255,255,255,0.8);
}

/* ── Dark theme ────────────────────────────────────────────────────────── */
html[data-theme="dark"] {
  --bg-page:         #090e1a;
  --bg-hero:         linear-gradient(160deg, #060b14 0%, #0d0f2b 50%, #06101e 100%);
  --bg-card:         rgba(15,23,42,0.85);
  --bg-card-hover:   rgba(20,30,55,0.95);
  --bg-input:        #0f172a;
  --bg-subtle:       #0d1625;
  --bg-code:         #0d1625;
  --border-color:    rgba(99,102,241,0.25);
  --border-subtle:   rgba(255,255,255,0.08);
  --text-primary:    #f1f5f9;
  --text-secondary:  #94a3b8;
  --text-muted:      #64748b;
  --text-hero:       #f1f5f9;
  --glass-bg:        rgba(15,23,42,0.70);
  --glass-border:    rgba(255,255,255,0.08);
  --glass-blur:      blur(20px) saturate(120%);
  --input-border:    rgba(99,102,241,0.40);
  --input-focus:     #818cf8;
  --tag-bg:          rgba(99,102,241,0.20);
  --tag-color:       #a5b4fc;
  --btn-text:        #ffffff;
  --real-bg:         rgba(34,197,94,0.12);
  --real-border:     rgba(34,197,94,0.35);
  --fake-bg:         rgba(239,68,68,0.12);
  --fake-border:     rgba(239,68,68,0.35);
  --unv-bg:          rgba(234,179,8,0.12);
  --unv-border:      rgba(234,179,8,0.35);
  --stat-bg:         rgba(15,23,42,0.7);
}


/* ═══════════════════════════════════════════════════════════════════════════
   2. GLOBAL RESET & BASE
═══════════════════════════════════════════════════════════════════════════ */

*, *::before, *::after { box-sizing: border-box; }

body,
.gradio-app,
.gradio-container,
#app,
footer { background: var(--bg-page) !important; }

body {
  font-family: var(--font-sans) !important;
  color: var(--text-primary) !important;
  -webkit-font-smoothing: antialiased;
  line-height: 1.6;
  transition: background 0.3s ease, color 0.3s ease;
}

/* Import Inter from Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');


/* ═══════════════════════════════════════════════════════════════════════════
   3. HERO BANNER
═══════════════════════════════════════════════════════════════════════════ */

.fnd-hero {
  background: var(--bg-hero);
  border-radius: var(--radius-xl);
  padding: var(--space-12) var(--space-8);
  text-align: center;
  position: relative;
  overflow: hidden;
  margin-bottom: var(--space-6);
  box-shadow: var(--shadow-xl);
}

.fnd-hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 60% 50% at 20% 30%, rgba(99,102,241,0.35) 0%, transparent 70%),
    radial-gradient(ellipse 50% 40% at 80% 70%, rgba(6,182,212,0.25) 0%, transparent 70%);
  pointer-events: none;
}

.fnd-hero-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.20);
  color: rgba(255,255,255,0.90);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: var(--space-1) var(--space-4);
  border-radius: var(--radius-full);
  margin-bottom: var(--space-4);
  backdrop-filter: blur(8px);
}

.fnd-hero h1 {
  font-size: clamp(1.6rem, 4vw, 2.8rem);
  font-weight: 800;
  color: #ffffff !important;
  line-height: 1.15;
  margin: 0 0 var(--space-3);
  background: linear-gradient(135deg, #ffffff 0%, #c7d2fe 60%, #67e8f9 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.fnd-hero p {
  font-size: clamp(0.85rem, 2vw, 1.05rem);
  color: rgba(255,255,255,0.72) !important;
  max-width: 640px;
  margin: 0 auto var(--space-4);
}

.fnd-hero-pills {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-2);
  margin-top: var(--space-4);
}

.fnd-hero-pill {
  background: rgba(255,255,255,0.10);
  border: 1px solid rgba(255,255,255,0.18);
  color: rgba(255,255,255,0.85);
  font-size: 0.75rem;
  padding: 4px 12px;
  border-radius: var(--radius-full);
  backdrop-filter: blur(6px);
}


/* ═══════════════════════════════════════════════════════════════════════════
   4. THEME TOGGLE
═══════════════════════════════════════════════════════════════════════════ */

.fnd-theme-bar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.fnd-theme-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  background: var(--glass-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  padding: 6px 14px;
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-secondary);
  backdrop-filter: var(--glass-blur);
  transition: all 0.25s var(--ease-out);
  box-shadow: var(--shadow-sm);
}

.fnd-theme-toggle:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
  box-shadow: var(--shadow-md);
}


/* ═══════════════════════════════════════════════════════════════════════════
   5. GLASS CARDS
═══════════════════════════════════════════════════════════════════════════ */

.fnd-card {
  background: var(--glass-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  backdrop-filter: var(--glass-blur);
  box-shadow: var(--shadow-md);
  transition: box-shadow 0.25s var(--ease-out), border-color 0.25s ease;
  position: relative;
}

.fnd-card:hover {
  box-shadow: var(--shadow-lg);
  border-color: rgba(99,102,241,0.30);
}

.fnd-card-title {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin: 0 0 var(--space-4);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}


/* ═══════════════════════════════════════════════════════════════════════════
   6. INPUT AREA
═══════════════════════════════════════════════════════════════════════════ */

.fnd-input-wrap textarea,
.fnd-input-wrap input {
  background: var(--bg-input) !important;
  border: 1.5px solid var(--input-border) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-sans) !important;
  font-size: 0.95rem !important;
  line-height: 1.6 !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
  padding: 12px 14px !important;
  resize: vertical !important;
}

.fnd-input-wrap textarea:focus,
.fnd-input-wrap input:focus {
  border-color: var(--input-focus) !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
  outline: none !important;
}

.fnd-input-wrap label span {
  font-weight: 600 !important;
  color: var(--text-primary) !important;
  font-size: 0.9rem !important;
}


/* ═══════════════════════════════════════════════════════════════════════════
   7. BUTTONS
═══════════════════════════════════════════════════════════════════════════ */

.fnd-btn-primary,
.fnd-btn-primary button {
  background: var(--brand-gradient) !important;
  border: none !important;
  border-radius: var(--radius-md) !important;
  color: var(--btn-text) !important;
  font-weight: 700 !important;
  font-size: 1rem !important;
  letter-spacing: 0.02em;
  padding: 14px 32px !important;
  cursor: pointer !important;
  box-shadow: 0 4px 20px rgba(99,102,241,0.40) !important;
  transition: all 0.25s var(--ease-out) !important;
  position: relative;
  overflow: hidden;
}

.fnd-btn-primary:hover button,
.fnd-btn-primary button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 32px rgba(99,102,241,0.55) !important;
}

.fnd-btn-primary:active button,
.fnd-btn-primary button:active {
  transform: translateY(0) !important;
}

.fnd-btn-secondary button {
  background: var(--glass-bg) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-secondary) !important;
  font-weight: 500 !important;
  font-size: 0.85rem !important;
  padding: 8px 18px !important;
  cursor: pointer !important;
  backdrop-filter: var(--glass-blur);
  transition: all 0.2s ease !important;
}

.fnd-btn-secondary button:hover {
  background: var(--bg-card-hover) !important;
  color: var(--text-primary) !important;
  border-color: var(--brand-primary) !important;
}

/* Sample news dropdown */
.fnd-sample select,
.fnd-sample button,
.fnd-sample .wrap {
  background: var(--bg-input) !important;
  border: 1px solid var(--input-border) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-secondary) !important;
  font-size: 0.85rem !important;
}


/* ═══════════════════════════════════════════════════════════════════════════
   8. VERDICT CARD
═══════════════════════════════════════════════════════════════════════════ */

.fnd-verdict-real {
  background: var(--real-bg) !important;
  border: 1.5px solid var(--real-border) !important;
}
.fnd-verdict-fake {
  background: var(--fake-bg) !important;
  border: 1.5px solid var(--fake-border) !important;
}
.fnd-verdict-unv {
  background: var(--unv-bg) !important;
  border: 1.5px solid var(--unv-border) !important;
}

.fnd-verdict-icon {
  font-size: 3rem;
  line-height: 1;
  display: block;
  margin-bottom: var(--space-3);
}

.fnd-verdict-label {
  font-size: clamp(1.4rem, 3vw, 2rem);
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: var(--space-2);
}

.fnd-verdict-label.real { color: var(--real-color); }
.fnd-verdict-label.fake { color: var(--fake-color); }
.fnd-verdict-label.unv  { color: var(--unv-color);  }

.fnd-verdict-sub {
  font-size: 0.88rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
}

/* ── Confidence meters ─────────────────────────────────────────────────── */

.fnd-conf-block {
  margin: var(--space-4) 0 0;
}

.fnd-conf-row {
  margin-bottom: var(--space-3);
}

.fnd-conf-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: var(--space-1);
}

.fnd-conf-label {
  font-size: 0.80rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.fnd-conf-pct {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-primary);
}

.fnd-conf-track {
  height: 8px;
  background: var(--border-subtle);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.fnd-conf-fill {
  height: 100%;
  border-radius: var(--radius-full);
  background: var(--brand-gradient);
  animation: bar-grow 0.8s var(--ease-out) forwards;
  width: 0%;
}

.fnd-conf-fill.real { background: linear-gradient(90deg, #10b981, #22c55e); }
.fnd-conf-fill.fake { background: linear-gradient(90deg, #f43f5e, #ef4444); }
.fnd-conf-fill.unv  { background: linear-gradient(90deg, #d97706, #eab308); }

@keyframes bar-grow {
  from { width: 0% !important; }
  to   { width: var(--target-width) !important; }
}

@media (prefers-reduced-motion: reduce) {
  .fnd-conf-fill { animation: none; }
}


/* ═══════════════════════════════════════════════════════════════════════════
   9. REASONING SECTION
═══════════════════════════════════════════════════════════════════════════ */

.fnd-reasoning {
  list-style: none;
  padding: 0;
  margin: 0;
}

.fnd-reasoning li {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--border-subtle);
  font-size: 0.90rem;
  color: var(--text-secondary);
  line-height: 1.6;
  animation: slide-in 0.4s var(--ease-out) both;
}

.fnd-reasoning li:last-child { border-bottom: none; }

.fnd-reasoning li::before {
  content: '›';
  color: var(--brand-primary);
  font-weight: 700;
  font-size: 1.1rem;
  flex-shrink: 0;
  line-height: 1.4;
}

@keyframes slide-in {
  from { opacity: 0; transform: translateX(-10px); }
  to   { opacity: 1; transform: translateX(0); }
}


/* ═══════════════════════════════════════════════════════════════════════════
   10. KEYWORD BADGES
═══════════════════════════════════════════════════════════════════════════ */

.fnd-kw-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-3);
}

.fnd-kw {
  background: var(--tag-bg);
  color: var(--tag-color);
  font-size: 0.78rem;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  border: 1px solid rgba(99,102,241,0.20);
  transition: transform 0.15s ease;
}

.fnd-kw:hover { transform: translateY(-1px); }


/* ═══════════════════════════════════════════════════════════════════════════
   11. SOURCE CARDS
═══════════════════════════════════════════════════════════════════════════ */

.fnd-source-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  margin-bottom: var(--space-3);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
  position: relative;
  overflow: hidden;
}

.fnd-source-card:hover {
  box-shadow: var(--shadow-md);
}

.fnd-source-card::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 4px;
}

.fnd-source-card.supporting::before   { background: var(--real-color); }
.fnd-source-card.contradicting::before { background: var(--fake-color); }
.fnd-source-card.neutral::before      { background: var(--neu-color); }

.fnd-source-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-2);
  flex-wrap: wrap;
  gap: var(--space-2);
}

.fnd-source-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}

.fnd-source-badges {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  flex-wrap: wrap;
}

.fnd-badge {
  font-size: 0.70rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.fnd-badge-sup  { background: var(--real-bg);  color: var(--real-color);  border: 1px solid var(--real-border);  }
.fnd-badge-con  { background: var(--fake-bg);  color: var(--fake-color);  border: 1px solid var(--fake-border);  }
.fnd-badge-neu  { background: var(--unv-bg);   color: var(--unv-color);   border: 1px solid var(--unv-border);   }
.fnd-badge-fc   { background: #eff6ff; color: #3b82f6; border: 1px solid #bfdbfe; }
.fnd-badge-dark { background: #1e293b; color: #94a3b8; border: 1px solid #334155; }

.fnd-trust-score {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  font-weight: 600;
}

.fnd-trust-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.trust-high  .fnd-trust-dot { background: var(--real-color); }
.trust-mid   .fnd-trust-dot { background: var(--unv-color);  }
.trust-low   .fnd-trust-dot { background: var(--fake-color); }

.trust-high { color: var(--real-color); }
.trust-mid  { color: var(--unv-color);  }
.trust-low  { color: var(--fake-color); }

.fnd-source-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--space-1);
  line-height: 1.4;
}

.fnd-source-snippet {
  font-size: 0.80rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: var(--space-2);
}

.fnd-source-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.fnd-source-link {
  font-size: 0.75rem;
  color: var(--brand-primary);
  text-decoration: none;
  font-weight: 500;
  word-break: break-all;
  transition: color 0.15s ease;
}

.fnd-source-link:hover { color: var(--brand-secondary); text-decoration: underline; }

.fnd-source-date {
  font-size: 0.72rem;
  color: var(--text-muted);
}


/* ═══════════════════════════════════════════════════════════════════════════
   12. TABS
═══════════════════════════════════════════════════════════════════════════ */

.tabs button.selected,
.tab-nav button.selected {
  color: var(--brand-primary) !important;
  border-bottom: 2px solid var(--brand-primary) !important;
  font-weight: 600 !important;
}

.tabs button,
.tab-nav button {
  color: var(--text-muted) !important;
  font-family: var(--font-sans) !important;
  font-size: 0.88rem !important;
  padding: 10px 16px !important;
  background: transparent !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  transition: color 0.2s ease, border-color 0.2s ease !important;
}

.tabs button:hover,
.tab-nav button:hover {
  color: var(--text-primary) !important;
}

.tabitem {
  padding: var(--space-4) 0 !important;
}


/* ═══════════════════════════════════════════════════════════════════════════
   13. HISTORY & STATS
═══════════════════════════════════════════════════════════════════════════ */

.hist-empty, .stats-empty {
  text-align: center;
  padding: var(--space-12) var(--space-4);
  color: var(--text-muted);
}

.hist-empty-icon { font-size: 2.5rem; display: block; margin-bottom: var(--space-3); }
.hist-empty p    { font-size: 0.9rem; margin: 0 0 var(--space-2); }
.hist-sub        { font-size: 0.78rem; color: var(--text-muted); }

.hist-row {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--border-subtle);
  transition: background 0.15s ease;
}

.hist-row:hover   { background: var(--bg-subtle); border-radius: var(--radius-md); }
.hist-row:last-child { border-bottom: none; }

.hist-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
  width: 28px;
  text-align: center;
}

.hist-info    { flex: 1; min-width: 0; }
.hist-query   { font-size: 0.875rem; color: var(--text-primary); font-weight: 500;
                white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hist-meta    { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: 4px; }
.hist-verdict { font-size: 0.70rem; font-weight: 700; padding: 1px 7px;
                border-radius: var(--radius-full); }
.hist-real    { background: var(--real-bg); color: var(--real-color); }
.hist-fake    { background: var(--fake-bg); color: var(--fake-color); }
.hist-unv     { background: var(--unv-bg);  color: var(--unv-color);  }
.hist-conf, .hist-time, .hist-src {
  font-size: 0.72rem; color: var(--text-muted);
}

/* Stats grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.stat-card {
  background: var(--stat-bg);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--space-4) var(--space-3);
  text-align: center;
  backdrop-filter: var(--glass-blur);
}

.stat-num { font-size: 1.6rem; font-weight: 800; color: var(--brand-primary); }
.stat-lbl { font-size: 0.72rem; color: var(--text-muted); margin-top: 2px; font-weight: 500; }

.stat-bars    { margin-top: var(--space-4); }
.stat-bar-row { display: flex; align-items: center; gap: var(--space-3);
                margin-bottom: var(--space-3); }
.stat-bar-label { font-size: 0.80rem; font-weight: 600; color: var(--text-secondary);
                  width: 110px; flex-shrink: 0; }
.stat-bar-track { flex: 1; height: 10px; background: var(--border-subtle);
                  border-radius: var(--radius-full); overflow: hidden; }
.stat-bar-fill  { height: 100%; border-radius: var(--radius-full);
                  transition: width 0.8s var(--ease-out); }
.stat-bar-pct   { font-size: 0.80rem; font-weight: 700; color: var(--text-primary);
                  width: 36px; text-align: right; }


/* ═══════════════════════════════════════════════════════════════════════════
   14. LOADING OVERLAY
═══════════════════════════════════════════════════════════════════════════ */

.fnd-loading {
  display: none;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: var(--space-12) var(--space-8);
  text-align: center;
}

.fnd-loading.active { display: flex; }

.fnd-spinner {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, transparent, var(--brand-primary));
  animation: spin 1s linear infinite;
  position: relative;
}

.fnd-spinner::after {
  content: '';
  position: absolute;
  inset: 5px;
  border-radius: 50%;
  background: var(--bg-page);
}

@keyframes spin { to { transform: rotate(360deg); } }

.fnd-loading-label {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.fnd-loading-sub {
  font-size: 0.82rem;
  color: var(--text-muted);
}

/* Progress steps */
.fnd-steps {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  text-align: left;
  min-width: 240px;
}

.fnd-step {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.82rem;
  color: var(--text-muted);
  transition: color 0.3s ease;
}

.fnd-step.done  { color: var(--real-color); }
.fnd-step.active { color: var(--brand-primary); font-weight: 600; }

.fnd-step-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

.fnd-step.active .fnd-step-dot {
  animation: pulse-dot 1s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.5; transform: scale(1.4); }
}


/* ═══════════════════════════════════════════════════════════════════════════
   15. EXPORT / ACTION ROW
═══════════════════════════════════════════════════════════════════════════ */

.fnd-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-4);
}

.fnd-action-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 8px 14px;
  background: var(--glass-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  backdrop-filter: var(--glass-blur);
  transition: all 0.2s ease;
  text-decoration: none;
}

.fnd-action-btn:hover {
  background: var(--brand-primary);
  color: white;
  border-color: var(--brand-primary);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99,102,241,0.35);
}


/* ═══════════════════════════════════════════════════════════════════════════
   16. URL MODE BANNER
═══════════════════════════════════════════════════════════════════════════ */

.fnd-url-banner {
  background: linear-gradient(90deg,
    rgba(6,182,212,0.12) 0%, rgba(99,102,241,0.12) 100%);
  border: 1px solid rgba(6,182,212,0.30);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  font-size: 0.82rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.fnd-url-domain {
  font-weight: 700;
  color: var(--brand-accent);
}


/* ═══════════════════════════════════════════════════════════════════════════
   17. FOOTER / TEAM SECTION
═══════════════════════════════════════════════════════════════════════════ */

.fnd-footer {
  background: var(--bg-hero);
  border-radius: var(--radius-xl);
  padding: var(--space-12) var(--space-8);
  margin-top: var(--space-8);
  text-align: center;
  position: relative;
  overflow: hidden;
}

.fnd-footer::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 50% 60% at 10% 80%, rgba(99,102,241,0.25) 0%, transparent 70%),
    radial-gradient(ellipse 40% 40% at 90% 20%, rgba(6,182,212,0.20) 0%, transparent 70%);
  pointer-events: none;
}

.fnd-footer h2 {
  font-size: clamp(1.2rem, 3vw, 1.8rem);
  font-weight: 700;
  color: #ffffff;
  margin-bottom: var(--space-2);
  position: relative;
}

.fnd-footer-sub {
  font-size: 0.88rem;
  color: rgba(255,255,255,0.60);
  margin-bottom: var(--space-8);
  position: relative;
}

.fnd-team-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-8);
  position: relative;
}

.fnd-team-card {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: var(--radius-lg);
  padding: var(--space-6) var(--space-4);
  backdrop-filter: blur(12px);
  transition: all 0.25s var(--ease-out);
  text-align: center;
}

.fnd-team-card:hover {
  background: rgba(255,255,255,0.14);
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.30);
}

.fnd-avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--brand-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: 700;
  color: white;
  margin: 0 auto var(--space-3);
  box-shadow: 0 4px 16px rgba(99,102,241,0.40);
}

.fnd-team-name {
  font-size: 0.90rem;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 4px;
}

.fnd-team-role {
  font-size: 0.72rem;
  color: rgba(255,255,255,0.55);
  line-height: 1.4;
  margin-bottom: var(--space-2);
}

.fnd-team-badge {
  display: inline-block;
  background: rgba(99,102,241,0.30);
  border: 1px solid rgba(99,102,241,0.50);
  color: #c7d2fe;
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.fnd-footer-bottom {
  border-top: 1px solid rgba(255,255,255,0.10);
  padding-top: var(--space-6);
  position: relative;
}

.fnd-footer-info {
  font-size: 0.78rem;
  color: rgba(255,255,255,0.50);
  line-height: 1.8;
}

.fnd-footer-logo {
  font-size: 1.4rem;
  font-weight: 900;
  background: var(--brand-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: var(--space-4);
  display: block;
}

.fnd-footer-pills {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-2);
  margin: var(--space-4) 0;
}

.fnd-footer-pill {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  color: rgba(255,255,255,0.65);
  font-size: 0.72rem;
  padding: 3px 10px;
  border-radius: var(--radius-full);
}


/* ═══════════════════════════════════════════════════════════════════════════
   18. DISCLAIMER / ERROR / EMPTY STATES
═══════════════════════════════════════════════════════════════════════════ */

.fnd-disclaimer {
  background: var(--unv-bg);
  border: 1px solid var(--unv-border);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  font-size: 0.78rem;
  color: var(--text-secondary);
  margin-top: var(--space-4);
}

.fnd-error {
  background: var(--fake-bg);
  border: 1px solid var(--fake-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  color: var(--fake-color);
  font-size: 0.88rem;
  font-weight: 500;
}

.fnd-empty {
  text-align: center;
  padding: var(--space-12) var(--space-4);
  color: var(--text-muted);
}

.fnd-empty-icon { font-size: 3rem; display: block; margin-bottom: var(--space-4); }
.fnd-empty h3   { font-size: 1.1rem; color: var(--text-secondary); font-weight: 600; margin-bottom: var(--space-2); }
.fnd-empty p    { font-size: 0.85rem; max-width: 380px; margin: 0 auto; }


/* ═══════════════════════════════════════════════════════════════════════════
   19. RESPONSIVE
═══════════════════════════════════════════════════════════════════════════ */

@media (max-width: 768px) {
  .fnd-hero { padding: var(--space-8) var(--space-4); }
  .fnd-card { padding: var(--space-4); }
  .fnd-team-grid { grid-template-columns: repeat(2, 1fr); }
  .fnd-footer { padding: var(--space-8) var(--space-4); }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .fnd-actions { flex-direction: column; }
}

@media (max-width: 480px) {
  .fnd-team-grid { grid-template-columns: 1fr 1fr; }
  .fnd-hero h1 { font-size: 1.5rem; }
  .fnd-verdict-label { font-size: 1.3rem; }
  .stat-bar-label { width: 80px; }
  .fnd-source-header { flex-direction: column; align-items: flex-start; }
}


/* ═══════════════════════════════════════════════════════════════════════════
   20. GRADIO OVERRIDES (version-agnostic)
═══════════════════════════════════════════════════════════════════════════ */

/* Remove Gradio default white bg */
.contain,
.gap,
.flex {
  background: transparent !important;
}

/* Accordion */
.gr-accordion > div:first-child {
  background: var(--glass-bg) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-primary) !important;
}

/* Labels */
label span,
.label-wrap span {
  color: var(--text-primary) !important;
  font-family: var(--font-sans) !important;
}

/* HTML component wrapper */
.prose { max-width: none !important; }

/* Info text */
.info { color: var(--text-muted) !important; font-size: 0.78rem !important; }

/* File download */
.file-preview {
  background: var(--bg-card) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius-md) !important;
}
"""

# ── Theme toggle JavaScript ────────────────────────────────────────────────────

THEME_JS = """
function initTheme() {
  // Read saved theme or detect system preference
  const saved  = localStorage.getItem('fnd-theme');
  const system = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  const theme  = saved || system;
  document.documentElement.setAttribute('data-theme', theme);
  return theme;
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  const next    = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('fnd-theme', next);
  const btn = document.getElementById('fnd-theme-btn');
  if (btn) btn.textContent = next === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode';
  return next;
}

// Init on load
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  // Watch system preference changes
  window.matchMedia('(prefers-color-scheme: dark)')
    .addEventListener('change', e => {
      if (!localStorage.getItem('fnd-theme')) {
        document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
      }
    });
});
"""
