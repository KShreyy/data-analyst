-- ============================================================
-- Retail Sales Performance & Customer Segmentation Analysis
-- Schema + core analysis queries (SQLite dialect; portable to
-- MySQL/Postgres with minor date-function tweaks)
-- ============================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id     INTEGER PRIMARY KEY,
    region          TEXT,
    signup_days_ago INTEGER,
    loyalty_score   REAL
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id   INTEGER PRIMARY KEY,
    customer_id      INTEGER REFERENCES customers(customer_id),
    region           TEXT,
    category         TEXT,
    transaction_date TEXT,
    amount           REAL,
    campaign         TEXT
);

CREATE TABLE IF NOT EXISTS campaign_ab_sessions (
    session_id  INTEGER PRIMARY KEY,
    campaign    TEXT,
    converted   INTEGER
);

-- ------------------------------------------------------------
-- 1. Overall sales KPIs
-- ------------------------------------------------------------
SELECT
    COUNT(*)                         AS total_transactions,
    ROUND(SUM(amount), 2)            AS total_revenue,
    ROUND(AVG(amount), 2)            AS avg_order_value,
    COUNT(DISTINCT customer_id)      AS unique_customers
FROM transactions;

-- ------------------------------------------------------------
-- 2. Revenue by region and category
-- ------------------------------------------------------------
SELECT
    region,
    category,
    COUNT(*)                AS orders,
    ROUND(SUM(amount), 2)   AS revenue
FROM transactions
GROUP BY region, category
ORDER BY revenue DESC;

-- ------------------------------------------------------------
-- 3. Monthly sales trend (seasonality check)
-- ------------------------------------------------------------
SELECT
    strftime('%Y-%m', transaction_date) AS month,
    ROUND(SUM(amount), 2)               AS revenue,
    COUNT(*)                            AS orders
FROM transactions
GROUP BY month
ORDER BY month;

-- ------------------------------------------------------------
-- 4. RFM base table: Recency, Frequency, Monetary per customer
--    ("today" is fixed at the day after the data window ends)
-- ------------------------------------------------------------
WITH last_date AS (
    SELECT DATE(MAX(transaction_date), '+1 day') AS ref_date FROM transactions
),
rfm AS (
    SELECT
        t.customer_id,
        CAST(julianday((SELECT ref_date FROM last_date)) - julianday(MAX(t.transaction_date)) AS INTEGER) AS recency_days,
        COUNT(*)                    AS frequency,
        ROUND(SUM(t.amount), 2)     AS monetary
    FROM transactions t
    GROUP BY t.customer_id
)
SELECT * FROM rfm ORDER BY monetary DESC;

-- ------------------------------------------------------------
-- 5. Revenue concentration by customer decile (Pareto check)
-- ------------------------------------------------------------
WITH cust_rev AS (
    SELECT customer_id, SUM(amount) AS total_spend
    FROM transactions
    GROUP BY customer_id
),
ranked AS (
    SELECT
        customer_id,
        total_spend,
        NTILE(10) OVER (ORDER BY total_spend DESC) AS decile
    FROM cust_rev
)
SELECT
    decile,
    COUNT(*)                       AS customers,
    ROUND(SUM(total_spend), 2)     AS decile_revenue,
    ROUND(100.0 * SUM(total_spend) / (SELECT SUM(total_spend) FROM cust_rev), 2) AS pct_of_total_revenue
FROM ranked
GROUP BY decile
ORDER BY decile;

-- ------------------------------------------------------------
-- 6. Campaign A/B conversion rate comparison
-- ------------------------------------------------------------
SELECT
    campaign,
    COUNT(*)                              AS sessions,
    SUM(converted)                        AS conversions,
    ROUND(100.0 * SUM(converted) / COUNT(*), 2) AS conversion_rate_pct
FROM campaign_ab_sessions
GROUP BY campaign;
