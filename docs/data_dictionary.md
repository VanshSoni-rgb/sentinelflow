# SentinelFlow Data Dictionary

## fact_transactions (1,000,000 rows)

| column | type | description |
|---|---|---|
| transaction_id | varchar | TX1000000000+ PK |
| ts | timestamptz | event time UTC |
| account_id | varchar | FK dim_account |
| customer_id | varchar | FK dim_customer |
| merchant_id | varchar | FK dim_merchant |
| device_id | varchar | FK dim_device |
| channel | varchar | card_present / ecom / ach / wire / p2p / atm |
| mcc | varchar | ISO 18245 |
| amount | numeric(14,2) | USD |
| currency | char(3) | USD |
| country | char(2) | customer country |
| merchant_country | char(2) | |
| auth_code | varchar | approved/declined/review |
| is_fraud | boolean | ground truth |
| fraud_typology | varchar | 14 typologies |
| fraud_reported_at | timestamptz | |
| aml_flag | boolean | |
| aml_typology | varchar | 9 typologies |
| transaction_risk_score | numeric(5,1) | 0-100 heuristic |
| velocity_24h | int | |
| seconds_since_last | numeric | |
| is_night | int | 0-5h local |
| is_weekend | int | |
| is_high_risk | int | score>72 |
| ml_score | numeric(6,4) | model output |
| ml_decision | varchar | approve/review/decline |

See full 47-feature list in `src/sentinelflow/ml/features.py`.
