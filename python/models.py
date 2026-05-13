"""
PROJECT 03: SALES MANAGEMENT SYSTEM
File: models.py
CRUD operations for Customers, Products, Orders, OrderDetails, Employees

"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from db_connection import db_cursor


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOMERS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Customer:
    customer_id: Optional[int]
    customer_name: str
    address: str
    phone_number: str
    email: Optional[str] = None
    created_at: Optional[datetime] = None


class CustomerRepository:
    def create(self, c: Customer) -> int:
        sql = """INSERT INTO Customers (CustomerName, Address, PhoneNumber, Email)
                 VALUES (%(name)s, %(address)s, %(phone)s, %(email)s)"""
        with db_cursor(commit=True) as (_, cur):
            cur.execute(sql, {
                "name": c.customer_name,
                "address": c.address,
                "phone": c.phone_number,
                "email": c.email,
            })
            return cur.lastrowid  # type: ignore[return-value]

    def get_by_id(self, customer_id: int) -> Optional[dict]:
        with db_cursor() as (_, cur):
            cur.execute("SELECT * FROM Customers WHERE CustomerID = %s", (customer_id,))
            return cur.fetchone()

    def search(self, keyword: str) -> list[dict]:
        sql = """SELECT * FROM Customers
                  WHERE CustomerName LIKE %(kw)s OR PhoneNumber LIKE %(kw)s
                  ORDER BY CustomerName"""
        with db_cursor() as (_, cur):
            cur.execute(sql, {"kw": f"%{keyword}%"})
            return cur.fetchall()  # type: ignore[return-value]

    def get_all(self) -> list[dict]:
        with db_cursor() as (_, cur):
            cur.execute("SELECT * FROM Customers ORDER BY CustomerID")
            return cur.fetchall()  # type: ignore[return-value]

    def update(self, c: Customer) -> None:
        sql = """UPDATE Customers
                    SET CustomerName=%(name)s, Address=%(address)s,
                        PhoneNumber=%(phone)s, Email=%(email)s
                  WHERE CustomerID=%(id)s"""
        with db_cursor(commit=True) as (_, cur):
            cur.execute(sql, {
                "name": c.customer_name,
                "address": c.address,
                "phone": c.phone_number,
                "email": c.email,
                "id": c.customer_id,
            })

    def delete(self, customer_id: int) -> None:
        with db_cursor(commit=True) as (_, cur):
            cur.execute("DELETE FROM Customers WHERE CustomerID = %s", (customer_id,))

    def total_spend(self, customer_id: int) -> Decimal:
        """Gọi UDF fn_CustomerTotalSpend."""
        with db_cursor() as (_, cur):
            cur.execute("SELECT fn_CustomerTotalSpend(%s) AS spend", (customer_id,))
            row = cur.fetchone()
            return Decimal(str(row["spend"])) if row and row["spend"] is not None else Decimal(0)  # type: ignore[index]

    def get_top_customers(self, top_n: int = 5) -> list[dict]:
        sql = """
            SELECT
                c.CustomerID,
                c.CustomerName,
                c.PhoneNumber,
                COALESCE(SUM(od.Quantity * od.SalePrice), 0) AS TotalSpend
            FROM Customers c
            LEFT JOIN Orders o      ON o.CustomerID = c.CustomerID
                                    AND o.Status != 'Cancelled'
            LEFT JOIN OrderDetails od ON od.OrderID = o.OrderID
            GROUP BY c.CustomerID, c.CustomerName, c.PhoneNumber
            ORDER BY TotalSpend DESC
            LIMIT %(n)s
        """
        with db_cursor() as (_, cur):
            cur.execute(sql, {"n": top_n})
            return cur.fetchall()  # type: ignore[return-value]


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Product:
    product_id: Optional[int]
    product_name: str
    price: Decimal
    stock_quantity: int
    category: Optional[str] = None


class ProductRepository:
    def create(self, p: Product) -> int:
        sql = """INSERT INTO Products (ProductName, Price, StockQuantity, Category)
                 VALUES (%(name)s, %(price)s, %(stock)s, %(cat)s)"""
        with db_cursor(commit=True) as (_, cur):
            cur.execute(sql, {
                "name": p.product_name,
                "price": p.price,
                "stock": p.stock_quantity,
                "cat": p.category,
            })
            return cur.lastrowid  # type: ignore[return-value]

    def get_all(self) -> list[dict]:
        with db_cursor() as (_, cur):
            cur.execute("SELECT * FROM Products ORDER BY ProductID")
            return cur.fetchall()  # type: ignore[return-value]

    def get_by_id(self, product_id: int) -> Optional[dict]:
        with db_cursor() as (_, cur):
            cur.execute("SELECT * FROM Products WHERE ProductID = %s", (product_id,))
            return cur.fetchone()
    
    def search(self, keyword: str) -> list[dict]:
        sql = """SELECT * FROM Products
                WHERE ProductName LIKE %(kw)s
                    OR Category   LIKE %(kw)s
                ORDER BY ProductName"""
        with db_cursor() as (_, cur):
            cur.execute(sql, {"kw": f"%{keyword}%"})
            return cur.fetchall()

    def update(self, p: Product) -> None:
        sql = """UPDATE Products
                    SET ProductName=%(name)s, Price=%(price)s,
                        StockQuantity=%(stock)s, Category=%(cat)s
                  WHERE ProductID=%(id)s"""
        with db_cursor(commit=True) as (_, cur):
            cur.execute(sql, {
                "name": p.product_name,
                "price": p.price,
                "stock": p.stock_quantity,
                "cat": p.category,
                "id": p.product_id,
            })

    def delete(self, product_id: int) -> None:
        with db_cursor(commit=True) as (_, cur):
            cur.execute("DELETE FROM Products WHERE ProductID = %s", (product_id,))

    def restock(self, product_id: int, qty: int) -> None:
        """Gọi stored procedure sp_RestockProduct."""
        with db_cursor(commit=True) as (_, cur):
            cur.callproc("sp_RestockProduct", [product_id, qty])

    def get_low_stock(self) -> list[dict]:
        """Lấy danh sách sản phẩm gần hết kho từ view vw_LowStock."""
        with db_cursor() as (_, cur):
            cur.execute("SELECT * FROM vw_LowStock")
            return cur.fetchall()  # type: ignore[return-value]

    def performance(self) -> list[dict]:
        """Lấy hiệu suất bán hàng từ view vw_ProductPerformance."""
        with db_cursor() as (_, cur):
            cur.execute(
                "SELECT * FROM vw_ProductPerformance ORDER BY TotalSold DESC"
            )
            return cur.fetchall()  # type: ignore[return-value]


# ══════════════════════════════════════════════════════════════════════════════
# EMPLOYEES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Employee:
    employee_id: Optional[int]
    employee_name: str
    job_title: str
    email: Optional[str] = None
    phone_number: Optional[str] = None


class EmployeeRepository:
    def create(self, e: Employee) -> int:
        sql = """INSERT INTO Employees (EmployeeName, JobTitle, Email, PhoneNumber)
                 VALUES (%(name)s, %(title)s, %(email)s, %(phone)s)"""
        with db_cursor(commit=True) as (_, cur):
            cur.execute(sql, {
                "name": e.employee_name,
                "title": e.job_title,
                "email": e.email,
                "phone": e.phone_number,
            })
            return cur.lastrowid  # type: ignore[return-value]

    def get_all(self) -> list[dict]:
        with db_cursor() as (_, cur):
            cur.execute("SELECT * FROM Employees ORDER BY EmployeeID")
            return cur.fetchall()  # type: ignore[return-value]

    def get_by_id(self, employee_id: int) -> Optional[dict]:
        with db_cursor() as (_, cur):
            cur.execute(
                "SELECT * FROM Employees WHERE EmployeeID = %s", (employee_id,)
            )
            return cur.fetchone()

    def update(self, e: Employee) -> None:
        sql = """UPDATE Employees
                    SET EmployeeName=%(name)s, JobTitle=%(title)s,
                        Email=%(email)s, PhoneNumber=%(phone)s
                  WHERE EmployeeID=%(id)s"""
        with db_cursor(commit=True) as (_, cur):
            cur.execute(sql, {
                "name": e.employee_name,
                "title": e.job_title,
                "email": e.email,
                "phone": e.phone_number,
                "id": e.employee_id,
            })

    def delete(self, employee_id: int) -> None:
        with db_cursor(commit=True) as (_, cur):
            cur.execute(
                "DELETE FROM Employees WHERE EmployeeID = %s", (employee_id,)
            )


# ══════════════════════════════════════════════════════════════════════════════
# ORDERS
# ══════════════════════════════════════════════════════════════════════════════

class OrderRepository:
    # ── Tạo đơn hàng ──────────────────────────────────────────────────────────
    def create(
        self,
        customer_id: int,
        employee_id: Optional[int] = None,
        notes: str = "",
    ) -> int:
        """
        Gọi sp_CreateOrder qua session variable để lấy OUT param p_OrderID.
        sp_CreateOrder(IN p_CustomerID, IN p_EmployeeID, IN p_Notes, OUT p_OrderID)

        Cách thực hiện:
          1. SET @p_OrderID = 0;
          2. CALL sp_CreateOrder(..., @p_OrderID);
          3. SELECT @p_OrderID AS oid;
        """
        with db_cursor(commit=False) as (conn, cur):
            cur.execute("SET @p_OrderID = 0")
            cur.execute(
                "CALL sp_CreateOrder(%s, %s, %s, @p_OrderID)",
                (customer_id, employee_id, notes),
            )
            conn.get_warnings = True
            while cur.nextset():
                pass
            cur.execute("SELECT @p_OrderID AS oid")
            row = cur.fetchone()
            conn.commit()
            return int(row["oid"])  # type: ignore[index]
        
    def search(
        self,
        keyword: str = "",
        status: str = "",
    ) -> list[dict]:
        """
        Tìm kiếm đơn hàng theo tên khách / nhân viên, lọc theo status, hoặc kết hợp cả hai.
 
        Gọi linh hoạt:
            search()                             → toàn bộ (= get_all)
            search(keyword="Nguyen")             → theo tên
            search(status="Pending")             → theo status
            search(keyword="Hung", status="Shipped") → kết hợp
        """
        conditions: list[str] = []
        params: dict = {}
 
        if keyword:
            conditions.append(
                "(CustomerName LIKE %(kw)s OR SalesRep LIKE %(kw)s)"
            )
            params["kw"] = f"%{keyword}%"
        if status:
            conditions.append("Status = %(status)s")
            params["status"] = status
 
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = f"SELECT * FROM vw_OrderSummary {where} ORDER BY OrderDate DESC"
 
        with db_cursor() as (_, cur):
            cur.execute(sql, params)
            return cur.fetchall()  # type: ignore[return-value]
 
    def filter_by_status(self, status: str) -> list[dict]:
        """Shorthand cho search(status=status) — tiện dùng khi chỉ cần lọc status."""
        return self.search(status=status)
 

    # ── Thêm sản phẩm vào đơn ─────────────────────────────────────────────────
    def add_item(self, order_id: int, product_id: int, quantity: int) -> None:
        """
        Gọi sp_AddOrderItem.
        Procedure tự xử lý kiểm tra stock và cập nhật kho qua trigger.
        """
        with db_cursor(commit=False) as (conn, cur):
            cur.execute(
                "CALL sp_AddOrderItem(%s, %s, %s)",
                (order_id, product_id, quantity),
            )
            while cur.nextset():
                pass
            conn.commit()

    # ── Cập nhật trạng thái ───────────────────────────────────────────────────
    def update_status(self, order_id: int, status: str) -> None:
        """
        Gọi sp_UpdateOrderStatus.
        """
        with db_cursor(commit=False) as (conn, cur):
            cur.execute(
                "CALL sp_UpdateOrderStatus(%s, %s)",
                (order_id, status),
            )
            while cur.nextset():
                pass
            conn.commit()

    # ── Xóa đơn hàng (an toàn) ────────────────────────────────────────────────
    def delete_order(self, order_id: int) -> None:
        """
        Gọi sp_DeleteOrder — chỉ cho phép xóa đơn đã Cancelled.
        Procedure xóa OrderDetails thủ công trước để trigger hoàn kho đúng,
        sau đó mới xóa Orders.
        """
        with db_cursor(commit=False) as (conn, cur):
            cur.execute("CALL sp_DeleteOrder(%s)", (order_id,))
            while cur.nextset():
                pass
            conn.commit()
    
    # ── Cập nhật số lượng món hàng ────────────────────────────────────────────
    def update_item_quantity(self, order_id: int, product_id: int, new_quantity: int) -> None:
        """
        Cập nhật số lượng của một sản phẩm đã có trong đơn hàng.
        Gọi trg_AfterOrderDetailUpdate.
        """
        sql = "UPDATE OrderDetails SET Quantity = %s WHERE OrderID = %s AND ProductID = %s"
        with db_cursor(commit=True) as (_, cur):
            cur.execute(sql, (new_quantity, order_id, product_id))

    # ── Xóa một món hàng khỏi đơn ─────────────────────────────────────────────
    def remove_item(self, order_id: int, product_id: int) -> None:
        """
        Xóa hoàn toàn một sản phẩm khỏi đơn hàng.
        Gọi trg_AfterOrderDetailDelete để hoàn kho.
        """
        sql = "DELETE FROM OrderDetails WHERE OrderID = %s AND ProductID = %s"
        with db_cursor(commit=True) as (_, cur):
            cur.execute(sql, (order_id, product_id))

    # ── Queries ───────────────────────────────────────────────────────────────
    def get_all(self) -> list[dict]:
        with db_cursor() as (_, cur):
            cur.execute("SELECT * FROM vw_OrderSummary ORDER BY OrderDate DESC")
            return cur.fetchall()  # type: ignore[return-value]

    def get_by_id(self, order_id: int) -> Optional[dict]:
        with db_cursor() as (_, cur):
            cur.execute(
                "SELECT * FROM vw_OrderSummary WHERE OrderID = %s", (order_id,)
            )
            return cur.fetchone()

    def get_details(self, order_id: int) -> list[dict]:
        sql = """SELECT od.*, p.ProductName
                   FROM OrderDetails od
                   JOIN Products p ON p.ProductID = od.ProductID
                  WHERE od.OrderID = %s"""
        with db_cursor() as (_, cur):
            cur.execute(sql, (order_id,))
            return cur.fetchall()  # type: ignore[return-value]

    def monthly_report(self, year: int, month: int) -> list[dict]:
        """Gọi sp_MonthlySalesReport và đọc result set trả về."""
        with db_cursor() as (_, cur):
            cur.callproc("sp_MonthlySalesReport", [year, month])
            for result in cur.stored_results():
                return result.fetchall()  # type: ignore[return-value]
            return []

    def daily_summary(self) -> list[dict]:
        with db_cursor() as (_, cur):
            cur.execute("SELECT * FROM vw_DailySales LIMIT 30")
            return cur.fetchall()  # type: ignore[return-value]

    def order_total(self, order_id: int) -> Decimal:
        """Gọi UDF fn_OrderTotal."""
        with db_cursor() as (_, cur):
            cur.execute("SELECT fn_OrderTotal(%s) AS total", (order_id,))
            row = cur.fetchone()
            return (
                Decimal(str(row["total"]))  # type: ignore[index]
                if row and row["total"] is not None  # type: ignore[index]
                else Decimal(0)
            )

    def apply_discount(self, amount: Decimal, pct_discount: Decimal) -> Decimal:
        """
        Gọi UDF fn_ApplyDiscount(amount, pct_discount).
        pct_discount: phần trăm giảm giá (0–100).
        """
        with db_cursor() as (_, cur):
            cur.execute(
                "SELECT fn_ApplyDiscount(%s, %s) AS discounted",
                (float(amount), float(pct_discount)),
            )
            row = cur.fetchone()
            return (
                Decimal(str(row["discounted"]))  # type: ignore[index]
                if row and row["discounted"] is not None  # type: ignore[index]
                else amount
            )
