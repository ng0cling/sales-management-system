"""
PROJECT 03: SALES MANAGEMENT SYSTEM
File: gui/app.py
Sidebar navigation and main App window. Entry point: python -m gui.app
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tkinter as tk
from tkinter import ttk

from gui.constants import (
    CLR_BG, CLR_SIDEBAR, CLR_CARD, CLR_ACCENT, CLR_TEXT, CLR_SUBTEXT,
    FONT_BODY, FONT_SMALL,
)
from gui.widgets import StatusBar
from gui.panels import (
    CustomersPanel, ProductsPanel, OrdersPanel,
    EmployeesPanel, ReportsPanel, BasePanel,
)

NAV_ITEMS = [
    ("👤  Customers", "customers"),
    ("📦  Products",  "products"),
    ("🛒  Orders",    "orders"),
    ("🧑‍💼  Employees", "employees"),
    ("📊  Reports",   "reports"),
]


class Sidebar(tk.Frame):
    def __init__(self, parent, on_select):
        super().__init__(parent, bg=CLR_SIDEBAR, width=190)
        self.pack_propagate(False)
        self._on_select  = on_select
        self._active_key = None
        self._buttons    = {}

        tk.Label(self, text="🏪  Sales\nManagement",
                 bg=CLR_SIDEBAR, fg=CLR_ACCENT,
                 font=("Segoe UI", 13, "bold"),
                 justify="left", pady=20, padx=16).pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=4)

        for label, key in NAV_ITEMS:
            btn = tk.Button(
                self, text=f"  {label}", anchor="w",
                font=FONT_BODY, bg=CLR_SIDEBAR, fg=CLR_TEXT,
                relief="flat", padx=10, pady=10, cursor="hand2",
                activebackground=CLR_CARD, activeforeground=CLR_ACCENT,
                command=lambda k=key: self._select(k),
            )
            btn.pack(fill="x")
            self._buttons[key] = btn

    def _select(self, key: str):
        if self._active_key:
            self._buttons[self._active_key].config(bg=CLR_SIDEBAR, fg=CLR_TEXT)
        self._active_key = key
        self._buttons[key].config(bg=CLR_ACCENT, fg="#1e1e2e")
        self._on_select(key)

    def select_default(self):
        self._select(NAV_ITEMS[0][1])


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sales Management System")
        self.geometry("1280x760")
        self.minsize(900, 580)
        self.configure(bg=CLR_BG)

        self.status_bar = StatusBar(self)
        self.status_bar.pack(side="bottom", fill="x")

        container = tk.Frame(self, bg=CLR_BG)
        container.pack(fill="both", expand=True)

        self.sidebar = Sidebar(container, self._show_panel)
        self.sidebar.pack(side="left", fill="y")

        self.content = tk.Frame(container, bg=CLR_BG)
        self.content.pack(side="left", fill="both", expand=True)

        self._panels: dict[str, BasePanel] = {
            "customers": CustomersPanel(self.content, self.status_bar),
            "products":  ProductsPanel(self.content,  self.status_bar),
            "orders":    OrdersPanel(self.content,    self.status_bar),
            "employees": EmployeesPanel(self.content, self.status_bar),
            "reports":   ReportsPanel(self.content,   self.status_bar),
        }

        self._current: BasePanel | None = None
        self.sidebar.select_default()

    def _show_panel(self, key: str):
        if self._current:
            self._current.pack_forget()
        panel = self._panels[key]
        panel.pack(fill="both", expand=True)
        self._current = panel


if __name__ == "__main__":
    app = App()
    app.mainloop()