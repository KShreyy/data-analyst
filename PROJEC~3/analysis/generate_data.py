"""
Generates 3 years of simulated daily closing-price data for 13 NIFTY sector
indices via correlated geometric Brownian motion, calibrated to broadly
realistic sector volatility/drift profiles, with two designed "market
correction" windows in which defensive sectors (IT, FMCG) are given a lower
beta / positive idiosyncratic drift so they outperform during the drawdown —
mirroring the resume's finding.

NOTE: This is SIMULATED data for demonstration purposes (no live market data
source was available in this environment). In production, swap
`generate_data.py`'s output for real NSE/Yahoo Finance daily OHLC pulls — the
SQL and analysis code downstream is agnostic to the data source.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(11)

SECTORS = {
    # sector: (annual_drift, annual_vol, beta_to_market)
    "NIFTY IT":               (0.14, 0.22, 0.85),
    "NIFTY FMCG":              (0.11, 0.15, 0.55),
    "NIFTY PHARMA":            (0.10, 0.18, 0.65),
    "NIFTY AUTO":              (0.13, 0.24, 1.05),
    "NIFTY BANK":              (0.12, 0.20, 1.15),
    "NIFTY FINANCIAL SERVICES":(0.12, 0.21, 1.20),
    "NIFTY METAL":             (0.09, 0.32, 1.40),
    "NIFTY REALTY":            (0.08, 0.35, 1.50),
    "NIFTY ENERGY":            (0.10, 0.23, 1.10),
    "NIFTY INFRA":             (0.09, 0.22, 1.05),
    "NIFTY PSU BANK":          (0.07, 0.34, 1.35),
    "NIFTY MEDIA":             (0.05, 0.30, 1.20),
    "NIFTY CONSUMER DURABLES": (0.12, 0.20, 0.95),
}
DEFENSIVE = {"NIFTY IT", "NIFTY FMCG"}

n_days = 756  # ~3 trading years
dates = pd.bdate_range("2023-01-02", periods=n_days)

# Market factor: standard GBM, with two designed correction windows
mkt_drift, mkt_vol = 0.11, 0.16
dt = 1 / 252
market_shocks = rng.normal((mkt_drift - 0.5 * mkt_vol**2) * dt, mkt_vol * np.sqrt(dt), size=n_days)

# Correction windows: sharp negative market drift for ~15 trading days each
correction_1 = (dates >= "2024-06-10") & (dates <= "2024-07-05")
correction_2 = (dates >= "2025-02-10") & (dates <= "2025-03-10")
market_shocks[correction_1] -= 0.010
market_shocks[correction_2] -= 0.011

market_log_returns = market_shocks
market_index = 100 * np.exp(np.cumsum(market_log_returns))

records = {"date": dates}
for sector, (drift, vol, beta) in SECTORS.items():
    idio_vol = np.sqrt(max(vol**2 - (beta * mkt_vol) ** 2, 0.01))
    idio_shocks = rng.normal((drift - 0.5 * vol**2) * dt, idio_vol * np.sqrt(dt), size=n_days)

    # Defensive sectors get a positive idiosyncratic bump specifically during
    # the correction windows (lower effective beta in a downturn)
    if sector in DEFENSIVE:
        idio_shocks[correction_1] += 0.006
        idio_shocks[correction_2] += 0.007

    log_returns = beta * market_log_returns + idio_shocks
    price = 100 * np.exp(np.cumsum(log_returns))
    records[sector] = price

prices = pd.DataFrame(records)
prices_long = prices.melt(id_vars="date", var_name="sector", value_name="close")
prices_long["volume"] = rng.integers(2_000_000, 15_000_000, size=len(prices_long))
prices_long.to_csv("/sessions/great-friendly-wright/mnt/outputs/projects/project3_nifty50_sector_analysis/data/nifty50_sector_prices.csv", index=False)

print("Rows:", len(prices_long), "| Sectors:", len(SECTORS), "| Date range:", dates.min().date(), "to", dates.max().date())
