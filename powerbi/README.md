# Power BI – SentinelFlow

Exports generated via:
```
make powerbi-export
```

Files:
- fact_transactions.csv — 1,000,000 rows
- dim_customer.csv — 50,000
- dim_merchant.csv — 12,500
- dim_date.csv
- fact_alerts.csv — 1,240

Import template: `SentinelFlow.pbix` (included)

Relationships:
- dim_customer[customer_id] 1:* fact_transactions[customer_id]
- dim_merchant[merchant_id] 1:* fact_transactions[merchant_id]
- dim_date[full_date] 1:* fact_transactions[ts_date]

DAX Measures:
```
Fraud Rate % = DIVIDE( CALCULATE(COUNTROWS(fact_transactions), fact_transactions[is_fraud]=TRUE()), COUNTROWS(fact_transactions))
Loss Prevented = SUMX(FILTER(fact_transactions, fact_transactions[ml_decision]="decline" && fact_transactions[is_fraud]=TRUE()), fact_transactions[amount])
Alert Precision = DIVIDE([True Positives],[Alerts])
SAR Eligible Count = CALCULATE(DISTINCTCOUNT(fact_transactions[customer_id]), fact_transactions[aml_flag]=TRUE())
Fraud Loss = CALCULATE(SUM(fact_transactions[amount]), fact_transactions[is_fraud]=TRUE())
```

Pages included: Executive, Fraud Deep Dive, AML Workbench, Network, Regulatory.
