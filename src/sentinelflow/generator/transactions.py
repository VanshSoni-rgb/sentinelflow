"""SentinelFlow 1,000,000 transaction generator
Deterministic, typology-injected.
"""
import argparse, time
import numpy as np
import pandas as pd
from .entities import gen_customers, gen_merchants, gen_accounts, gen_devices, MCC_CODES, HIGH_RISK_COUNTRIES

RNG_SEED_DEFAULT = 42

FRAUD_TYPOLOGIES = [
 "card_present_counterfeit","cnp","account_takeover","app_scam","first_party",
 "bust_out","synthetic_id","merchant_collusion","velocity_burst","geo_impossible",
 "bin_attack","triangulation","refund_fraud","loyalty_abuse"
]
AML_TYPOLOGIES = [
 "structuring","smurfing","rapid_movement","layering","mule_account",
 "round_trip","high_risk_jurisdiction","tbml","pep_proximity"
]

def build_base_transactions(n:int, customers, accounts, merchants, devices, seed:int):
    np.random.seed(seed)
    start = pd.Timestamp("2023-01-01")
    end = pd.Timestamp("2024-06-30")
    ts = pd.to_datetime(np.random.randint(start.value//10**9, end.value//10**9, n), unit="s")
    ts = ts.sort_values()
    acct = accounts.sample(n, replace=True, random_state=seed+1)
    merch = merchants.sample(n, replace=True, random_state=seed+2).reset_index(drop=True)
    dev = devices.sample(n, replace=True, random_state=seed+3).reset_index(drop=True)
    # amount lognormal, channel dependent
    base_amt = np.random.lognormal(mean=3.9, sigma=1.25, size=n)
    channel = np.random.choice(["card_present","ecom","ach","wire","p2p","atm"], n, p=[0.31,0.29,0.15,0.07,0.12,0.06])
    mult = {"card_present":1.0,"ecom":1.15,"ach":3.2,"wire":12.5,"p2p":0.85,"atm":0.6}
    amount = np.array([base_amt[i]*mult[channel[i]] for i in range(n)]).round(2)
    amount = np.clip(amount, 1.0, 95000)
    df = pd.DataFrame({
        "transaction_id": [f"TX{1000000000+i}" for i in range(n)],
        "ts": ts.values,
        "account_id": acct["account_id"].values,
        "customer_id": acct["customer_id"].values,
        "merchant_id": merch["merchant_id"].values,
        "mcc": merch["mcc"].values,
        "mcc_risk": merch["mcc_risk"].values,
        "merchant_country": merch["merchant_country"].values,
        "device_id": dev["device_id"].values,
        "device_type": dev["device_type"].values,
        "channel": channel,
        "amount": amount,
        "currency": "USD",
        "auth_code": np.random.choice(["approved","declined","review"], n, p=[0.935,0.045,0.02]),
        "country": np.random.choice(["US","GB","CA","DE","FR","SG"], n, p=[0.55,0.14,0.1,0.08,0.07,0.06]),
    })
    # map customer risk
    cust_risk_map = customers.set_index("customer_id")["risk_tier"].to_dict()
    df["customer_risk_tier"] = df["customer_id"].map(cust_risk_map)
    return df

def inject_fraud(df:pd.DataFrame, target_rate=0.0087, seed=42)->pd.DataFrame:
    np.random.seed(seed+99)
    n = len(df)
    n_fraud = int(n*target_rate)
    # score for fraud likelihood
    score = (
        df["mcc_risk"]*0.25 +
        (df["amount"]>1500).astype(int)*0.5 +
        df["channel"].isin(["ecom","wire"]).astype(int)*0.3 +
        (df["customer_risk_tier"].isin(["high","pep"])).astype(int)*0.4 +
        np.random.rand(n)*0.5
    )
    fraud_idx = score.nlargest(n_fraud).index
    df["is_fraud"] = False
    df["fraud_typology"] = None
    df.loc[fraud_idx, "is_fraud"] = True
    # assign typologies round-robin weighted
    typos = np.random.choice(FRAUD_TYPOLOGIES, n_fraud, p=[0.18,0.20,0.11,0.08,0.07,0.05,0.04,0.04,0.07,0.04,0.03,0.03,0.04,0.02])
    df.loc[fraud_idx, "fraud_typology"] = typos
    # exaggerate fraud amount for some typologies
    mask = df["fraud_typology"].isin(["bust_out","app_scam","wire"])
    df.loc[mask & df["is_fraud"], "amount"] *= np.random.uniform(1.5,3.5, mask.sum())
    df["amount"] = df["amount"].round(2)
    # fraud label time
    df["fraud_reported_at"] = pd.NaT
    df.loc[fraud_idx, "fraud_reported_at"] = df.loc[fraud_idx, "ts"] + pd.to_timedelta(np.random.randint(1,72, n_fraud), unit="h")
    return df

def inject_aml(df:pd.DataFrame, seed:int=42)->pd.DataFrame:
    np.random.seed(seed+123)
    df["aml_flag"] = False
    df["aml_typology"] = None
    # Structuring: amounts 9500-9999, wires/ach
    struct_mask = (df["amount"].between(9500, 9999)) & (df["channel"].isin(["wire","ach"]))
    struct_idx = df[struct_mask].sample(frac=0.7, random_state=seed).index
    df.loc[struct_idx, ["aml_flag","aml_typology"]] = [True, "structuring"]
    # High risk jurisdiction
    hr_mask = df["merchant_country"].isin(HIGH_RISK_COUNTRIES) & (df["amount"]>2000)
    hr_idx = df[hr_mask].sample(frac=0.5, random_state=seed+1).index
    df.loc[hr_idx, ["aml_flag","aml_typology"]] = [True, "high_risk_jurisdiction"]
    # Rapid movement: add smurf rings post-hoc (mark 400 accounts)
    mule_accts = np.random.choice(df["account_id"].unique(), 400, replace=False)
    mule_mask = df["account_id"].isin(mule_accts) & (df["amount"]>800)
    df.loc[mule_mask, "aml_flag"] = df.loc[mule_mask, "aml_flag"] | (np.random.rand(mule_mask.sum())<0.15)
    df.loc[mule_mask & df["aml_flag"] & df["aml_typology"].isna(), "aml_typology"] = "mule_account"
    # PEP proximity
    pep_mask = (df["customer_risk_tier"]=="pep") & (df["amount"]>5000)
    df.loc[pep_mask, "aml_flag"] = True
    df.loc[pep_mask & df["aml_typology"].isna(), "aml_typology"] = "pep_proximity"
    # fill remaining AML typologies randomly to reach ~1240 alerts (scale for small n)
    current_aml = df["aml_flag"].sum()
    target_aml = min(1240, int(len(df)*0.00124))
    if len(df) < 50000:
        target_aml = max(5, int(len(df)*0.012))
    if current_aml < target_aml:
        need = target_aml - current_aml
        pool = df[~df["aml_flag"]]
        if len(pool) > 0:
            sample_n = min(len(pool), max(need, need*2))
            cand = pool.sample(sample_n, replace=False, random_state=seed+5)
            pick = cand.head(need).index
        df.loc[pick, "aml_flag"] = True
        df.loc[pick, "aml_typology"] = np.random.choice(["smurfing","layering","rapid_movement","round_trip","tbml"], need)
    return df

def add_features(df:pd.DataFrame)->pd.DataFrame:
    df = df.sort_values("ts").reset_index(drop=True)
    df["hour"] = pd.to_datetime(df["ts"]).dt.hour
    df["dow"] = pd.to_datetime(df["ts"]).dt.dayofweek
    df["is_night"] = df["hour"].isin([0,1,2,3,4,5]).astype(int)
    df["is_weekend"] = (df["dow"]>=5).astype(int)
    # velocity 24h per account (approx rolling count)
    df["velocity_24h"] = df.groupby("account_id").cumcount().astype(int) % 12 + 1 # simplified fast
    # time since last
    df["ts_prev"] = df.groupby("account_id")["ts"].shift(1)
    df["seconds_since_last"] = (pd.to_datetime(df["ts"]) - pd.to_datetime(df["ts_prev"])).dt.total_seconds().fillna(86400)
    df.drop(columns=["ts_prev"], inplace=True)
    # risk score heuristic
    df["transaction_risk_score"] = (
        np.log1p(df["amount"])/8*30 +
        df["mcc_risk"]*6 +
        df["is_night"]*8 +
        (df["channel"]=="wire").astype(int)*12 +
        (df["merchant_country"].isin(HIGH_RISK_COUNTRIES)).astype(int)*15
    ).clip(0,100).round(1)
    df["is_high_risk"] = (df["transaction_risk_score"]>72).astype(int)
    return df

def generate(n:int=1_000_000, seed:int=RNG_SEED_DEFAULT):
    print(f"[SentinelFlow] Generating {n:,} transactions | seed={seed}")
    t0=time.time()
    customers = gen_customers(50_000, seed)
    merchants = gen_merchants(12_500, seed+1)
    accounts = gen_accounts(customers, 250_000, seed+2)
    devices = gen_devices(78_000, seed+3)
    df = build_base_transactions(n, customers, accounts, merchants, devices, seed)
    df = inject_fraud(df, target_rate=0.0087, seed=seed)
    df = inject_aml(df, seed=seed)
    df = add_features(df)
    print(f"Done in {time.time()-t0:.1f}s — fraud={(df['is_fraud'].mean()*100):.2f}%  aml={df['aml_flag'].sum()}")
    return df, {"customers":customers,"merchants":merchants,"accounts":accounts,"devices":devices}

def main():
    ap = argparse.ArgumentParser(description="SentinelFlow generator")
    ap.add_argument("--rows", type=int, default=1_000_000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--output", type=str, default="data/transactions_1m.parquet")
    ap.add_argument("--csv", action="store_true")
    args = ap.parse_args()
    df, masters = generate(args.rows, args.seed)
    import os
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    if args.csv or args.output.endswith(".csv"):
        df.to_csv(args.output, index=False)
    else:
        df.to_parquet(args.output, index=False)
    # save masters
    for k,v in masters.items():
        v.to_parquet(f"data/master_{k}.parquet", index=False)
    # also always write sample
    os.makedirs("data/samples", exist_ok=True)
    df.head(1000).to_csv("data/samples/transactions_sample_1k.csv", index=False)
    print(f"Saved → {args.output}  ({len(df):,} rows)")
    print(df[["is_fraud","aml_flag"]].sum())

if __name__ == "__main__":
    main()
