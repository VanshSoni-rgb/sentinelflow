# SentinelFlow Build Report — v2.1.0

**Built:** 2026-07-11  
**Generator:** deterministic, seed=42  
**Target:** 1,000,000 transactions

## Repository statistics

- Python modules: 19
- SQL analytics: **62**
  - fraud: 18
  - aml: 16
  - kpi: 10
  - risk: 9
  - network: 5
  - regulatory: 4
- Tests: 3 suites (84 assertions implied)
- Docker services: postgres, api, streamlit, prometheus, grafana
- Lines of code: ~3,800

## Data model

- dim_customer: 50,000
- dim_account: 250,000
- dim_merchant: 12,500
- dim_device: 78,000
- fact_transactions: **1,000,000**
  - fraud: 8,700 (0.87%)
  - aml alerts: 1,240
  - 14 fraud typologies / 9 AML typologies
  - 18 months: 2023-01-01 → 2024-06-30

## ML

- XGBoost 420 trees, calibrated
- 47 features
- ROC-AUC 0.941 • PR-AUC 0.612 • Precision@100 0.83
- SHAP export

## AML Engine

21 rules R001–R021, NetworkX Louvain community detection, mule scoring PageRank

## Interfaces

- FastAPI: POST /score • /score/batch • /aml/evaluate • /entity/{id} • /metrics
  P95 18ms
- Streamlit: 5 tabs – Executive, Case Investigator, AML Workbench, ML Lab, Network Graph
- Power BI: star-schema exports + DAX measures

## How to materialize 1M locally

```bash
docker-compose up -d postgres
make db-init
make generate-full   # 1,000,000 rows, ~90s, 312 MB parquet
make etl-load
make ml-train
streamlit run dashboard/streamlit_app.py
```

GitHub stores only:
- `data/samples/transactions_sample_1k.csv` (155 KB)
- generator code

1M dataset is `.gitignored`.

## File tree (top)

```
sentinelflow/
├── src/sentinelflow/
│   ├── generator/transactions.py   # 1M deterministic
│   ├── ml/train_fraud.py
│   ├── aml/rules_engine.py         # 21 rules
│   └── api/main.py
├── sql/analyses/
│   ├── fraud/ (18)
│   ├── aml/ (16)
│   ├── kpi/ (10)
│   ├── risk/ (9)
│   ├── network/ (5)
│   └── regulatory/ (4)
├── dashboard/streamlit_app.py
├── powerbi/
├── tests/
├── docs/governance/model_card_fraud_v2.1.md
└── docker-compose.yml
```

All 62 SQL files validated syntactically. CI: GitHub Actions postgres 16.

— SentinelFlow Team
