-- ============================================================
-- Customer Value & Loyalty — SQL Segmentation Layer
-- Engine: SQLite (portable to MySQL/Postgres with no syntax changes
-- needed at this scale — no window functions requiring vendor-specific
-- extensions are used here).
-- Source: customer_features.csv, engineered in feature_engineering.py
-- ============================================================

-- ------------------------------------------------------------
-- Q1. What separates high-value customers from low-value ones,
--     and which profiles show the strongest repeat purchase behavior?
--
-- Uses Loyalty B (value/tenure) as the value axis, cross-referenced
-- with Loyalty A (engagement) and discount usage to see WHAT actually
-- distinguishes the tiers beyond the score itself.
-- ------------------------------------------------------------
SELECT
    loyalty_B,
    COUNT(*) AS customers,
    ROUND(AVG(Age), 1) AS avg_age,
    ROUND(AVG("Purchase Amount (USD)"), 2) AS avg_purchase_amount,
    ROUND(AVG("Previous Purchases"), 1) AS avg_previous_purchases,
    ROUND(AVG(discount_used) * 100, 1) AS pct_using_discount,
    ROUND(AVG(is_subscriber) * 100, 1) AS pct_subscribers,
    ROUND(AVG("Review Rating"), 2) AS avg_review_rating
FROM customer_features
GROUP BY loyalty_B
ORDER BY avg_purchase_amount DESC;

-- ------------------------------------------------------------
-- Q1b. Repeat purchase behavior by engagement tier (Loyalty A) —
--      shows engagement doesn't necessarily mean bigger baskets
-- ------------------------------------------------------------
SELECT
    loyalty_A,
    COUNT(*) AS customers,
    ROUND(AVG("Previous Purchases"), 1) AS avg_previous_purchases,
    ROUND(AVG("Purchase Amount (USD)"), 2) AS avg_purchase_amount,
    ROUND(AVG(discount_used) * 100, 1) AS pct_using_discount
FROM customer_features
GROUP BY loyalty_A
ORDER BY
    CASE loyalty_A
        WHEN 'Low Engagement' THEN 1
        WHEN 'Medium Engagement' THEN 2
        WHEN 'High Engagement' THEN 3
    END;

-- ------------------------------------------------------------
-- Q2. Which seasons and categories are associated with lower-tenure
--     customers vs. those with high previous purchase counts?
--
-- "Tenure" proxy = Previous Purchases. Split into Low/High via median,
-- then see which category/season each group skews toward — this
-- identifies entry-point categories (low tenure) vs. retention
-- categories (high tenure).
-- ------------------------------------------------------------
WITH tenure_split AS (
    SELECT *,
        CASE WHEN "Previous Purchases" >= (
            SELECT AVG("Previous Purchases") FROM customer_features
        ) THEN 'High Tenure' ELSE 'Low Tenure' END AS tenure_group
    FROM customer_features
)
SELECT
    Category,
    tenure_group,
    COUNT(*) AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY tenure_group), 1) AS pct_within_tenure_group
FROM tenure_split
GROUP BY Category, tenure_group
ORDER BY tenure_group, customers DESC;

-- Same cut by season
WITH tenure_split AS (
    SELECT *,
        CASE WHEN "Previous Purchases" >= (
            SELECT AVG("Previous Purchases") FROM customer_features
        ) THEN 'High Tenure' ELSE 'Low Tenure' END AS tenure_group
    FROM customer_features
)
SELECT
    Season,
    tenure_group,
    COUNT(*) AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY tenure_group), 1) AS pct_within_tenure_group
FROM tenure_split
GROUP BY Season, tenure_group
ORDER BY tenure_group, customers DESC;

-- ------------------------------------------------------------
-- Q3. Which geographies signal organic demand vs. discount-driven
--     volume?
--
-- "Organic demand" = high average spend + LOW discount dependency.
-- "Discount-driven" = high volume/spend that relies heavily on
-- discount usage. Ranks states on both axes so you can see which
-- ones the brand could target WITHOUT needing to keep discounting.
-- ------------------------------------------------------------
SELECT
    Location,
    COUNT(*) AS customers,
    ROUND(AVG("Purchase Amount (USD)"), 2) AS avg_purchase_amount,
    ROUND(AVG(discount_used) * 100, 1) AS pct_using_discount,
    ROUND(AVG("Purchase Amount (USD)") * (1 - AVG(discount_used)), 2) AS organic_demand_index
FROM customer_features
GROUP BY Location
HAVING COUNT(*) >= 30   -- filter out states with too few customers to be reliable
ORDER BY organic_demand_index DESC
LIMIT 15;

-- Bottom 15 — most discount-reliant states (opposite end)
SELECT
    Location,
    COUNT(*) AS customers,
    ROUND(AVG("Purchase Amount (USD)"), 2) AS avg_purchase_amount,
    ROUND(AVG(discount_used) * 100, 1) AS pct_using_discount,
    ROUND(AVG("Purchase Amount (USD)") * (1 - AVG(discount_used)), 2) AS organic_demand_index
FROM customer_features
GROUP BY Location
HAVING COUNT(*) >= 30
ORDER BY organic_demand_index ASC
LIMIT 15;

-- ------------------------------------------------------------
-- Bonus: Ideal Customer Profile — the "High Engagement + High Value"
-- intersection (business question 5)
-- ------------------------------------------------------------
SELECT
    Gender,
    ROUND(AVG(Age), 1) AS avg_age,
    Category,
    "Payment Method",
    COUNT(*) AS customers
FROM customer_features
WHERE loyalty_A = 'High Engagement' AND loyalty_B = 'High Value'
GROUP BY Gender, Category, "Payment Method"
ORDER BY customers DESC
LIMIT 10;
