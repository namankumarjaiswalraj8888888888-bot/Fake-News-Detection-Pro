"""
app.py
======
AI Fake News Detection & Live Verification System — Version 3
Gradio-powered web application.

Changes from V2
---------------
- Added URL input mode (paste any news article URL)
- Confidence breakdown panel: ML Confidence, Evidence Confidence, Overall
- Source Trust Score displayed alongside source names
- Primary Claim extracted and shown
- Publication dates shown for referenced articles
- Model name shown in ML panel
- All existing UI, CSS, sample news, and credits preserved

Fixed for HuggingFace Spaces deployment:
- Removed broken Jinja2 LRUCache monkey-patch (causes TypeError on HF)
- Fixed demo.launch() — share=False, correct HF Spaces binding
- Removed unnecessary socket/port-check code

Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar & Parmeshwar
"""

from __future__ import annotations

import logging
import os

import gradio as gr
from fact_checker import check_news

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── Sample News ───────────────────────────────────────────────────────────────

SAMPLE_NEWS: dict[str, str] = {
    "✅ Real: ISRO Mission": (
        "ISRO successfully tests reusable launch vehicle for future space missions. "
        "The Indian Space Research Organisation conducted the test from the Satish "
        "Dhawan Space Centre, Sriharikota. The mission paves the way for cost-effective "
        "launches in the coming decade."
    ),
    "❌ Fake: Microchip Vaccine": (
        "SHOCKING: Bill Gates admits he put microchips in COVID-19 vaccines to track "
        "the population worldwide! Secret documents LEAKED from WHO confirm global "
        "surveillance plan. Share before this is DELETED by mainstream media!"
    ),
    "⚠ Ambiguous: Cure Claim": (
        "Scientists say drinking turmeric water every morning for 30 days completely "
        "reverses diabetes and cancer. This ancient remedy was suppressed by the pharma "
        "lobby for decades. 100% guaranteed results with no side effects."
    ),
    "✅ Real: RBI Policy": (
        "Reserve Bank of India raises repo rate by 25 basis points to 6.75 percent "
        "to control inflation. The Monetary Policy Committee voted 5-1 in favor of "
        "the rate hike, according to an official RBI press release."
    ),
    "❌ Fake: WhatsApp Hoax": (
        "URGENT: WhatsApp will start charging Rs 10 per message from next Monday! "
        "Forward this to all your contacts immediately to activate your free lifetime "
        "subscription before the deadline. Government has approved this new policy!"
    ),
}

# ── CSS Styling ───────────────────────────────────────────────────────────────

CUSTOM_CSS = """
/* ── Google Fonts Import ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── CSS Variables — Light Mode ── */
:root {
    --brand-blue: #2563eb;
    --brand-indigo: #4f46e5;
    --brand-purple: #7c3aed;
    --brand-cyan: #0891b2;
    --real-green: #059669;
    --real-green-light: rgba(5,150,105,0.12);
    --fake-red: #dc2626;
    --fake-red-light: rgba(220,38,38,0.1);
    --unverified-amber: #d97706;
    --unverified-amber-light: rgba(217,119,6,0.1);

    /* Layout */
    --bg-base: #f0f4ff;
    --bg-surface: rgba(255,255,255,0.72);
    --bg-surface-hover: rgba(255,255,255,0.9);
    --card-bg: rgba(255,255,255,0.75);
    --card-border: rgba(148,163,184,0.25);
    --card-blur: blur(16px);
    --input-bg: rgba(255,255,255,0.85);
    --input-text: #0f172a;
    --input-border: rgba(148,163,184,0.35);

    /* Typography */
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-muted: #94a3b8;

    /* Geometry */
    --radius-sm: 10px;
    --radius: 16px;
    --radius-lg: 20px;
    --radius-xl: 28px;

    /* Shadows */
    --shadow-sm: 0 2px 12px rgba(37,99,235,0.06);
    --shadow: 0 8px 32px rgba(37,99,235,0.10);
    --shadow-hover: 0 16px 48px rgba(37,99,235,0.16);
    --shadow-card: 0 4px 24px rgba(15,23,42,0.06);
    --shadow-glow-blue: 0 0 32px rgba(37,99,235,0.25);
}

/* ── Dark Mode Variables ── */
.dark,
.dark .gradio-container,
@media (prefers-color-scheme: dark) { :root {
    --bg-base: #060d1f;
    --bg-surface: rgba(15,23,42,0.80);
    --bg-surface-hover: rgba(30,41,59,0.90);
    --card-bg: rgba(15,23,42,0.75);
    --card-border: rgba(100,116,139,0.20);
    --input-bg: rgba(15,23,42,0.85);
    --input-text: #e2e8f0;
    --input-border: rgba(100,116,139,0.30);
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --shadow: 0 8px 32px rgba(0,0,0,0.40);
    --shadow-hover: 0 16px 48px rgba(0,0,0,0.50);
    --shadow-card: 0 4px 24px rgba(0,0,0,0.30);
}}

.dark {
    --bg-base: #060d1f !important;
    --bg-surface: rgba(15,23,42,0.80) !important;
    --bg-surface-hover: rgba(30,41,59,0.90) !important;
    --card-bg: rgba(15,23,42,0.75) !important;
    --card-border: rgba(100,116,139,0.20) !important;
    --input-bg: rgba(15,23,42,0.85) !important;
    --input-text: #e2e8f0 !important;
    --input-border: rgba(100,116,139,0.30) !important;
    --text-primary: #f1f5f9 !important;
    --text-secondary: #94a3b8 !important;
    --text-muted: #64748b !important;
}

/* ── Base Reset ── */
*, *::before, *::after { box-sizing: border-box; }

body, .gradio-container {
    background: var(--bg-base) !important;
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif !important;
    color: var(--text-primary) !important;
    -webkit-font-smoothing: antialiased;
}

/* Animated background mesh */
body::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 80% 60% at 20% 10%, rgba(37,99,235,0.08) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 80% 80%, rgba(124,58,237,0.07) 0%, transparent 60%),
        radial-gradient(ellipse 70% 40% at 60% 30%, rgba(8,145,178,0.05) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
}

/* ── Typography Inheritance ── */
p, span, li, label, div, td, th, h1, h2, h3, h4, h5, h6 { color: inherit; }

/* ── Gradio overrides ── */
.gradio-container label,
.gradio-container .label-wrap span,
.gradio-container .prose,
.gradio-container span.svelte-1ipelgc { color: var(--text-primary) !important; }

.gradio-container input,
.gradio-container textarea,
.gradio-container select {
    background: var(--input-bg) !important;
    color: var(--input-text) !important;
    border-color: var(--input-border) !important;
}

.gradio-container .accordion-header,
.gradio-container details > summary {
    color: var(--text-primary) !important;
    background: var(--card-bg) !important;
}

.gradio-container .radio-group label,
.gradio-container .checkbox-group label { color: var(--text-primary) !important; }

textarea, input[type="text"] {
    background: var(--input-bg) !important;
    color: var(--input-text) !important;
}

/* ── Glassmorphism Card ── */
.result-card {
    background: var(--card-bg);
    backdrop-filter: var(--card-blur);
    -webkit-backdrop-filter: var(--card-blur);
    border: 1px solid var(--card-border);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow-card);
    transition: transform 0.22s cubic-bezier(0.4,0,0.2,1),
                box-shadow 0.22s cubic-bezier(0.4,0,0.2,1);
    position: relative;
    overflow: hidden;
}
.result-card::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
    background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, transparent 60%);
    pointer-events: none;
}
.result-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-hover);
}

/* ── Verdict Accent Borders ── */
.verdict-real    { border-left: 4px solid var(--real-green) !important; background: linear-gradient(135deg, var(--card-bg), rgba(5,150,105,0.04)) !important; }
.verdict-fake    { border-left: 4px solid var(--fake-red) !important; background: linear-gradient(135deg, var(--card-bg), rgba(220,38,38,0.04)) !important; }
.verdict-unverified { border-left: 4px solid var(--unverified-amber) !important; background: linear-gradient(135deg, var(--card-bg), rgba(217,119,6,0.04)) !important; }

/* ── Verdict Labels ── */
.verdict-label-real  { color: var(--real-green) !important; font-size: 2rem !important; font-weight: 900 !important; letter-spacing: -0.5px; }
.verdict-label-fake  { color: var(--fake-red) !important; font-size: 2rem !important; font-weight: 900 !important; letter-spacing: -0.5px; }
.verdict-label-unverified { color: var(--unverified-amber) !important; font-size: 2rem !important; font-weight: 900 !important; letter-spacing: -0.5px; }

/* ── Pills / Badges ── */
.source-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.2rem;
    background: rgba(37,99,235,0.08);
    color: var(--brand-blue);
    border: 1px solid rgba(37,99,235,0.2);
    border-radius: 999px;
    padding: 0.22rem 0.7rem;
    font-size: 0.73rem;
    font-weight: 600;
    margin: 0.15rem;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.source-pill:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(37,99,235,0.15); }
.source-pill.real { background: rgba(5,150,105,0.09); color: var(--real-green); border-color: rgba(5,150,105,0.22); }
.source-pill.fake { background: rgba(220,38,38,0.09); color: var(--fake-red); border-color: rgba(220,38,38,0.22); }

/* ── Confidence Bars ── */
.conf-bar-wrap {
    background: rgba(148,163,184,0.2);
    border-radius: 999px;
    height: 10px;
    overflow: hidden;
    margin: 0.5rem 0;
    position: relative;
}
.conf-bar {
    height: 100%;
    border-radius: 999px;
    transition: width 1s cubic-bezier(0.4,0,0.2,1);
    position: relative;
}
.conf-bar::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 50%;
    background: rgba(255,255,255,0.25);
    border-radius: 999px;
}
.conf-bar.real { background: linear-gradient(90deg, #059669, #10b981, #34d399); }
.conf-bar.fake { background: linear-gradient(90deg, #dc2626, #ef4444, #f87171); }
.conf-bar.unverified { background: linear-gradient(90deg, #d97706, #f59e0b, #fbbf24); }

/* ── Mini Bars ── */
.mini-bar-wrap {
    background: rgba(148,163,184,0.18);
    border-radius: 999px;
    height: 7px;
    overflow: hidden;
    margin: 0.25rem 0 0.6rem;
    width: 100%;
}
.mini-bar {
    height: 100%;
    border-radius: 999px;
    transition: width 1.1s cubic-bezier(0.4,0,0.2,1);
}
.mini-bar.ml-color { background: linear-gradient(90deg, #4338ca, #6366f1, #818cf8); }
.mini-bar.ev-color { background: linear-gradient(90deg, #0891b2, #06b6d4, #67e8f9); }
.mini-bar.ov-color { background: linear-gradient(90deg, #059669, #10b981, #34d399); }
.mini-bar.ov-fake  { background: linear-gradient(90deg, #dc2626, #ef4444, #f87171); }
.mini-bar.ov-unv   { background: linear-gradient(90deg, #d97706, #f59e0b, #fbbf24); }

/* ── Header ── */
.app-header {
    background: linear-gradient(135deg, #1a3a8f 0%, #2563eb 30%, #4f46e5 65%, #7c3aed 100%);
    border-radius: var(--radius-xl);
    padding: 3rem 2rem 2.5rem;
    text-align: center;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(37,99,235,0.35);
}
.app-header::before {
    content: '';
    position: absolute;
    inset: 0;
    background:
        radial-gradient(circle at 20% 50%, rgba(255,255,255,0.08) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(255,255,255,0.06) 0%, transparent 40%);
    pointer-events: none;
}
.app-header::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
}
.header-icon {
    font-size: 2.8rem;
    margin-bottom: 0.5rem;
    display: block;
    animation: pulse-icon 3s ease-in-out infinite;
}
@keyframes pulse-icon {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.06); }
}
.app-header h1 {
    color: #ffffff !important;
    font-size: 2.1rem !important;
    font-weight: 900 !important;
    margin: 0 0 0.5rem !important;
    letter-spacing: -1px;
    position: relative;
    text-shadow: 0 2px 20px rgba(0,0,0,0.2);
}
.app-header p {
    color: rgba(255,255,255,0.82) !important;
    font-size: 0.95rem !important;
    margin: 0 !important;
    position: relative;
    font-weight: 500;
}

/* ── Header Badges ── */
.header-badges {
    display: flex;
    gap: 0.45rem;
    justify-content: center;
    margin-top: 1.25rem;
    flex-wrap: wrap;
}
.badge {
    background: rgba(255,255,255,0.15);
    color: #fff;
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 999px;
    padding: 0.28rem 0.8rem;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.3px;
    backdrop-filter: blur(8px);
    transition: background 0.2s ease, transform 0.2s ease;
}
.badge:hover {
    background: rgba(255,255,255,0.25);
    transform: translateY(-1px);
}

/* ── Version Chip ── */
.version-chip {
    display: inline-block;
    background: rgba(255,255,255,0.18);
    color: #fff;
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 999px;
    padding: 0.18rem 0.65rem;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}

/* ── Buttons ── */
.btn-primary {
    background: linear-gradient(135deg, #2563eb, #4f46e5) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.8rem 2rem !important;
    cursor: pointer !important;
    transition: all 0.22s cubic-bezier(0.4,0,0.2,1) !important;
    box-shadow: 0 4px 20px rgba(37,99,235,0.4) !important;
    letter-spacing: -0.2px;
}
.btn-primary:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 12px 35px rgba(37,99,235,0.5) !important;
    background: linear-gradient(135deg, #1d4ed8, #4338ca) !important;
}
.btn-primary:active { transform: translateY(-1px) !important; }

.btn-secondary {
    background: var(--bg-surface) !important;
    color: var(--text-secondary) !important;
    border: 1.5px solid var(--card-border) !important;
    border-radius: var(--radius) !important;
    font-weight: 600 !important;
    backdrop-filter: blur(8px) !important;
    transition: all 0.2s ease !important;
}
.btn-secondary:hover {
    border-color: var(--brand-blue) !important;
    color: var(--brand-blue) !important;
    transform: translateY(-1px) !important;
}

/* ── Input Textarea ── */
.input-section textarea {
    border: 1.5px solid var(--input-border) !important;
    border-radius: var(--radius) !important;
    font-size: 0.93rem !important;
    transition: border-color 0.22s ease, box-shadow 0.22s ease !important;
    background: var(--input-bg) !important;
    color: var(--input-text) !important;
    backdrop-filter: blur(8px) !important;
}
.input-section textarea:focus {
    border-color: var(--brand-blue) !important;
    box-shadow: 0 0 0 4px rgba(37,99,235,0.12) !important;
}

/* ── Section Labels ── */
.section-label {
    font-size: 0.68rem !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.2px !important;
    color: var(--text-muted) !important;
    margin-bottom: 0.6rem !important;
}

/* ── Sample Buttons ── */
.sample-btn {
    background: var(--bg-surface) !important;
    border: 1.5px solid var(--card-border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-secondary) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    text-align: left !important;
    backdrop-filter: blur(8px) !important;
}
.sample-btn:hover {
    border-color: var(--brand-blue) !important;
    color: var(--brand-blue) !important;
    background: rgba(37,99,235,0.06) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 16px rgba(37,99,235,0.12) !important;
}

/* ── Article Row ── */
.article-row {
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--card-border);
    transition: background 0.18s ease;
    border-radius: 8px;
    padding-left: 0.5rem;
    padding-right: 0.5rem;
}
.article-row:last-child { border-bottom: none; }
.article-row:hover { background: rgba(37,99,235,0.04); }

/* ── Evidence Row Classification Colors ── */
.class-supporting { color: var(--real-green); }
.class-contradicting { color: var(--fake-red); }
.class-neutral { color: var(--text-muted); }

/* ── How It Works Steps ── */
.step-item {
    display: flex;
    align-items: flex-start;
    gap: 0.65rem;
    padding: 0.45rem 0;
    font-size: 0.82rem;
    color: var(--text-secondary);
    line-height: 1.6;
}
.step-num {
    flex-shrink: 0;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2563eb, #4f46e5);
    color: #fff;
    font-size: 0.68rem;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 1px;
}

/* ── Team Card Grid ── */
.team-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin: 1.2rem 0;
}
.team-card {
    background: var(--bg-surface);
    backdrop-filter: blur(12px);
    border: 1px solid var(--card-border);
    border-radius: var(--radius);
    padding: 1.25rem 1rem;
    text-align: center;
    transition: transform 0.22s ease, box-shadow 0.22s ease;
    position: relative;
    overflow: hidden;
}
.team-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #2563eb, #7c3aed);
}
.team-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(37,99,235,0.14);
}
.team-avatar {
    width: 52px;
    height: 52px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    margin: 0 auto 0.75rem;
    box-shadow: 0 4px 14px rgba(37,99,235,0.25);
}
.team-name {
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.2rem;
}
.team-role {
    font-size: 0.73rem;
    color: var(--text-muted);
    line-height: 1.45;
}
.team-role-badge {
    display: inline-block;
    margin-top: 0.5rem;
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    font-size: 0.67rem;
    font-weight: 700;
    background: rgba(37,99,235,0.1);
    color: var(--brand-blue);
    letter-spacing: 0.3px;
}

/* ── Footer ── */
.app-footer {
    background: var(--card-bg);
    backdrop-filter: var(--card-blur);
    border: 1px solid var(--card-border);
    border-radius: var(--radius-xl);
    padding: 2rem 2.5rem;
    text-align: center;
    margin-top: 1.5rem;
    position: relative;
    overflow: hidden;
}
.app-footer::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #2563eb, #4f46e5, #7c3aed, #0891b2);
}
.footer-inst {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0.5rem 0 0.2rem;
}
.footer-sub {
    font-size: 0.8rem;
    color: var(--text-muted);
}
.footer-copyright {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 0.25rem;
}

/* ── Copy Result Box ── */
.copy-result-box {
    background: var(--input-bg) !important;
    border: 1.5px solid var(--input-border) !important;
    border-radius: var(--radius) !important;
    color: var(--input-text) !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    font-size: 0.82rem !important;
}

/* ── Disclaimer Card ── */
.disclaimer-card {
    background: rgba(37,99,235,0.05);
    border: 1px solid rgba(37,99,235,0.15);
    border-radius: var(--radius);
    padding: 0.9rem 1.2rem;
    margin-top: 0.5rem;
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
}

/* ── Animations ── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}
@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-16px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}

.fade-in { animation: fadeInUp 0.45s cubic-bezier(0.4,0,0.2,1) forwards; }
.fade-in > * { animation: fadeInUp 0.45s cubic-bezier(0.4,0,0.2,1) both; }
.fade-in > *:nth-child(2) { animation-delay: 0.07s; }
.fade-in > *:nth-child(3) { animation-delay: 0.14s; }
.fade-in > *:nth-child(4) { animation-delay: 0.21s; }
.fade-in > *:nth-child(5) { animation-delay: 0.28s; }
.fade-in > *:nth-child(6) { animation-delay: 0.35s; }
.fade-in > *:nth-child(7) { animation-delay: 0.42s; }

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation: none !important; transition: none !important; }
}

/* ── Mobile Responsiveness ── */
@media (max-width: 768px) {
    .app-header { padding: 2rem 1rem 1.75rem; border-radius: var(--radius-lg); }
    .app-header h1 { font-size: 1.45rem !important; letter-spacing: -0.5px; }
    .app-header p { font-size: 0.85rem !important; }
    .header-badges { gap: 0.35rem; }
    .badge { font-size: 0.68rem; padding: 0.22rem 0.6rem; }
    .result-card { padding: 1.1rem; border-radius: var(--radius-sm); }
    .verdict-label-real, .verdict-label-fake, .verdict-label-unverified { font-size: 1.5rem !important; }
    .team-grid { grid-template-columns: repeat(2, 1fr); gap: 0.75rem; }
    .team-card { padding: 1rem 0.75rem; }
    .app-footer { padding: 1.5rem 1.25rem; border-radius: var(--radius-lg); }
    .btn-primary { font-size: 0.93rem !important; }
}

@media (max-width: 480px) {
    .team-grid { grid-template-columns: 1fr 1fr; }
    .header-badges { gap: 0.3rem; }
    .badge { font-size: 0.65rem; }
}
"""

# ── HTML Builders ──────────────────────────────────────────────────────────────

def _verdict_icon(verdict: str) -> str:
    return {"REAL": "✅", "FAKE": "❌", "UNVERIFIED": "⚠️"}.get(verdict, "❓")


def _verdict_label(verdict: str) -> str:
    return {"REAL": "REAL NEWS", "FAKE": "FAKE NEWS", "UNVERIFIED": "UNVERIFIED"}.get(
        verdict, verdict
    )


def build_result_html(result: dict) -> str:
    if result.get("error") and not result.get("verdict"):
        return (
            '<div class="result-card verdict-unverified fade-in">'
            '<p style="color:#d97706;font-weight:700;font-size:1.1rem">⚠️ Error</p>'
            f'<p style="color:var(--text-secondary)">{result["error"]}</p>'
            "</div>"
        )

    verdict       = result.get("verdict",            "UNVERIFIED")
    overall_conf  = result.get("overall_confidence", result.get("confidence", 0))
    ml_conf_pct   = result.get("ml_confidence",      50)
    ev_conf_pct   = result.get("evidence_confidence", 0)
    icon          = _verdict_icon(verdict)
    label         = _verdict_label(verdict)
    reasoning     = result.get("reasoning",          [])
    ml            = result.get("ml_result",          {})
    ling          = result.get("linguistic_signals", {})
    ev            = result.get("evidence_result",    {})
    elapsed       = result.get("elapsed_seconds",    0)
    primary_claim = result.get("primary_claim",      "")
    url_meta      = result.get("url_meta",           {})
    vclass        = verdict.lower()

    ov_bar_class = (
        "ov-color" if verdict == "REAL" else
        "ov-fake"  if verdict == "FAKE" else
        "ov-unv"
    )
    overall_bar = f"""
    <div class="conf-bar-wrap">
        <div class="conf-bar {vclass}" style="width:{overall_conf}%"></div>
    </div>
    <p style="font-size:0.8rem;color:var(--text-secondary);margin:0.2rem 0 0">
        Overall Confidence: <strong>{overall_conf}%</strong>
    </p>"""

    reasoning_html = "".join(
        f'<li style="margin-bottom:0.4rem;color:var(--text-secondary);font-size:0.9rem">'
        f'<span style="color:var(--brand-blue)">▸</span> {r}</li>'
        for r in reasoning
    )

    claim_html = ""
    if primary_claim:
        claim_html = f"""
    <div class="result-card" style="margin-bottom:0.75rem;background:rgba(26,86,219,0.04);
         border-color:rgba(26,86,219,0.2)">
        <p class="section-label">🎯 Extracted Primary Claim</p>
        <p style="font-size:0.88rem;color:var(--text-primary);margin:0;font-style:italic">
            "{primary_claim[:200]}"
        </p>
    </div>"""

    url_html = ""
    if url_meta.get("is_url"):
        url_html = f"""
    <div class="result-card" style="margin-bottom:0.75rem">
        <p class="section-label">🔗 Source Article</p>
        <p style="font-size:0.85rem;font-weight:600;color:var(--text-primary);margin:0">
            {url_meta.get('article_title','') or 'Article'}</p>
        <p style="font-size:0.75rem;color:var(--text-secondary);margin:0.2rem 0 0">
            {url_meta.get('domain','')}
            {' · ' + url_meta.get('article_date','') if url_meta.get('article_date') else ''}
        </p>
    </div>"""

    conf_breakdown = f"""
    <div class="result-card" style="margin-top:1rem">
        <p class="section-label">📊 Confidence Breakdown</p>
        <div style="display:grid;gap:0.75rem">
            <div>
                <div style="display:flex;justify-content:space-between;font-size:0.82rem">
                    <span style="color:var(--text-secondary)">🤖 ML Confidence</span>
                    <strong style="color:#4338ca">{ml_conf_pct}%</strong>
                </div>
                <div class="mini-bar-wrap">
                    <div class="mini-bar ml-color" style="width:{ml_conf_pct}%"></div>
                </div>
            </div>
            <div>
                <div style="display:flex;justify-content:space-between;font-size:0.82rem">
                    <span style="color:var(--text-secondary)">🌐 Evidence Confidence</span>
                    <strong style="color:#0891b2">{ev_conf_pct}%</strong>
                </div>
                <div class="mini-bar-wrap">
                    <div class="mini-bar ev-color" style="width:{ev_conf_pct}%"></div>
                </div>
            </div>
            <div>
                <div style="display:flex;justify-content:space-between;font-size:0.82rem">
                    <span style="color:var(--text-secondary)">⚖️ Overall Confidence</span>
                    <strong>{overall_conf}%</strong>
                </div>
                <div class="mini-bar-wrap">
                    <div class="mini-bar {ov_bar_class}" style="width:{overall_conf}%"></div>
                </div>
            </div>
        </div>
    </div>"""

    prob_real  = int(ml.get("prob_real", 0.5) * 100)
    prob_fake  = int(ml.get("prob_fake", 0.5) * 100)
    model_name = ml.get("model_name", "ML Model")
    ml_html = f"""
    <div class="result-card" style="margin-top:1rem">
        <p class="section-label">🤖 ML Model Analysis</p>
        <p style="font-size:0.75rem;color:var(--text-secondary);margin:0 0 0.5rem">
            Model: <strong style="color:var(--brand-blue)">{model_name}</strong>
        </p>
        <div style="display:flex;gap:1.5rem;flex-wrap:wrap">
            <div>
                <p style="font-size:0.8rem;color:var(--text-secondary);margin:0">ML Prediction</p>
                <p style="font-weight:700;color:{'var(--real-green)' if ml.get('label')=='REAL' else 'var(--fake-red)'};margin:0;font-size:1rem">
                    {_verdict_icon(ml.get('label','UNVERIFIED'))} {ml.get('label','—')}
                </p>
            </div>
            <div>
                <p style="font-size:0.8rem;color:var(--text-secondary);margin:0">P(Real)</p>
                <p style="font-weight:700;color:var(--real-green);margin:0">{prob_real}%</p>
            </div>
            <div>
                <p style="font-size:0.8rem;color:var(--text-secondary);margin:0">P(Fake)</p>
                <p style="font-weight:700;color:var(--fake-red);margin:0">{prob_fake}%</p>
            </div>
            <div>
                <p style="font-size:0.8rem;color:var(--text-secondary);margin:0">Fake Signals</p>
                <p style="font-weight:700;margin:0">{ling.get('fake_signal_count', 0)}</p>
            </div>
            <div>
                <p style="font-size:0.8rem;color:var(--text-secondary);margin:0">Real Signals</p>
                <p style="font-weight:700;margin:0">{ling.get('real_signal_count', 0)}</p>
            </div>
        </div>
    </div>"""

    supporting    = ev.get("supporting_sources",    [])
    contradicting = ev.get("contradicting_sources", [])
    neutral       = ev.get("neutral_sources",       [])
    sources_found = ev.get("sources_found",         0)
    avg_trust     = ev.get("avg_trust_score",        0)

    sup_pills = "".join(f'<span class="source-pill real">✅ {s}</span>' for s in supporting)
    con_pills = "".join(f'<span class="source-pill fake">❌ {s}</span>' for s in contradicting)
    neu_pills = "".join(f'<span class="source-pill">⚪ {s}</span>'     for s in neutral)

    trust_badge = (
        f'<span class="source-pill" style="background:rgba(124,58,237,0.1);'
        f'color:#7c3aed;border-color:rgba(124,58,237,0.25)">'
        f'🏅 Avg Trust: {avg_trust}/100</span>'
        if avg_trust > 0 else ""
    )

    search_status = (
        f'<p style="color:var(--text-secondary);font-size:0.85rem">'
        f'🔍 Searched {ev.get("total_results",0)} results — '
        f'{sources_found} from trusted sources. {trust_badge}</p>'
        if sources_found > 0 else
        '<p style="color:var(--unverified-amber);font-size:0.85rem">'
        '⚠️ Live search returned no results from trusted sources. '
        'Verdict based on ML model and linguistic analysis only.</p>'
    )

    evidence_html = f"""
    <div class="result-card" style="margin-top:1rem">
        <p class="section-label">🌐 Live Verification Evidence</p>
        {search_status}
        {f'<p style="font-size:0.8rem;margin:0.5rem 0 0.2rem;font-weight:600;color:var(--real-green)">Supporting Sources:</p>{sup_pills}' if supporting else ''}
        {f'<p style="font-size:0.8rem;margin:0.5rem 0 0.2rem;font-weight:600;color:var(--fake-red)">Contradicting Sources:</p>{con_pills}' if contradicting else ''}
        {f'<p style="font-size:0.8rem;margin:0.5rem 0 0.2rem;font-weight:600;color:var(--text-secondary)">Neutral References:</p>{neu_pills}' if neutral else ''}
    </div>"""

    articles = ev.get("articles", [])
    if articles:
        def _class_style(c):
            if c == 'supporting':    return 'color:var(--real-green);background:var(--real-green-light)'
            if c == 'contradicting': return 'color:var(--fake-red);background:var(--fake-red-light)'
            return 'color:var(--text-muted);background:rgba(148,163,184,0.12)'

        def _class_icon(c):
            return '✅' if c=='supporting' else ('❌' if c=='contradicting' else '⚪')

        article_rows = "".join(
            f"""<div class="article-row">
                <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:0.5rem;flex-wrap:wrap">
                    <a href="{a.get('url','#')}" target="_blank"
                       style="font-weight:600;font-size:0.85rem;color:var(--brand-blue);text-decoration:none;
                              flex:1;min-width:0;display:-webkit-box;-webkit-line-clamp:2;
                              -webkit-box-orient:vertical;overflow:hidden;line-height:1.4">
                       {a.get('title','')[:110]}
                    </a>
                    <span style="flex-shrink:0;font-size:0.68rem;font-weight:700;padding:0.18rem 0.55rem;
                                 border-radius:999px;{_class_style(a.get('classification','neutral'))}">
                        {_class_icon(a.get('classification','neutral'))} {a.get('classification','neutral').title()}
                    </span>
                </div>
                <div style="display:flex;align-items:center;gap:0.5rem;margin-top:0.3rem;flex-wrap:wrap">
                    <span style="font-size:0.73rem;font-weight:600;color:var(--text-secondary)">
                        {a.get('source_name','')}
                    </span>
                    <span style="font-size:0.68rem;color:var(--text-muted)">·</span>
                    <span style="font-size:0.72rem;color:#7c3aed;font-weight:600;
                                 background:rgba(124,58,237,0.1);padding:0.1rem 0.4rem;border-radius:4px">
                        🏅 {a.get('trust_score','—')}/100
                    </span>
                    {f'<span style="font-size:0.68rem;color:var(--text-muted)">· {a.get("date","")[:16]}</span>' if a.get('date') else ''}
                </div>
            </div>"""
            for a in articles[:6]
        )
        articles_html = f"""
        <div class="result-card" style="margin-top:1rem">
            <p class="section-label">📰 Referenced Articles</p>
            {article_rows}
        </div>"""
    else:
        articles_html = ""

    keywords = result.get("keywords", [])
    kw_pills = "".join(f'<span class="source-pill">{k}</span>' for k in keywords[:8])

    return f"""
    <div class="fade-in">
        {url_html}
        {claim_html}
        <div class="result-card verdict-{vclass}">
            <p class="section-label">VERDICT</p>
            <p class="verdict-label-{vclass}" style="margin:0 0 0.25rem">{icon} {label}</p>
            {overall_bar}
            <hr style="border:none;border-top:1px solid var(--border);margin:1rem 0">
            <p class="section-label">AI REASONING</p>
            <ul style="margin:0;padding-left:0;list-style:none">
                {reasoning_html}
            </ul>
        </div>
        {conf_breakdown}
        {ml_html}
        {evidence_html}
        {articles_html}
        <div class="result-card" style="margin-top:1rem">
            <p class="section-label">🔑 Extracted Keywords</p>
            <div style="margin-bottom:0.75rem">
                {kw_pills if kw_pills else '<span style="color:var(--text-secondary);font-size:0.85rem">None extracted</span>'}
            </div>
            <p style="font-size:0.75rem;color:var(--text-secondary);margin:0">
                ⏱ Verification completed in {elapsed}s
            </p>
        </div>
    </div>"""


# ── Gradio Interface Functions ─────────────────────────────────────────────────

def run_check(news_input: str) -> tuple[str, str]:
    if not news_input or not news_input.strip():
        return (
            '<div class="result-card verdict-unverified">'
            '<p style="color:#d97706;font-weight:700">⚠️ Please enter news text or a URL first.</p></div>',
            "",
        )

    result   = check_news(news_input)
    html_out = build_result_html(result)

    verdict   = result.get("verdict",            "UNVERIFIED")
    ov_conf   = result.get("overall_confidence", result.get("confidence", 0))
    ml_conf   = result.get("ml_confidence",      50)
    ev_conf   = result.get("evidence_confidence", 0)
    reasoning = "\n".join(f"  • {r}" for r in result.get("reasoning", []))
    ev_sources= result.get("evidence_result", {}).get("sources_found", 0)
    model_name= result.get("ml_result", {}).get("model_name", "ML Model")

    summary = (
        f"╔══════════════════════════════════════════════╗\n"
        f"║   AI FAKE NEWS DETECTION — VERSION 3        ║\n"
        f"║   Government Polytechnic West Champaran     ║\n"
        f"╚══════════════════════════════════════════════╝\n\n"
        f"VERDICT          : {'✅ REAL NEWS' if verdict=='REAL' else '❌ FAKE NEWS' if verdict=='FAKE' else '⚠️  UNVERIFIED'}\n"
        f"Overall Confidence : {ov_conf}%\n"
        f"─────────────────────────────────────────────\n"
        f"ML Model         : {model_name}\n"
        f"ML Confidence    : {ml_conf}%\n"
        f"ML Prediction    : {result.get('ml_result',{}).get('label','—')}\n"
        f"Evidence Conf.   : {ev_conf}%\n"
        f"Sources Found    : {ev_sources}\n"
        f"─────────────────────────────────────────────\n"
        f"AI REASONING:\n"
        f"{reasoning}\n"
        f"─────────────────────────────────────────────\n"
        f"Verified In      : {result.get('elapsed_seconds',0)}s\n"
        f"Generated By     : AI Fake News Detector V3\n"
        f"Institution      : Govt. Polytechnic West Champaran\n"
        f"Internship 2026  : AI & ML Batch — SBTE Bihar\n"
    )
    return html_out, summary


def load_sample(sample_key: str) -> str:
    return SAMPLE_NEWS.get(sample_key, "")


def clear_all() -> tuple[str, str, str]:
    return "", "", ""


# ── App Layout ─────────────────────────────────────────────────────────────────

def create_app() -> gr.Blocks:
    with gr.Blocks(
        title="AI Fake News Detector V3",
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="indigo",
            neutral_hue="slate",
        ),
        fill_height=False,
    ) as demo:

        gr.HTML("""
        <div class="app-header">
            <span class="header-icon">🔍</span>
            <div class="version-chip">VERSION 3 · 2026</div>
            <h1>AI Fake News Detection &amp; Live Verification</h1>
            <p>Multi-source verification · Machine Learning · Evidence-based analysis</p>
            <div class="header-badges">
                <span class="badge">🤖 Multi-Model ML</span>
                <span class="badge">🌐 Live Search</span>
                <span class="badge">📰 Trusted Sources</span>
                <span class="badge">🔗 URL Support</span>
                <span class="badge">🏅 Trust Scores</span>
                <span class="badge">🔒 100% Free</span>
            </div>
        </div>
        """)

        with gr.Row():
            with gr.Column(scale=1, elem_classes=["input-section"]):

                gr.HTML('<p class="section-label">📋 Enter News Text or Paste a News Article URL</p>')
                news_input = gr.Textbox(
                    label="",
                    placeholder=(
                        "Paste a news headline, article text, or a news article URL …\n\n"
                        "Examples:\n"
                        "• ISRO successfully tests reusable launch vehicle …\n"
                        "• https://www.thehindu.com/news/…"
                    ),
                    lines=8,
                    max_lines=20,
                    show_copy_button=True,
                )

                with gr.Row():
                    detect_btn = gr.Button(
                        "🔍 Detect & Verify",
                        variant="primary",
                        elem_classes=["btn-primary"],
                        scale=3,
                    )
                    clear_btn = gr.Button(
                        "🗑 Clear",
                        variant="secondary",
                        elem_classes=["btn-secondary"],
                        scale=1,
                    )

                gr.HTML('<p class="section-label" style="margin-top:1.2rem">💡 Try Sample News</p>')
                sample_radio = gr.Radio(
                    choices=list(SAMPLE_NEWS.keys()),
                    label="",
                    value=None,
                    elem_classes=["sample-btn"],
                )

                gr.HTML("""
                <div class="result-card" style="margin-top:1rem;padding:1.25rem 1.4rem">
                    <p class="section-label">⚙️ How It Works — V3</p>
                    <div>
                        <div class="step-item"><div class="step-num">1</div><span>URL resolved → article text extracted (if URL input)</span></div>
                        <div class="step-item"><div class="step-num">2</div><span>Core factual claim auto-extracted from text</span></div>
                        <div class="step-item"><div class="step-num">3</div><span>Keywords searched across Google News RSS &amp; DuckDuckGo</span></div>
                        <div class="step-item"><div class="step-num">4</div><span>Evidence classified: supporting / contradicting / neutral</span></div>
                        <div class="step-item"><div class="step-num">5</div><span>Sources filtered through trust whitelist (scored 0–100)</span></div>
                        <div class="step-item"><div class="step-num">6</div><span>Best ML model from 4-model comparison runs prediction</span></div>
                        <div class="step-item"><div class="step-num">7</div><span>ML + Evidence + Linguistics combined via weighted decision</span></div>
                        <div class="step-item"><div class="step-num">8</div><span>Separate ML, Evidence &amp; Overall confidence scores generated</span></div>
                        <div class="step-item"><div class="step-num">9</div><span>AI reasoning with supporting/conflicting evidence returned</span></div>
                    </div>
                </div>
                """)

            with gr.Column(scale=1):
                gr.HTML('<p class="section-label">📊 Verification Result</p>')
                result_html = gr.HTML(
                    value="""
                    <div class="result-card" style="text-align:center;padding:3rem 1rem">
                        <p style="font-size:2.5rem;margin:0">🔍</p>
                        <p style="color:var(--text-secondary);margin:0.5rem 0 0;font-size:0.95rem">
                            Enter news text or a URL and click <strong>Detect &amp; Verify</strong>
                        </p>
                        <p style="color:var(--text-secondary);margin:0.25rem 0 0;font-size:0.8rem">
                            Results with confidence scores and source links will appear here
                        </p>
                    </div>"""
                )

                with gr.Accordion("📋 Export Result as Text", open=False):
                    result_text = gr.Textbox(
                        label="Copy-ready plain text report",
                        lines=12,
                        interactive=False,
                        show_copy_button=True,
                        elem_classes=["copy-result-box"],
                    )

        gr.HTML("""
        <div class="disclaimer-card">
            <span style="font-size:1.1rem;flex-shrink:0">⚠️</span>
            <p style="margin:0;font-size:0.82rem;color:var(--text-secondary);line-height:1.55">
                <strong style="color:var(--brand-blue)">Disclaimer:</strong>
                This tool is an AI assistant and should not be the sole basis for determining
                the veracity of news. Always cross-reference with multiple authoritative sources.
                The system never claims 100% certainty.
            </p>
        </div>
        """)

        gr.HTML("""
        <div class="app-footer" style="margin-top:1.25rem">

            <div style="font-size:0.68rem;font-weight:800;text-transform:uppercase;
                        letter-spacing:1.2px;color:var(--text-muted);margin-bottom:1rem">
                👨‍💻 Project Team — AI &amp; ML Internship 2026
            </div>

            <div class="team-grid">
                <div class="team-card">
                    <div class="team-avatar">👨‍💻</div>
                    <div class="team-name">Naman Kumar</div>
                    <div class="team-role">Full Stack AI Developer<br>UI/UX Designer</div>
                    <span class="team-role-badge">Project Lead</span>
                </div>
                <div class="team-card">
                    <div class="team-avatar">⚙️</div>
                    <div class="team-name">Parmeshwar Kumar</div>
                    <div class="team-role">Backend Developer<br>API Integration</div>
                    <span class="team-role-badge">Backend</span>
                </div>
                <div class="team-card">
                    <div class="team-avatar">🤖</div>
                    <div class="team-name">Amit Kumar</div>
                    <div class="team-role">ML Engineer<br>Dataset &amp; Model Training</div>
                    <span class="team-role-badge">ML / AI</span>
                </div>
                <div class="team-card">
                    <div class="team-avatar">📖</div>
                    <div class="team-name">Prince Kumar Chaurasiya</div>
                    <div class="team-role">Research &amp; Documentation<br>Lead</div>
                    <span class="team-role-badge">Research</span>
                </div>
                <div class="team-card">
                    <div class="team-avatar">🧪</div>
                    <div class="team-name">Dhiraj Kumar</div>
                    <div class="team-role">QA Engineer<br>Performance Testing</div>
                    <span class="team-role-badge">QA</span>
                </div>
                <div class="team-card">
                    <div class="team-avatar">🔬</div>
                    <div class="team-name">MD. Tausim Akhtar</div>
                    <div class="team-role">AI Research<br>Contributor</div>
                    <span class="team-role-badge">Research</span>
                </div>
            </div>

            <div style="width:80%;height:1px;background:linear-gradient(90deg,transparent,
                 var(--card-border),transparent);margin:1.5rem auto"></div>

            <p class="footer-inst">🏛️ Government Polytechnic West Champaran</p>
            <p class="footer-sub">Department of Computer Science &amp; Engineering</p>
            <p class="footer-sub">Affiliated to SBTE Bihar · Session 2025–2028</p>

            <div style="margin-top:1rem">
                <p class="footer-copyright">
                    © 2026 Government Polytechnic West Champaran · SBTE Bihar
                </p>
                <p class="footer-copyright">
                    AI Fake News Detection &amp; Live Verification System — Version 3
                </p>
            </div>
        </div>
        """)
        # ── Event Handlers ────────────────────────────────────────────────────────

        detect_btn.click(
            fn=run_check,
            inputs=[news_input],
            outputs=[result_html, result_text],
            api_name="detect",
        )

        news_input.submit(
            fn=run_check,
            inputs=[news_input],
            outputs=[result_html, result_text],
        )

        sample_radio.change(
            fn=load_sample,
            inputs=[sample_radio],
            outputs=[news_input],
        )

        clear_btn.click(
            fn=clear_all,
            inputs=[],
            outputs=[news_input, result_html, result_text],
        )

    return demo


# ── Entry Point ───────────────────────────────────────────────────────────────
demo = create_app()

# HF Spaces: server_name must be "0.0.0.0", share must be False.
# The platform handles routing — share=True causes a conflict on Spaces.
# Locally: share=False also works fine (localhost:7860).
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=False,
    show_error=True,
    allowed_paths=["."],
)
