# Model Card — SentinelFlow Fraud v2.1

**Model:** XGBoost ensemble + Isotonic calibration  
**Version:** 2.1.0  
**Date:** 2024-06-15

## Intended Use
Real-time card / ACH / wire fraud scoring. Investigator triage, NOT sole auto-decline.

## Training Data
SentinelFlow synthetic 1,000,000 transactions, Jan 2023–Jun 2024. 8,721 fraud (0.87%). Time split 70/15/15.

## Features
47 engineered: amount_log, velocity_24h, seconds_since_last, mcc_risk, channel_* , geo_risk, device_risk, customer_risk_tier…

## Metrics (holdout)
- ROC-AUC: 0.941
- PR-AUC: 0.612
- Precision@100: 0.83
- Recall@0.5% FPR: 0.61
- Calibration ECE: 0.018

## Limitations
- Synthetic data – calibrate on production before deployment
- No 3DS / chargeback feedback loop in v2.1
- Geographic bias: US-heavy 55%

## Ethical / Fairness
- Age, gender, ethnicity NOT used
- Country used only for high-risk jurisdiction list (FATF-aligned)
- Threshold tuned to equal opportunity across risk_tier

## Monitoring
PSI weekly, AUC daily, drift alert PSI>0.25

## Approvals
Model Owner: Risk Analytics • Validated: 2024-06-10 • Next review: 2024-09-10
