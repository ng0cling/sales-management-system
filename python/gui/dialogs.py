"""
PROJECT 03: SALES MANAGEMENT SYSTEM
File: gui/dialogs.py
All dialog/popup windows: BaseDialog, CRUD dialogs, Pickers, OrderDetailWindow.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation

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
    fmt_vnd, run_in_thread,
)
from gui.widgets import StyledButton, LabeledEntry, LabeledCombobox, DataTable, StatusBar

customer_repo = CustomerRepository()
employee_repo = EmployeeRepository()
product_repo  = ProductRepository()
order_repo    = OrderRepository()


# ── BaseDialog ────────────────────────────────────────────────────────────────

class BaseDialog(tk.Toplevel):
    def __init__(self, parent, title: str, width=420, height=480):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=CLR_CARD)
        self.resizable(False, False)
        self.result = None
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width()  - width)  // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.grab_set()

    def build_header(self, title: str):
        tk.Label(self, text=title, bg=CLR_SIDEBAR, fg=CLR_ACCENT,
                 font=FONT_TITLE, pady=14).pack(fill="x")

    def build_footer(self, ok_text="Save", ok_cmd=None, cancel_cmd=None):
        tk.Frame(self, bg=CLR_HEADER_BG, height=1).pack(fill="x", side="bottom")
        frame = tk.Frame(self, bg=CLR_CARD, pady=10)
        frame.pack(fill="x", padx=20, side="bottom")
        StyledButton(frame, ok_text, command=ok_cmd, kind="primary").pack(side="right", padx=(8,0))
        StyledButton(frame, "Cancel", command=cancel_cmd or self.destroy,
                     kind="neutral").pack(side="right")

    def body_frame(self) -> tk.Frame:
        f = tk.Frame(self, bg=CLR_CARD, padx=20, pady=10)
        f.pack(fill="both", expand=True)
        return f


# ── CRUD Dialogs ──────────────────────────────────────────────────────────────

class CustomerDialog(BaseDialog):
    def __init__(self, parent, row: dict | None = None):
        super().__init__(parent, "Add Customer" if row is None else "Edit Customer")
        self.build_header("👤  Customer Information")
        body = self.body_frame()
        self.name    = LabeledEntry(body, "Full name",     required=True)
        self.address = LabeledEntry(body, "Address",       required=True)
        self.phone   = LabeledEntry(body, "Phone number",  required=True)
        self.email   = LabeledEntry(body, "Email (optional)")
        for w in (self.name, self.address, self.phone, self.email):
            w.pack(fill="x", pady=6)
        if row:
            self.name.set(row.get("CustomerName", ""))
            self.address.set(row.get("Address", ""))
            self.phone.set(row.get("PhoneNumber", ""))
            self.email.set(row.get("Email", ""))
        self.build_footer(ok_cmd=self._ok)

    def _ok(self):
        name, addr, phone = self.name.get(), self.address.get(), self.phone.get()
        if not name or not addr or not phone:
            messagebox.showwarning("Missing information",
                                   "Please fill in Full name, Address, and Phone number.",
                                   parent=self)
            return
        self.result = {"customer_name": name, "address": addr,
                       "phone_number": phone, "email": self.email.get() or None}
        self.destroy()


class ProductDialog(BaseDialog):
    def __init__(self, parent, row: dict | None = None):
        super().__init__(parent, "Add Product" if row is None else "Edit Product")
        self.build_header("📦  Product Information")
        body = self.body_frame()
        self.name     = LabeledEntry(body, "Product name",      required=True)
        self.price    = LabeledEntry(body, "Price (VND)",        required=True)
        self.stock    = LabeledEntry(body, "Stock quantity",     required=True)
        self.category = LabeledEntry(body, "Category (optional)")
        for w in (self.name, self.price, self.stock, self.category):
            w.pack(fill="x", pady=6)
        if row:
            self.name.set(row.get("ProductName", ""))
            self.price.set(str(row.get("Price", "")))
            self.stock.set(str(row.get("StockQuantity", "")))
            self.category.set(row.get("Category", ""))
        self.build_footer(ok_cmd=self._ok)

    def _ok(self):
        name = self.name.get()
        if not name:
            messagebox.showwarning("Missing information", "Please enter product name.", parent=self)
            return
        try:
            price = Decimal(self.price.get())
            if price < 0: raise ValueError
        except (InvalidOperation, ValueError):
            messagebox.showerror("Error", "Price must be a non-negative number.", parent=self)
            return
        try:
            stock = int(self.stock.get())
            if stock < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Stock must be a non-negative integer.", parent=self)
            return
        self.result = {"product_name": name, "price": price,
                       "stock_quantity": stock, "category": self.category.get() or None}
        self.destroy()


class EmployeeDialog(BaseDialog):
    def __init__(self, parent, row: dict | None = None):
        super().__init__(parent, "Add Employee" if row is None else "Edit Employee", height=400)
        self.build_header("🧑‍💼  Employee Information")
        body = self.body_frame()
        self.name  = LabeledEntry(body, "Full name",              required=True)
        self.title = LabeledEntry(body, "Job title",              required=True)
        self.email = LabeledEntry(body, "Email (optional)")
        self.phone = LabeledEntry(body, "Phone number (optional)")
        for w in (self.name, self.title, self.email, self.phone):
            w.pack(fill="x", pady=6)
        if row:
            self.name.set(row.get("EmployeeName", ""))
            self.title.set(row.get("JobTitle", ""))
            self.email.set(row.get("Email", ""))
            self.phone.set(row.get("PhoneNumber", ""))
        self.build_footer(ok_cmd=self._ok)

    def _ok(self):
        name, title = self.name.get(), self.title.get()
        if not name or not title:
            messagebox.showwarning("Missing information",
                                   "Please enter Full name and Job title.", parent=self)
            return
        self.result = {"employee_name": name, "job_title": title,
                       "email": self.email.get() or None,
                       "phone_number": self.phone.get() or None}
        self.destroy()


# ── Pickers ───────────────────────────────────────────────────────────────────

class CustomerPicker(BaseDialog):
    def __init__(self, parent):
        super().__init__(parent, "Select Customer", width=600, height=500)
        self.build_header("🔍  Find Customer")
        sf = tk.Frame(self, bg=CLR_CARD, padx=20, pady=10)
        sf.pack(fill="x")
        tk.Label(sf, text="Search name or phone:", bg=CLR_CARD,
                 fg=CLR_SUBTEXT, font=FONT_SMALL).pack(side="left")
        self.search_var = tk.StringVar()
        se = tk.Entry(sf, textvariable=self.search_var, bg="#45475a", fg=CLR_TEXT,
                      font=FONT_BODY, relief="flat", insertbackground=CLR_TEXT)
        se.pack(side="left", fill="x", expand=True, padx=10, ipady=3)
        se.bind("<Return>", lambda e: self._do_search())
        StyledButton(sf, "Search", command=self._do_search).pack(side="left")
        self.table = DataTable(self, columns=[
            ("id",      "ID",            50,  "center"),
            ("name",    "Customer Name", 200, "w"),
            ("phone",   "Phone Number",  120, "w"),
            ("address", "Address",       200, "w"),
        ])
        self.table.pack(fill="both", expand=True, padx=20, pady=10)
        self.table.bind_double(lambda e: self._on_select())
        self.build_footer(ok_text="Select", ok_cmd=self._on_select)
        self._do_search()

    def _do_search(self):
        kw = self.search_var.get().strip()
        def task():
            return customer_repo.search(kw) if kw else customer_repo.get_all()
        def callback(data, err):
            self.table.clear()
            if err:
                messagebox.showerror("Error", str(err), parent=self); return
            for r in (data or []):
                self.table.insert((r["CustomerID"], r["CustomerName"],
                                   r.get("PhoneNumber", ""), r.get("Address", "")))
        run_in_thread(task, callback)

    def _on_select(self):
        v = self.table.selected_values()
        if v:
            self.result = {"id": v[0], "name": v[1]}; self.destroy()
        else:
            messagebox.showwarning("Selection", "Please select a customer.", parent=self)


class ProductPicker(BaseDialog):
    def __init__(self, parent, existing_ids: set):
        super().__init__(parent, "Select Product", width=700, height=550)
        self.build_header("🔍  Find Available Products")
        self.existing_ids = existing_ids
        sf = tk.Frame(self, bg=CLR_CARD, padx=20, pady=10)
        sf.pack(fill="x")
        self.search_var = tk.StringVar()
        se = tk.Entry(sf, textvariable=self.search_var, bg="#45475a", fg=CLR_TEXT,
                      font=FONT_BODY, relief="flat", insertbackground=CLR_TEXT)
        se.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=3)
        se.bind("<Return>", lambda e: self._do_search())
        StyledButton(sf, "Search", command=self._do_search).pack(side="left")
        self.table = DataTable(self, columns=[
            ("id",    "ID",           50,  "center"),
            ("name",  "Product Name", 200, "w"),
            ("cat",   "Category",     120, "w"),
            ("price", "Price",        120, "e"),
            ("stock", "Stock",         80, "center"),
        ])
        self.table.pack(fill="both", expand=True, padx=20, pady=10)
        self.table.bind_double(lambda e: self._on_select())
        self.build_footer(ok_text="Select Product", ok_cmd=self._on_select)
        self._do_search()

    def _do_search(self):
        kw = self.search_var.get().strip()
        def task():
            return product_repo.search(kw) if kw else product_repo.get_all()
        def callback(data, err):
            self.table.clear()
            if err:
                messagebox.showerror("Error", str(err), parent=self); return
            for r in (data or []):
                pid, stock = r["ProductID"], int(r["StockQuantity"])
                if pid not in self.existing_ids and stock > 0:
                    self.table.insert((pid, r["ProductName"],
                                       r.get("Category", "-"), fmt_vnd(r["Price"]), stock))
        run_in_thread(task, callback)

    def _on_select(self):
        v = self.table.selected_values()
        if v:
            self.result = {"id": v[0], "name": v[1], "stock": v[4]}; self.destroy()
        else:
            messagebox.showwarning("Selection", "Please select a product.", parent=self)


# ── Order dialogs ─────────────────────────────────────────────────────────────

class CreateOrderDialog(BaseDialog):
    def __init__(self, parent):
        super().__init__(parent, "Create New Order", width=460, height=350)
        self.build_header("🛒  Create Order")
        body = self.body_frame()
        self.selected_customer_id = None

        tk.Label(body, text="Customer *", bg=CLR_CARD,
                 fg=CLR_SUBTEXT, font=FONT_SMALL).pack(anchor="w")
        csf = tk.Frame(body, bg=CLR_CARD)
        csf.pack(fill="x", pady=(0, 10))
        self.cust_display_var = tk.StringVar(value="None selected")
        tk.Entry(csf, textvariable=self.cust_display_var, state="readonly",
                 bg="#45475a", fg=CLR_ACCENT, font=FONT_BODY,
                 relief="flat").pack(side="left", fill="x", expand=True, ipady=5)
        StyledButton(csf, "🔍", command=self._pick_customer).pack(side="right", padx=(5, 0))

        employees = employee_repo.get_all()
        self._emp_map = {"-- None --": None}
        self._emp_map.update({r["EmployeeName"]: r["EmployeeID"] for r in employees})
        self.emp_combo = LabeledCombobox(body, "Sales representative", list(self._emp_map.keys()))
        self.emp_combo.set("-- None --")
        self.emp_combo.pack(fill="x", pady=6)

        self.notes = LabeledEntry(body, "Notes")
        self.notes.pack(fill="x", pady=6)
        self.build_footer(ok_text="Create Order", ok_cmd=self._ok)

    def _pick_customer(self):
        picker = CustomerPicker(self)
        self.wait_window(picker)
        if picker.result:
            self.selected_customer_id = picker.result["id"]
            self.cust_display_var.set(f"ID: {picker.result['id']} - {picker.result['name']}")

    def _ok(self):
        if not self.selected_customer_id:
            messagebox.showwarning("Missing Information", "Please select a customer.", parent=self)
            return
        self.result = {"customer_id": self.selected_customer_id,
                       "employee_id": self._emp_map.get(self.emp_combo.get()),
                       "notes": self.notes.get()}
        self.destroy()


class AddProductDialog(BaseDialog):
    def __init__(self, parent, existing_ids: set):
        super().__init__(parent, "Add Product to Order", width=420, height=300)
        self.build_header("➕  Add Product")
        self.existing_ids     = existing_ids
        self.selected_product = None
        body = self.body_frame()
        tk.Label(body, text="Product *", bg=CLR_CARD,
                 fg=CLR_SUBTEXT, font=FONT_SMALL).pack(anchor="w")
        pf = tk.Frame(body, bg=CLR_CARD)
        pf.pack(fill="x", pady=(0, 10))
        self.prod_display_var = tk.StringVar(value="Click 🔍 to select product")
        tk.Entry(pf, textvariable=self.prod_display_var, state="readonly",
                 bg="#45475a", fg=CLR_ACCENT, font=FONT_BODY,
                 relief="flat").pack(side="left", fill="x", expand=True, ipady=5)
        StyledButton(pf, "🔍", command=self._open_picker).pack(side="right", padx=(5, 0))
        self.qty = LabeledEntry(body, "Quantity *")
        self.qty.pack(fill="x", pady=6)
        self.build_footer(ok_text="Add to Order", ok_cmd=self._ok)

    def _open_picker(self):
        picker = ProductPicker(self, self.existing_ids)
        self.wait_window(picker)
        if picker.result:
            self.selected_product = picker.result
            self.prod_display_var.set(
                f"[{picker.result['id']}] {picker.result['name']} (Stock: {picker.result['stock']})")

    def _ok(self):
        if not self.selected_product:
            messagebox.showwarning("Missing", "Please select a product first.", parent=self); return
        try:
            qty   = int(self.qty.get())
            stock = int(self.selected_product["stock"])
            if qty <= 0: raise ValueError("Positive")
            if qty > stock: raise ValueError("OverStock")
        except ValueError as e:
            msg = f"Not enough stock! (Available: {stock})" if str(e) == "OverStock" \
                  else "Quantity must be a positive integer."
            messagebox.showerror("Error", msg, parent=self); return
        self.result = {"product_id": self.selected_product["id"], "quantity": qty}
        self.destroy()


class EditQuantityDialog(BaseDialog):
    def __init__(self, parent, product_name: str, current_qty: int):
        super().__init__(parent, "Edit Quantity", width=380, height=260)
        self.build_header("✏️  Edit Quantity")
        self.build_footer(ok_text="Update", ok_cmd=self._ok)
        body = self.body_frame()
        tk.Label(body, text=product_name, bg=CLR_CARD, fg=CLR_TEXT,
                 font=FONT_HEADER, wraplength=320, justify="left").pack(anchor="w", pady=(0, 12))
        self.qty = LabeledEntry(body, f"New quantity  (current: {current_qty}) *")
        self.qty.set(str(current_qty))
        self.qty.pack(fill="x", pady=4)

    def _ok(self):
        try:
            qty = int(self.qty.get())
            if qty <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive integer.", parent=self); return
        self.result = qty
        self.destroy()


class RestockDialog(BaseDialog):
    def __init__(self, parent, product_name: str):
        super().__init__(parent, "Restock", width=500, height=220)
        self.build_header(f"📥  Restock: {product_name[:30]}")
        self.build_footer(ok_text="Restock", ok_cmd=self._ok)
        body = self.body_frame()
        self.qty = LabeledEntry(body, "Additional quantity *")
        self.qty.pack(fill="x", pady=10)

    def _ok(self):
        try:
            qty = int(self.qty.get())
            if qty <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive integer.", parent=self); return
        self.result = qty
        self.destroy()


# ── Order Detail Window ───────────────────────────────────────────────────────

class OrderDetailWindow(tk.Toplevel):
    EDITABLE = {"Pending", "Processing"}

    def __init__(self, parent, oid: int, status_bar: StatusBar, on_close=None):
        super().__init__(parent)
        self.oid, self.status_bar, self._on_close = oid, status_bar, on_close
        self.title(f"Order #{oid} — Details")
        self.configure(bg=CLR_BG)
        self.geometry("780x540")
        self.minsize(640, 420)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._build()
        self._refresh()

    def _build(self):
        self._header = tk.Label(self, text="", bg=CLR_SIDEBAR, fg=CLR_TEXT,
                                font=FONT_HEADER, anchor="w", padx=16, pady=10)
        self._header.pack(fill="x")

        self._toolbar_frame = tk.Frame(self, bg=CLR_BG, pady=6, padx=12)
        self._toolbar_frame.pack(fill="x")
        self._btn_add    = StyledButton(self._toolbar_frame, "➕ Add Product",  command=self._do_add,    kind="success")
        self._btn_edit   = StyledButton(self._toolbar_frame, "✏️ Edit Qty",     command=self._do_edit,   kind="primary")
        self._btn_remove = StyledButton(self._toolbar_frame, "🗑️ Remove",       command=self._do_remove, kind="danger")
        for btn in (self._btn_add, self._btn_edit, self._btn_remove):
            btn.pack(side="left", padx=4)

        self.table = DataTable(self, [
            ("pid",   "Product ID",  90, "center"),
            ("name",  "Product",    300, "w"),
            ("qty",   "Qty",         70, "center"),
            ("price", "Unit Price", 150, "e"),
            ("sub",   "Subtotal",   150, "e"),
        ])
        self.table.pack(fill="both", expand=True, padx=12, pady=4)

        footer = tk.Frame(self, bg=CLR_BG, pady=10, padx=14)
        footer.pack(fill="x")
        self._total_lbl = tk.Label(footer, text="", bg=CLR_BG, fg=CLR_SUCCESS, font=FONT_TITLE)
        self._total_lbl.pack(side="left")
        StyledButton(footer, "✖  Close", command=self._close, kind="neutral").pack(side="right")

    def _refresh(self):
        order   = order_repo.get_by_id(self.oid)
        details = order_repo.get_details(self.oid)
        total   = order_repo.order_total(self.oid)
        if not order:
            self._header.config(text=f"Order #{self.oid} not found."); return

        status   = order.get("Status", "")
        editable = status in self.EDITABLE
        self._header.config(text=(
            f"Order #{self.oid}   │   Customer: {order.get('CustomerName', '')}   │   "
            f"Status: {status}   │   Sales Rep: {order.get('SalesRep', '') or '—'}"
        ))
        if editable:
            self._toolbar_frame.pack(fill="x", after=self._header)
        else:
            self._toolbar_frame.pack_forget()

        self.table.clear()
        for d in details:
            sub = Decimal(str(d["Quantity"])) * Decimal(str(d["SalePrice"]))
            self.table.insert((d["ProductID"], d["ProductName"],
                               d["Quantity"], fmt_vnd(d["SalePrice"]), fmt_vnd(sub)))
        suffix = "" if editable else "  ⚠ read-only"
        self._total_lbl.config(text=f"Total:  {fmt_vnd(total)}{suffix}")

    def _selected_item(self) -> tuple | None:
        vals = self.table.selected_values()
        if not vals:
            messagebox.showinfo("No selection", "Please select a product row first.", parent=self)
            return None
        return int(vals[0]), vals[1], int(vals[2])

    def _do_add(self):
        existing_ids = {d["ProductID"] for d in order_repo.get_details(self.oid)}
        dlg = AddProductDialog(self, existing_ids)
        self.wait_window(dlg)
        if dlg.result:
            try:
                order_repo.add_item(self.oid, dlg.result["product_id"], dlg.result["quantity"])
                self.status_bar.success(f"Added product to order #{self.oid}.")
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self)

    def _do_edit(self):
        item = self._selected_item()
        if item is None: return
        pid, pname, current_qty = item
        dlg = EditQuantityDialog(self, pname, current_qty)
        self.wait_window(dlg)
        if dlg.result is None: return
        if dlg.result == current_qty:
            self.status_bar.info("Quantity unchanged."); return
        try:
            order_repo.update_item_quantity(self.oid, pid, dlg.result)
            self.status_bar.success(f"'{pname}': {current_qty} → {dlg.result}.")
            self._refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _do_remove(self):
        item = self._selected_item()
        if item is None: return
        pid, pname, _ = item
        if not messagebox.askyesno("Confirm removal",
                                   f"Remove '{pname}' from order #{self.oid}?\n"
                                   "Stock will be restored automatically.", parent=self):
            return
        try:
            order_repo.remove_item(self.oid, pid)
            self.status_bar.success(f"Removed '{pname}' from order #{self.oid}.")
            self._refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _close(self):
        if self._on_close: self._on_close()
        self.destroy()