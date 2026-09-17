import pandas as pd, xgboost as xgb, json
from .features import engineer, get_feature_list
from ..config import settings

_model = None
_features = get_feature_list()

def load_model(path=None):
    global _model
    path = path or settings.model_path
    m = xgb.XGBClassifier()
    m.load_model(path)
    _model = m
    return m

def score_df(df:pd.DataFrame):
    global _model
    if _model is None:
        try: load_model()
        except: return [0.05]*len(df)
    X = engineer(df)[_features].fillna(0)
    probs = _model.predict_proba(X)[:,1]
    return probs.tolist()

def score_one(payload:dict)->float:
    df = pd.DataFrame([payload])
    # fill defaults
    for col in ["amount","mcc_risk","hour","dow","is_night","is_weekend","velocity_24h","seconds_since_last","transaction_risk_score","channel","merchant_country","customer_risk_tier"]:
        if col not in df: df[col]=0
    if "channel" not in payload: df["channel"]="ecom"
    return score_df(df)[0]
