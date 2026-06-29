"""
history.py
==========
Version 4 — In-session search history and statistics.

Stores the last N verification results in memory (per Gradio session).
Provides statistics panel data: total checks, REAL/FAKE/UNVERIFIED counts,
average confidence, average analysis time.

Note: History does NOT persist across page refreshes (Gradio stateless).
For persistent history, integrate a DB or file-backed store in a future version.

AI Fake News Detection & Live Verification System — Version 4
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar & Parmeshwar
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from config import EXPORT_MAX_HISTORY


class VerificationHistory:
    """
    Lightweight in-memory store for one Gradio session's verification history.
    Instantiated once per session via gr.State().
    """

    def __init__(self) -> None:
        self._entries: list[dict] = []

    # ── Write ─────────────────────────────────────────────────────────────────

    def add(self, result: dict, query_text: str = "") -> None:
        """Append a completed verification result. Trims to EXPORT_MAX_HISTORY."""
        entry = {
            "timestamp":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query":        (query_text or result.get("original_text", ""))[:200],
            "verdict":      result.get("verdict", "UNVERIFIED"),
            "confidence":   result.get("overall_confidence", 0),
            "ml_conf":      result.get("ml_confidence", 0),
            "ev_conf":      result.get("evidence_confidence", 0),
            "elapsed":      result.get("elapsed_seconds", 0),
            "sources":      result.get("evidence_result", {}).get("sources_found", 0),
            "keywords":     result.get("keywords", []),
            "result":       result,      # full result for re-export
        }
        self._entries.insert(0, entry)   # newest first
        if len(self._entries) > EXPORT_MAX_HISTORY:
            self._entries = self._entries[:EXPORT_MAX_HISTORY]

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_all(self) -> list[dict]:
        return list(self._entries)

    def get_latest(self) -> Optional[dict]:
        return self._entries[0] if self._entries else None

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries = []

    # ── Statistics ────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        """Return aggregate statistics across all checks in this session."""
        total = len(self._entries)
        if total == 0:
            return {
                "total":          0,
                "real_count":     0,
                "fake_count":     0,
                "unverified_count": 0,
                "real_pct":       0,
                "fake_pct":       0,
                "unverified_pct": 0,
                "avg_confidence": 0,
                "avg_elapsed":    0.0,
                "avg_sources":    0,
            }

        real_c = sum(1 for e in self._entries if e["verdict"] == "REAL")
        fake_c = sum(1 for e in self._entries if e["verdict"] == "FAKE")
        unv_c  = total - real_c - fake_c

        avg_conf    = round(sum(e["confidence"] for e in self._entries) / total)
        avg_elapsed = round(sum(e["elapsed"]    for e in self._entries) / total, 2)
        avg_sources = round(sum(e["sources"]    for e in self._entries) / total)

        return {
            "total":            total,
            "real_count":       real_c,
            "fake_count":       fake_c,
            "unverified_count": unv_c,
            "real_pct":         round(real_c / total * 100),
            "fake_pct":         round(fake_c / total * 100),
            "unverified_pct":   round(unv_c  / total * 100),
            "avg_confidence":   avg_conf,
            "avg_elapsed":      avg_elapsed,
            "avg_sources":      avg_sources,
        }

    # ── HTML Renderers ────────────────────────────────────────────────────────

    def render_history_html(self) -> str:
        """Render compact history list as HTML for a Gradio HTML component."""
        if not self._entries:
            return (
                '<div class="hist-empty">'
                '<span class="hist-empty-icon">📋</span>'
                '<p>No checks yet in this session.</p>'
                '<p class="hist-sub">Your recent analyses will appear here.</p>'
                '</div>'
            )

        rows = []
        for e in self._entries[:10]:
            v   = e["verdict"]
            ico = {"REAL": "✅", "FAKE": "❌"}.get(v, "⚠️")
            cls = {"REAL": "hist-real", "FAKE": "hist-fake"}.get(v, "hist-unv")
            q   = e["query"][:80] + ("…" if len(e["query"]) > 80 else "")
            rows.append(
                f'<div class="hist-row">'
                f'  <span class="hist-icon {cls}">{ico}</span>'
                f'  <div class="hist-info">'
                f'    <div class="hist-query">{q}</div>'
                f'    <div class="hist-meta">'
                f'      <span class="hist-verdict {cls}">{v}</span>'
                f'      <span class="hist-conf">{e["confidence"]}% conf</span>'
                f'      <span class="hist-time">{e["timestamp"]}</span>'
                f'      <span class="hist-src">{e["sources"]} sources</span>'
                f'    </div>'
                f'  </div>'
                f'</div>'
            )
        return "\n".join(rows)

    def render_stats_html(self) -> str:
        """Render session statistics as HTML."""
        s = self.stats()
        if s["total"] == 0:
            return (
                '<div class="stats-empty">'
                '<p>Run at least one check to see session statistics.</p>'
                '</div>'
            )

        bars = [
            ("✅ REAL",       s["real_pct"],       "#22c55e"),
            ("❌ FAKE",       s["fake_pct"],        "#ef4444"),
            ("⚠️ UNVERIFIED", s["unverified_pct"],  "#eab308"),
        ]
        bar_html = ""
        for label, pct, color in bars:
            bar_html += (
                f'<div class="stat-bar-row">'
                f'  <span class="stat-bar-label">{label}</span>'
                f'  <div class="stat-bar-track">'
                f'    <div class="stat-bar-fill" style="width:{pct}%;background:{color}"></div>'
                f'  </div>'
                f'  <span class="stat-bar-pct">{pct}%</span>'
                f'</div>'
            )

        return (
            f'<div class="stats-grid">'
            f'  <div class="stat-card">'
            f'    <div class="stat-num">{s["total"]}</div>'
            f'    <div class="stat-lbl">Total Checks</div>'
            f'  </div>'
            f'  <div class="stat-card">'
            f'    <div class="stat-num">{s["avg_confidence"]}%</div>'
            f'    <div class="stat-lbl">Avg Confidence</div>'
            f'  </div>'
            f'  <div class="stat-card">'
            f'    <div class="stat-num">{s["avg_elapsed"]}s</div>'
            f'    <div class="stat-lbl">Avg Time</div>'
            f'  </div>'
            f'  <div class="stat-card">'
            f'    <div class="stat-num">{s["avg_sources"]}</div>'
            f'    <div class="stat-lbl">Avg Sources</div>'
            f'  </div>'
            f'</div>'
            f'<div class="stat-bars">{bar_html}</div>'
        )
