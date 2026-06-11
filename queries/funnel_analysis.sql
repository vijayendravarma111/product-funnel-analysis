-- SQL Funnel Analysis using CTEs
-- This query aggregates events to calculate counts, step-by-step conversions, drop-off percentages, and overall conversion rates by A/B test group.

WITH user_funnel_stages AS (
    -- Step 1: Pivot event streams to find which funnel stages each user reached
    SELECT 
        user_id,
        ab_group,
        MAX(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) AS has_view,
        MAX(CASE WHEN event_type = 'cart' THEN 1 ELSE 0 END) AS has_cart,
        MAX(CASE WHEN event_type = 'checkout' THEN 1 ELSE 0 END) AS has_checkout,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS has_purchase
    FROM events
    GROUP BY user_id, ab_group
),

funnel_aggregates AS (
    -- Step 2: Sum the stages grouped by A/B testing groups
    SELECT
        ab_group,
        SUM(has_view) AS views,
        SUM(has_cart) AS carts,
        SUM(has_checkout) AS checkouts,
        SUM(has_purchase) AS purchases
    FROM user_funnel_stages
    GROUP BY ab_group
    
    UNION ALL
    
    -- Combine with aggregate overall totals across all groups
    SELECT
        'Overall' AS ab_group,
        SUM(has_view) AS views,
        SUM(has_cart) AS carts,
        SUM(has_checkout) AS checkouts,
        SUM(has_purchase) AS purchases
    FROM user_funnel_stages
)

-- Step 3: Compute conversion and drop-off metrics for each step
SELECT
    ab_group,
    views AS stage_1_views,
    
    carts AS stage_2_carts,
    ROUND(CAST(carts AS REAL) / views * 100, 2) AS view_to_cart_conv_pct,
    ROUND((1.0 - CAST(carts AS REAL) / views) * 100, 2) AS view_to_cart_drop_pct,
    
    checkouts AS stage_3_checkouts,
    ROUND(CAST(checkouts AS REAL) / carts * 100, 2) AS cart_to_checkout_conv_pct,
    ROUND((1.0 - CAST(checkouts AS REAL) / carts) * 100, 2) AS cart_to_checkout_drop_pct,
    
    purchases AS stage_4_purchases,
    ROUND(CAST(purchases AS REAL) / checkouts * 100, 2) AS checkout_to_purchase_conv_pct,
    ROUND((1.0 - CAST(purchases AS REAL) / checkouts) * 100, 2) AS checkout_to_purchase_drop_pct,
    
    ROUND(CAST(purchases AS REAL) / views * 100, 2) AS overall_conversion_pct
FROM funnel_aggregates;
