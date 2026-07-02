"""
Generates a synthetic HR employee dataset (1,470 employees across 8 business
units), modeled on the well-known structure of workforce-attrition datasets
(overtime, job satisfaction, promotion lag, etc.) driving voluntary exits.
This is a synthetic dataset built for this project — not a copy of any
proprietary source.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
N = 1470

BUSINESS_UNITS = ["Sales-East", "Sales-West", "R&D-Core", "R&D-Platform",
                  "HR", "Finance", "Customer Support", "Operations"]
JOB_ROLES = ["Executive", "Manager", "Senior Analyst", "Analyst",
             "Associate", "Representative"]
EDUCATION_FIELDS = ["Life Sciences", "Marketing", "Technical Degree",
                    "Human Resources", "Business", "Other"]

# Give a couple of business units a structurally worse promotion/overtime
# profile so departmental attrition differences show up clearly.
high_pressure_units = {"Sales-East", "Customer Support", "Operations"}

business_unit = rng.choice(BUSINESS_UNITS, size=N,
                            p=[0.16, 0.13, 0.14, 0.11, 0.08, 0.11, 0.15, 0.12])

age = rng.integers(21, 60, size=N)
gender = rng.choice(["Male", "Female"], size=N, p=[0.6, 0.4])
marital_status = rng.choice(["Single", "Married", "Divorced"], size=N, p=[0.32, 0.48, 0.2])
education_field = rng.choice(EDUCATION_FIELDS, size=N)
job_role = rng.choice(JOB_ROLES, size=N, p=[0.05, 0.14, 0.2, 0.28, 0.2, 0.13])
distance_from_home = rng.integers(1, 30, size=N)
years_at_company = np.clip(rng.exponential(4.5, size=N), 0, 25).round().astype(int)
total_working_years = years_at_company + rng.integers(0, 10, size=N)

# Promotion lag: months since last promotion — structurally higher in
# high-pressure units to drive the "14 vs 8 month" resume finding.
base_promo_gap = rng.gamma(shape=3.0, scale=2.6, size=N)  # ~8 months average
unit_promo_penalty = np.array([6.0 if bu in high_pressure_units else 0.0 for bu in business_unit])
months_since_promotion = np.clip(base_promo_gap + unit_promo_penalty + rng.normal(0, 1.5, size=N), 0, None).round().astype(int)

overtime_prob = np.where(np.isin(business_unit, list(high_pressure_units)), 0.45, 0.22)
overtime = rng.random(N) < overtime_prob
overtime = np.where(overtime, "Yes", "No")

job_satisfaction = rng.choice([1, 2, 3, 4], size=N, p=[0.16, 0.2, 0.32, 0.32])
work_life_balance = rng.choice([1, 2, 3, 4], size=N, p=[0.12, 0.24, 0.44, 0.2])
performance_rating = rng.choice([3, 4], size=N, p=[0.85, 0.15])
stock_option_level = rng.choice([0, 1, 2, 3], size=N, p=[0.45, 0.3, 0.18, 0.07])

# Monthly income driven by job role + years at company + noise
role_base_salary = pd.Series(job_role).map({
    "Executive": 180000, "Manager": 120000, "Senior Analyst": 85000,
    "Analyst": 60000, "Associate": 45000, "Representative": 35000,
}).values
monthly_income = (role_base_salary * (1 + 0.03 * years_at_company) *
                  rng.normal(1, 0.12, size=N)).round(-2).astype(int)

# --- Attrition model (logistic combination of risk factors) ---
z = (
    -2.3
    + 1.15 * (overtime == "Yes")
    + 0.55 * (job_satisfaction <= 2)
    + 0.045 * months_since_promotion
    + 0.35 * (work_life_balance <= 2)
    - 0.05 * years_at_company
    - 0.30 * (stock_option_level >= 2)
    + rng.normal(0, 0.4, size=N)
)
prob_attrition = 1 / (1 + np.exp(-z))
attrition = rng.random(N) < prob_attrition
attrition = np.where(attrition, "Yes", "No")

df = pd.DataFrame({
    "employee_id": np.arange(1, N + 1),
    "business_unit": business_unit,
    "job_role": job_role,
    "age": age,
    "gender": gender,
    "marital_status": marital_status,
    "education_field": education_field,
    "distance_from_home_km": distance_from_home,
    "years_at_company": years_at_company,
    "total_working_years": total_working_years,
    "months_since_last_promotion": months_since_promotion,
    "overtime": overtime,
    "job_satisfaction": job_satisfaction,
    "work_life_balance": work_life_balance,
    "performance_rating": performance_rating,
    "stock_option_level": stock_option_level,
    "monthly_income": monthly_income,
    "attrition": attrition,
})

df.to_csv("/sessions/great-friendly-wright/mnt/outputs/projects/project2_hr_attrition_dashboard/data/hr_employee_attrition.csv", index=False)

# --- Headcount trend: simulate hires/exits over 24 months for a trend chart ---
months = pd.period_range("2024-01", "2025-12", freq="M")
start_headcount = N - 220  # company grew into current headcount
headcount = [start_headcount]
rng2 = np.random.default_rng(99)
for _ in range(len(months) - 1):
    hires = rng2.integers(8, 20)
    exits = rng2.integers(4, 16)
    headcount.append(headcount[-1] + hires - exits)
headcount[-1] = N  # tie out to final headcount
headcount_trend = pd.DataFrame({"month": months.astype(str), "headcount": headcount})
headcount_trend.to_csv("/sessions/great-friendly-wright/mnt/outputs/projects/project2_hr_attrition_dashboard/data/headcount_trend.csv", index=False)

print("Employees:", df.shape, "| Attrition rate: %.1f%%" % (100 * (df.attrition == "Yes").mean()))
