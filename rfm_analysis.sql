-- ============================================================
-- CUSTOMER RFM SEGMENTATION - MYSQL
-- ============================================================

CREATE DATABASE IF NOT EXISTS rfm_analysis;
USE rfm_analysis;

-- ------------------------------------------------------------
-- 1. TRANSACTION TABLE
-- ------------------------------------------------------------

DROP TABLE IF EXISTS transactions;

CREATE TABLE transactions (
    InvoiceNo VARCHAR(30),
    StockCode VARCHAR(50),
    Description VARCHAR(255),
    Quantity INT,
    InvoiceDate DATETIME,
    UnitPrice DECIMAL(12,4),
    CustomerID INT,
    Country VARCHAR(100)
);

-- Import the cleaned transaction CSV into the table using
-- MySQL Workbench's Table Data Import Wizard or LOAD DATA.
--
-- Example:
-- LOAD DATA LOCAL INFILE 'path/to/online_retail_II.csv'
-- INTO TABLE transactions
-- FIELDS TERMINATED BY ','
-- ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS;

-- ------------------------------------------------------------
-- 2. BASIC DATA CHECK
-- ------------------------------------------------------------

SELECT COUNT(*) AS total_rows
FROM transactions;

SELECT
    MIN(InvoiceDate) AS first_transaction,
    MAX(InvoiceDate) AS last_transaction
FROM transactions;

-- ------------------------------------------------------------
-- 3. CLEAN TRANSACTION VIEW
-- ------------------------------------------------------------

DROP VIEW IF EXISTS clean_transactions;

CREATE VIEW clean_transactions AS
SELECT
    InvoiceNo,
    StockCode,
    Description,
    Quantity,
    InvoiceDate,
    UnitPrice,
    CustomerID,
    Country,
    Quantity * UnitPrice AS Revenue
FROM transactions
WHERE CustomerID IS NOT NULL
  AND Quantity > 0
  AND UnitPrice > 0
  AND InvoiceNo NOT LIKE 'C%';

-- ------------------------------------------------------------
-- 4. CUSTOMER-LEVEL RFM TABLE
-- ------------------------------------------------------------

DROP VIEW IF EXISTS customer_rfm;

CREATE VIEW customer_rfm AS
SELECT
    CustomerID,

    DATEDIFF(
        (SELECT MAX(InvoiceDate) FROM clean_transactions),
        MAX(InvoiceDate)
    ) AS Recency,

    COUNT(DISTINCT InvoiceNo) AS Frequency,

    ROUND(SUM(Revenue), 2) AS Monetary

FROM clean_transactions
GROUP BY CustomerID;

-- ------------------------------------------------------------
-- 5. VIEW RFM TABLE
-- ------------------------------------------------------------

SELECT *
FROM customer_rfm
ORDER BY Monetary DESC;

-- ------------------------------------------------------------
-- 6. TOP CUSTOMERS BY MONETARY VALUE
-- ------------------------------------------------------------

SELECT
    CustomerID,
    Recency,
    Frequency,
    Monetary
FROM customer_rfm
ORDER BY Monetary DESC
LIMIT 20;

-- ------------------------------------------------------------
-- 7. MOST RECENT CUSTOMERS
-- ------------------------------------------------------------

SELECT
    CustomerID,
    Recency,
    Frequency,
    Monetary
FROM customer_rfm
ORDER BY Recency ASC
LIMIT 20;

-- ------------------------------------------------------------
-- 8. MOST FREQUENT CUSTOMERS
-- ------------------------------------------------------------

SELECT
    CustomerID,
    Recency,
    Frequency,
    Monetary
FROM customer_rfm
ORDER BY Frequency DESC
LIMIT 20;

-- ------------------------------------------------------------
-- 9. SIMPLE BUSINESS SEGMENT EXAMPLES
-- ------------------------------------------------------------

SELECT
    CustomerID,
    Recency,
    Frequency,
    Monetary,

    CASE
        WHEN Recency <= 30
             AND Frequency >= 5
             AND Monetary >= 1000
            THEN 'Champions'

        WHEN Recency <= 60
             AND Frequency >= 3
            THEN 'Loyal Customers'

        WHEN Recency <= 30
             AND Frequency <= 2
            THEN 'Recent Customers'

        WHEN Recency > 90
             AND Frequency >= 5
             AND Monetary >= 1000
            THEN 'At Risk'

        WHEN Recency > 180
             AND Frequency <= 2
             AND Monetary < 500
            THEN 'Lost Customers'

        WHEN Monetary >= 1000
            THEN 'High Value'

        ELSE 'Potential Loyalists'
    END AS Segment

FROM customer_rfm;

-- ------------------------------------------------------------
-- 10. SEGMENT SUMMARY
-- ------------------------------------------------------------

WITH segmented AS (
    SELECT
        CustomerID,
        Recency,
        Frequency,
        Monetary,

        CASE
            WHEN Recency <= 30
                 AND Frequency >= 5
                 AND Monetary >= 1000
                THEN 'Champions'

            WHEN Recency <= 60
                 AND Frequency >= 3
                THEN 'Loyal Customers'

            WHEN Recency <= 30
                 AND Frequency <= 2
                THEN 'Recent Customers'

            WHEN Recency > 90
                 AND Frequency >= 5
                 AND Monetary >= 1000
                THEN 'At Risk'

            WHEN Recency > 180
                 AND Frequency <= 2
                 AND Monetary < 500
                THEN 'Lost Customers'

            WHEN Monetary >= 1000
                THEN 'High Value'

            ELSE 'Potential Loyalists'
        END AS Segment

    FROM customer_rfm
)

SELECT
    Segment,
    COUNT(*) AS Customers,
    ROUND(AVG(Recency), 2) AS Avg_Recency,
    ROUND(AVG(Frequency), 2) AS Avg_Frequency,
    ROUND(AVG(Monetary), 2) AS Avg_Monetary,
    ROUND(SUM(Monetary), 2) AS Total_Revenue
FROM segmented
GROUP BY Segment
ORDER BY Total_Revenue DESC;

-- ------------------------------------------------------------
-- 11. HIGH-VALUE CUSTOMERS
-- ------------------------------------------------------------

SELECT
    CustomerID,
    Recency,
    Frequency,
    Monetary
FROM customer_rfm
WHERE Recency <= 30
  AND Frequency >= 5
  AND Monetary >= 1000
ORDER BY Monetary DESC;

-- ------------------------------------------------------------
-- 12. AT-RISK CUSTOMERS
-- ------------------------------------------------------------

SELECT
    CustomerID,
    Recency,
    Frequency,
    Monetary
FROM customer_rfm
WHERE Recency > 90
  AND Frequency >= 5
ORDER BY Monetary DESC;

-- ------------------------------------------------------------
-- 13. LOST CUSTOMERS
-- ------------------------------------------------------------

SELECT
    CustomerID,
    Recency,
    Frequency,
    Monetary
FROM customer_rfm
WHERE Recency > 180
  AND Frequency <= 2
ORDER BY Monetary DESC;
