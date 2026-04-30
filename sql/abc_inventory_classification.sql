/* NAME: abc-inventory-classification.sql
PURPOSE: to classify olist products into A,B,C tiers based on their revenuer contribution to prioritize inventory and marketing efforts
RUBRIC REQUIREMENTS
 - Defines a specific, actionable question and a multi-step analytical strategy
 - Implements a multi-step analysis by chaining 3+ CTEs in a logical progression
 - Utilizes window functions (OVER), multi-table joins, and advanced aggregations
 - Produces a clean, rounded, and sorted output designed for stakeholder readability
*/

-- Refactored version

WITH product_revenue AS (
    SELECT
        p.product_id,
        p.product_category_name,
        ROUND(SUM(oi.price),2) AS total_item_revenue
    FROM products p
    JOIN order_items oi ON p.product_id = oi.product_id
    -- M2 PARAMETER INJECTION:
    -- If $1 is passed from Python, it filters to that category.
    -- If None/NULL is passed, it calculates the entire dataset.
    WHERE ($1 IS NULL OR p.product_category_name = $1)
    GROUP BY p.product_id, p.product_category_name
),

cumulative_revenue AS (
    SELECT
        product_id,
        product_category_name,
        total_item_revenue,
        SUM(total_item_revenue) OVER (
            ORDER BY total_item_revenue DESC
        ) AS running_revenue,
        SUM(total_item_revenue) OVER () AS total_company_revenue
    FROM product_revenue
),

percentage_calc AS (
    SELECT
        product_id,
        product_category_name,
        total_item_revenue,
        running_revenue,
        (running_revenue / total_company_revenue) AS cumulative_percent
    FROM cumulative_revenue
)

SELECT
    product_id,
    product_category_name,
    total_item_revenue,
    cumulative_percent,
    CASE
        WHEN cumulative_percent <= 0.80 THEN 'A'
        WHEN cumulative_percent <= 0.95 THEN 'B'
        ELSE 'C'
    END AS abc_tier
FROM percentage_calc
ORDER BY total_item_revenue DESC;
