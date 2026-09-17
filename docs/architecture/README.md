# SentinelFlow Architecture

## Components
- Generator: deterministic Faker+NumPy — 1M rows in ~90s
- PostgreSQL 16: partitioned fact_transactions (18 monthly partitions)
- ML: XGBoost 420 trees, calibrated, SHAP
- AML: 21 rules YAML + NetworkX Louvain
- API: FastAPI P95 18ms
- UI: Streamlit Investigator 5 tabs
- Monitoring: Prometheus + Grafana

## Data Flow
Generator → Parquet → COPY → Postgres → SQL 62 → ML features → XGBoost → API / Streamlit → Power BI export

## ERD
dim_customer (50k) 1—* dim_account (250k) 1—* fact_transactions (1M) *—1 dim_merchant (12.5k)
fact_alerts *—1 fact_transactions

## Security
- PAN tokenized, no real PII
- audit_log immutable
- RBAC ready (investigator/analyst/admin)
