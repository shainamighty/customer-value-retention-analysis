"""
Customer Value & Loyalty Feature Engineering
D2C Fashion Brand — Decoding Customer Value project

This script:
1. Cleans the raw dataset
2. Builds TWO competing loyalty definitions from different variable combinations
3. Builds a discount-dependency score
4. Builds a satisfaction flag
5. Compares the two loyalty definitions against each other and against revenue
6. Exports a clean customer-level feature table for SQL/Power BI

Every feature here is built to answer a specific business question — see the
comment above each block for which question it serves.
"""

import pandas as pd
import numpy as np

# ------------------------------------------------------------
# 1. LOAD & CLEAN
# ------------------------------------------------------------
df = pd.read_csv("Dataset.csv")

# Discount Applied and Promo Code Used are 100% identical columns in this
# dataset (verified: every row where one is Yes, the other is Yes too).
# Keeping both would double-count the same signal in any model or score,
# so we drop the duplicate and keep one.
df = df.drop(columns=["Promo Code Used"])

# Review Rating has 37 missing values (~1% of rows). Rather than silently
# imputing (which would fabricate a satisfaction opinion the customer never
# gave), we flag missingness explicitly as its own signal — a customer who
# never left a review is behaviorally different from one who left a 3-star
# review, and collapsing that distinction would hide it.
df["has_review"] = df["Review Rating"].notna().astype(int)
df["Review Rating"] = df["Review Rating"].fillna(df["Review Rating"].median())

# Standardize binary Yes/No columns to 0/1 for modeling use
df["discount_used"] = (df["Discount Applied"] == "Yes").astype(int)
df["is_subscriber"] = (df["Subscription Status"] == "Yes").astype(int)

# ------------------------------------------------------------
# 2. FREQUENCY SCORE
# Question this answers: "how often does this customer actually show up?"
# Frequency of Purchases is the only real recency/cadence signal in this
# dataset (there are no timestamps). We convert the 7 text categories into
# an ordered numeric scale so it can be used in scoring and correlation
# analysis, not just grouped.
# ------------------------------------------------------------
frequency_order = {
    "Weekly": 7,
    "Bi-Weekly": 6,
    "Fortnightly": 5,
    "Monthly": 4,
    "Quarterly": 3,
    "Every 3 Months": 3,  # Quarterly and "Every 3 Months" are the same cadence
    "Annually": 1,
}
df["frequency_score"] = df["Frequency of Purchases"].map(frequency_order)

# ------------------------------------------------------------
# 3. LOYALTY DEFINITION A — "Engagement Loyalty"
# Question this answers: "who shows up often and has made a formal
# commitment to the brand (subscription)?" This treats loyalty as a
# BEHAVIORAL/RELATIONSHIP signal, independent of how much money they spend.
# ------------------------------------------------------------
# Normalize frequency_score to 0-1, combine with subscription flag (weighted
# higher since it's a deliberate opt-in, not passive behavior)
df["engagement_score"] = (
    0.6 * (df["frequency_score"] - 1) / (7 - 1)   # normalize 1-7 to 0-1
    + 0.4 * df["is_subscriber"]
)

df["loyalty_A"] = pd.cut(
    df["engagement_score"],
    bins=[-0.01, 0.33, 0.66, 1.0],
    labels=["Low Engagement", "Medium Engagement", "High Engagement"],
)

# ------------------------------------------------------------
# 4. LOYALTY DEFINITION B — "Value & Tenure Loyalty"
# Question this answers: "who has spent the most, over the longest history,
# regardless of how often they engage or whether they're subscribed?"
# This treats loyalty as an OUTCOME/VALUE signal — pure spend + tenure proxy.
# ------------------------------------------------------------
# Previous Purchases is our tenure/volume proxy; Purchase Amount is the
# current transaction value. Normalize both, combine equally.
df["prev_purchases_norm"] = (df["Previous Purchases"] - df["Previous Purchases"].min()) / (
    df["Previous Purchases"].max() - df["Previous Purchases"].min()
)
df["purchase_amount_norm"] = (df["Purchase Amount (USD)"] - df["Purchase Amount (USD)"].min()) / (
    df["Purchase Amount (USD)"].max() - df["Purchase Amount (USD)"].min()
)
df["value_score"] = 0.5 * df["prev_purchases_norm"] + 0.5 * df["purchase_amount_norm"]

df["loyalty_B"] = pd.qcut(
    df["value_score"], q=3, labels=["Low Value", "Mid Value", "High Value"]
)

# ------------------------------------------------------------
# 5. DISCOUNT DEPENDENCY SCORE
# Question this answers: "is this customer's purchase behavior propped up
# by discounts, or would they likely buy anyway?" At the individual-row
# level this dataset only gives us a single Yes/No discount flag, so the
# score here is really only meaningful in aggregate (per segment) — we
# still compute it here so it can be grouped later in SQL/Power BI.
# ------------------------------------------------------------
df["discount_dependency_flag"] = df["discount_used"]

# ------------------------------------------------------------
# 6. SATISFACTION FLAG
# Question this answers: "is this customer satisfied, or just present?"
# A customer can be high-frequency AND unhappy — this flag exists so we
# can catch that combination in segmentation instead of assuming
# engagement = satisfaction.
# ------------------------------------------------------------
df["satisfied_flag"] = (df["Review Rating"] >= 4.0).astype(int)

# ------------------------------------------------------------
# 7. EXPORT clean feature table
# ------------------------------------------------------------
output_cols = [
    "Customer ID", "Age", "Gender", "Category", "Location", "Season",
    "Purchase Amount (USD)", "Previous Purchases", "Review Rating", "has_review",
    "Subscription Status", "is_subscriber", "Discount Applied", "discount_used",
    "Payment Method", "Shipping Type", "Frequency of Purchases", "frequency_score",
    "engagement_score", "loyalty_A",
    "value_score", "loyalty_B",
    "discount_dependency_flag", "satisfied_flag",
]
df_out = df[output_cols].rename(columns={"Customer ID": "customer_id"})
df_out.to_csv("customer_features.csv", index=False)

print("Saved customer_features.csv:", df_out.shape)
print()

# ------------------------------------------------------------
# 8. COMPARE THE TWO LOYALTY DEFINITIONS
# This is the core "argue for one" analysis the brief requires.
# ------------------------------------------------------------
print("=" * 60)
print("LOYALTY DEFINITION A (Engagement) distribution:")
print(df["loyalty_A"].value_counts())
print()
print("LOYALTY DEFINITION B (Value/Tenure) distribution:")
print(df["loyalty_B"].value_counts())
print()

print("=" * 60)
print("Cross-tab: do A and B agree on who's 'loyal'?")
crosstab = pd.crosstab(df["loyalty_A"], df["loyalty_B"])
print(crosstab)
print()
# Measure agreement: what % of customers land in the "matching" diagonal
# (Low-Low, Medium-Mid, High-High)?
agreement = (
    crosstab.loc["Low Engagement", "Low Value"]
    + crosstab.loc["Medium Engagement", "Mid Value"]
    + crosstab.loc["High Engagement", "High Value"]
) / crosstab.values.sum()
print(f"Diagonal agreement rate between definitions A and B: {agreement:.1%}")
print()

print("=" * 60)
print("Which definition better separates discount-dependent customers?")
print("Discount usage rate by Loyalty A tier:")
print(df.groupby("loyalty_A")["discount_used"].mean().round(3))
print()
print("Discount usage rate by Loyalty B tier:")
print(df.groupby("loyalty_B")["discount_used"].mean().round(3))
print()

print("=" * 60)
print("Which definition better separates satisfaction?")
print("Avg review rating by Loyalty A tier:")
print(df.groupby("loyalty_A")["Review Rating"].mean().round(2))
print()
print("Avg review rating by Loyalty B tier:")
print(df.groupby("loyalty_B")["Review Rating"].mean().round(2))
