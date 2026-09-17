"""AML Rules Engine – 21 rules"""
import pandas as pd

RULES = [
 ("R001", "structuring_near_10k", lambda r: 9500 <= r.amount <= 9999 and r.channel in ("wire","ach")),
 ("R002", "high_risk_geo", lambda r: r.merchant_country in ("IR","KP","SY","MM","AF","CY","VG","PA","LR")),
 ("R003", "pep_large", lambda r: r.customer_risk_tier=="pep" and r.amount>5000),
 ("R004", "wire_burst", lambda r: r.velocity_24h>=4 and r.channel=="wire"),
 ("R005", "mcc_crypto", lambda r: r.mcc=="6051" and r.amount>2000),
 ("R006", "gambling_spike", lambda r: r.mcc=="7995" and r.amount>1500),
 ("R007", "rapid_movement_24h", lambda r: r.velocity_24h>7),
 ("R008", "night_wire", lambda r: r.is_night==1 and r.channel=="wire" and r.amount>3000),
 ("R009", "round_amount", lambda r: r.amount % 1000 == 0 and r.amount>=5000),
 ("R010", "high_risk_score", lambda r: r.transaction_risk_score>85),
 ("R011", "cross_border_large", lambda r: r.country!=r.merchant_country and r.amount>4000),
 ("R012", "mule_inbound_outbound", lambda r: r.velocity_24h>5 and r.amount>800),
 ("R013", "tbml_invoice", lambda r: r.mcc in ("7399","5122") and r.amount>9000),
 ("R014", "first_time_high", lambda r: r.seconds_since_last>2592000 and r.amount>2000),
 ("R015", "high_risk_corridor", lambda r: r.merchant_country in ("AE","SG","CY") and r.amount>7500),
 ("R016", "smurf_pattern", lambda r: 800 <= r.amount <= 2900 and r.channel=="p2p"),
 ("R017", "bust_out_velocity", lambda r: r.velocity_24h>10),
 ("R018", "crypto_fiat_bridge", lambda r: r.mcc=="6051"),
 ("R019", "app_scam_flag", lambda r: r.channel=="p2p" and r.amount>1200 and r.is_night==1),
 ("R020", "layering_velocity", lambda r: r.velocity_24h>=6 and r.channel in ("ach","wire")),
 ("R021", "sanctions_hit", lambda r: r.merchant_country in ("IR","KP","SY")),
]

def evaluate_row(row)->list:
    hits=[]
    for code,name,fn in RULES:
        try:
            if fn(row): hits.append(code)
        except: pass
    return hits

def evaluate_df(df:pd.DataFrame)->pd.DataFrame:
    out=df.copy()
    out["rule_hits"] = out.apply(evaluate_row, axis=1)
    out["aml_score"] = out["rule_hits"].apply(len)
    out["aml_alert"] = out["aml_score"]>0
    return out
