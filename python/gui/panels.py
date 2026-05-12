"""
PROJECT 03: SALES MANAGEMENT SYSTEM
File: gui/panels.py
All main panels: BasePanel, CustomersPanel, ProductsPanel, OrdersPanel, EmployeesPanel, ReportsPanel.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal, InvalidOperation
from datetime import date
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from csv_export import export_csv

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from models import (
    Customer, CustomerRepository,
    Employee, EmployeeRepository,
    Product, ProductRepository,
    OrderRepository,
)
from gui.constants import (
    CLR_BG, CLR_CARD, CLR_ACCENT, CLR_SUCCESS, CLR_DANGER, CLR_WARNING,
    CLR_TEXT, CLR_SUBTEXT, CLR_HEADER_BG, CLR_SIDEBAR,
    FONT_TITLE, FONT_HEADER, FONT_BODY, FONT_SMALL,
    ORDER_STATUSES, ORDER_TRANSITIONS,
    fmt_vnd, run_in_thread,
)
from gui.widgets import StyledButton, LabeledEntry, DataTable, StatusBar
from gui.dialogs import (
    CustomerDialog, ProductDialog, EmployeeDialog,
    CreateOrderDialog, AddProductDialog, EditQuantityDialog,
    RestockDialog, OrderDetailWindow,
)

customer_repo = CustomerRepository()
employee_repo = EmployeeRepository()
product_repo  = ProductRepository()
order_repo    = OrderRepository()

class BasePanel(tk.Frame):
    def __init__(self, parent, status_bar: StatusBar):
        super().__init__(parent, bg=CLR_BG)
        self.status = status_bar
        self._build()

    def _build(self):
        raise NotImplementedError

    def _toolbar(self, buttons: list[tuple]) -> tk.Frame:
        bar = tk.Frame(self, bg=CLR_BG, pady=8, padx=12)
        bar.pack(fill="x")
        for text, kind, cmd in buttons:
            StyledButton(bar, text, command=cmd, kind=kind).pack(side="left", padx=4)
        return bar


# ─── CUSTOMERS PANEL ──────────────────────────────────────────────────────────

class CustomersPanel(BasePanel):
    def _build(self):
        tk.Label(self, text="👤  Customer Management",
                 bg=CLR_BG, fg=CLR_ACCENT, font=FONT_TITLE,
                 pady=10).pack(anchor="w", padx=14)

        search_frame = tk.Frame(self, bg=CLR_BG, padx=12, pady=4)
        search_frame.pack(fill="x")
        tk.Label(search_frame, text="Search:", bg=CLR_BG,
                 fg=CLR_TEXT, font=FONT_BODY).pack(side="left")
        self._search_var = tk.StringVar()
        se = tk.Entry(search_frame, textvariable=self._search_var,
                      bg=CLR_CARD, fg=CLR_TEXT, insertbackground=CLR_TEXT,
                      relief="flat", font=FONT_BODY, width=30)
        se.pack(side="left", padx=8, ipady=4)
        se.bind("<Return>", lambda _: self._search())
        StyledButton(search_frame, "🔍 Search", command=self._search,
                     kind="primary").pack(side="left")
        StyledButton(search_frame, "↺ Refresh", command=self.load,
                     kind="neutral").pack(side="left", padx=6)

        self._toolbar([
            ("➕ Add Customer",  "success", self._add),
            ("✏️ Edit",          "primary", self._edit),
            ("🗑️ Delete",        "danger",  self._delete),
            ("💰 View Spending", "warning", self._total_spend),
        ])

        self.table = DataTable(self, [
            ("id",    "ID",        60,  "center"),
            ("name",  "Full Name", 220, "w"),
            ("phone", "Phone",     130, "center"),
            ("email", "Email",     200, "w"),
            ("addr",  "Address",   230, "w"),
        ])
        self.table.pack(fill="both", expand=True, padx=12, pady=8)
        self.load()

    def load(self):
        def task():
            return customer_repo.get_all()

        def callback(rows, err):
            self.table.clear()
            if err:
                self.status.error(str(err))
                return
            for r in (rows or []):
                self.table.insert((
                    r["CustomerID"], r["CustomerName"],
                    r.get("PhoneNumber", ""),
                    r.get("Email", "") or "",
                    r.get("Address", "") or "",
                ))
            self.status.info(f"Loaded {len(rows or [])} customers.")

        run_in_thread(task, callback)

    def _search(self):
        kw = self._search_var.get().strip()

        def task():
            return customer_repo.search(kw) if kw else customer_repo.get_all()

        def callback(rows, err):
            self.table.clear()
            if err:
                self.status.error(str(err))
                return
            for r in (rows or []):
                self.table.insert((
                    r["CustomerID"], r["CustomerName"],
                    r.get("PhoneNumber", ""),
                    r.get("Email", "") or "",
                    r.get("Address", "") or "",
                ))
            self.status.info(f"Found {len(rows or [])} customers.")

        run_in_thread(task, callback)

    def _selected_id(self) -> int | None:
        vals = self.table.selected_values()
        if not vals:
            messagebox.showinfo("No selection", "Please select a customer.")
            return None
        return int(vals[0])

    def _add(self):
        dlg = CustomerDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            try:
                cid = customer_repo.create(Customer(customer_id=None, **dlg.result))
                self.status.success(f"Added customer ID={cid}")
                self.load()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _edit(self):
        cid = self._selected_id()
        if cid is None:
            return
        row = customer_repo.get_by_id(cid)
        dlg = CustomerDialog(self, row)
        self.wait_window(dlg)
        if dlg.result:
            try:
                customer_repo.update(Customer(customer_id=cid, **dlg.result))
                self.status.success(f"Updated customer ID={cid}")
                self.load()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _delete(self):
        cid = self._selected_id()
        if cid is None:
            return
        if messagebox.askyesno("Confirm deletion",
                               f"Are you sure you want to delete customer ID={cid}?"):
            try:
                customer_repo.delete(cid)
                self.status.success(f"Deleted customer ID={cid}")
                self.load()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _total_spend(self):
        cid = self._selected_id()
        if cid is None:
            return
        try:
            spend = customer_repo.total_spend(cid)
            row   = customer_repo.get_by_id(cid)
            name  = row["CustomerName"] if row else f"ID {cid}"
            messagebox.showinfo("Total spending",
                                f"Customer: {name}\nTotal spending: {fmt_vnd(spend)}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ─── PRODUCTS PANEL ───────────────────────────────────────────────────────────

class ProductsPanel(BasePanel):
    def _build(self):
        tk.Label(self, text="📦  Product Management",
                 bg=CLR_BG, fg=CLR_ACCENT, font=FONT_TITLE,
                 pady=10).pack(anchor="w", padx=14)

        # ── Search bar ────────────────────────────────────────────────────────
        search_frame = tk.Frame(self, bg=CLR_BG, padx=12, pady=4)
        search_frame.pack(fill="x")
        tk.Label(search_frame, text="Search:", bg=CLR_BG,
                 fg=CLR_TEXT, font=FONT_BODY).pack(side="left")
        self._search_var = tk.StringVar()
        se = tk.Entry(search_frame, textvariable=self._search_var,
                      bg=CLR_CARD, fg=CLR_TEXT, insertbackground=CLR_TEXT,
                      relief="flat", font=FONT_BODY, width=30)
        se.pack(side="left", padx=8, ipady=4)
        se.bind("<Return>", lambda _: self._search())
        StyledButton(search_frame, "🔍 Search", command=self._search,
                     kind="primary").pack(side="left")
        StyledButton(search_frame, "↺ Refresh", command=self.load,
                     kind="neutral").pack(side="left", padx=6)

        self._toolbar([
            ("➕ Add Product", "success", self._add),
            ("✏️ Edit",        "primary", self._edit),
            ("🗑️ Delete",      "danger",  self._delete),
            ("📥 Restock",     "warning", self._restock),
            ("⚠️ Low Stock",   "warning", self._low_stock),
        ])

        self.table = DataTable(self, [
            ("id",    "ID",           60,  "center"),
            ("name",  "Product Name", 250, "w"),
            ("price", "Price (VND)",  150, "e"),
            ("stock", "Stock",         90, "center"),
            ("cat",   "Category",     150, "w"),
        ])
        self.table.pack(fill="both", expand=True, padx=12, pady=8)
        self.load()

    def _populate(self, rows: list[dict]):
        self.table.clear()
        for r in rows:
            tags = ("low",) if int(r["StockQuantity"]) <= 5 else ()
            self.table.insert((
                r["ProductID"], r["ProductName"],
                fmt_vnd(r["Price"]),
                r["StockQuantity"],
                r.get("Category", "") or "",
            ), tags=tags)
        self.table.tree.tag_configure("low", foreground=CLR_WARNING)

    def load(self):
        def task():
            return product_repo.get_all()

        def callback(rows, err):
            if err:
                self.status.error(str(err))
                return
            self._populate(rows or [])
            self.status.info(f"Loaded {len(rows or [])} products.")

        run_in_thread(task, callback)

    def _search(self):
        kw = self._search_var.get().strip()

        def task():
            return product_repo.search(kw) if kw else product_repo.get_all()

        def callback(rows, err):
            if err:
                self.status.error(str(err))
                return
            self._populate(rows or [])
            self.status.info(f"Found {len(rows or [])} products.")

        run_in_thread(task, callback)

    def _selected_id(self) -> int | None:
        vals = self.table.selected_values()
        if not vals:
            messagebox.showinfo("No selection", "Please select a product.")
            return None
        return int(vals[0])

    def _add(self):
        dlg = ProductDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            try:
                pid = product_repo.create(Product(product_id=None, **dlg.result))
                self.status.success(f"Added product ID={pid}")
                self.load()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _edit(self):
        pid = self._selected_id()
        if pid is None:
            return
        row = product_repo.get_by_id(pid)
        dlg = ProductDialog(self, row)
        self.wait_window(dlg)
        if dlg.result:
            try:
                product_repo.update(Product(product_id=pid, **dlg.result))
                self.status.success(f"Updated product ID={pid}")
                self.load()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _delete(self):
        pid = self._selected_id()
        if pid is None:
            return
        if messagebox.askyesno("Confirm deletion",
                               f"Are you sure you want to delete product ID={pid}?"):
            try:
                product_repo.delete(pid)
                self.status.success(f"Deleted product ID={pid}")
                self.load()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _restock(self):
        pid = self._selected_id()
        if pid is None:
            return
        row = product_repo.get_by_id(pid)
        dlg = RestockDialog(self, row["ProductName"] if row else f"ID {pid}")
        self.wait_window(dlg)
        if dlg.result:
            try:
                product_repo.restock(pid, dlg.result)
                self.status.success(f"Added {dlg.result} units to stock.")
                self.load()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _low_stock(self):
        def task():
            return product_repo.get_low_stock()

        def callback(rows, err):
            if err:
                self.status.error(str(err))
                return
            win = tk.Toplevel(self)
            win.title("⚠️  Low Stock Products")
            win.configure(bg=CLR_BG)
            win.geometry("560x380")
            tk.Label(win, text="⚠️  Low Stock Products",
                     bg=CLR_BG, fg=CLR_WARNING, font=FONT_TITLE, pady=10).pack()
            tbl = DataTable(win, [
                ("id",    "ID",       60,  "center"),
                ("name",  "Product", 260,  "w"),
                ("stock", "Stock",    90,  "center"),
                ("cat",   "Category",130,  "w"),
            ])
            tbl.pack(fill="both", expand=True, padx=12, pady=8)
            for r in (rows or []):
                tbl.insert((
                    r.get("ProductID", ""),
                    r.get("ProductName", ""),
                    r.get("StockQuantity", ""),
                    r.get("Category", ""),
                ))
            tk.Label(win, text=f"{len(rows or [])} products need restocking",
                     bg=CLR_BG, fg=CLR_SUBTEXT, font=FONT_SMALL).pack(pady=4)

        run_in_thread(task, callback)


# ─── ORDERS PANEL ─────────────────────────────────────────────────────────────

class OrdersPanel(BasePanel):
    def _build(self):
        tk.Label(self, text="🛒  Order Management",
                 bg=CLR_BG, fg=CLR_ACCENT, font=FONT_TITLE,
                 pady=10).pack(anchor="w", padx=14)

        # ── Search + Filter bar ───────────────────────────────────────────────
        filter_frame = tk.Frame(self, bg=CLR_BG, padx=12, pady=4)
        filter_frame.pack(fill="x")

        tk.Label(filter_frame, text="Search:", bg=CLR_BG,
                 fg=CLR_TEXT, font=FONT_BODY).pack(side="left")
        self._search_var = tk.StringVar()
        se = tk.Entry(filter_frame, textvariable=self._search_var,
                      bg=CLR_CARD, fg=CLR_TEXT, insertbackground=CLR_TEXT,
                      relief="flat", font=FONT_BODY, width=24)
        se.pack(side="left", padx=(6, 12), ipady=4)
        se.bind("<Return>", lambda _: self._search())

        tk.Label(filter_frame, text="Status:", bg=CLR_BG,
                 fg=CLR_TEXT, font=FONT_BODY).pack(side="left")
        self._status_var = tk.StringVar(value="All")
        status_cb = ttk.Combobox(
            filter_frame, textvariable=self._status_var,
            values=["All"] + ORDER_STATUSES,
            state="readonly", width=13, font=FONT_BODY,
        )
        status_cb.pack(side="left", padx=6, ipady=3)
        status_cb.bind("<<ComboboxSelected>>", lambda _: self._search())

        StyledButton(filter_frame, "🔍 Search", command=self._search,
                     kind="primary").pack(side="left", padx=(8, 4))
        StyledButton(filter_frame, "↺ Refresh", command=self.load,
                     kind="neutral").pack(side="left")

        self._toolbar([
            ("➕ Create Order",   "success", self._create_order),
            ("🔎 Order Details",  "neutral", self._view_details),
            ("🔄 Change Status",  "primary", self._update_status),
            ("💸 Apply Discount", "neutral", self._apply_discount),
            ("🗑️ Delete Order",   "danger",  self._delete_order),
        ])

        self.table = DataTable(self, [
            ("id",       "ID",          60,  "center"),
            ("customer", "Customer",   200,  "w"),
            ("emp",      "Sales Rep",  150,  "w"),
            ("status",   "Status",     110,  "center"),
            ("date",     "Order Date", 110,  "center"),
            ("total",    "Total",      140,  "e"),
        ])
        self.table.pack(fill="both", expand=True, padx=12, pady=8)

        self.table.tree.tag_configure("Pending",    foreground=CLR_WARNING)
        self.table.tree.tag_configure("Processing", foreground=CLR_ACCENT)
        self.table.tree.tag_configure("Shipped",    foreground="#89dceb")
        self.table.tree.tag_configure("Delivered",  foreground=CLR_SUCCESS)
        self.table.tree.tag_configure("Cancelled",  foreground=CLR_DANGER)
        self.load()

    def _populate(self, rows: list[dict]):
        self.table.clear()
        for r in rows:
            status = r.get("Status", "")
            date_s = str(r.get("OrderDate", ""))[:10]
            self.table.insert((
                r["OrderID"],
                r.get("CustomerName", ""),
                r.get("SalesRep", "") or "—",
                status, date_s,
                fmt_vnd(r.get("TotalAmount", 0)),
            ), tags=(status,))

    def load(self):
        self._search_var.set("")
        self._status_var.set("All")

        def task():
            return order_repo.get_all()

        def callback(rows, err):
            if err:
                self.status.error(str(err))
                return
            self._populate(rows or [])
            self.status.info(f"Loaded {len(rows or [])} orders.")

        run_in_thread(task, callback)

    def _search(self):
        kw     = self._search_var.get().strip()
        status = self._status_var.get()

        def task():
            return order_repo.search(
                keyword=kw,
                status=status if status != "All" else "",
            )

        def callback(rows, err):
            if err:
                self.status.error(str(err))
                return
            self._populate(rows or [])
            if kw:
                self.status.info(f"Found {len(rows)} orders matching '{kw}'.")
            elif status != "All":
                self.status.info(f"Found {len(rows)} orders with status '{status}'.")
            else:
                self.status.info(f"Loaded {len(rows)} orders.")

        run_in_thread(task, callback)

    def _selected_id(self) -> int | None:
        vals = self.table.selected_values()
        if not vals:
            messagebox.showinfo("No selection", "Please select an order.")
            return None
        return int(vals[0])

    def _create_order(self):
        dlg = CreateOrderDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            try:
                d   = dlg.result
                oid = order_repo.create(d["customer_id"], d["employee_id"], d["notes"])
                self.status.success(f"Created order #{oid}.")
                self.load()
                if messagebox.askyesno("Add products",
                                       f"Order #{oid} created.\n"
                                       "Do you want to add products now?"):
                    OrderDetailWindow(self, oid, self.status, on_close=self.load)
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _update_status(self):
        oid = self._selected_id()
        if oid is None:
            return
        order = order_repo.get_by_id(oid)
        if not order:
            messagebox.showerror("Error", "Order not found.")
            return

        win = tk.Toplevel(self)
        win.title(f"Update status of order #{oid}")
        win.configure(bg=CLR_CARD)
        win.geometry("360x260")

        tk.Label(win, text=f"Order #{oid} — Current status: {order['Status']}",
                 bg=CLR_CARD, fg=CLR_TEXT, font=FONT_HEADER, pady=10).pack()
        tk.Label(win, text="Select new status:",
                 bg=CLR_CARD, fg=CLR_SUBTEXT, font=FONT_SMALL).pack(pady=4)

        # Dùng ORDER_TRANSITIONS constant — single source of truth cho toàn app
        available = ORDER_TRANSITIONS.get(order["Status"], [])
        var = tk.StringVar(value=available[0] if available else "")
        for s in available:
            tk.Radiobutton(win, text=s, variable=var, value=s,
                           bg=CLR_CARD, fg=CLR_TEXT, selectcolor=CLR_SIDEBAR,
                           font=FONT_BODY).pack(anchor="w", padx=40, pady=3)

        def do_update():
            new_status = var.get()
            if not new_status:
                messagebox.showwarning("No option",
                                       "This status cannot be changed further.",
                                       parent=win)
                return
            try:
                order_repo.update_status(oid, new_status)
                self.status.success(f"Order #{oid} → {new_status}")
                self.load()
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)

        StyledButton(win, "✅ Update", command=do_update, kind="primary").pack(pady=12)

    def _view_details(self):
        oid = self._selected_id()
        if oid is None:
            return
        OrderDetailWindow(self, oid, self.status, on_close=self.load)

    def _apply_discount(self):
        oid = self._selected_id()
        if oid is None:
            return
        total = order_repo.order_total(oid)
        if total == 0:
            messagebox.showinfo("Information", "Order is empty or not found.")
            return
        pct_str = simpledialog.askstring(
            "Discount",
            f"Order #{oid} total: {fmt_vnd(total)}\n\n"
            "Enter discount percentage (0–100):",
            parent=self)
        if pct_str is None:
            return
        try:
            pct       = Decimal(pct_str)
            discounted = order_repo.apply_discount(total, pct)
            saving    = total - discounted
            messagebox.showinfo(
                "Discount preview",
                f"Original total:  {fmt_vnd(total)}\n"
                f"Discount ({pct}%):  -{fmt_vnd(saving)}\n"
                f"Final amount:      {fmt_vnd(discounted)}\n\n"
                "⚠ This is a preview — not saved to the database.",
            )
        except (InvalidOperation, Exception) as e:
            messagebox.showerror("Error", str(e))

    def _delete_order(self):
        oid = self._selected_id()
        if oid is None:
            return
        order = order_repo.get_by_id(oid)
        if order and order["Status"] != "Cancelled":
            messagebox.showwarning("Cannot delete",
                                   "Only cancelled orders can be deleted.")
            return
        if messagebox.askyesno("Confirm deletion",
                               f"Permanently delete order #{oid}?"):
            try:
                order_repo.delete_order(oid)
                self.status.success(f"Deleted order #{oid}.")
                self.load()
            except Exception as e:
                messagebox.showerror("Error", str(e))


# ─── EMPLOYEES PANEL ──────────────────────────────────────────────────────────

class EmployeesPanel(BasePanel):
    def _build(self):
        tk.Label(self, text="🧑‍💼  Employee Management",
                 bg=CLR_BG, fg=CLR_ACCENT, font=FONT_TITLE,
                 pady=10).pack(anchor="w", padx=14)

        self._toolbar([
            ("➕ Add Employee", "success", self._add),
            ("✏️ Edit",         "primary", self._edit),
            ("🗑️ Delete",       "danger",  self._delete),
            ("↺ Refresh",       "neutral", self.load),
        ])

        self.table = DataTable(self, [
            ("id",    "ID",        60,  "center"),
            ("name",  "Full Name", 220, "w"),
            ("title", "Job Title", 180, "w"),
            ("email", "Email",     220, "w"),
            ("phone", "Phone",     130, "center"),
        ])
        self.table.pack(fill="both", expand=True, padx=12, pady=8)
        self.load()

    def load(self):
        def task():
            return employee_repo.get_all()

        def callback(rows, err):
            self.table.clear()
            if err:
                self.status.error(str(err))
                return
            for r in (rows or []):
                self.table.insert((
                    r["EmployeeID"], r["EmployeeName"], r["JobTitle"],
                    r.get("Email", "") or "",
                    r.get("PhoneNumber", "") or "",
                ))
            self.status.info(f"Loaded {len(rows or [])} employees.")

        run_in_thread(task, callback)

    def _selected_id(self) -> int | None:
        vals = self.table.selected_values()
        if not vals:
            messagebox.showinfo("No selection", "Please select an employee.")
            return None
        return int(vals[0])

    def _add(self):
        dlg = EmployeeDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            try:
                eid = employee_repo.create(Employee(employee_id=None, **dlg.result))
                self.status.success(f"Added employee ID={eid}")
                self.load()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _edit(self):
        eid = self._selected_id()
        if eid is None:
            return
        row = employee_repo.get_by_id(eid)
        dlg = EmployeeDialog(self, row)
        self.wait_window(dlg)
        if dlg.result:
            try:
                employee_repo.update(Employee(employee_id=eid, **dlg.result))
                self.status.success(f"Updated employee ID={eid}")
                self.load()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _delete(self):
        eid = self._selected_id()
        if eid is None:
            return
        if messagebox.askyesno("Confirm deletion",
                               f"Are you sure you want to delete employee ID={eid}?"):
            try:
                employee_repo.delete(eid)
                self.status.success(f"Deleted employee ID={eid}")
                self.load()
            except Exception as e:
                messagebox.showerror("Error", str(e))


# ─── REPORTS PANEL ────────────────────────────────────────────────────────────

class ReportsPanel(BasePanel):
    def _build(self):
        tk.Label(self, text="📊  Reports & Analytics",
                 bg=CLR_BG, fg=CLR_ACCENT, font=FONT_TITLE,
                 pady=10).pack(anchor="w", padx=14)

        nb_frame = tk.Frame(self, bg=CLR_BG)
        nb_frame.pack(fill="both", expand=True, padx=12, pady=6)

        style = ttk.Style()
        style.configure("Report.TNotebook",     background=CLR_BG, borderwidth=0)
        style.configure("Report.TNotebook.Tab", background=CLR_CARD, foreground=CLR_TEXT,
                         padding=[14, 6], font=FONT_BODY)
        style.map("Report.TNotebook.Tab",
                  background=[("selected", CLR_ACCENT)],
                  foreground=[("selected", "#1e1e2e")])

        self.nb = ttk.Notebook(nb_frame, style="Report.TNotebook")
        self.nb.pack(fill="both", expand=True)

        self._build_dashboard_tab()
        self._build_daily_tab()
        self._build_monthly_tab()
        self._build_top_customers_tab()
        self._build_product_perf_tab()          # ← was missing, now added

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def _build_dashboard_tab(self):
        tab = tk.Frame(self.nb, bg=CLR_BG)
        self.nb.add(tab, text="📊  Dashboard")

        ctrl = tk.Frame(tab, bg=CLR_BG, pady=8, padx=12)
        ctrl.pack(fill="x")
        StyledButton(ctrl, "🔄 Refresh Dashboard",
                     command=self._load_dashboard, kind="primary").pack(side="left")
        self._dash_status = tk.Label(ctrl, text="", bg=CLR_BG,
                                     fg=CLR_SUBTEXT, font=FONT_SMALL)
        self._dash_status.pack(side="left", padx=12)

        kpi_row = tk.Frame(tab, bg=CLR_BG, padx=12)
        kpi_row.pack(fill="x", pady=(0, 6))
        self._kpi_frames = {}
        for key, label, color in [
            ("total_orders",    "Total Orders",    CLR_ACCENT),
            ("total_revenue",   "Total Revenue",   CLR_SUCCESS),
            ("avg_order",       "Avg Order Value", CLR_WARNING),
            ("total_customers", "Total Customers", "#cba6f7"),
        ]:
            card = tk.Frame(kpi_row, bg=CLR_CARD, padx=18, pady=12,
                            highlightbackground=color, highlightthickness=2)
            card.pack(side="left", expand=True, fill="x", padx=5)
            tk.Label(card, text=label, bg=CLR_CARD, fg=color, font=FONT_SMALL).pack(anchor="w")
            val_lbl = tk.Label(card, text="—", bg=CLR_CARD, fg=CLR_TEXT, font=FONT_TITLE)
            val_lbl.pack(anchor="w")
            self._kpi_frames[key] = val_lbl

        self._dash_canvas_frame = tk.Frame(tab, bg=CLR_BG)
        self._dash_canvas_frame.pack(fill="both", expand=True, padx=12, pady=4)

        # Load once when tab becomes visible (guard against repeated fires)
        self._dashboard_loaded = False
        def _on_visible(e):
            if not self._dashboard_loaded:
                self._load_dashboard()
        tab.bind("<Visibility>", _on_visible)

    def _load_dashboard(self):
        canvas_frame = self._dash_canvas_frame

        if not HAS_MATPLOTLIB:
            for w in canvas_frame.winfo_children():
                w.destroy()
            tk.Label(canvas_frame,
                     text="⚠  matplotlib not installed.\npip install matplotlib",
                     bg=CLR_BG, fg=CLR_WARNING, font=FONT_HEADER).pack(pady=40)
            return

        self._dash_status.config(text="Loading...", fg=CLR_ACCENT)
        self._dashboard_loaded = False
        canvas_frame.update_idletasks()

        # ── Bước 1: fetch data trên background thread ──────────────────────────
        def fetch():
            return {
                "daily_rows": order_repo.daily_summary(),
                "top_custs":  customer_repo.get_top_customers(6),
                "perf_rows":  product_repo.performance(),
                "all_orders": order_repo.get_all(),
                "all_custs":  customer_repo.get_all(),
            }

        # ── Bước 2: render chart trên main thread (Tkinter/matplotlib yêu cầu) ─
        def render(data, err):
            if err:
                self._dash_status.config(text=f"Error: {err}", fg=CLR_DANGER)
                return

            try:
                daily_rows  = data["daily_rows"]
                top_custs   = data["top_custs"]
                perf_rows   = data["perf_rows"]
                all_orders  = data["all_orders"]

                # KPIs
                total_orders    = len(all_orders)
                total_revenue   = sum(float(r.get("DailyRevenue") or 0) for r in daily_rows)
                avg_order       = total_revenue / total_orders if total_orders else 0
                total_customers = len(data["all_custs"])

                self._kpi_frames["total_orders"].config(text=str(total_orders))
                self._kpi_frames["total_revenue"].config(text=fmt_vnd(total_revenue))
                self._kpi_frames["avg_order"].config(text=fmt_vnd(avg_order))
                self._kpi_frames["total_customers"].config(text=str(total_customers))

                # Status breakdown for pie
                status_counts = {}
                for r in all_orders:
                    s = r.get("Status", "Unknown")
                    status_counts[s] = status_counts.get(s, 0) + 1

                # Revenue trend (last 10 days)
                trend_rows    = sorted(daily_rows, key=lambda r: str(r.get("SaleDate", "")))[-10:]
                trend_dates   = [str(r.get("SaleDate", ""))[:10] for r in trend_rows]
                trend_revenue = [float(r.get("DailyRevenue") or 0) for r in trend_rows]

                # Top products
                top_prods  = perf_rows[:6]
                prod_names = [str(r.get("ProductName", ""))[:22] for r in top_prods]
                prod_sold  = [int(r.get("TotalSold") or 0) for r in top_prods]

                # Top customers
                cust_names = [str(r.get("CustomerName", ""))[:14] for r in top_custs]
                cust_spend = [float(r.get("TotalSpend") or 0) for r in top_custs]

                # Clear old chart widgets
                for widget in canvas_frame.winfo_children():
                    widget.destroy()

                BG     = "#1e1e2e"
                CARD   = "#313244"
                ACCENT = "#89b4fa"

                fig = plt.figure(figsize=(13, 6), facecolor=BG)
                gs  = gridspec.GridSpec(2, 3, figure=fig,
                                        hspace=0.60, wspace=0.45,
                                        left=0.22, right=0.97,
                                        top=0.93,  bottom=0.14)

                ax1 = fig.add_subplot(gs[0, :2])
                ax2 = fig.add_subplot(gs[0, 2])
                ax3 = fig.add_subplot(gs[1, :2])
                ax4 = fig.add_subplot(gs[1, 2])

                COLORS = ["#89b4fa","#a6e3a1","#fab387","#f38ba8","#cba6f7","#89dceb"]

                def style_ax(ax, title):
                    ax.set_facecolor(CARD)
                    ax.tick_params(colors="#a6adc8", labelsize=7.5)
                    ax.set_title(title, color="#cdd6f4", fontsize=9, fontweight="bold", pad=6)
                    for spine in ax.spines.values():
                        spine.set_edgecolor("#45475a")

                # Chart 1: Revenue trend
                style_ax(ax1, "📈 Revenue Trend (Recent Days)")
                if trend_revenue:
                    ax1.plot(trend_dates, trend_revenue, color=ACCENT,
                             linewidth=2, marker="o", markersize=5)
                    ax1.fill_between(trend_dates, trend_revenue, alpha=0.15, color=ACCENT)
                    ax1.yaxis.set_major_formatter(
                        plt.FuncFormatter(lambda x, _: f"{x/1e6:.0f}M"))
                    ax1.set_xticklabels(trend_dates, rotation=30, ha="right", fontsize=7)
                    ax1.grid(axis="y", color="#45475a", linewidth=0.5, linestyle="--")
                else:
                    ax1.text(0.5, 0.5, "No data", ha="center", va="center",
                             color="#a6adc8", transform=ax1.transAxes)

                # Chart 2: Status pie
                style_ax(ax2, "🥧 Order Status")
                if status_counts:
                    sc = {"Pending":"#fab387","Processing":"#89b4fa","Shipped":"#89dceb",
                          "Delivered":"#a6e3a1","Cancelled":"#f38ba8"}
                    pie_labels = list(status_counts.keys())
                    pie_vals   = list(status_counts.values())
                    pie_colors = [sc.get(l, "#cba6f7") for l in pie_labels]
                    _, texts, autotexts = ax2.pie(
                        pie_vals, labels=pie_labels, colors=pie_colors,
                        autopct="%1.0f%%", startangle=90,
                        textprops={"color": "#cdd6f4", "fontsize": 7.5},
                        wedgeprops={"linewidth": 0.5, "edgecolor": BG},
                    )
                    for at in autotexts:
                        at.set_color("#1e1e2e"); at.set_fontsize(7)

                # Chart 3: Top products bar
                style_ax(ax3, "📦 Top Products by Units Sold")
                if prod_names:
                    bars = ax3.barh(prod_names[::-1], prod_sold[::-1],
                                    color=COLORS[:len(prod_names)], height=0.6)
                    ax3.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
                    ax3.set_xlabel("Units Sold", color="#a6adc8", fontsize=7.5)
                    ax3.grid(axis="x", color="#45475a", linewidth=0.5, linestyle="--")
                    for bar, val in zip(bars, prod_sold[::-1]):
                        if val > 0:
                            ax3.text(bar.get_width() + 0.05,
                                     bar.get_y() + bar.get_height() / 2,
                                     str(val), va="center", color="#cdd6f4", fontsize=7.5)

                # Chart 4: Top customers
                style_ax(ax4, "🏆 Top Customers")
                if cust_names:
                    ax4.barh(cust_names[::-1], cust_spend[::-1], color="#cba6f7", height=0.6)
                    ax4.xaxis.set_major_formatter(
                        plt.FuncFormatter(lambda x, _: f"{x/1e6:.0f}M"))
                    ax4.set_xlabel("Spend (VND)", color="#a6adc8", fontsize=7.5)
                    ax4.grid(axis="x", color="#45475a", linewidth=0.5, linestyle="--")

                canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)
                plt.close(fig)

                self._dash_status.config(text="Last updated just now", fg="#a6adc8")
                self._dashboard_loaded = True

            except Exception as e:
                self._dash_status.config(text=f"Error: {e}", fg=CLR_DANGER)

        run_in_thread(fetch, render)

    # ── Daily Sales ────────────────────────────────────────────────────────────

    def _build_daily_tab(self):
        tab = tk.Frame(self.nb, bg=CLR_BG)
        self.nb.add(tab, text="📅  Daily Sales")

        ctrl = tk.Frame(tab, bg=CLR_BG, pady=10, padx=12)
        ctrl.pack(fill="x")
        StyledButton(ctrl, "🔄 Load Report",
                     command=self._load_daily, kind="primary").pack(side="left")
        StyledButton(ctrl, "📄 Export CSV",
                     command=self._export_daily_csv, kind="secondary").pack(side="left", padx=10)

        self.daily_table = DataTable(tab, [
            ("date",    "Date",    120, "center"),
            ("orders",  "Orders",   80, "center"),
            ("revenue", "Revenue", 200, "e"),
        ])
        self.daily_table.pack(fill="both", expand=True, padx=12, pady=4)

    def _load_daily(self):
        def task():
            return order_repo.daily_summary()

        def callback(rows, err):
            if err:
                self.status.error(str(err))
                return
            self.daily_rows = rows or []  # Lưu rows để export
            self.daily_table.clear()
            for r in self.daily_rows:
                date_s  = str(r.get("OrderDate") or r.get("SaleDate") or "")[:10]
                orders  = r.get("TotalOrders") or r.get("OrderCount") or r.get("DailyOrders") or ""
                revenue = r.get("TotalRevenue") or r.get("Revenue") or r.get("DailyRevenue") or 0
                self.daily_table.insert((date_s, orders, fmt_vnd(revenue)))
            self.status.info(f"Daily sales report: {len(self.daily_rows)} days.")

        run_in_thread(task, callback)

    def _export_daily_csv(self):
        if not hasattr(self, 'daily_rows') or not self.daily_rows:
            messagebox.showwarning("Export CSV", "No data to export. Load the report first.")
            return
        path = export_csv("daily_sales_report.csv", self.daily_rows)
        if path:
            messagebox.showinfo("Export CSV", f"Exported to: {path}")
        else:
            messagebox.showerror("Export CSV", "Failed to export CSV.")

    # ── Monthly Sales ──────────────────────────────────────────────────────────

    def _build_monthly_tab(self):
        tab = tk.Frame(self.nb, bg=CLR_BG)
        self.nb.add(tab, text="📆  Monthly Sales")

        ctrl = tk.Frame(tab, bg=CLR_BG, pady=10, padx=12)
        ctrl.pack(fill="x")
        tk.Label(ctrl, text="Year:",  bg=CLR_BG, fg=CLR_TEXT, font=FONT_BODY).pack(side="left")
        self._year_var = tk.StringVar(value=str(date.today().year))
        tk.Entry(ctrl, textvariable=self._year_var, width=6,
                 bg=CLR_CARD, fg=CLR_TEXT, insertbackground=CLR_TEXT,
                 relief="flat", font=FONT_BODY).pack(side="left", padx=6, ipady=4)

        tk.Label(ctrl, text="Month:", bg=CLR_BG, fg=CLR_TEXT, font=FONT_BODY).pack(side="left")
        self._month_var = tk.StringVar(value=str(date.today().month))
        tk.Entry(ctrl, textvariable=self._month_var, width=4,
                 bg=CLR_CARD, fg=CLR_TEXT, insertbackground=CLR_TEXT,
                 relief="flat", font=FONT_BODY).pack(side="left", padx=6, ipady=4)

        StyledButton(ctrl, "📊 View Report",
                     command=self._load_monthly, kind="primary").pack(side="left", padx=10)
        StyledButton(ctrl, "📄 Export CSV",
                     command=self._export_monthly_csv, kind="secondary").pack(side="left", padx=10)

        self.monthly_table = DataTable(tab, [
            ("id",       "Order ID",   80,  "center"),
            ("customer", "Customer",  200,  "w"),
            ("status",   "Status",    110,  "center"),
            ("date",     "Date",      110,  "center"),
            ("total",    "Total",     180,  "e"),
        ])

        self.monthly_table.pack(fill="both", expand=True, padx=12, pady=4)

    def _load_monthly(self):
        try:
            year  = int(self._year_var.get())
            month = int(self._month_var.get())
            if not (1 <= month <= 12):
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Invalid year/month.")
            return

        def task():
            return order_repo.monthly_report(year, month)

        def callback(rows, err):
            if err:
                self.status.error(str(err))
                return
            self.monthly_rows = rows or []  # Lưu rows để export
            self.monthly_table.clear()
            for r in self.monthly_rows:
                self.monthly_table.insert((
                    r.get("OrderID", ""),
                    r.get("CustomerName", ""),
                    r.get("Status", ""),
                    str(r.get("OrderDate", ""))[:10],
                    fmt_vnd(r.get("OrderTotal", 0)),
                ))
            self.status.info(f"Monthly report {month}/{year}: {len(self.monthly_rows)} orders.")

        run_in_thread(task, callback)

    def _export_monthly_csv(self):
        if not hasattr(self, 'monthly_rows') or not self.monthly_rows:
            messagebox.showwarning("Export CSV", "No data to export. Load the report first.")
            return
        path = export_csv("monthly_sales_report.csv", self.monthly_rows)
        if path:
            messagebox.showinfo("Export CSV", f"Exported to: {path}")
        else:
            messagebox.showerror("Export CSV", "Failed to export CSV.")

    # ── Top Customers ──────────────────────────────────────────────────────────

    def _build_top_customers_tab(self):
        tab = tk.Frame(self.nb, bg=CLR_BG)
        self.nb.add(tab, text="🏆  Top Customers")

        ctrl = tk.Frame(tab, bg=CLR_BG, pady=10, padx=12)
        ctrl.pack(fill="x")
        tk.Label(ctrl, text="Top N:", bg=CLR_BG, fg=CLR_TEXT,
                 font=FONT_BODY).pack(side="left")
        self._top_n_var = tk.StringVar(value="10")
        tk.Entry(ctrl, textvariable=self._top_n_var, width=5,
                 bg=CLR_CARD, fg=CLR_TEXT, insertbackground=CLR_TEXT,
                 relief="flat", font=FONT_BODY).pack(side="left", padx=6, ipady=4)
        StyledButton(ctrl, "🏆 Show Top",
                     command=self._load_top_customers, kind="warning").pack(side="left")
        StyledButton(ctrl, "📄 Export CSV",
                     command=self._export_top_customers_csv, kind="secondary").pack(side="left", padx=10)

        self.top_cust_table = DataTable(tab, [
            ("rank",  "#",            50, "center"),
            ("id",    "ID",           60, "center"),
            ("name",  "Customer",    220, "w"),
            ("phone", "Phone",       130, "center"),
            ("spend", "Total spent", 180, "e"),
        ])
        self.top_cust_table.pack(fill="both", expand=True, padx=12, pady=4)

    def _load_top_customers(self):
        try:
            n = int(self._top_n_var.get())
            if n <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Top N must be a positive integer.")
            return

        def task():
            return customer_repo.get_top_customers(n)

        def callback(rows, err):
            if err:
                self.status.error(str(err))
                return
            self.top_cust_rows = rows or []  # Lưu rows để export
            self.top_cust_table.clear()
            for i, r in enumerate(self.top_cust_rows, 1):
                self.top_cust_table.insert((
                    i,
                    r["CustomerID"],
                    r["CustomerName"],
                    r.get("PhoneNumber", ""),
                    fmt_vnd(r.get("TotalSpend", 0)),
                ))
            self.status.info(f"Top {len(self.top_cust_rows)} customers by spending.")

        run_in_thread(task, callback)

    def _export_top_customers_csv(self):
        if not hasattr(self, 'top_cust_rows') or not self.top_cust_rows:
            messagebox.showwarning("Export CSV", "No data to export. Load the report first.")
            return
        path = export_csv("top_customers_report.csv", self.top_cust_rows)
        if path:
            messagebox.showinfo("Export CSV", f"Exported to: {path}")
        else:
            messagebox.showerror("Export CSV", "Failed to export CSV.")

    # ── Product Performance ────────────────────────────────────────────────────
    # FIX: this method was called in _build() but never defined — added below.

    def _build_product_perf_tab(self):
        tab = tk.Frame(self.nb, bg=CLR_BG)
        self.nb.add(tab, text="📦  Product Performance")

        ctrl = tk.Frame(tab, bg=CLR_BG, pady=10, padx=12)
        ctrl.pack(fill="x")
        StyledButton(ctrl, "🔄 Load Report",
                     command=self._load_product_perf, kind="primary").pack(side="left")
        StyledButton(ctrl, "📄 Export CSV",
                     command=self._export_product_perf_csv, kind="secondary").pack(side="left", padx=10)

        self.perf_table = DataTable(tab, [
            ("rank",     "#",              50, "center"),
            ("id",       "Product ID",     90, "center"),
            ("name",     "Product Name",  260, "w"),
            ("category", "Category",      130, "w"),
            ("sold",     "Units Sold",     90, "center"),
            ("revenue",  "Revenue",       160, "e"),
        ])
        self.perf_table.pack(fill="both", expand=True, padx=12, pady=4)

    def _load_product_perf(self):
        def task():
            return product_repo.performance()

        def callback(rows, err):
            if err:
                self.status.error(str(err))
                return
            self.perf_rows = rows or []  # Lưu rows để export
            self.perf_table.clear()
            for i, r in enumerate(self.perf_rows, 1):
                self.perf_table.insert((
                    i,
                    r.get("ProductID", ""),
                    r.get("ProductName", ""),
                    r.get("Category", "") or "—",
                    r.get("TotalSold") or r.get("UnitsSold") or 0,
                    fmt_vnd(r.get("TotalRevenue") or r.get("Revenue") or 0),
                ))
            self.status.info(f"Product performance: {len(self.perf_rows)} products.")

        run_in_thread(task, callback)

    def _export_product_perf_csv(self):
        if not hasattr(self, 'perf_rows') or not self.perf_rows:
            messagebox.showwarning("Export CSV", "No data to export. Load the report first.")
            return
        path = export_csv("product_performance_report.csv", self.perf_rows)
        if path:
            messagebox.showinfo("Export CSV", f"Exported to: {path}")
        else:
            messagebox.showerror("Export CSV", "Failed to export CSV.")


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════