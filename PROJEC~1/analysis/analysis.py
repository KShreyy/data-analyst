"""
Retail Sales Performance & Customer Segmentation Analysis
----------------------------------------------------------
- Loads transactions/customers into SQLite and runs the SQL in ../sql
- Builds an RFM (Recency, Frequency, Monetary) segmentation in Python
- Runs a two-proportion z-test comparing two promo campaigns
- Saves all chart figures to ../figures
"""
import sqlite3
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

BASE = "/sessions/great-friendly-wright/mnt/outputs/projects/project1_retail_customer_segmentation"
sns.set_theme(style="whitegrid")

# ------------------------------------------------------------------
# 1. Load data, build SQLite DB
# ------------------------------------------------------------------
txns = pd.read_csv(f"{BASE}/data/retail_transactions.csv", parse_dates=["transaction_date"])
customers = pd.read_csv(f"{BASE}/data/customers.csv")
ab = pd.read_csv(f"{BASE}/data/campaign_ab_sessions.csv")

conn = sqlite3.connect(":memory:")
customers.to_sql("customers", conn, index=False, if_exists="replace")
txns.to_sql("transactions", conn, index=False, if_exists="replace")
ab.to_sql("campaign_ab_sessions", conn, index=False, if_exists="replace")

kpis = pd.read_sql("""
    SELECT COUNT(*) AS total_transactions,
           ROUND(SUM(amount),2) AS total_revenue,
           ROUND(AVG(amount),2) AS avg_order_value,
           COUNT(DISTINCT customer_id) AS unique_customers
    FROM transactions
""", conn)
print("=== Overall KPIs ===")
print(kpis.to_string(index=False))

region_cat = pd.read_sql("""
    SELECT region, category, COUNT(*) AS orders, ROUND(SUM(amount),2) AS revenue
    FROM transactions GROUP BY region, category ORDER BY revenue DESC
""", conn)

monthly = pd.read_sql("""
    SELECT strftime('%Y-%m', transaction_date) AS month,
           ROUND(SUM(amount),2) AS revenue, COUNT(*) AS orders
    FROM transactions GROUP BY month ORDER BY month
""", conn)

# ------------------------------------------------------------------
# 2. RFM segmentation
# ------------------------------------------------------------------
ref_date = txns["transaction_date"].max() + pd.Timedelta(days=1)
rfm = txns.groupby("customer_id").agg(
    recency_days=("transaction_date", lambda s: (ref_date - s.max()).days),
    frequency=("transaction_id", "count"),
    monetary=("amount", "sum"),
).reset_index()

# Score 1-5 (5 = best) via quintiles; recency reversed (lower days = better)
rfm["R"] = pd.qcut(rfm["recency_days"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
rfm["F"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm["M"] = pd.qcut(rfm["monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm["rfm_score"] = rfm["R"] + rfm["F"] + rfm["M"]

def segment(row):
    if row["rfm_score"] >= 13:
        return "Champions"
    elif row["rfm_score"] >= 10:
        return "Loyal Customers"
    elif row["rfm_score"] >= 7:
        return "Potential Loyalists"
    elif row["rfm_score"] >= 5:
        return "At Risk"
    else:
        return "Hibernating"

rfm["segment"] = rfm.apply(segment, axis=1)
rfm.to_csv(f"{BASE}/data/rfm_segments.csv", index=False)

# Revenue concentration (Pareto): top 20% of customers by monetary value
rfm_sorted = rfm.sort_values("monetary", ascending=False).reset_index(drop=True)
top20_cut = int(len(rfm_sorted) * 0.2)
top20_revenue_share = rfm_sorted.loc[:top20_cut - 1, "monetary"].sum() / rfm_sorted["monetary"].sum() * 100
print(f"\nTop 20% of customers ({top20_cut} of {len(rfm_sorted)}) drive "
      f"{top20_revenue_share:.1f}% of total revenue")

seg_counts = rfm["segment"].value_counts()
print("\n=== Customer segments ===")
print(seg_counts.to_string())

# ------------------------------------------------------------------
# 3. A/B test: two-proportion z-test on campaign conversion rate
# ------------------------------------------------------------------
summary = ab.groupby("campaign")["converted"].agg(["count", "sum"])
n_a, x_a = summary.loc["A_flat10", ["count", "sum"]]
n_b, x_b = summary.loc["B_tiered", ["count", "sum"]]
p_a, p_b = x_a / n_a, x_b / n_b
p_pool = (x_a + x_b) / (n_a + n_b)
se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b))
z = (p_b - p_a) / se
# two-sided p-value from standard normal via exact erf (no scipy needed)
p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
lift_pct = (p_b - p_a) / p_a * 100

print("\n=== Campaign A/B test (two-proportion z-test) ===")
print(f"Campaign A (Flat 10% Off):     n={n_a:.0f}, conversions={x_a:.0f}, rate={p_a*100:.2f}%")
print(f"Campaign B (Tiered discount):  n={n_b:.0f}, conversions={x_b:.0f}, rate={p_b*100:.2f}%")
print(f"Relative lift: {lift_pct:.1f}%  |  z = {z:.3f}  |  p-value = {p_value:.4f}")
print("Statistically significant at alpha=0.05" if p_value < 0.05 else "Not significant at alpha=0.05")

# ------------------------------------------------------------------
# 4. Figures
# ------------------------------------------------------------------
# 4a. Monthly revenue trend
plt.figure(figsize=(9, 4.5))
plt.plot(monthly["month"], monthly["revenue"], marker="o", color="#1f77b4")
plt.xticks(rotation=45, ha="right")
plt.title("Monthly Revenue Trend (2024–2025)")
plt.ylabel("Revenue (₹)")
plt.tight_layout()
plt.savefig(f"{BASE}/figures/01_monthly_revenue_trend.png", dpi=150)
plt.close()

# 4b. Revenue by region and category (heatmap)
pivot = region_cat.pivot(index="region", columns="category", values="revenue")
plt.figure(figsize=(9, 4.5))
sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Blues", cbar_kws={"label": "Revenue (₹)"})
plt.title("Revenue by Region × Category")
plt.tight_layout()
plt.savefig(f"{BASE}/figures/02_region_category_heatmap.png", dpi=150)
plt.close()

# 4c. Customer segment distribution
plt.figure(figsize=(7, 4.5))
order = seg_counts.index
sns.barplot(x=seg_counts.values, y=seg_counts.index, order=order, palette="viridis")
plt.title("Customer Segments (RFM)")
plt.xlabel("Number of Customers")
plt.tight_layout()
plt.savefig(f"{BASE}/figures/03_rfm_segment_distribution.png", dpi=150)
plt.close()

# 4d. Pareto curve
rfm_sorted["cum_pct_customers"] = (np.arange(1, len(rfm_sorted) + 1) / len(rfm_sorted)) * 100
rfm_sorted["cum_pct_revenue"] = rfm_sorted["monetary"].cumsum() / rfm_sorted["monetary"].sum() * 100
plt.figure(figsize=(7, 4.5))
plt.plot(rfm_sorted["cum_pct_customers"], rfm_sorted["cum_pct_revenue"], color="#d62728")
plt.axvline(20, linestyle="--", color="grey")
plt.axhline(top20_revenue_share, linestyle="--", color="grey")
plt.title("Revenue Concentration (Pareto Curve)")
plt.xlabel("% of Customers (ranked by spend)")
plt.ylabel("Cumulative % of Revenue")
plt.tight_layout()
plt.savefig(f"{BASE}/figures/04_pareto_curve.png", dpi=150)
plt.close()

# 4e. Campaign conversion comparison
plt.figure(figsize=(5.5, 4.5))
rates = [p_a * 100, p_b * 100]
bars = plt.bar(["A: Flat 10% Off", "B: Tiered Discount"], rates, color=["#1f77b4", "#ff7f0e"])
for b, r in zip(bars, rates):
    plt.text(b.get_x() + b.get_width()/2, r + 0.05, f"{r:.2f}%", ha="center")
plt.title(f"Campaign Conversion Rate\n(p = {p_value:.4f})")
plt.ylabel("Conversion Rate (%)")
plt.tight_layout()
plt.savefig(f"{BASE}/figures/05_campaign_ab_conversion.png", dpi=150)
plt.close()

print("\nFigures saved to figures/")
