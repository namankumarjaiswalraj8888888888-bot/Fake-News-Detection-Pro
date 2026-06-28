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

# ── CSS Styling (preserved from V2, with minor V3 additions) ──────────────────

CUSTOM_CSS = """
/* ── Variables & Reset ── */
:root {
    --brand-blue: #1a56db;
    --brand-indigo: #4338ca;
    --brand-purple: #7c3aed;
    --real-green: #059669;
    --fake-red: #dc2626;
    --unverified-amber: #d97706;
    --bg-light: #f8fafc;
    --card-bg: #ffffff;
    --border: #e2e8f0;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --radius: 14px;
    --shadow: 0 4px 24px rgba(0,0,0,0.08);
    --shadow-hover: 0 8px 32px rgba(0,0,0,0.14);
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-light: #0f172a;
        --card-bg: #1e293b;
        --border: #334155;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
    }
}

body, .gradio-container {
    background: var(--bg-light) !important;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
    color: var(--text-primary) !important;
}

/* ── Header ── */
.app-header {
    background: linear-gradient(135deg, #1a56db 0%, #4338ca 50%, #7c3aed 100%);
    border-radius: var(--radius);
    padding: 2.5rem 2rem;
    text-align: center;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.app-header::before {
    content: '';
    position: absolute;
    inset: 0;
    background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.04'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}
.app-header h1 {
    color: #ffffff !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    margin: 0 0 0.5rem !important;
    letter-spacing: -0.5px;
    position: relative;
}
.app-header p {
    color: rgba(255,255,255,0.85) !important;
    font-size: 1rem !important;
    margin: 0 !important;
    position: relative;
}
.header-badges {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
    margin-top: 1rem;
    flex-wrap: wrap;
}
.badge {
    background: rgba(255,255,255,0.2);
    color: #fff;
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 999px;
    padding: 0.25rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}

/* ── Cards ── */
.result-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow);
    transition: box-shadow 0.2s ease;
}
.result-card:hover { box-shadow: var(--shadow-hover); }

/* ── Verdict Banner ── */
.verdict-real { border-left: 5px solid var(--real-green) !important; }
.verdict-fake { border-left: 5px solid var(--fake-red) !important; }
.verdict-unverified { border-left: 5px solid var(--unverified-amber) !important; }

.verdict-label-real  { color: var(--real-green) !important; font-size: 1.8rem !important; font-weight: 800 !important; }
.verdict-label-fake  { color: var(--fake-red) !important; font-size: 1.8rem !important; font-weight: 800 !important; }
.verdict-label-unverified { color: var(--unverified-amber) !important; font-size: 1.8rem !important; font-weight: 800 !important; }

/* ── Source Pills ── */
.source-pill {
    display: inline-block;
    background: rgba(26,86,219,0.1);
    color: var(--brand-blue);
    border: 1px solid rgba(26,86,219,0.25);
    border-radius: 999px;
    padding: 0.2rem 0.65rem;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 0.15rem;
}
.source-pill.real { background: rgba(5,150,105,0.1); color: var(--real-green); border-color: rgba(5,150,105,0.25); }
.source-pill.fake { background: rgba(220,38,38,0.1); color: var(--fake-red); border-color: rgba(220,38,38,0.25); }

/* ── Confidence Bar ── */
.conf-bar-wrap {
    background: var(--border);
    border-radius: 999px;
    height: 12px;
    overflow: hidden;
    margin: 0.5rem 0;
}
.conf-bar {
    height: 100%;
    border-radius: 999px;
    transition: width 0.8s cubic-bezier(0.4,0,0.2,1);
}
.conf-bar.real { background: linear-gradient(90deg, #059669, #34d399); }
.conf-bar.fake { background: linear-gradient(90deg, #dc2626, #f87171); }
.conf-bar.unverified { background: linear-gradient(90deg, #d97706, #fbbf24); }

/* ── Input Area ── */
.input-section textarea {
    border: 2px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-size: 0.95rem !important;
    transition: border-color 0.2s ease !important;
    background: var(--card-bg) !important;
    color: var(--text-primary) !important;
}
.input-section textarea:focus {
    border-color: var(--brand-blue) !important;
    box-shadow: 0 0 0 3px rgba(26,86,219,0.15) !important;
}

/* ── Buttons ── */
.btn-primary {
    background: linear-gradient(135deg, #1a56db, #4338ca) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.75rem 2rem !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(26,86,219,0.35) !important;
}
.btn-primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(26,86,219,0.45) !important;
}
.btn-secondary {
    background: var(--card-bg) !important;
    color: var(--text-secondary) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-weight: 600 !important;
}
.btn-secondary:hover {
    border-color: var(--brand-blue) !important;
    color: var(--brand-blue) !important;
}

/* ── Sample Buttons ── */
.sample-btn {
    background: var(--card-bg) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-secondary) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    text-align: left !important;
}
.sample-btn:hover {
    border-color: var(--brand-blue) !important;
    color: var(--brand-blue) !important;
    background: rgba(26,86,219,0.05) !important;
    transform: translateY(-1px) !important;
}

/* ── Section Labels ── */
.section-label {
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    color: var(--text-secondary) !important;
    margin-bottom: 0.5rem !important;
}

/* ── Mini confidence bars (V3) ── */
.mini-bar-wrap {
    background: var(--border);
    border-radius: 999px;
    height: 6px;
    overflow: hidden;
    margin: 0.2rem 0 0.5rem;
    width: 100%;
}
.mini-bar {
    height: 100%;
    border-radius: 999px;
}
.mini-bar.ml-color  { background: linear-gradient(90deg, #4338ca, #818cf8); }
.mini-bar.ev-color  { background: linear-gradient(90deg, #0891b2, #67e8f9); }
.mini-bar.ov-color  { background: linear-gradient(90deg, #059669, #34d399); }
.mini-bar.ov-fake   { background: linear-gradient(90deg, #dc2626, #f87171); }
.mini-bar.ov-unv    { background: linear-gradient(90deg, #d97706, #fbbf24); }

/* ── Footer ── */
.app-footer {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem 2rem;
    text-align: center;
    margin-top: 1.5rem;
}
.app-footer p {
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
    margin: 0.2rem 0 !important;
}
.dev-name {
    font-weight: 700 !important;
    color: var(--brand-blue) !important;
}

/* ── Animations ── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
.fade-in { animation: fadeInUp 0.4s ease forwards; }

/* ── Responsive ── */
@media (max-width: 768px) {
    .app-header h1 { font-size: 1.4rem !important; }
    .app-header { padding: 1.5rem 1rem; }
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
    """Convert a check_news() result dict into a rich HTML display."""

    # ── Error state ────────────────────────────────────────────────────────────
    if result.get("error") and not result.get("verdict"):
        return (
            '<div class="result-card verdict-unverified fade-in">'
            '<p style="color:#d97706;font-weight:700;font-size:1.1rem">⚠️ Error</p>'
            f'<p style="color:var(--text-secondary)">{result["error"]}</p>'
            "</div>"
        )

    verdict          = result.get("verdict",            "UNVERIFIED")
    overall_conf     = result.get("overall_confidence", result.get("confidence", 0))
    ml_conf_pct      = result.get("ml_confidence",      50)
    ev_conf_pct      = result.get("evidence_confidence", 0)
    icon             = _verdict_icon(verdict)
    label            = _verdict_label(verdict)
    reasoning        = result.get("reasoning",          [])
    ml               = result.get("ml_result",          {})
    ling             = result.get("linguistic_signals", {})
    ev               = result.get("evidence_result",    {})
    elapsed          = result.get("elapsed_seconds",    0)
    primary_claim    = result.get("primary_claim",      "")
    url_meta         = result.get("url_meta",           {})
    vclass           = verdict.lower()

    # ── Overall confidence bar ─────────────────────────────────────────────────
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

    # ── Reasoning ──────────────────────────────────────────────────────────────
    reasoning_html = "".join(
        f'<li style="margin-bottom:0.4rem;color:var(--text-secondary);font-size:0.9rem">'
        f'<span style="color:var(--brand-blue)">▸</span> {r}</li>'
        for r in reasoning
    )

    # ── Primary claim ──────────────────────────────────────────────────────────
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

    # ── URL meta ───────────────────────────────────────────────────────────────
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

    # ── Confidence breakdown (V3 new section) ──────────────────────────────────
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

    # ── ML Analysis ────────────────────────────────────────────────────────────
    prob_real    = int(ml.get("prob_real", 0.5) * 100)
    prob_fake    = int(ml.get("prob_fake", 0.5) * 100)
    model_name   = ml.get("model_name", "ML Model")
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

    # ── Evidence sources ───────────────────────────────────────────────────────
    supporting   = ev.get("supporting_sources",    [])
    contradicting= ev.get("contradicting_sources", [])
    neutral      = ev.get("neutral_sources",       [])
    sources_found= ev.get("sources_found",         0)
    avg_trust    = ev.get("avg_trust_score",        0)

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

    # ── Articles list (V3: shows publication date, trust score, source link) ──
    articles = ev.get("articles", [])
    if articles:
        article_rows = "".join(
            f"""<div style="padding:0.6rem 0;border-bottom:1px solid var(--border)">
                <a href="{a.get('url','#')}" target="_blank"
                   style="font-weight:600;font-size:0.85rem;color:var(--brand-blue);text-decoration:none">
                   {a.get('title','')[:100]}…</a>
                <p style="font-size:0.75rem;color:var(--text-secondary);margin:0.1rem 0 0">
                    <strong>{a.get('source_name','')}</strong>
                    &nbsp;·&nbsp;
                    Trust: <strong style="color:#7c3aed">{a.get('trust_score', '—')}/100</strong>
                    {' · ' + a.get('date','')[:20] if a.get('date') else ''}
                    &nbsp;·&nbsp;
                    <span style="color:{'var(--real-green)' if a.get('classification')=='supporting'
                                        else 'var(--fake-red)' if a.get('classification')=='contradicting'
                                        else 'var(--text-secondary)'}">
                        {a.get('classification','neutral').title()}
                    </span>
                </p>
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

    # ── Keywords ───────────────────────────────────────────────────────────────
    keywords  = result.get("keywords", [])
    kw_pills  = "".join(f'<span class="source-pill">{k}</span>' for k in keywords[:8])

    return f"""
    <div class="fade-in">
        <!-- URL / Article info -->
        {url_html}

        <!-- Primary Claim -->
        {claim_html}

        <!-- Main verdict card -->
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

        <!-- Confidence Breakdown -->
        {conf_breakdown}

        <!-- ML Analysis -->
        {ml_html}

        <!-- Evidence -->
        {evidence_html}

        <!-- Articles -->
        {articles_html}

        <!-- Keywords & Meta -->
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
    """Called when the user clicks 'Detect & Verify'."""
    if not news_input or not news_input.strip():
        return (
            '<div class="result-card verdict-unverified">'
            '<p style="color:#d97706;font-weight:700">⚠️ Please enter news text or a URL first.</p></div>',
            "",
        )

    result   = check_news(news_input)
    html_out = build_result_html(result)

    verdict    = result.get("verdict",            "UNVERIFIED")
    ov_conf    = result.get("overall_confidence", result.get("confidence", 0))
    ml_conf    = result.get("ml_confidence",      50)
    ev_conf    = result.get("evidence_confidence", 0)
    reasoning  = "\n".join(f"  • {r}" for r in result.get("reasoning", []))
    ev_sources = result.get("evidence_result", {}).get("sources_found", 0)
    model_name = result.get("ml_result", {}).get("model_name", "ML Model")

    summary = (
        f"AI FAKE NEWS DETECTION RESULT — VERSION 3\n"
        f"==========================================\n"
        f"Verdict            : {verdict}\n"
        f"Overall Confidence : {ov_conf}%\n"
        f"ML Confidence      : {ml_conf}%  ({model_name})\n"
        f"Evidence Confidence: {ev_conf}%\n"
        f"ML Prediction      : {result.get('ml_result',{}).get('label','—')}\n"
        f"Sources Found      : {ev_sources}\n\n"
        f"AI Reasoning:\n{reasoning}\n\n"
        f"Verification Time  : {result.get('elapsed_seconds',0)}s\n"
        f"— AI Fake News Detector V3 | Government Polytechnic West Champaran —"
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
    ) as demo:

        # ── Header ──────────────────────────────────────────────────────────────
        gr.HTML("""
        <div class="app-header">
            <h1>🔍 AI Fake News Detection &amp; Live Verification System</h1>
            <p>Multi-source verification · Machine Learning · Evidence-based analysis · Version 3</p>
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

        # ── Main Content ─────────────────────────────────────────────────────────
        with gr.Row():
            # Left Column: Input
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
                <div class="result-card" style="margin-top:1rem;padding:1rem">
                    <p class="section-label">⚙️ How It Works (V3)</p>
                    <ol style="color:var(--text-secondary);font-size:0.82rem;margin:0;padding-left:1.2rem;line-height:1.9">
                        <li>URL resolved → article text extracted (if URL input)</li>
                        <li>Core factual claim auto-extracted</li>
                        <li>Keywords searched in parallel across Google News RSS &amp; DuckDuckGo</li>
                        <li>Evidence classified (supporting / contradicting / neutral)</li>
                        <li>Sources filtered through trust whitelist (scored 0–100)</li>
                        <li>Best ML model from 4-model comparison runs prediction</li>
                        <li>ML + Evidence + Linguistics combined via weighted decision</li>
                        <li>Separate ML, Evidence &amp; Overall confidence scores generated</li>
                        <li>AI reasoning with supporting/conflicting evidence returned</li>
                    </ol>
                </div>
                """)

            # Right Column: Results
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

                with gr.Accordion("📋 Copy Result as Text", open=False):
                    result_text = gr.Textbox(
                        label="Plain text result (select all → copy)",
                        lines=10,
                        interactive=False,
                        show_copy_button=True,
                    )

        # ── Disclaimer ────────────────────────────────────────────────────────────
        gr.HTML("""
        <div class="result-card" style="margin-top:0.5rem;background:rgba(26,86,219,0.04);
             border-color:rgba(26,86,219,0.2)">
            <p style="margin:0;font-size:0.82rem;color:var(--text-secondary)">
                <strong style="color:var(--brand-blue)">⚠️ Disclaimer:</strong>
                This tool is an AI assistant and should not be the sole basis for
                determining the veracity of news. Always cross-reference with multiple
                authoritative sources. The system never claims 100% certainty.
            </p>
        </div>
        """)

        # ── Developer & Footer ────────────────────────────────────────────────────
        gr.HTML("""
        <div class="app-footer" style="margin-top:1rem">
            <p style="font-size:1rem;font-weight:700;color:var(--text-primary);margin-bottom:0.5rem">
                👨‍💻 Developed By
            </p>
            <p><span class="dev-name">Naman Kumar</span> &amp; <span class="dev-name">Parmeshwar</span></p>
            <p style="margin-top:0.75rem">
                🎓 AI &amp; Machine Learning Internship Project 2026<br>
                <strong>Government Polytechnic West Champaran</strong><br>
                Department of Computer Science &amp; Engineering · SBTE Bihar · Diploma Engineering<br>
                Session 2025–2028
            </p>
            <hr style="border:none;border-top:1px solid var(--border);margin:1rem 0">
            <p>© 2026 Naman Kumar &amp; Parmeshwar · Government Polytechnic West Champaran<br>
            AI &amp; Machine Learning Internship Project — Version 3</p>
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

if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        share=False,
        show_error=True,
    )
