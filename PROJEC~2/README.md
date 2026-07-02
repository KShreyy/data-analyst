# HR Attrition & Workforce Analytics Dashboard

**Skills used:** SQL (aggregation, window functions) · Python (Pandas, NumPy) ·
Statistical Analysis (point-biserial correlation, chi-square test of
independence) · Data Visualization (Matplotlib, Seaborn) · Power BI/Tableau-ready
KPI exports

## Problem

HR leadership wants to know which factors are actually associated with voluntary
attrition, whether specific business units are structurally higher-risk, and
what a leadership-ready KPI dashboard should highlight.

## Dataset

`data/hr_employee_attrition.csv` — 1,470 synthetic employee records across 8
business units, modeled on the structure of well-known workforce-attrition
datasets (overtime, job satisfaction, promotion lag, tenure, income, etc.).
Built with `analysis/generate_data.py` using a logistic risk model so that
overtime, low job satisfaction, and long promotion gaps genuinely drive
attrition — not random labels. Fixed random seed, fully reproducible.

`data/headcount_trend.csv` — simulated month-by-month headcount for 2024–2025
to support a trend chart.

## Approach

1. **SQL** (`sql/schema_and_queries.sql`): overall attrition rate, attrition and
   promotion-gap by business unit, the overtime × attrition contingency table,
   job-satisfaction attrition bands, salary bands, and gender mix by department.
2. **Statistical analysis** (`analysis/analysis.py`):
   - Point-biserial correlation between attrition and each numeric driver
     (job satisfaction, work-life balance, promotion gap, tenure, commute
     distance, income).
   - **Chi-square test of independence** on overtime vs. attrition to confirm
     the relationship isn't due to chance.
3. **Visualization**: headcount trend, attrition rate by department (with the
   high-risk units flagged), salary band distribution, correlation chart, and
   gender mix by department — all in `figures/`, structured so the same tables
   can be loaded straight into Power BI for an interactive KPI dashboard.

## Key Findings

- **Overall attrition: 21.6%**, with three business units (Sales-East, Customer
  Support, Operations) running well above the company average.
- **Promotion lag is the standout departmental signal:** high-attrition units
  average a **12.6-month gap** since last promotion vs. **8.1 months** in the
  rest of the company — a ~55% longer wait, and a concrete lever for retention.
- **Overtime is strongly associated with attrition:** a chi-square test of
  independence is highly significant (χ² = 76.3, p < 0.001) — employees working
  overtime leave at roughly double the rate of those who don't.
- **Job satisfaction and work-life balance** show the strongest negative
  correlation with attrition among the numeric drivers tested.
- **Recommendation:** prioritize a promotion-cadence review in the three
  flagged business units, and treat overtime load as an early-warning KPI,
  not just a productivity metric.

## How to Run

```bash
cd analysis
python3 generate_data.py   # builds data/*.csv
python3 analysis.py        # runs SQL + stats tests, saves figures/
```

## Files

```
project2_hr_attrition_dashboard/
├── data/                     # employee records, headcount trend
├── sql/schema_and_queries.sql
├── analysis/generate_data.py
├── analysis/analysis.py
└── figures/                  # 5 chart PNGs
```
