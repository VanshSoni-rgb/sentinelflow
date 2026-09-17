"""Entity master data generator - deterministic"""
import numpy as np
import pandas as pd
from faker import Faker
from typing import Tuple

MCC_CODES = [
    ("5411", "Grocery", 1), ("5812", "Restaurants", 3), ("5541", "Gas", 2),
    ("5311", "Dept Store", 2), ("5999", "Retail", 2), ("6012", "Financial Inst", 5),
    ("7299", "Services", 2), ("5732", "Electronics", 3), ("5912", "Pharmacy", 1),
    ("4121", "Taxi", 2), ("4814", "Telecom", 1), ("4899", "Cable",1),
    ("7995", "Gambling",5), ("5122", "Drugs",2), ("6051", "Crypto",5),
    ("7399", "Business Svcs",3), ("7011", "Hotels",2), ("4111", "Transit",1),
]
HIGH_RISK_COUNTRIES = ["CY", "VG", "PA", "LR", "MM", "AF", "IR", "KP", "SY"]
COUNTRIES = ["US","GB","CA","DE","FR","SG","AE","IN","BR","AU"] + HIGH_RISK_COUNTRIES

def gen_customers(n:int, seed:int=42)->pd.DataFrame:
    fake = Faker()
    Faker.seed(seed)
    np.random.seed(seed)
    ids = [f"C{1000000+i}" for i in range(n)]
    # risk tier: 78% low, 17% medium, 4% high, 1% PEP
    tiers = np.random.choice(["low","medium","high","pep"], n, p=[0.78,0.17,0.04,0.01])
    kyc_dates = pd.to_datetime("2020-01-01") + pd.to_timedelta(np.random.randint(0,1500,n), unit="D")
    p = np.array([0.42,0.12,0.08,0.07,0.05,0.04,0.03,0.06,0.04,0.03,0.006,0.006,0.006,0.006,0.006,0.006,0.006,0.006,0.006], dtype=float)
    p = p / p.sum()
    return pd.DataFrame({
        "customer_id": ids,
        "full_name": [fake.name() for _ in range(n)],
        "country": np.random.choice(COUNTRIES, n, p=p),
        "risk_tier": tiers,
        "kyc_date": kyc_dates,
        "pep_flag": tiers=="pep",
        "age": np.random.randint(18,79,n),
        "occupation_risk": np.random.choice([1,2,3,4,5], n, p=[0.5,0.25,0.15,0.07,0.03]),
    })

def gen_merchants(n:int, seed:int=43)->pd.DataFrame:
    np.random.seed(seed)
    mcc_df = pd.DataFrame(MCC_CODES, columns=["mcc","mcc_desc","mcc_risk"])
    picks = mcc_df.sample(n, replace=True, random_state=seed).reset_index(drop=True)
    picks["merchant_id"] = [f"M{200000+i}" for i in range(n)]
    picks["merchant_country"] = np.random.choice(COUNTRIES, n)
    picks["high_risk_merchant"] = picks["mcc_risk"]>=4
    return picks[["merchant_id","mcc","mcc_desc","mcc_risk","merchant_country","high_risk_merchant"]]

def gen_accounts(customers:pd.DataFrame, n_accounts:int, seed:int=44)->pd.DataFrame:
    np.random.seed(seed)
    cust_sample = customers.sample(n_accounts, replace=True, random_state=seed)
    types = np.random.choice(["checking","savings","credit","business"], n_accounts, p=[0.48,0.28,0.19,0.05])
    return pd.DataFrame({
        "account_id": [f"A{5000000+i}" for i in range(n_accounts)],
        "customer_id": cust_sample["customer_id"].values,
        "account_type": types,
        "open_date": pd.to_datetime("2021-06-01") + pd.to_timedelta(np.random.randint(0,900,n_accounts), unit="D"),
        "account_risk_score": np.clip(np.random.normal(35,18,n_accounts), 5, 95).round(1),
    })

def gen_devices(n:int=78000, seed:int=45)->pd.DataFrame:
    np.random.seed(seed)
    return pd.DataFrame({
        "device_id": [f"D{900000+i}" for i in range(n)],
        "device_type": np.random.choice(["ios","android","web","pos"], n, p=[0.34,0.38,0.20,0.08]),
        "device_risk": np.random.beta(2,8,n).round(3),
    })
