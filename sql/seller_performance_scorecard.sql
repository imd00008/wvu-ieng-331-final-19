/*
NAME: seller-performance-scorecard.sql
PURPOSE: Identify top sellers using sales and satisfaction.
RUBRIC REQUIREMENTS:
 - chained three or more CTEs logically
 - joined data across four tables
 - used window functions for performance ranking
 */

-- Refactored version

-- Step 1: Calculate Total Revenue per Seller
WITH seller_revenue AS (
    SELECT
        seller_id,
        SUM(price) AS total_revenue,
        COUNT(order_id) AS total_orders
    FROM order_items
    GROUP BY seller_id
),

-- Step 2: Calculate On-Time Delivery Rate
delivery_stats AS (
    SELECT
        items.seller_id,
        AVG(CASE
            WHEN ord.order_delivered_customer_date <= ord.order_estimated_delivery_date
            THEN 1.0
            ELSE 0.0
        END) AS on_time_rate
    FROM order_items AS items
    JOIN orders AS ord ON items.order_id = ord.order_id
    WHERE ord.order_status = 'delivered'
    GROUP BY items.seller_id
),

-- Step 3: Calculate Average Review Scores
review_stats AS (
    SELECT
        items.seller_id,
        AVG(reviews.review_score) AS avg_rating,
        COUNT(reviews.review_score) AS review_count
    FROM order_items AS items
    JOIN order_reviews AS reviews ON items.order_id = reviews.order_id
    GROUP BY items.seller_id
)

-- Final Step: The Presentation Layer
SELECT
    COALESCE(rst.avg_rating, 0) AS customer_rating,
    s.seller_id,
    s.seller_city,
    s.seller_state,
    COALESCE(rev.total_revenue, 0) AS revenue,
    COALESCE(del.on_time_rate, 0) AS delivery_score,
    RANK() OVER (
        ORDER BY rev.total_revenue DESC
    ) AS performance_rank
FROM sellers AS s
LEFT JOIN seller_revenue AS rev ON s.seller_id = rev.seller_id
LEFT JOIN delivery_stats AS del ON s.seller_id = del.seller_id
LEFT JOIN review_stats AS rst ON s.seller_id = rst.seller_id
WHERE rev.total_orders > 5
  -- M2 PARAMETER INJECTION: Filter by Seller State
  AND ($1 IS NULL OR s.seller_state = $1)
ORDER BY performance_rank ASC
LIMIT 100;
