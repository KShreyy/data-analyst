# NIFTY 50 Sector Performance & Market Trend Analysis

**Skills used:** Python (Pandas, NumPy) · SQL (window functions: `LAG`,
rolling `ROWS BETWEEN`) · Statistical/Time-Series Analysis (rolling
volatility, moving-average crossovers, correlation matrices) · Data
Visualization (Matplotlib, Seaborn) · Tableau-ready data export

## Problem

An investment research team wants a sector-level view of the Indian equity
market over the past 3 years: which sectors led, which are most volatile, how
they move together, and — critically — which sectors held up best during
market corrections.

## Dataset

`data/nifty50_sector_prices.csv` — ~3 years (756 trading days) of simulated
daily closing prices and volume for **13 NIFTY sector indices**
(IT, FMCG, Pharma, Auto, Bank, Financial Services, Metal, Realty, Energy,
Infra, PSU Bank, Media, Consumer Durables), generated in
`analysis/generate_data.py` via correlated geometric Brownian motion with
sector-specific drift/volatility/beta parameters and two designed market
correction windows.

> **Note on data source:** this environment had no live internet access to
> NSE/Yahoo Finance, so price series are simulated (fixed seed, fully
> reproducible) rather than pulled from a live feed. Sector volatility/beta
> assumptions are calibrated to broadly realistic profiles. The SQL and Python
> analysis code is written to be data-source agnostic — swapping in a real
> `yfinance`/NSE pull only requires replacing `generate_data.py`'s output with
> the same `date, sector, close, volume` schema.

## Approach

1. **SQL** (`sql/schema_and_queries.sql`): total return per sector, 30-day
   rolling return via `LAG`, 52-week high/low via windowed `MAX`/`MIN`, and
   SMA-50/SMA-200 series via windowed `AVG`.
2. **Python analysis** (`analysis/analysis.py`):
   - 30-day rolling volatility (annualized) per sector.
   - 52-week high/low proximity (% below rolling high).
   - SMA-50 vs. SMA-200 golden-cross/death-cross detection.
   - Full 13×13 sector correlation matrix on daily returns.
   - Return comparison across two designated correction windows
     (Jun–Jul 2024, Feb–Mar 2025).
3. **Visualization**: monthly-return heatmap, volume trend, IT/FMCG vs.
   sector-average momentum chart (corrections shaded), correlation matrix,
   and rolling-volatility comparison — all in `figures/`. Cleaned tables are
   ready to load into a Tableau workbook for an interactive dashboard.

## Key Findings

- **IT and FMCG were the clear defensive leaders**, posting the best average
  rank across both correction windows — FMCG was flat-to-positive in both,
  and IT was only mildly negative in the second, while cyclical sectors
  (Metal, PSU Bank, Realty) fell 20–39% in the same windows.
- **3-year total return leaders:** Metal, FMCG, and Pharma led the pack, while
  PSU Bank was the only sector to post a negative 3-year return.
- **SMA-50/SMA-200 crossovers** flag several golden-cross entry signals
  through 2024–2025 across Bank, Financial Services, and Infra — a starting
  point for a momentum-based watchlist.
- **Correlation matrix** shows Financial Services, Bank, and Infra move
  tightly together (high correlation), while FMCG and IT are comparatively
  uncorrelated with the more cyclical sectors — supporting their use as
  portfolio diversifiers/hedges during downturns.

## How to Run

```bash
cd analysis
python3 generate_data.py   # builds data/nifty50_sector_prices.csv
python3 analysis.py        # runs SQL + rolling stats + correlation, saves figures/
```

## Files

```
project3_nifty50_sector_analysis/
├── data/nifty50_sector_prices.csv
├── sql/schema_and_queries.sql
├── analysis/generate_data.py
├── analysis/analysis.py
└── figures/                  # 5 chart PNGs
```
