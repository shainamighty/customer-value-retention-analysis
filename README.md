# Decoding Customer Value: A SQL-Driven Retention Strategy

Customer segmentation and retention analysis for a D2C fashion brand (~3,900 customers), answering one core question: **is this brand building genuine customer loyalty, or renting customers with discounts?**

## The problem

The brand had transactional data but no structured way to understand its customers — no loyalty score, no churn label, no timestamps. Every concept of "loyalty" and "value" had to be constructed from raw variables, tested, and justified rather than assumed.

## Approach

- **Python**: cleaned the dataset and engineered customer-level features, including two independently-built, competing loyalty definitions:
  - **Definition A — Engagement Loyalty**: built from purchase frequency + subscription status
  - **Definition B — Value/Tenure Loyalty**: built from previous purchase count + spend
- **SQL**: segmentation queries answering which customer profiles drive value, which categories/seasons associate with tenure, and which states show organic vs. discount-driven demand
- **Power BI**: 4-panel dashboard (customer value pyramid, promo dependency by engagement tier, top states by spend, category breakdown)
- **Business deliverables**: a retention playbook (promo sunset plan + geographic targeting) and a 1-page executive summary

## Key finding

The two loyalty definitions agree on only **33.6%** of customers, proving loyalty isn't one measurable thing in this data. Definition A was chosen as the primary lens because it — unlike Definition B — cleanly separates discount-dependent customers (22% → 43% → **100%** discount usage across its three tiers).

The sharper insight: customers in the highest engagement tier are **100% discount-reliant**, but their estimated lifetime value is statistically no different from low-engagement customers (~$1,500 either way). The brand is currently paying full discount cost for engagement it isn't converting into extra revenue.

## Files

| File | Description |
|---|---|
| `feature_engineering.py` | Data cleaning + feature engineering, including both loyalty definitions |
| `segmentation_queries.sql` | SQL segmentation answering the core business questions |
| `customer_features.csv` | Final engineered customer-level dataset |
| `customer_value.db` | SQLite database used for the SQL layer |
| `project.pbix` | Power BI dashboard (4 panels) |
| `Executive_Summary.docx` | 1-page summary of method, findings, and recommendation |
| `Retention_Playbook.docx` | Promotional sunset plan + geographic targeting recommendations |

## Tech stack

Python (pandas) · SQL (SQLite) · Power BI
