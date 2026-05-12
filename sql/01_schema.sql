-- ============================================================
-- PROJECT 03: SALES MANAGEMENT SYSTEM
-- ============================================================

CREATE DATABASE IF NOT EXISTS sales_management
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE sales_management;

-- ─────────────────────────────────────────────────────────────
-- TABLE: Customers
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Customers (
  CustomerID    INT            NOT NULL AUTO_INCREMENT,
  CustomerName  VARCHAR(100)   NOT NULL,
  Address       VARCHAR(255)   NOT NULL,
  PhoneNumber   VARCHAR(20)    NOT NULL UNIQUE,
  Email         VARCHAR(100)            UNIQUE,
  CreatedAt     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT pk_customers PRIMARY KEY (CustomerID)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────────────────────
-- TABLE: Employees
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Employees (
  EmployeeID    INT            NOT NULL AUTO_INCREMENT,
  EmployeeName  VARCHAR(100)   NOT NULL,
  JobTitle      VARCHAR(80)    NOT NULL,
  Email         VARCHAR(100)            UNIQUE,
  PhoneNumber   VARCHAR(20),
  HireDate      DATE           NOT NULL DEFAULT (CURRENT_DATE),
  CONSTRAINT pk_employees PRIMARY KEY (EmployeeID)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────────────────────
-- TABLE: Products
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Products (
  ProductID     INT              NOT NULL AUTO_INCREMENT,
  ProductName   VARCHAR(150)     NOT NULL,
  Price         DECIMAL(15, 2)   NOT NULL CHECK (Price >= 0),
  StockQuantity INT              NOT NULL DEFAULT 0 CHECK (StockQuantity >= 0),
  Category      VARCHAR(80),
  CreatedAt     DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT pk_products PRIMARY KEY (ProductID)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────────────────────
-- TABLE: Orders
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Orders (
  OrderID      INT          NOT NULL AUTO_INCREMENT,
  CustomerID   INT          NOT NULL,
  EmployeeID   INT,
  OrderDate    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  Status       ENUM('Pending','Processing','Shipped','Delivered','Cancelled')
                            NOT NULL DEFAULT 'Pending',
  Notes        TEXT,
  CONSTRAINT pk_orders     PRIMARY KEY (OrderID),
  CONSTRAINT fk_ord_cust   FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
                            ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_ord_emp    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
                            ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────────────────────
-- TABLE: OrderDetails
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS OrderDetails (
  OrderDetailID INT              NOT NULL AUTO_INCREMENT,
  OrderID       INT              NOT NULL,
  ProductID     INT              NOT NULL,
  Quantity      INT              NOT NULL CHECK (Quantity > 0),
  SalePrice     DECIMAL(15, 2)   NOT NULL CHECK (SalePrice >= 0),
  CONSTRAINT pk_orderdetails  PRIMARY KEY (OrderDetailID),
  CONSTRAINT fk_od_order      FOREIGN KEY (OrderID)    REFERENCES Orders(OrderID)
                               ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_od_product    FOREIGN KEY (ProductID)  REFERENCES Products(ProductID)
                               ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT uq_order_product UNIQUE (OrderID, ProductID)
) ENGINE=InnoDB;

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_orders_customer  ON Orders(CustomerID);
CREATE INDEX idx_orders_date      ON Orders(OrderDate);
CREATE INDEX idx_orders_status    ON Orders(Status);
CREATE INDEX idx_products_name    ON Products(ProductName);
CREATE INDEX idx_products_cat     ON Products(Category);
CREATE INDEX idx_od_product       ON OrderDetails(ProductID);
CREATE INDEX idx_customers_phone  ON Customers(PhoneNumber);
