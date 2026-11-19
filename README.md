# Duka Electronics Sales Exploration & Mobile Money Agent Clean-Up (`plp-da-a3-duka-sales-and-agent-cleanup`)

## Project Overview
This repository delivers two end-to-end data analytics engagements:
1. **Engagement 1 — Duka Electronics (`duka_sales_exploration.ipynb`):** Half-year (Jan–Jun 2026) exploratory sales analysis across 1,000 orders, feature engineering (`revenue`, `month`, `weekday`, `is_weekend`, `price_band`), branch/product rankings, high-value segment filtering (`outputs/premium_online_coast_capital.csv`), and Excel reconciliation (`excel/duka_branch_summary.xlsx`).
2. **Engagement 2 — Mobile Money Agent Network (`cleaning_pipeline.py` & `agent_cleanup.ipynb`):** Automated data quality audit, deduplication, standardisation, IQR outlier flagging, agent register merge, county/weekly aggregations, clean data export (`outputs/agent_transactions_clean.csv`), and a 6-dimension Data Quality & Kenya Data Protection Act (2019) Privacy Report.

---

## How to Reproduce & Run

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
