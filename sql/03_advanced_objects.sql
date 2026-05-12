-- ============================================================
-- PROJECT 03: SALES MANAGEMENT SYSTEM
-- File: 03_advanced_objects.sql
-- Views | Stored Procedures | UDFs | Triggers
-- ============================================================

DELIMITER $$

-- ============================================================
-- VIEWS
-- ============================================================

-- View: Full order summary
CREATE OR REPLACE VIEW vw_OrderSummary AS
SELECT
  o.OrderID,
  o.OrderDate,
  o.Status,
  c.CustomerName,
  c.PhoneNumber AS CustomerPhone,
  e.EmployeeName AS SalesRep,
  COUNT(od.OrderDetailID)                       AS TotalItems,
  SUM(od.Quantity * od.SalePrice)               AS TotalAmount
FROM Orders o
JOIN Customers    c  ON c.CustomerID  = o.CustomerID
LEFT JOIN Employees e ON e.EmployeeID = o.EmployeeID
JOIN OrderDetails od  ON od.OrderID   = o.OrderID
GROUP BY o.OrderID, o.OrderDate, o.Status,
         c.CustomerName, c.PhoneNumber, e.EmployeeName$$

-- View: Daily sales report
CREATE OR REPLACE VIEW vw_DailySales AS
SELECT
  DATE(o.OrderDate)               AS SaleDate,
  COUNT(DISTINCT o.OrderID)       AS TotalOrders,
  SUM(od.Quantity * od.SalePrice) AS DailyRevenue
FROM Orders o
JOIN OrderDetails od ON od.OrderID = o.OrderID
WHERE o.Status != 'Cancelled'
GROUP BY DATE(o.OrderDate)
ORDER BY SaleDate DESC$$

-- View: Product sales performance
CREATE OR REPLACE VIEW vw_ProductPerformance AS
SELECT
  p.ProductID,
  p.ProductName,
  p.Category,
  p.Price,
  p.StockQuantity,
  COALESCE(SUM(od.Quantity), 0)                AS TotalSold,
  COALESCE(SUM(od.Quantity * od.SalePrice), 0) AS TotalRevenue
FROM Products p
LEFT JOIN OrderDetails od ON od.ProductID = p.ProductID
LEFT JOIN Orders       o  ON o.OrderID    = od.OrderID
WHERE o.Status != 'Cancelled'
   OR o.OrderID IS NULL
GROUP BY p.ProductID, p.ProductName, p.Category, p.Price, p.StockQuantity$$

-- View: Low stock alert (stock < 10)
CREATE OR REPLACE VIEW vw_LowStock AS
SELECT ProductID, ProductName, Category, StockQuantity
FROM Products
WHERE StockQuantity < 10
ORDER BY StockQuantity ASC$$


-- ============================================================
-- USER-DEFINED FUNCTIONS
-- ============================================================

DROP FUNCTION IF EXISTS fn_OrderTotal$$
CREATE FUNCTION fn_OrderTotal(p_OrderID INT)
RETURNS DECIMAL(15,2)
NOT DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE v_total DECIMAL(15,2);
  SELECT COALESCE(SUM(Quantity * SalePrice), 0)
    INTO v_total
    FROM OrderDetails
   WHERE OrderID = p_OrderID;
  RETURN v_total;
END$$

DROP FUNCTION IF EXISTS fn_ApplyDiscount$$
CREATE FUNCTION fn_ApplyDiscount(p_Amount DECIMAL(15,2), p_PctDiscount DECIMAL(5,2))
RETURNS DECIMAL(15,2)
NO SQL
DETERMINISTIC
BEGIN
  IF p_PctDiscount < 0 OR p_PctDiscount > 100 THEN
    RETURN p_Amount;
  END IF;
  RETURN ROUND(p_Amount * (1 - p_PctDiscount / 100), 2);
END$$

DROP FUNCTION IF EXISTS fn_CustomerTotalSpend$$
CREATE FUNCTION fn_CustomerTotalSpend(p_CustomerID INT)
RETURNS DECIMAL(15,2)
NOT DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE v_total DECIMAL(15,2);
  SELECT COALESCE(SUM(od.Quantity * od.SalePrice), 0)
    INTO v_total
    FROM Orders o
    JOIN OrderDetails od ON od.OrderID = o.OrderID
   WHERE o.CustomerID = p_CustomerID
     AND o.Status != 'Cancelled';
  RETURN v_total;
END$$


-- ============================================================
-- STORED PROCEDURES
-- ============================================================

-- 1. Procedure: Create a new order
DROP PROCEDURE IF EXISTS sp_CreateOrder$$
CREATE PROCEDURE sp_CreateOrder(
  IN  p_CustomerID INT,
  IN  p_EmployeeID INT,
  IN  p_Notes      TEXT,
  OUT p_OrderID    INT
)
BEGIN
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;  
  END;

  START TRANSACTION;

  INSERT INTO Orders (CustomerID, EmployeeID, OrderDate, Status, Notes)
  VALUES (p_CustomerID, p_EmployeeID, NOW(), 'Pending', p_Notes);

  SET p_OrderID = LAST_INSERT_ID();

  COMMIT;
END$$


-- 2. Procedure: Add item to an order
DROP PROCEDURE IF EXISTS sp_AddOrderItem$$
CREATE PROCEDURE sp_AddOrderItem(
  IN p_OrderID   INT,
  IN p_ProductID INT,
  IN p_Quantity  INT
)
BEGIN
  DECLARE v_price   DECIMAL(15,2);
  DECLARE v_stock   INT;
  DECLARE v_status  VARCHAR(20);
  DECLARE v_oldQty  INT DEFAULT NULL;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  START TRANSACTION;

  -- Lock and check order
  SELECT Status INTO v_status
    FROM Orders
   WHERE OrderID = p_OrderID
   FOR UPDATE;

  IF v_status IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Order not found.';
  END IF;

  IF v_status NOT IN ('Pending', 'Processing') THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Items can only be added to Pending or Processing orders.';
  END IF;

  -- Lock and check product stock
  SELECT Price, StockQuantity INTO v_price, v_stock
    FROM Products
   WHERE ProductID = p_ProductID
   FOR UPDATE;

  IF v_stock < p_Quantity THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Insufficient stock for the requested quantity.';
  END IF;

  -- Lock existing OrderDetail row if exists (prevent race condition)
  SELECT Quantity INTO v_oldQty
    FROM OrderDetails
   WHERE OrderID = p_OrderID AND ProductID = p_ProductID
   FOR UPDATE;

  IF v_oldQty IS NOT NULL THEN
    UPDATE OrderDetails
       SET Quantity = v_oldQty + p_Quantity
     WHERE OrderID = p_OrderID AND ProductID = p_ProductID;
  ELSE
    INSERT INTO OrderDetails (OrderID, ProductID, Quantity, SalePrice)
    VALUES (p_OrderID, p_ProductID, p_Quantity, v_price);
  END IF;

  COMMIT;
END$$


-- 3. Procedure: Update order status
DROP PROCEDURE IF EXISTS sp_UpdateOrderStatus$$
CREATE PROCEDURE sp_UpdateOrderStatus(
  IN p_OrderID INT,
  IN p_Status  VARCHAR(20)
)
BEGIN
  DECLARE v_exists INT DEFAULT 0;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  START TRANSACTION;

  -- Lock row, kiểm tra order tồn tại
  SELECT COUNT(*) INTO v_exists
    FROM Orders
   WHERE OrderID = p_OrderID
   FOR UPDATE;

  IF v_exists = 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Order not found.';
  END IF;

  -- Validate giá trị ENUM hợp lệ
  IF p_Status NOT IN ('Pending','Processing','Shipped','Delivered','Cancelled') THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Invalid status value.';
  END IF;

  -- Transition rules được enforce bởi trg_BeforeOrderUpdate
  UPDATE Orders SET Status = p_Status WHERE OrderID = p_OrderID;

  COMMIT;
END$$


-- 4. Procedure: Delete an order safely
DROP PROCEDURE IF EXISTS sp_DeleteOrder$$
CREATE PROCEDURE sp_DeleteOrder(IN p_OrderID INT)
BEGIN
  DECLARE v_status VARCHAR(20);

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  START TRANSACTION;

  SELECT Status INTO v_status
    FROM Orders
   WHERE OrderID = p_OrderID
   FOR UPDATE;

  IF v_status IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Order not found.';
  END IF;

  -- Chỉ cho phép xóa đơn đã Cancelled 
  IF v_status != 'Cancelled' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Only Cancelled orders can be deleted. Cancel the order first.';
  END IF;

  -- Xóa OrderDetails thủ công trước
  DELETE FROM OrderDetails WHERE OrderID = p_OrderID;

  -- Sau đó mới xóa Orders
  DELETE FROM Orders WHERE OrderID = p_OrderID;

  COMMIT;
END$$


-- 5. Procedure: Monthly sales report
DROP PROCEDURE IF EXISTS sp_MonthlySalesReport$$
CREATE PROCEDURE sp_MonthlySalesReport(IN p_Year INT, IN p_Month INT)
BEGIN
  DECLARE v_start DATE;
  DECLARE v_end   DATE;

  SET v_start = DATE(CONCAT(p_Year, '-', LPAD(p_Month, 2, '0'), '-01'));
  SET v_end   = LAST_DAY(v_start);

  SELECT
    o.OrderID,
    o.OrderDate,
    c.CustomerName,
    fn_OrderTotal(o.OrderID) AS OrderTotal,
    o.Status
  FROM Orders o
  JOIN Customers c ON c.CustomerID = o.CustomerID
  WHERE o.OrderDate >= v_start
    AND o.OrderDate <= v_end + INTERVAL 1 DAY - INTERVAL 1 SECOND
    AND o.Status != 'Cancelled'
  ORDER BY o.OrderDate;
END$$


-- 6. Procedure: Restock product
DROP PROCEDURE IF EXISTS sp_RestockProduct$$
CREATE PROCEDURE sp_RestockProduct(IN p_ProductID INT, IN p_Quantity INT)
BEGIN
  DECLARE v_count INT DEFAULT 0;

  IF p_Quantity <= 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Restock quantity must be greater than 0.';
  END IF;

  SELECT COUNT(*) INTO v_count FROM Products WHERE ProductID = p_ProductID;

  IF v_count = 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Product not found.';
  END IF;

  UPDATE Products
     SET StockQuantity = StockQuantity + p_Quantity
   WHERE ProductID = p_ProductID;
END$$


-- ============================================================
-- TRIGGERS
-- ============================================================

-- Trigger 1: Trừ kho khi thêm OrderDetail
DROP TRIGGER IF EXISTS trg_AfterOrderDetailInsert$$
CREATE TRIGGER trg_AfterOrderDetailInsert
AFTER INSERT ON OrderDetails
FOR EACH ROW
BEGIN
  UPDATE Products
     SET StockQuantity = StockQuantity - NEW.Quantity
   WHERE ProductID = NEW.ProductID;
END$$


-- Trigger 2: Hoàn kho khi xóa OrderDetail
DROP TRIGGER IF EXISTS trg_AfterOrderDetailDelete$$
CREATE TRIGGER trg_AfterOrderDetailDelete
AFTER DELETE ON OrderDetails
FOR EACH ROW
BEGIN
  DECLARE v_status VARCHAR(20) DEFAULT NULL;

  SELECT Status INTO v_status
    FROM Orders
   WHERE OrderID = OLD.OrderID;

  -- Chỉ restore khi đơn đang active (Pending/Processing/Shipped)
  IF v_status IS NOT NULL
     AND v_status NOT IN ('Cancelled', 'Delivered') THEN
    UPDATE Products
       SET StockQuantity = StockQuantity + OLD.Quantity
     WHERE ProductID = OLD.ProductID;
  END IF;
END$$


-- Trigger 3: Guard kiểm tra stock trước UPDATE
DROP TRIGGER IF EXISTS trg_BeforeOrderDetailUpdate$$
CREATE TRIGGER trg_BeforeOrderDetailUpdate
BEFORE UPDATE ON OrderDetails
FOR EACH ROW
BEGIN
  DECLARE v_stock      INT;
  DECLARE v_extraNeed  INT;

  -- Chỉ kiểm tra khi quantity tăng lên
  IF NEW.Quantity > OLD.Quantity THEN
    SET v_extraNeed = NEW.Quantity - OLD.Quantity;

    SELECT StockQuantity INTO v_stock
      FROM Products
     WHERE ProductID = NEW.ProductID;

    IF v_stock IS NULL THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Product not found.';
    END IF;

    IF v_stock < v_extraNeed THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Insufficient stock for the updated quantity.';
    END IF;
  END IF;
END$$


-- Trigger 4: Điều chỉnh kho sau UPDATE
DROP TRIGGER IF EXISTS trg_AfterOrderDetailUpdate$$
CREATE TRIGGER trg_AfterOrderDetailUpdate
AFTER UPDATE ON OrderDetails
FOR EACH ROW
BEGIN
  UPDATE Products
     SET StockQuantity = StockQuantity + OLD.Quantity - NEW.Quantity
   WHERE ProductID = NEW.ProductID;
END$$


-- Trigger 5: Validate chuyển trạng thái đơn hàng (state machine)
DROP TRIGGER IF EXISTS trg_BeforeOrderUpdate$$
CREATE TRIGGER trg_BeforeOrderUpdate
BEFORE UPDATE ON Orders
FOR EACH ROW
BEGIN
  IF OLD.Status != NEW.Status THEN

    IF OLD.Status = 'Delivered' THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot change the status of a delivered order.';
    END IF;

    IF OLD.Status = 'Cancelled' THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot reactivate a cancelled order.';
    END IF;

    IF NOT (
      (OLD.Status = 'Pending'    AND NEW.Status IN ('Processing', 'Cancelled')) OR
      (OLD.Status = 'Processing' AND NEW.Status IN ('Shipped',    'Cancelled')) OR
      (OLD.Status = 'Shipped'    AND NEW.Status IN ('Delivered',  'Cancelled'))
    ) THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Invalid status transition.';
    END IF;

  END IF;
END$$


-- Trigger 6: Hoàn toàn bộ kho khi hủy đơn
DROP TRIGGER IF EXISTS trg_AfterOrderCancel$$
CREATE TRIGGER trg_AfterOrderCancel
AFTER UPDATE ON Orders
FOR EACH ROW
BEGIN
  IF NEW.Status = 'Cancelled' AND OLD.Status != 'Cancelled' THEN
    UPDATE Products p
      JOIN OrderDetails od ON p.ProductID = od.ProductID
       SET p.StockQuantity = p.StockQuantity + od.Quantity
     WHERE od.OrderID = NEW.OrderID;
  END IF;
END$$

DELIMITER ;

-- ============================================================
-- DATABASE SECURITY
-- ============================================================

CREATE USER IF NOT EXISTS 'sales_rep'@'localhost' IDENTIFIED BY 'SalesRep@2024!';
CREATE USER IF NOT EXISTS 'inventory'@'localhost' IDENTIFIED BY 'Inventory@2024!';
CREATE USER IF NOT EXISTS 'app_user'@'localhost' IDENTIFIED BY 'AppUser@2024!';

-- Quyền dữ liệu cơ bản
GRANT SELECT, INSERT, UPDATE, DELETE ON sales_management.Customers TO 'app_user'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON sales_management.Employees TO 'app_user'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON sales_management.Products  TO 'app_user'@'localhost';

-- Với Orders: Không cho DELETE trực tiếp
GRANT SELECT, INSERT, UPDATE ON sales_management.Orders TO 'app_user'@'localhost';

-- Với OrderDetails: CHỌ CHO DELETE để xóa item
GRANT SELECT, INSERT, UPDATE, DELETE ON sales_management.OrderDetails TO 'app_user'@'localhost';

-- Quyền thực thi các Advanced Objects
GRANT EXECUTE ON sales_management.* TO 'app_user'@'localhost';

-- Quyền xem các báo cáo (Views)
GRANT SELECT ON sales_management.vw_OrderSummary TO 'app_user'@'localhost';
GRANT SELECT ON sales_management.vw_DailySales TO 'app_user'@'localhost';
GRANT SELECT ON sales_management.vw_ProductPerformance TO 'app_user'@'localhost';
GRANT SELECT ON sales_management.vw_LowStock TO 'app_user'@'localhost';

-- Quản lý đơn hàng: Không cho xóa vĩnh viễn
GRANT SELECT, INSERT, UPDATE ON sales_management.Orders TO 'sales_rep'@'localhost';
GRANT SELECT, INSERT, UPDATE ON sales_management.OrderDetails TO 'sales_rep'@'localhost';

-- Chỉ xem thông tin hỗ trợ
GRANT SELECT ON sales_management.Customers TO 'sales_rep'@'localhost';
GRANT SELECT ON sales_management.Products TO 'sales_rep'@'localhost';

-- Thực thi các Procedure liên quan đến bán hàng
GRANT EXECUTE ON PROCEDURE sales_management.sp_CreateOrder TO 'sales_rep'@'localhost';
GRANT EXECUTE ON PROCEDURE sales_management.sp_AddOrderItem TO 'sales_rep'@'localhost';
GRANT EXECUTE ON PROCEDURE sales_management.sp_UpdateOrderStatus TO 'sales_rep'@'localhost';
GRANT EXECUTE ON FUNCTION sales_management.fn_OrderTotal TO 'sales_rep'@'localhost';

-- Quyền cho inventory
GRANT SELECT, INSERT, UPDATE ON sales_management.Products TO 'inventory'@'localhost';
GRANT SELECT ON sales_management.vw_LowStock TO 'inventory'@'localhost';
GRANT EXECUTE ON PROCEDURE sales_management.sp_RestockProduct TO 'inventory'@'localhost';

FLUSH PRIVILEGES;