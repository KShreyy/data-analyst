"""
NIFTY 50 Sector Performance & Market Trend Analysis
------------------------------------------------------
- Loads sector price data into SQLite and runs the SQL in ../sql
- Computes 30-day rolling volatility, 52-week high/low proximity,
  SMA-50/SMA-200 crossover signals, and a sector correlation matrix in Python
- Identifies which sectors outperformed during two market-correction windows
- Saves all chart figures to ../figures
"""
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

BASE = "/sessions/great-friendly-wright/mnt/outputs/projects/project3_nifty50_sector_analysis"
sns.set_theme(style="whitegrid")

df = pd.read_csv(f"{BASE}/data/nifty50_sector_prices.csv", parse_dates=["date"])
conn = sqlite3.connect(":memory:")
df.to_sql("sector_prices", conn, index=False, if_exists="replace")

# ------------------------------------------------------------------
# 1. Total return per sector (SQL)
# ------------------------------------------------------------------
total_return = pd.read_sql("""
    WITH bounds AS (
        SELECT sector, MIN(date) AS first_date, MAX(date) AS last_date
        FROM sector_prices GROUP BY sector
    ),
    first_last AS (
        SELECT sp.sector,
               MAX(CASE WHEN sp.date = b.first_date THEN sp.close END) AS first_close,
               MAX(CASE WHEN sp.date = b.last_date THEN sp.close END)  AS last_close
        FROM sector_prices sp JOIN bounds b ON sp.sector = b.sector
        GROUP BY sp.sector
    )
    SELECT sector, ROUND(first_close,2) AS start_price, ROUND(last_close,2) AS end_price,
           ROUND(100.0*(last_close-first_close)/first_close, 2) AS total_return_pct
    FROM first_last ORDER BY total_return_pct DESC
""", conn)
print("=== Total return by sector (3-year window) ===")
print(total_return.to_string(index=False))

# ------------------------------------------------------------------
# 2. Pivot to wide format for time-series calcs
# ------------------------------------------------------------------
wide = df.pivot(index="date", columns="sector", values="close").sort_index()
returns = wide.pct_change()

# 30-day rolling volatility (annualized)
rolling_vol = returns.rolling(30).std() * np.sqrt(252) * 100

# 52-week (252d) high/low proximity: % below 52w high
roll_high = wide.rolling(252, min_periods=30).max()
roll_low = wide.rolling(252, min_periods=30).min()
pct_below_high = (wide / roll_high - 1) * 100

# SMA 50 / 200 crossover
sma50 = wide.rolling(50).mean()
sma200 = wide.rolling(200).mean()
golden_cross = (sma50 > sma200) & (sma50.shift(1) <= sma200.shift(1))
death_cross = (sma50 < sma200) & (sma50.shift(1) >= sma200.shift(1))

print("\n=== Golden cross events (SMA50 crosses above SMA200) ===")
for sector in wide.columns:
    dates_gc = wide.index[golden_cross[sector]]
    if len(dates_gc):
        print(f"{sector}: {[d.date().isoformat() for d in dates_gc]}")

# ------------------------------------------------------------------
# 3. Sector correlation matrix (of daily returns)
# ------------------------------------------------------------------
corr_matrix = returns.corr()

# ------------------------------------------------------------------
# 4. Performance during market correction windows
# ------------------------------------------------------------------
corrections = {
    "Correction 1 (Jun-Jul 2024)": ("2024-06-10", "2024-07-05"),
    "Correction 2 (Feb-Mar 2025)": ("2025-02-10", "2025-03-10"),
}
correction_perf = {}
for label, (start, end) in corrections.items():
    window = wide.loc[start:end]
    perf = (window.iloc[-1] / window.iloc[0] - 1) * 100
    correction_perf[label] = perf.round(2)

correction_df = pd.DataFrame(correction_perf).sort_values(list(corrections.keys())[0])
print("\n=== Sector return during market corrections (%) ===")
print(correction_df.to_string())
print("\nBest performers during corrections (avg rank):")
avg_rank = correction_df.rank(ascending=False).mean(axis=1).sort_values()
print(avg_rank.head(5).to_string())

# ------------------------------------------------------------------
# 5. Figures
# ------------------------------------------------------------------
# 5a. Sector performance heatmap (monthly returns)
monthly_returns = wide.resample("ME").last().pct_change() * 100
plt.figure(figsize=(11, 5.5))
sns.heatmap(monthly_returns.T, cmap="RdYlGn", center=0, cbar_kws={"label": "Monthly Return (%)"})
plt.title("Sector Performance Heatmap (Monthly Returns)")
plt.xlabel("Month index")
plt.tight_layout()
plt.savefig(f"{BASE}/figures/01_sector_performance_heatmap.png", dpi=150)
plt.close()

# 5b. Volume trend (aggregate market volume)
vol_trend = df.groupby("date")["volume"].sum().rolling(20).mean()
plt.figure(figsize=(9, 4.5))
plt.plot(vol_trend.index, vol_trend.values, color="#8c564b")
plt.title("Market Volume Trend (20-day rolling avg)")
plt.ylabel("Volume")
plt.tight_layout()
plt.savefig(f"{BASE}/figures/02_volume_trend.png", dpi=150)
plt.close()

# 5c. Price momentum: IT & FMCG vs market avg through the corrections
market_avg = wide.mean(axis=1)
plt.figure(figsize=(10, 5))
plt.plot(wide.index, wide["NIFTY IT"] / wide["NIFTY IT"].iloc[0] * 100, label="NIFTY IT")
plt.plot(wide.index, wide["NIFTY FMCG"] / wide["NIFTY FMCG"].iloc[0] * 100, label="NIFTY FMCG")
plt.plot(wide.index, market_avg / market_avg.iloc[0] * 100, label="Sector Average", linestyle="--", color="grey")
for start, end in corrections.values():
    plt.axvspan(pd.Timestamp(start), pd.Timestamp(end), color="red", alpha=0.12)
plt.title("IT & FMCG vs. Sector Average (correction windows shaded)")
plt.ylabel("Indexed Price (start=100)")
plt.legend()
plt.tight_layout()
plt.savefig(f"{BASE}/figures/03_defensive_sector_momentum.png", dpi=150)
plt.close()

# 5d. Sector correlation matrix
plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, cmap="coolwarm", center=0, annot=True, fmt=".2f", annot_kws={"size": 7})
plt.title("Sector Correlation Matrix (Daily Returns)")
plt.tight_layout()
plt.savefig(f"{BASE}/figures/04_sector_correlation_matrix.png", dpi=150)
plt.close()

# 5e. 30-day rolling volatility comparison
plt.figure(figsize=(10, 5))
top_vol_sectors = rolling_vol.iloc[-1].sort_values(ascending=False).head(5).index
for s in top_vol_sectors:
    plt.plot(rolling_vol.index, rolling_vol[s], label=s)
plt.title("30-Day Rolling Volatility — 5 Most Volatile Sectors (Annualized)")
plt.ylabel("Volatility (%)")
plt.legend()
plt.tight_layout()
plt.savefig(f"{BASE}/figures/05_rolling_volatility.png", dpi=150)
plt.close()

print("\nFigures saved to figures/")
