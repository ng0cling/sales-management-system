"""
PROJECT 03: SALES MANAGEMENT SYSTEM
File: gui/constants.py
Theme constants, fonts, order config, utilities.
"""

from __future__ import annotations
import threading
import tkinter as tk

# ── Colors ────────────────────────────────────────────────────────────────────
CLR_BG        = "#1e1e2e"
CLR_SIDEBAR   = "#181825"
CLR_CARD      = "#313244"
CLR_ACCENT    = "#89b4fa"
CLR_SUCCESS   = "#a6e3a1"
CLR_DANGER    = "#f38ba8"
CLR_WARNING   = "#fab387"
CLR_TEXT      = "#cdd6f4"
CLR_SUBTEXT   = "#a6adc8"
CLR_HEADER_BG = "#45475a"

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_TITLE  = ("Segoe UI", 16, "bold")
FONT_HEADER = ("Segoe UI", 11, "bold")
FONT_BODY   = ("Segoe UI", 10)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 10)

# ── Order config ──────────────────────────────────────────────────────────────
ORDER_STATUSES = ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]

ORDER_TRANSITIONS: dict[str, list[str]] = {
    "Pending":    ["Processing", "Cancelled"],
    "Processing": ["Shipped",    "Cancelled"],
    "Shipped":    ["Delivered",  "Cancelled"],
    "Delivered":  [],
    "Cancelled":  [],
}

# ── Utilities ─────────────────────────────────────────────────────────────────

def fmt_vnd(value) -> str:
    try:
        return f"{float(value):,.0f} VND"
    except (TypeError, ValueError):
        return "0 VND"


def run_in_thread(func, callback=None):
    def worker():
        result, error = None, None
        try:
            result = func()
        except Exception as e:
            error = e
        if callback:
            try:
                root = tk._default_root
                if root is not None:
                    root.after(0, lambda: callback(result, error))
                else:
                    callback(result, error)
            except Exception:
                callback(result, error)
    threading.Thread(target=worker, daemon=True).start()