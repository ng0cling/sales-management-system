-- ============================================================
-- PROJECT 03: SALES MANAGEMENT SYSTEM
-- File: 02_sample_data.sql
-- ============================================================

USE sales_management;

-- ─── Customers ───────────────────────────────────────────────
INSERT INTO Customers (CustomerName, Address, PhoneNumber, Email) VALUES
  ('Nguyen Van An',       '12 Tran Hung Dao, Hanoi',          '0901234501', 'an.nguyen@gmail.com'),
  ('Le Thi Bich',         '45 Nguyen Hue, Ho Chi Minh City',  '0901234502', 'bich.le@yahoo.com'),
  ('Tran Van Cuong',      '78 Le Loi, Da Nang',               '0901234503', 'cuong.tran@outlook.com'),
  ('Pham Thi Dung',       '9 Bach Dang, Hai Phong',           '0901234504', 'dung.pham@gmail.com'),
  ('Hoang Van Em',        '23 Dinh Tien Hoang, Can Tho',      '0901234505', 'em.hoang@gmail.com'),
  ('Bui Thi Phuong',      '56 Hung Vuong, Hue',               '0901234506', 'phuong.bui@gmail.com'),
  ('Vo Van Giang',        '34 Ly Thuong Kiet, Nha Trang',     '0901234507', 'giang.vo@gmail.com');

-- ─── Employees ───────────────────────────────────────────────
INSERT INTO Employees (EmployeeName, JobTitle, Email, PhoneNumber, HireDate) VALUES
  ('Nguyen Thi Hoa',   'Sales Manager',       'hoa.nguyen@company.vn', '0911111101', '2021-03-15'),
  ('Tran Van Hung',    'Sales Representative','hung.tran@company.vn',  '0911111102', '2022-06-01'),
  ('Le Minh Khoa',     'Inventory Clerk',     'khoa.le@company.vn',    '0911111103', '2022-09-10'),
  ('Pham Quynh Lan',   'Accountant',          'lan.pham@company.vn',   '0911111104', '2023-01-20'),
  ('Hoang Duc Manh',   'Sales Representative','manh.hoang@company.vn', '0911111105', '2023-05-05');

-- ─── Products ────────────────────────────────────────────────
INSERT INTO Products (ProductName, Price, StockQuantity, Category) VALUES
  ('Laptop Dell XPS 15',          28500000,  25, 'Electronics'),
  ('iPhone 15 Pro Max 256GB',     32000000,  40, 'Electronics'),
  ('Samsung Galaxy S24 Ultra',    28000000,  30, 'Electronics'),
  ('Sony WH-1000XM5 Headphones',  8500000,   60, 'Audio'),
  ('Logitech MX Master 3 Mouse',  2200000,  100, 'Peripherals'),
  ('Mechanical Keyboard Keychron K2', 2800000, 80, 'Peripherals'),
  ('LG 27" 4K Monitor',           12000000,  20, 'Displays'),
  ('iPad Air 5th Gen',            17500000,  35, 'Electronics'),
  ('USB-C Hub 7-in-1',             850000,  150, 'Accessories'),
  ('Webcam Logitech C920 HD',     2100000,   70, 'Peripherals');

-- ─── Orders ──────────────────────────────────────────────────
INSERT INTO Orders (CustomerID, EmployeeID, OrderDate, Status) VALUES
  (1, 2, '2026-01-10 09:30:00', 'Delivered'),
  (2, 2, '2026-01-15 10:00:00', 'Delivered'),
  (3, 5, '2026-02-03 14:20:00', 'Shipped'),
  (4, 2, '2026-02-20 11:00:00', 'Processing'),
  (5, 5, '2026-03-05 16:00:00', 'Pending'),
  (1, 2, '2026-03-12 09:00:00', 'Delivered'),
  (6, 5, '2026-03-18 13:00:00', 'Cancelled'),
  (7, 2, '2026-04-01 10:30:00', 'Delivered');

-- ─── OrderDetails ────────────────────────────────────────────
INSERT INTO OrderDetails (OrderID, ProductID, Quantity, SalePrice) VALUES
  (1, 1, 1, 28500000),
  (1, 5, 2,  2200000),
  (2, 2, 1, 32000000),
  (2, 4, 1,  8500000),
  (3, 7, 1, 12000000),
  (3, 6, 1,  2800000),
  (4, 3, 1, 28000000),
  (5, 8, 1, 17500000),
  (5, 9, 3,   850000),
  (6, 1, 2, 28500000),
  (7, 2, 1, 32000000),
  (8, 10,2,  2100000);
