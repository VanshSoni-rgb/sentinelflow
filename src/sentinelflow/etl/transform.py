"""Power BI star-schema export"""
import argparse, pandas as pd
from sqlalchemy import create_engine
from ..config import settings

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--powerbi", action="store_true")
    ap.add_argument("--output", default="powerbi/")
    args = ap.parse_args()
    eng = create_engine(settings.database_url)
    # Pull from postgres – fallback to parquet
    try:
        fact = pd.read_sql("SELECT * FROM sentinel.vw_fact_transactions_enriched LIMIT 1000000", eng)
        dim_cust = pd.read_sql("SELECT * FROM sentinel.dim_customer", eng)
        dim_merch = pd.read_sql("SELECT * FROM sentinel.dim_merchant", eng)
    except Exception:
        fact = pd.read_parquet("data/transactions_1m.parquet")
        dim_cust = pd.read_parquet("data/master_customers.parquet")
        dim_merch = pd.read_parquet("data/master_merchants.parquet")
    import os; os.makedirs(args.output, exist_ok=True)
    fact.to_csv(f"{args.output}/fact_transactions.csv", index=False)
    dim_cust.to_csv(f"{args.output}/dim_customer.csv", index=False)
    dim_merch.to_csv(f"{args.output}/dim_merchant.csv", index=False)
    # dim_date
    dates = pd.date_range("2023-01-01","2024-06-30")
    dim_date = pd.DataFrame({"date_key": dates.strftime("%Y%m%d").astype(int),
        "full_date": dates, "year": dates.year, "month": dates.month,
        "quarter": dates.quarter, "dow": dates.dayofweek, "is_weekend": dates.dayofweek>=5})
    dim_date.to_csv(f"{args.output}/dim_date.csv", index=False)
    # alerts
    alerts = fact[fact["aml_flag"]==True][["transaction_id","customer_id","aml_typology","amount","transaction_risk_score"]].copy()
    alerts["alert_type"]="AML"; alerts["status"]="open"
    alerts.to_csv(f"{args.output}/fact_alerts.csv", index=False)
    print(f"Power BI exports → {args.output} | fact rows {len(fact):,}")

if __name__=="__main__":
    main()
