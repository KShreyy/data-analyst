-- ============================================================
-- HR Attrition & Workforce Analytics Dashboard
-- Schema + core analysis queries (SQLite dialect)
-- ============================================================

CREATE TABLE IF NOT EXISTS employees (
    employee_id                  INTEGER PRIMARY KEY,
    business_unit                TEXT,
    job_role                     TEXT,
    age                          INTEGER,
    gender                       TEXT,
    marital_status                TEXT,
    education_field              TEXT,
    distance_from_home_km        INTEGER,
    years_at_company             INTEGER,
    total_working_years          INTEGER,
    months_since_last_promotion  INTEGER,
    overtime                     TEXT,
    job_satisfaction             INTEGER,
    work_life_balance            INTEGER,
    performance_rating           INTEGER,
    stock_option_level           INTEGER,
    monthly_income                INTEGER,
    attrition                    TEXT
);

-- ------------------------------------------------------------
-- 1. Overall attrition rate
-- ------------------------------------------------------------
SELECT
    COUNT(*) AS headcount,
    SUM(CASE WHEN attrition='Yes' THEN 1 ELSE 0 END) AS exits,
    ROUND(100.0 * SUM(CASE WHEN attrition='Yes' THEN 1 ELSE 0 END) / COUNT(*), 1) AS attrition_rate_pct
FROM employees;

-- ------------------------------------------------------------
-- 2. Attrition rate & average promotion gap by business unit
-- ------------------------------------------------------------
SELECT
    business_unit,
    COUNT(*) AS headcount,
    ROUND(100.0 * SUM(CASE WHEN attrition='Yes' THEN 1 ELSE 0 END) / COUNT(*), 1) AS attrition_rate_pct,
    ROUND(AVG(months_since_last_promotion), 1) AS avg_promotion_gap_months
FROM employees
GROUP BY business_unit
ORDER BY attrition_rate_pct DESC;

-- ------------------------------------------------------------
-- 3. Overtime vs attrition contingency table (feeds chi-square test)
-- ------------------------------------------------------------
SELECT
    overtime,
    SUM(CASE WHEN attrition='Yes' THEN 1 ELSE 0 END) AS attrition_yes,
    SUM(CASE WHEN attrition='No' THEN 1 ELSE 0 END)  AS attrition_no
FROM employees
GROUP BY overtime;

-- ------------------------------------------------------------
-- 4. Job satisfaction band vs attrition rate
-- ------------------------------------------------------------
SELECT
    job_satisfaction,
    COUNT(*) AS headcount,
    ROUND(100.0 * SUM(CASE WHEN attrition='Yes' THEN 1 ELSE 0 END) / COUNT(*), 1) AS attrition_rate_pct
FROM employees
GROUP BY job_satisfaction
ORDER BY job_satisfaction;

-- ------------------------------------------------------------
-- 5. Salary band distribution
-- ------------------------------------------------------------
SELECT
    CASE
        WHEN monthly_income < 40000 THEN '<40k'
        WHEN monthly_income < 60000 THEN '40-60k'
        WHEN monthly_income < 90000 THEN '60-90k'
        WHEN monthly_income < 130000 THEN '90-130k'
        ELSE '130k+'
    END AS salary_band,
    COUNT(*) AS headcount
FROM employees
GROUP BY salary_band
ORDER BY MIN(monthly_income);

-- ------------------------------------------------------------
-- 6. Gender mix by business unit (diversity metric)
-- ------------------------------------------------------------
SELECT
    business_unit,
    gender,
    COUNT(*) AS headcount,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY business_unit), 1) AS pct_of_department
FROM employees
GROUP BY business_unit, gender
ORDER BY business_unit, gender;
