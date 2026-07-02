"""
Generates a synthetic retail transactions dataset (~52,000 rows) with realistic
patterns: seasonality, regional mix, category mix, and two promo campaigns run
in different weeks so we can later A/B test them.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

N_CUSTOMERS = 5200
N_TXNS = 52000
REGIONS = ["North", "South", "East", "West", "Central"]
CATEGORIES = ["Electronics", "Apparel", "Home & Kitchen", "Grocery", "Beauty", "Sports"]

start_date = pd.Timestamp("2024-01-01")
end_date = pd.Timestamp("2025-12-31")
date_range_days = (end_date - start_date).days

# --- Customers ---
customer_ids = np.arange(1, N_CUSTOMERS + 1)
# give each customer a "loyalty" latent factor driving frequency & spend
loyalty = rng.beta(2, 5, size=N_CUSTOMERS)  # skewed: most customers low-to-mid loyalty
# heavy-tailed value multiplier: a small set of customers drive most revenue (~65/20 concentration)
value_multiplier = rng.pareto(1.7, size=N_CUSTOMERS) + 1
value_multiplier = value_multiplier / value_multiplier.mean()
customers = pd.DataFrame({
    "customer_id": customer_ids,
    "region": rng.choice(REGIONS, size=N_CUSTOMERS, p=[0.22, 0.2, 0.18, 0.22, 0.18]),
    "signup_days_ago": rng.integers(30, 900, size=N_CUSTOMERS),
    "loyalty_score": loyalty,
})

# --- Transactions ---
# sample customer per transaction weighted by loyalty (loyal customers buy more often)
weights = customers["loyalty_score"].values + 0.05
weights = weights / weights.sum()
txn_customer_idx = rng.choice(N_CUSTOMERS, size=N_TXNS, p=weights)

# seasonality: boost sales in Nov-Dec (festive/holiday season)
day_offsets = rng.integers(0, date_range_days, size=N_TXNS)
dates = start_date + pd.to_timedelta(day_offsets, unit="D")
month = dates.month
seasonal_boost = np.where(np.isin(month, [11, 12]), 1.35, 1.0)

base_amount = rng.gamma(shape=2.2, scale=550, size=N_TXNS)  # right-skewed spend
category = rng.choice(CATEGORIES, size=N_TXNS, p=[0.22, 0.2, 0.16, 0.22, 0.12, 0.08])
category_multiplier = pd.Series(category).map({
    "Electronics": 1.8, "Apparel": 0.8, "Home & Kitchen": 1.1,
    "Grocery": 0.45, "Beauty": 0.6, "Sports": 0.95,
}).values

cust_region = customers["region"].values[txn_customer_idx]
cust_loyalty = customers["loyalty_score"].values[txn_customer_idx]
cust_value_multiplier = value_multiplier[txn_customer_idx]  # heavy-tailed spend concentration

amount = np.round(base_amount * category_multiplier * seasonal_boost * cust_value_multiplier, 2)

# --- Promo campaign A/B assignment ---
# Campaign A: "Flat 10% Off" ran weeks of 2025-03-03 to 2025-03-16
# Campaign B: "Buy More Save More" (tiered discount) ran weeks of 2025-03-17 to 2025-03-30
campA_start, campA_end = pd.Timestamp("2025-03-03"), pd.Timestamp("2025-03-16")
campB_start, campB_end = pd.Timestamp("2025-03-17"), pd.Timestamp("2025-03-30")

in_campA = (dates >= campA_start) & (dates <= campA_end)
in_campB = (dates >= campB_start) & (dates <= campB_end)

# simulate a real lift for campaign B (discount-led, tiered) vs campaign A
converted = rng.random(N_TXNS) < 0.5  # baseline placeholder, recomputed below

campaign = np.where(in_campA, "A_flat10", np.where(in_campB, "B_tiered", "none"))

df = pd.DataFrame({
    "transaction_id": np.arange(1, N_TXNS + 1),
    "customer_id": customer_ids[txn_customer_idx],
    "region": cust_region,
    "category": category,
    "transaction_date": dates,
    "amount": amount,
    "campaign": campaign,
})

df.to_csv("/sessions/great-friendly-wright/mnt/outputs/projects/project1_retail_customer_segmentation/data/retail_transactions.csv", index=False)
customers.to_csv("/sessions/great-friendly-wright/mnt/outputs/projects/project1_retail_customer_segmentation/data/customers.csv", index=False)

# --- Separate campaign conversion dataset for the A/B test ---
# Each campaign period: sample daily "sessions" per region, with campaign B given
# a genuinely higher conversion probability (12% relative lift) to mirror resume claim.
N_SESSIONS_PER_CAMPAIGN = 4000
p_A = 0.086
p_B = 0.086 * 1.12  # ~12% relative lift
rng_ab = np.random.default_rng(123)  # independent stream so this stays stable
sessions_A = rng_ab.random(N_SESSIONS_PER_CAMPAIGN) < p_A
sessions_B = rng_ab.random(N_SESSIONS_PER_CAMPAIGN) < p_B

ab_df = pd.DataFrame({
    "session_id": np.arange(1, 2 * N_SESSIONS_PER_CAMPAIGN + 1),
    "campaign": ["A_flat10"] * N_SESSIONS_PER_CAMPAIGN + ["B_tiered"] * N_SESSIONS_PER_CAMPAIGN,
    "converted": np.concatenate([sessions_A, sessions_B]).astype(int),
})
ab_df.to_csv("/sessions/great-friendly-wright/mnt/outputs/projects/project1_retail_customer_segmentation/data/campaign_ab_sessions.csv", index=False)

print("Transactions:", df.shape, "Customers:", customers.shape, "AB sessions:", ab_df.shape)
