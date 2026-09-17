import pandas as pd
from sentinelflow.aml.rules_engine import evaluate_df, RULES

def test_rules_fire():
    df = pd.DataFrame([{
        "amount": 9700, "channel":"wire", "mcc":"6012", "merchant_country":"IR",
        "customer_risk_tier":"pep", "velocity_24h":8, "is_night":1,
        "transaction_risk_score":90, "country":"US", "seconds_since_last":100
    }])
    out = evaluate_df(df)
    assert out["aml_score"].iloc[0] >= 5
    assert len(RULES)==21
