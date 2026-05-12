# Project 03: Sales Management System

## Overview
A full-stack Sales Management System built with **MySQL** and **Python**, featuring a modern Tkinter GUI. This project demonstrates advanced database design with stored procedures, triggers, views, and user-defined functions, along with a complete Python application for CRUD operations and reporting.

---

## Project Structure
```
sales_management/
├── README.md
├── sql/
│   ├── 01_schema.sql          # Database schema with tables, indexes, constraints
│   ├── 02_sample_data.sql     # Sample data: 7 customers, 5 employees, 10 products, 8 orders
│   └── 03_advanced_objects.sql # Views, stored procedures, UDFs, triggers, security
└── python/
    ├── db_connection.py       # MySQL connection pool & context manager
    ├── models.py              # Repository classes for CRUD operations
    ├── csv_export.py          # CSV export utility
    └── gui/
        ├── __init__.py
        ├── app.py             # Main GUI application entry point
        ├── constants.py       # Theme constants, fonts, utilities
        ├── widgets.py         # Reusable UI widgets
        ├── panels.py          # Main panels for customers, products, orders, etc.
        └── dialogs.py         # Popup dialogs for forms and pickers
```

---

## Database Design

### Entity Relationship (ER) Summary
```
Customers ──< Orders >── Employees
               │
               └──< OrderDetails >── Products
```

### Tables
| Table | Primary Key | Foreign Keys |
|-------|-------------|--------------|
| Customers | CustomerID | — |
| Employees | EmployeeID | — |
| Products | ProductID | — |
| Orders | OrderID | CustomerID → Customers, EmployeeID → Employees |
| OrderDetails | OrderDetailID | OrderID → Orders, ProductID → Products |

---

## Advanced Database Objects

### Views
| View | Purpose |
|------|---------|
| `vw_OrderSummary` | Full order info joined with customer and employee |
| `vw_DailySales` | Daily revenue aggregation (last 30 days) |
| `vw_ProductPerformance` | Units sold + revenue per product |
| `vw_LowStock` | Products with stock < 10 |

### Stored Procedures
| Procedure | Description |
|-----------|-------------|
| `sp_CreateOrder` | Creates an order, returns new OrderID |
| `sp_AddOrderItem` | Validates stock, inserts order detail |
| `sp_UpdateOrderStatus` | Updates order status |
| `sp_MonthlySalesReport` | Returns orders for given year/month |
| `sp_RestockProduct` | Increases product stock |

### User-Defined Functions
| Function | Returns |
|----------|---------|
| `fn_OrderTotal(OrderID)` | Total value of an order |
| `fn_ApplyDiscount(Amount, Pct)` | Amount after discount |
| `fn_CustomerTotalSpend(CustomerID)` | Lifetime spend per customer |

### Triggers
| Trigger | Event |
|---------|-------|
| `trg_AfterOrderDetailInsert` | Decreases stock on new order item |
| `trg_AfterOrderDetailDelete` | Restores stock on item deletion |
| `trg_AfterOrderDetailUpdate` | Adjusts stock on quantity change |
| `trg_BeforeOrderUpdate` | Validates order status transitions |
| `trg_AfterOrderCancel` | Restores stock on order cancellation |

---

## Setup Instructions

### 1. Prerequisites
- MySQL 8.0+
- Python 3.8+
- Required Python packages (see `requirements.txt`)

### 2. Database Setup
```bash
mysql -u root -p < sql/01_schema.sql
mysql -u root -p < sql/02_sample_data.sql
mysql -u root -p < sql/03_advanced_objects.sql
```

### 3. Python Setup
```bash
pip install -r requirements.txt
```

### 4. Configure Environment (optional — environment variables)
Create a `.env` file in the `python/` directory:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=app_user
DB_PASSWORD=AppUser@2024!
DB_NAME=sales_management
```

### 5. Run the GUI Application
```bash
cd python
python -m gui.app
```

### 6. Export Reports (optional)
Reports can be exported as CSV from the GUI.

---

## Database Security
Four user accounts are created with least-privilege access:

| User | Role | Permissions |
|------|------|-------------|
| `sales_rep` | Sales representative | SELECT/INSERT/UPDATE on Orders, OrderDetails; SELECT on Customers, Products |
| `inventory` | Inventory clerk | SELECT/INSERT/UPDATE on Products |
| `report_viewer` | Read-only analyst | SELECT on all tables |
| `app_user` | Application service | Full DML + EXECUTE on all objects |

---


