from prometheus_client import Counter, Histogram, Gauge
SCORE_COUNT = Counter("fraud_score_total", "scores")
SCORE_LAT = Histogram("fraud_score_latency_seconds", "lat")
DRIFT_PSI = Gauge("feature_drift_psi", "PSI", ["feature"])
MODEL_AUC = Gauge("model_auc", "AUC")
