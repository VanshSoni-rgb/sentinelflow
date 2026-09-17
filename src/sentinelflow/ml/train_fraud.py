"""Train fraud XGBoost – SentinelFlow"""
import argparse, json, time, os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve
from sklearn.isotonic import IsotonicRegression
import xgboost as xgb
from .features import engineer, get_feature_list

def load_data(source:str):
    if source=="postgres":
        from sqlalchemy import create_engine
        from ..config import settings
        eng = create_engine(settings.database_url)
        df = pd.read_sql("SELECT * FROM sentinel.fact_transactions ORDER BY ts", eng)
    else:
        df = pd.read_parquet(source) if source.endswith(".parquet") else pd.read_csv(source)
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/transactions_1m.parquet")
    ap.add_argument("--output", default="models/fraud_xgb_v21.json")
    args = ap.parse_args()
    print("[SentinelFlow ML] Loading…")
    df = load_data(args.input)
    if len(df) < 50000:
        print("WARN: Small dataset – using smoke mode")
    df = engineer(df)
    features = get_feature_list()
    # time split
    df = df.sort_values("ts")
    n=len(df); n_tr=int(n*0.70); n_val=int(n*0.15)
    tr, val, te = df.iloc[:n_tr], df.iloc[n_tr:n_tr+n_val], df.iloc[n_tr+n_val:]
    X_tr, y_tr = tr[features].fillna(0), tr["is_fraud"].astype(int)
    X_val, y_val = val[features].fillna(0), val["is_fraud"].astype(int)
    X_te, y_te = te[features].fillna(0), te["is_fraud"].astype(int)
    print(f"Train {len(X_tr):,}  Val {len(X_val):,}  Test {len(X_te):,} | fraud {y_tr.mean():.4f}")
    model = xgb.XGBClassifier(
        n_estimators=420, max_depth=7, learning_rate=0.07,
        subsample=0.82, colsample_bytree=0.78, min_child_weight=3,
        scale_pos_weight=110, eval_metric="aucpr", tree_method="hist", random_state=42
    )
    model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
    p_val = model.predict_proba(X_val)[:,1]
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(p_val, y_val)
    p_te = iso.transform(model.predict_proba(X_te)[:,1])
    auc = roc_auc_score(y_te, p_te)
    ap_score = average_precision_score(y_te, p_te)
    # precision@100
    idx = np.argsort(p_te)[::-1][:100]
    prec100 = y_te.iloc[idx].mean() if len(idx)>0 else 0
    print(f"ROC-AUC: {auc:.3f}  PR-AUC: {ap_score:.3f}  Precision@100: {prec100:.2f}")
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    model.save_model(args.output)
    # save calibrator + metadata
    meta = {
        "version": "2.1.0",
        "features": features,
        "roc_auc": auc,
        "pr_auc": ap_score,
        "precision_at_100": float(prec100),
        "trained_rows": len(X_tr),
        "fraud_rate": float(y_tr.mean()),
        "timestamp": time.time(),
    }
    with open(args.output.replace(".json","_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Saved → {args.output}")
    # SHAP summary (sample)
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(X_te.sample(min(500,len(X_te)), random_state=1))
        np.save(args.output.replace(".json","_shap.npy"), shap_vals)
        print("SHAP saved")
    except Exception as e:
        print("SHAP skipped:", e)

if __name__ == "__main__":
    main()
