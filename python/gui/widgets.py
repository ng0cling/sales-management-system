"""
PROJECT 03: SALES MANAGEMENT SYSTEM
File: gui/widgets.py
Reusable base widgets: StyledButton, LabeledEntry, LabeledCombobox, StatusBar, DataTable.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from gui.constants import (
    CLR_BG, CLR_CARD, CLR_ACCENT, CLR_SUCCESS, CLR_DANGER, CLR_WARNING,
    CLR_TEXT, CLR_SUBTEXT, CLR_HEADER_BG, CLR_SIDEBAR,
    FONT_TITLE, FONT_HEADER, FONT_BODY, FONT_SMALL,
)


class StyledButton(tk.Button):
    def __init__(self, parent, text, command=None, kind="primary", **kw):
        colors = {
            "primary": (CLR_ACCENT,  "#1e1e2e"),
            "success": (CLR_SUCCESS, "#1e1e2e"),
            "danger":  (CLR_DANGER,  "#1e1e2e"),
            "warning": (CLR_WARNING, "#1e1e2e"),
            "neutral": (CLR_CARD,    CLR_TEXT),
        }
        bg, fg = colors.get(kind, colors["primary"])
        super().__init__(
            parent, text=text, command=command,
            bg=bg, fg=fg, font=FONT_BODY, relief="flat",
            padx=12, pady=5, cursor="hand2",
            activebackground=fg, activeforeground=bg,
            **kw,
        )


class LabeledEntry(tk.Frame):
    def __init__(self, parent, label: str, required=False, **kw):
        super().__init__(parent, bg=CLR_CARD)
        tk.Label(self, text=label + (" *" if required else ""),
                 bg=CLR_CARD, fg=CLR_SUBTEXT, font=FONT_SMALL).pack(anchor="w")
        self.var = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.var,
                              bg="#45475a", fg=CLR_TEXT, insertbackground=CLR_TEXT,
                              relief="flat", font=FONT_BODY, **kw)
        self.entry.pack(fill="x", ipady=5)

    def get(self) -> str:   return self.var.get().strip()
    def set(self, v: str):  self.var.set(v or "")
    def clear(self):        self.var.set("")


class LabeledCombobox(tk.Frame):
    def __init__(self, parent, label: str, values: list, **kw):
        super().__init__(parent, bg=CLR_CARD)
        tk.Label(self, text=label, bg=CLR_CARD,
                 fg=CLR_SUBTEXT, font=FONT_SMALL).pack(anchor="w")
        self.var = tk.StringVar()
        self.combo = ttk.Combobox(self, textvariable=self.var,
                                  values=values, state="readonly", **kw)
        self.combo.pack(fill="x")

    def get(self) -> str:   return self.var.get()
    def set(self, v: str):  self.var.set(v or "")


class StatusBar(tk.Label):
    def __init__(self, parent):
        super().__init__(parent, text="Ready", anchor="w",
                         bg=CLR_SIDEBAR, fg=CLR_SUBTEXT, font=FONT_SMALL, padx=10)

    def info(self, msg: str):
        self.config(text=f"ℹ  {msg}", fg=CLR_ACCENT)
        self.after(5000, self._reset)

    def success(self, msg: str):
        self.config(text=f"✅  {msg}", fg=CLR_SUCCESS)
        self.after(5000, self._reset)

    def error(self, msg: str):
        self.config(text=f"❌  {msg}", fg=CLR_DANGER)
        self.after(8000, self._reset)

    def _reset(self):
        self.config(text="Ready", fg=CLR_SUBTEXT)


class DataTable(tk.Frame):
    def __init__(self, parent, columns: list[tuple], **kw):
        super().__init__(parent, bg=CLR_BG, **kw)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=CLR_CARD, foreground=CLR_TEXT,
                        rowheight=26, fieldbackground=CLR_CARD,
                        font=FONT_BODY, borderwidth=0)
        style.configure("Treeview.Heading",
                        background=CLR_HEADER_BG, foreground=CLR_TEXT,
                        font=FONT_HEADER, relief="flat")
        style.map("Treeview",
                  background=[("selected", CLR_ACCENT)],
                  foreground=[("selected", "#1e1e2e")])

        col_ids = [c[0] for c in columns]
        self.tree = ttk.Treeview(self, columns=col_ids, show="headings",
                                 selectmode="browse")
        for col_id, name, width, anchor in columns:
            self.tree.heading(col_id, text=name)
            self.tree.column(col_id, width=width, anchor=anchor, minwidth=50)

        vsb = ttk.Scrollbar(self, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def clear(self):
        self.tree.delete(*self.tree.get_children())

    def insert(self, values: tuple, tags=()):
        self.tree.insert("", "end", values=values, tags=tags)

    def selected_values(self) -> tuple | None:
        sel = self.tree.selection()
        return self.tree.item(sel[0], "values") if sel else None

    def bind_select(self, cb):  self.tree.bind("<<TreeviewSelect>>", cb)
    def bind_double(self, cb):  self.tree.bind("<Double-1>", cb)