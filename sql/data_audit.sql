/*
NAME: data_audit.sql
PURPOSE: Systematic Data Quality Audit of the Olist E-Commerce Dataset
RUBRIC REQUIREMENTS:
 - Profile all tables (Row Counts)
 - Check NULL rates for key columns
 - Detect abandoned foreign keys
 - Analyze date range coverage and gaps
 - Detect duplicate primary keys
*/

-- HOW TO USE:
-- We used CTEs to keep this organized like a report
-- To view a specific section, change the final statement 'SELECT * FROM summary_report'
-- to 'SELECT * FROM [CTE_NAME]'

-- Refactored version

WITH

-- SECTION 1: ROW COUNTS
-- Filters the orders table to the specific time window being audited.
table_counts AS (
    SELECT 'orders' AS table_name, count(*) AS total_rows
    FROM orders
    WHERE ($1 IS NULL OR CAST(order_purchase_timestamp AS DATE) >= $1)
      AND ($2 IS NULL OR CAST(order_purchase_timestamp AS DATE) <= $2)
    UNION ALL SELECT 'order_items', count(*) FROM order_items
    UNION ALL SELECT 'order_payments', count(*) FROM order_payments
    UNION ALL SELECT 'order_reviews', count(*) FROM order_reviews
    UNION ALL SELECT 'customers', count(*) FROM customers
    UNION ALL SELECT 'sellers', count(*) FROM sellers
    UNION ALL SELECT 'products', count(*) FROM products
    UNION ALL SELECT 'category_translation', count(*) FROM category_translation
    UNION ALL SELECT 'geolocation', count(*) FROM geolocation
),

-- SECTION 2: NULL RATE ANALYSIS
-- Checks null delivery dates specifically within the audited time window.
null_rates AS (
    SELECT
        'Product Category' AS metric,
        count(*) AS total,
        count(*) FILTER (WHERE product_category_name IS NULL) AS null_count,
        round(100.0 * count(*) FILTER (WHERE product_category_name IS NULL) / count(*), 2) AS null_pct
    FROM products
    UNION ALL
    SELECT
        'Delivery Date',
        count(*),
        count(*) FILTER (WHERE order_delivered_customer_date IS NULL),
        round(100.0 * count(*) FILTER (WHERE order_delivered_customer_date IS NULL) / count(*), 2)
    FROM orders
    WHERE ($1 IS NULL OR CAST(order_purchase_timestamp AS DATE) >= $1)
      AND ($2 IS NULL OR CAST(order_purchase_timestamp AS DATE) <= $2)
),

-- SECTION 3: ABANDONED FOREIGN KEYS
-- We check if orders point to customers that don't exist within the time window.
abandoned_keys AS (
    SELECT
        'Orders to Customers' AS relationship,
        count(o.order_id) AS abandon_count
    FROM orders o
    LEFT JOIN customers c ON o.customer_id = c.customer_id
    WHERE c.customer_id IS NULL
      AND ($1 IS NULL OR CAST(o.order_purchase_timestamp AS DATE) >= $1)
      AND ($2 IS NULL OR CAST(o.order_purchase_timestamp AS DATE) <= $2)
    UNION ALL
    SELECT
        'Items to Products',
        count(oi.order_id)
    FROM order_items oi
    LEFT JOIN products p ON oi.product_id = p.product_id
    WHERE p.product_id IS NULL
),

-- SECTION 4: DATE RANGE & GAPS
-- Confirms the actual date range the audit is analyzing.
date_profile AS (
    SELECT
        min(order_purchase_timestamp) AS start_date,
        max(order_purchase_timestamp) AS end_date,
        date_diff('day', min(order_purchase_timestamp), max(order_purchase_timestamp)) AS total_days_covered
    FROM orders
    WHERE ($1 IS NULL OR CAST(order_purchase_timestamp AS DATE) >= $1)
      AND ($2 IS NULL OR CAST(order_purchase_timestamp AS DATE) <= $2)
),

-- SECTION 5: DUPLICATE DETECTION
-- Primary keys MUST be unique. If count > 0, we have an issue with our data.
duplicate_pks AS (
    SELECT 'orders' AS table_name, count(*) AS duplicate_count
    FROM (
        SELECT order_id
        FROM orders
        WHERE ($1 IS NULL OR CAST(order_purchase_timestamp AS DATE) >= $1)
          AND ($2 IS NULL OR CAST(order_purchase_timestamp AS DATE) <= $2)
        GROUP BY 1 HAVING count(*) > 1
    )
    UNION ALL
    SELECT 'products', count(*)
    FROM (SELECT product_id FROM products GROUP BY 1 HAVING count(*) > 1)
),

-- FINAL SUMMARY
summary_report AS (
    SELECT
        (SELECT count(*) FROM table_counts) AS tables_checked,
        (SELECT sum(abandon_count) FROM abandoned_keys) AS total_abandons_found,
        (SELECT total_days_covered FROM date_profile) AS days_of_data,
        (SELECT sum(duplicate_count) FROM duplicate_pks) AS duplicate_pk_issues
)

SELECT * FROM summary_report;
