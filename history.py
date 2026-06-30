"""
history.py
==========
Version 5 — In-session verification history manager.

Changes from V4
---------------
- Max history raised from 20 → 100 (EXPORT_MAX_HISTORY from config).
- Added delete_at(index) — remove a single entry by position.
- Added search(query) — return entries whose text/verdict matches query.
- Added export_all() — dump history as JSON string for download.
- History entries now store all 5 V5 confidence keys.
- summary() helper used by the UI to render a one-line history row.
- Thread-safe via threading.Lock (same session can call from multiple threads).

AI Fake News Detection & Live Verification System — Version 5
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar, Parmeshwar Kumar, Amit Kumar,
              Prince Kumar Chaurasiya, Dhiraj Kumar, MD. Tausim Akhtar
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime

from config import EXPORT_MAX_HISTORY, APP_VERSION, INSTITUTION

logger = logging.getLogger(__name__)


class VerificationHistory:
    """
    Thread-safe in-memory store for the last EXPORT_MAX_HISTORY (100) results.

    Each entry is a dict with keys:
        timestamp, text_preview, verdict, overall_confidence,
        ml_confidence, evidence_confidence, linguistic_confidence,
        fact_confidence, elapsed_seconds, sources_found, primary_claim
    """

    def __init__(self, maxsize: int = EXPORT_MAX_HISTORY) -> None:
        self._entries: list[dict] = []
        self._max     = maxsize
        self._lock    = threading.Lock()

    # ── Add ───────────────────────────────────────────────────────────────────

    def add(self, result: dict) -> None:
        """
        Prepend a new entry from a check_news() result dict.
        Oldest entry is dropped when the store exceeds maxsize.
        """
        original = result.get("original_text", "")
        text_preview = (original[:90] + "…") if len(original) > 90 else original

        entry: dict = {
            "timestamp":             datetime.now().isoformat(timespec="seconds"),
            "text_preview":          text_preview,
            "verdict":               result.get("verdict",              "UNVERIFIED"),
            "overall_confidence":    result.get("overall_confidence",   0),
            "ml_confidence":         result.get("ml_confidence",        0),
            "evidence_confidence":   result.get("evidence_confidence",  0),
            "linguistic_confidence": result.get("linguistic_confidence",0),
            "fact_confidence":       result.get("fact_confidence",      0),
            "elapsed_seconds":       result.get("elapsed_seconds",      0.0),
            "sources_found":         result.get("evidence_result",{}).get("sources_found", 0),
            "primary_claim":         result.get("primary_claim",        ""),
            "combined_score":        result.get("combined_score",       0.0),
            "is_url":                result.get("url_meta",  {}).get("is_url", False),
            "url":                   result.get("url_meta",  {}).get("url",    ""),
            "error":                 result.get("error"),
        }

        with self._lock:
            self._entries.insert(0, entry)
            if len(self._entries) > self._max:
                self._entries = self._entries[: self._max]

        logger.debug("History: added '%s' → %s", text_preview[:40], entry["verdict"])

    # ── Read ──────────────────────────────────────────────────────────────────

    def all(self) -> list[dict]:
        """Return a shallow copy of all entries (newest first)."""
        with self._lock:
            return list(self._entries)

    def get(self, index: int) -> dict | None:
        """Return entry at position (0 = most recent) or None."""
        with self._lock:
            if 0 <= index < len(self._entries):
                return dict(self._entries[index])
            return None

    def count(self) -> int:
        with self._lock:
            return len(self._entries)

    def is_empty(self) -> bool:
        return self.count() == 0

    # ── Search ────────────────────────────────────────────────────────────────

    def search(self, query: str) -> list[tuple[int, dict]]:
        """
        Return (original_index, entry) pairs whose text_preview, verdict,
        or primary_claim contains query (case-insensitive).
        """
        q = query.strip().lower()
        if not q:
            with self._lock:
                return list(enumerate(self._entries))

        with self._lock:
            return [
                (i, e) for i, e in enumerate(self._entries)
                if (
                    q in e.get("text_preview",  "").lower()
                    or q in e.get("verdict",     "").lower()
                    or q in e.get("primary_claim","").lower()
                )
            ]

    # ── Delete ────────────────────────────────────────────────────────────────

    def delete_at(self, index: int) -> bool:
        """
        Remove the entry at position index.
        Returns True if successful, False if index out of range.
        """
        with self._lock:
            if 0 <= index < len(self._entries):
                removed = self._entries.pop(index)
                logger.debug("History: deleted '%s'", removed.get("text_preview","")[:40])
                return True
            return False

    def clear(self) -> None:
        """Remove all entries."""
        with self._lock:
            count = len(self._entries)
            self._entries = []
        logger.info("History: cleared %d entries", count)

    # ── Export ────────────────────────────────────────────────────────────────

    def export_all(self) -> str:
        """
        Return all history entries as a formatted JSON string.
        Safe for file download.
        """
        payload = {
            "export_version": APP_VERSION,
            "institution":    INSTITUTION,
            "exported_at":    datetime.now().isoformat(),
            "total_entries":  self.count(),
            "entries":        self.all(),
        }
        return json.dumps(payload, indent=2, ensure_ascii=False, default=str)

    # ── UI Helpers ────────────────────────────────────────────────────────────

    def summary(self, entry: dict) -> str:
        """
        Return a one-line summary string for a history row in the UI.
        Format:  [HH:MM]  VERDICT (conf%)  —  text preview…
        """
        ts       = entry.get("timestamp", "")
        time_str = ts[11:16] if len(ts) >= 16 else ts
        verdict  = entry.get("verdict",          "?")
        conf     = entry.get("overall_confidence", 0)
        preview  = entry.get("text_preview",       "")
        icon_map = {
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
        icon = icon_map.get(verdict, "❓")
        return f"[{time_str}]  {icon} {verdict} ({conf}%)  —  {preview}"

    def as_display_rows(self) -> list[list[str]]:
        """
        Return data as rows for a Gradio Dataframe:
        [timestamp, verdict, conf%, sources, preview]
        """
        with self._lock:
            return [
                [
                    e.get("timestamp", "")[:19],
                    e.get("verdict", ""),
                    f"{e.get('overall_confidence', 0)}%",
                    str(e.get("sources_found", 0)),
                    e.get("text_preview", ""),
                ]
                for e in self._entries
            ]


# ── Module-level singleton ────────────────────────────────────────────────────

history = VerificationHistory(maxsize=EXPORT_MAX_HISTORY)
