import argparse, pandas as pd
from sqlalchemy import create_engine, text
from ..config import settings

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/transactions_1m.parquet")
    args = ap.parse_args()
    print(f"Loading {args.input} → Postgres")
    df = pd.read_parquet(args.input) if args.input.endswith(".parquet") else pd.read_csv(args.input)
    eng = create_engine(settings.database_url, executemany_mode="values", executemany_values_page_size=10000)
    # load dims first
    for tbl, qcol in [("dim_customer","customer_id"),("dim_merchant","merchant_id")]:
        pass # masters preloaded separately in production
    # bulk insert fact in chunks
    cols = [c for c in df.columns if c in [
      "transaction_id","ts","account_id","customer_id","merchant_id","device_id","channel","mcc",
      "amount","currency","country","merchant_country","auth_code","is_fraud","fraud_typology",
      "fraud_reported_at","aml_flag","aml_typology","transaction_risk_score","velocity_24h",
      "seconds_since_last","is_night","is_weekend","is_high_risk"]]
    chunk=50000
    with eng.begin() as conn:
        conn.execute(text("TRUNCATE sentinel.fact_transactions"))
        for i in range(0,len(df),chunk):
            sub=df.iloc[i:i+chunk][cols]
            sub.to_sql("fact_transactions", conn, schema="sentinel", if_exists="append", index=False, method="multi")
            print(f"  {i+len(sub):,}/{len(df):,}")
    print("Done.")

if __name__=="__main__":
    main()
