-- ============================================================
-- NIFTY 50 Sector Performance & Market Trend Analysis
-- Schema + core analysis queries (SQLite dialect)
-- ============================================================

CREATE TABLE IF NOT EXISTS sector_prices (
    date    TEXT,
    sector  TEXT,
    close   REAL,
    volume  INTEGER
);

-- ------------------------------------------------------------
-- 1. Total return per sector over the full window
-- ------------------------------------------------------------
WITH bounds AS (
    SELECT sector, MIN(date) AS first_date, MAX(date) AS last_date
    FROM sector_prices GROUP BY sector
),
first_last AS (
    SELECT sp.sector,
           MAX(CASE WHEN sp.date = b.first_date THEN sp.close END) AS first_close,
           MAX(CASE WHEN sp.date = b.last_date THEN sp.close END)  AS last_close
    FROM sector_prices sp
    JOIN bounds b ON sp.sector = b.sector
    GROUP BY sp.sector
)
SELECT sector,
       ROUND(first_close, 2) AS start_price,
       ROUND(last_close, 2)  AS end_price,
       ROUND(100.0 * (last_close - first_close) / first_close, 2) AS total_return_pct
FROM first_last
ORDER BY total_return_pct DESC;

-- ------------------------------------------------------------
-- 2. 30-day rolling volatility (via window function on daily returns)
--    (daily_return computed with LAG; rolling stdev approximated in Python
--     for exact results — SQL window frame shown here for reference)
-- ------------------------------------------------------------
WITH daily_returns AS (
    SELECT sector, date, close,
           (close - LAG(close) OVER (PARTITION BY sector ORDER BY date))
             / LAG(close) OVER (PARTITION BY sector ORDER BY date) AS daily_return
    FROM sector_prices
)
SELECT sector, date, daily_return,
       AVG(daily_return) OVER (
           PARTITION BY sector ORDER BY date
           ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
       ) AS rolling_30d_avg_return
FROM daily_returns
ORDER BY sector, date;

-- ------------------------------------------------------------
-- 3. 52-week (252 trading day) high/low proximity
-- ------------------------------------------------------------
SELECT sector, date, close,
       MAX(close) OVER (
           PARTITION BY sector ORDER BY date
           ROWS BETWEEN 251 PRECEDING AND CURRENT ROW
       ) AS rolling_52w_high,
       MIN(close) OVER (
           PARTITION BY sector ORDER BY date
           ROWS BETWEEN 251 PRECEDING AND CURRENT ROW
       ) AS rolling_52w_low
FROM sector_prices
ORDER BY sector, date;

-- ------------------------------------------------------------
-- 4. SMA-50 vs SMA-200 (golden/death cross inputs)
-- ------------------------------------------------------------
SELECT sector, date, close,
       AVG(close) OVER (PARTITION BY sector ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)  AS sma_50,
       AVG(close) OVER (PARTITION BY sector ORDER BY date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) AS sma_200
FROM sector_prices
ORDER BY sector, date;
