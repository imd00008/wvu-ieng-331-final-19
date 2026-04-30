/*
NAME: deliver-time-by-geolocation.sql
PURPOSE: Identify regional patterns in delivery estimate accuracy
RUBRIC REQUIREMENTS:
 - chained 3 CTEs for logical progression
 - joined 3 distincy olist database tables
 - works in duckdb cli
 - utilized window functions to determine ranking
*/

-- Refactored version

-- STEP 1: Gather the raw data from 3 different tables.
WITH base_delivery_data AS (
    SELECT
        o.order_id,
        c.customer_state,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,
        o.order_purchase_timestamp,
        oi.price
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    -- Filter: We only care about orders that actually arrived.
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_estimated_delivery_date IS NOT NULL
      -- M2 PARAMETER INJECTION: Filter by order purchase date
      -- If $1 or $2 are NULL, it analyzes all historical deliveries.
      AND ($1 IS NULL OR CAST(o.order_purchase_timestamp AS DATE) >= $1)
      AND ($2 IS NULL OR CAST(o.order_purchase_timestamp AS DATE) <= $2)
),

-- STEP 2: Perform 'Date Arithmetic' to find the gaps.
delivery_calculations AS (
    SELECT
        customer_state,
        -- date_diff('day', start, end) tells us how many days passed.
        -- A positive number means the package arrived AFTER the estimate (Late).
        -- A negative number means it arrived BEFORE the estimate (Early).
        date_diff('day', order_estimated_delivery_date, order_delivered_customer_date) AS accuracy_gap,
        price
    FROM base_delivery_data
),

-- STEP 3: Summarize the data by state (Aggregation).
state_performance_metrics AS (
    SELECT
        customer_state,
        -- ROUND(AVG(...), 2) gives us the average delay rounded to 2 decimals.
        ROUND(AVG(accuracy_gap), 2) AS avg_days_off_estimate,
        COUNT(DISTINCT customer_state) AS state_count,
        COUNT(*) AS total_orders_analyzed
    FROM delivery_calculations
    GROUP BY customer_state
)

-- We want to see who is the "worst" or "best" (highest positive gap).
SELECT
    RANK() OVER (ORDER BY avg_days_off_estimate DESC) AS national_unreliability_rank,
    customer_state,
    avg_days_off_estimate,
    total_orders_analyzed
FROM state_performance_metrics
ORDER BY avg_days_off_estimate DESC;
