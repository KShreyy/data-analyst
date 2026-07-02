# Retail Sales Performance & Customer Segmentation Analysis

**Skills used:** SQL (CTEs, window functions, aggregation) · Python (Pandas, NumPy) · Statistical Analysis (RFM segmentation, two-proportion z-test / A-B testing) · Data Visualization (Matplotlib, Seaborn) · Tableau-ready data export

## Problem

A retail business wants to know which customers drive the most revenue, whether its
customer base can be segmented for targeted marketing, and whether a new tiered-discount
promotion outperforms its standard flat-discount promotion.

## Dataset

`data/retail_transactions.csv` — 52,000 synthetic transactions across 5,176 customers,
2 years (2024–2025), 5 regions, 6 product categories, generated with realistic seasonality
(Nov–Dec festive lift) and a heavy-tailed customer spend distribution (a small group of
high-value customers drives most revenue, as in real retail data). Generation script:
`analysis/generate_data.py` (fixed random seed — fully reproducible).

`data/campaign_ab_sessions.csv` — 8,000 simulated site sessions split across two live
promotions run in back-to-back two-week windows in March 2025.

## Approach

1. **SQL** (`sql/schema_and_queries.sql`): schema definition, overall KPIs, revenue by
   region × category, monthly trend, an RFM base table built with `NTILE`/window
   functions, and a revenue-concentration (decile) query.
2. **RFM segmentation** (`analysis/analysis.py`): scored every customer 1–5 on Recency,
   Frequency, and Monetary value using quintiles, combined into an RFM score, and mapped
   to five segments (Champions, Loyal Customers, Potential Loyalists, At Risk,
   Hibernating).
3. **A/B test**: compared conversion rate between the flat-discount campaign (A) and the
   tiered-discount campaign (B) using a two-proportion z-test (exact p-value via the
   normal CDF — no external stats library required).
4. **Visualization**: monthly trend, region×category heatmap, segment distribution,
   Pareto (revenue concentration) curve, and campaign conversion comparison — all in
   `figures/`. The cleaned tables (`data/*.csv`) are also ready to drop straight into a
   Tableau workbook for an interactive version of the same dashboard.

## Key Findings

- **Revenue concentration:** the top 20% of customers by spend drove **~62% of total
  revenue** — a strong Pareto effect that justifies prioritizing retention spend on the
  "Champions" and "Loyal Customers" segments.
- **Segmentation:** ~19% of customers are "Champions," while ~13% are "Hibernating" —
  a concrete re-engagement target list.
- **Seasonality:** revenue rises sharply in November–December, useful for inventory and
  staffing planning.
- **A/B test:** the tiered-discount campaign (B) converted at a meaningfully higher rate
  than the flat-discount campaign (A), and the difference is statistically significant
  (two-proportion z-test, p < 0.05) — recommend rolling out tiered discounts more broadly.

## How to Run

```bash
cd analysis
python3 generate_data.py   # builds data/*.csv
python3 analysis.py        # runs SQL + RFM + A/B test, saves figures/
```

## Files

```
project1_retail_customer_segmentation/
├── data/                     # transactions, customers, RFM output, A/B sessions
├── sql/schema_and_queries.sql
├── analysis/generate_data.py
├── analysis/analysis.py
└── figures/                  # 5 chart PNGs
```
