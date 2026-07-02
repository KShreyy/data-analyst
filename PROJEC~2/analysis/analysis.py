"""
HR Attrition & Workforce Analytics Dashboard
---------------------------------------------
- Loads the synthetic HR dataset into SQLite and runs the SQL in ../sql
- Computes point-biserial correlations between attrition and key drivers
- Runs a chi-square test of independence: overtime vs attrition
- Saves KPI chart figures (feeding a Power BI-style dashboard) to ../figures
"""
import math
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

BASE = "/sessions/great-friendly-wright/mnt/outputs/projects/project2_hr_attrition_dashboard"
sns.set_theme(style="whitegrid")

df = pd.read_csv(f"{BASE}/data/hr_employee_attrition.csv")
headcount = pd.read_csv(f"{BASE}/data/headcount_trend.csv")
df["attrition_flag"] = (df["attrition"] == "Yes").astype(int)

conn = sqlite3.connect(":memory:")
df.to_sql("employees", conn, index=False, if_exists="replace")

# ------------------------------------------------------------------
# 1. Overall KPIs
# ------------------------------------------------------------------
overall_rate = df["attrition_flag"].mean() * 100
print(f"=== Overall attrition rate: {overall_rate:.1f}% (n={len(df)}) ===")

# ------------------------------------------------------------------
# 2. Department-level attrition & promotion gap (SQL)
# ------------------------------------------------------------------
dept = pd.read_sql("""
    SELECT business_unit,
           COUNT(*) AS headcount,
           ROUND(100.0 * SUM(CASE WHEN attrition='Yes' THEN 1 ELSE 0 END) / COUNT(*), 1) AS attrition_rate_pct,
           ROUND(AVG(months_since_last_promotion), 1) AS avg_promotion_gap_months
    FROM employees
    GROUP BY business_unit
    ORDER BY attrition_rate_pct DESC
""", conn)
print("\n=== Department attrition & promotion gap ===")
print(dept.to_string(index=False))

high_units = dept[dept["attrition_rate_pct"] > 22]["business_unit"].tolist()
hp_gap = df[df.business_unit.isin(high_units)]["months_since_last_promotion"].mean()
other_gap = df[~df.business_unit.isin(high_units)]["months_since_last_promotion"].mean()
print(f"\nHigh-attrition units (>22%) avg promotion gap: {hp_gap:.1f} months")
print(f"Other units avg promotion gap: {other_gap:.1f} months")

# ------------------------------------------------------------------
# 3. Point-biserial correlation: attrition vs numeric drivers
#    (equivalent to Pearson correlation with a 0/1 variable)
# ------------------------------------------------------------------
def point_biserial(x, y):
    return np.corrcoef(x, y)[0, 1]

drivers = ["months_since_last_promotion", "job_satisfaction", "work_life_balance",
           "years_at_company", "distance_from_home_km", "monthly_income"]
corr = {d: point_biserial(df[d], df["attrition_flag"]) for d in drivers}
corr_df = pd.Series(corr).sort_values(key=abs, ascending=False).round(3)
print("\n=== Correlation with attrition (point-biserial) ===")
print(corr_df.to_string())

# ------------------------------------------------------------------
# 4. Chi-square test of independence: overtime vs attrition (df=1)
# ------------------------------------------------------------------
ct = pd.crosstab(df["overtime"], df["attrition"])
print("\n=== Contingency table: overtime x attrition ===")
print(ct)

chi2 = 0.0
n = ct.values.sum()
row_totals = ct.sum(axis=1).values
col_totals = ct.sum(axis=0).values
for i in range(ct.shape[0]):
    for j in range(ct.shape[1]):
        expected = row_totals[i] * col_totals[j] / n
        chi2 += (ct.values[i, j] - expected) ** 2 / expected
# df=1 chi-square p-value via erf (exact closed form for 1 dof)
p_value = 1 - math.erf(math.sqrt(chi2 / 2))
print(f"\nChi-square = {chi2:.2f}, df=1, p-value = {p_value:.6f}")
print("Statistically significant association (p<0.05)" if p_value < 0.05 else "Not significant")

# ------------------------------------------------------------------
# 5. Figures (feed a Power BI / Tableau-style KPI dashboard)
# ------------------------------------------------------------------
# 5a. Headcount trend
plt.figure(figsize=(9, 4.5))
plt.plot(headcount["month"], headcount["headcount"], marker="o", color="#2ca02c")
plt.xticks(rotation=45, ha="right")
plt.title("Headcount Trend (2024–2025)")
plt.ylabel("Employees")
plt.tight_layout()
plt.savefig(f"{BASE}/figures/01_headcount_trend.png", dpi=150)
plt.close()

# 5b. Attrition rate by department
plt.figure(figsize=(8, 4.5))
d = dept.sort_values("attrition_rate_pct", ascending=True)
colors = ["#d62728" if r > 22 else "#1f77b4" for r in d["attrition_rate_pct"]]
plt.barh(d["business_unit"], d["attrition_rate_pct"], color=colors)
plt.axvline(overall_rate, linestyle="--", color="grey", label=f"Company avg ({overall_rate:.1f}%)")
plt.title("Attrition Rate by Business Unit")
plt.xlabel("Attrition Rate (%)")
plt.legend()
plt.tight_layout()
plt.savefig(f"{BASE}/figures/02_attrition_by_department.png", dpi=150)
plt.close()

# 5c. Salary band distribution
bins = [0, 40000, 60000, 90000, 130000, 1_000_000]
labels = ["<40k", "40-60k", "60-90k", "90-130k", "130k+"]
df["salary_band"] = pd.cut(df["monthly_income"], bins=bins, labels=labels)
band_counts = df["salary_band"].value_counts().reindex(labels)
plt.figure(figsize=(7, 4.5))
sns.barplot(x=band_counts.index, y=band_counts.values, color="#9467bd")
plt.title("Salary Band Distribution")
plt.ylabel("Employees")
plt.tight_layout()
plt.savefig(f"{BASE}/figures/03_salary_band_distribution.png", dpi=150)
plt.close()

# 5d. Correlation bar chart
plt.figure(figsize=(7, 4.5))
corr_df.plot(kind="barh", color=["#d62728" if v > 0 else "#1f77b4" for v in corr_df.values])
plt.title("Correlation with Attrition")
plt.xlabel("Point-biserial correlation")
plt.tight_layout()
plt.savefig(f"{BASE}/figures/04_attrition_correlations.png", dpi=150)
plt.close()

# 5e. Diversity: gender mix by business unit
gender_mix = pd.crosstab(df["business_unit"], df["gender"], normalize="index") * 100
gender_mix.plot(kind="barh", stacked=True, figsize=(8, 4.5), color=["#ff7f0e", "#1f77b4"])
plt.title("Gender Mix by Business Unit (%)")
plt.xlabel("% of Department")
plt.tight_layout()
plt.savefig(f"{BASE}/figures/05_diversity_gender_mix.png", dpi=150)
plt.close()

print("\nFigures saved to figures/")
