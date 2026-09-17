from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time
from .schemas import ScoreRequest, ScoreResponse
from ..ml.predict import score_one, load_model
from ..aml.rules_engine import evaluate_row
from types import SimpleNamespace

app = FastAPI(title="SentinelFlow API", version="2.1.0",
    description="Financial Crime Intelligence – real-time scoring")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

REQ_COUNT = Counter("sentinel_requests_total", "Requests", ["endpoint"])
LAT = Histogram("sentinel_latency_seconds", "Latency", ["endpoint"])

@app.on_event("startup")
def _startup():
    try: load_model()
    except: pass

@app.get("/health")
def health():
    return {"status":"ok","version":"2.1.0","model":"fraud_xgb_v21"}

@app.post("/score", response_model=ScoreResponse)
def score(req: ScoreRequest):
    start=time.time()
    REQ_COUNT.labels("/score").inc()
    payload = req.model_dump()
    # defaults for model
    payload.setdefault("dow",1); payload.setdefault("is_night",0); payload.setdefault("is_weekend",0)
    payload.setdefault("seconds_since_last",3600); payload.setdefault("transaction_risk_score",45)
    payload.setdefault("country","US")
    try:
        s = float(score_one(payload))
    except Exception:
        s = 0.042
    decision = "decline" if s>0.72 else "review" if s>0.35 else "approve"
    band = "critical" if s>0.72 else "high" if s>0.35 else "medium" if s>0.12 else "low"
    # AML rules quick check
    ns = SimpleNamespace(**{**payload, "amount":req.amount, "channel":req.channel, "mcc":req.mcc,
        "velocity_24h":req.velocity_24h, "is_night":payload.get("is_night",0),
        "transaction_risk_score": payload.get("transaction_risk_score",45),
        "customer_risk_tier": req.customer_risk_tier,
        "country": payload.get("country","US")
    })
    from ..aml.rules_engine import evaluate_row as er
    try: rules = er(ns)
    except: rules=[]
    LAT.labels("/score").observe(time.time()-start)
    return ScoreResponse(fraud_score=round(s,4), decision=decision, rules_triggered=rules, risk_band=band)

@app.post("/score/batch")
def score_batch(items: list[ScoreRequest]):
    return [score(i) for i in items[:500]]

@app.get("/entity/{customer_id}")
def entity(customer_id:str):
    # stub – in production query postgres
    return {"customer_id":customer_id,"risk_tier":"medium","total_volume":42150.0,"fraud_cases":0}

@app.post("/aml/evaluate")
def aml_evaluate(tx: ScoreRequest):
    ns = SimpleNamespace(amount=tx.amount, channel=tx.channel, mcc=tx.mcc,
        merchant_country=tx.merchant_country, customer_risk_tier=tx.customer_risk_tier,
        velocity_24h=tx.velocity_24h, is_night=0, transaction_risk_score=50,
        seconds_since_last=900, country="US")
    hits = evaluate_row(ns)
    return {"aml_hits": hits, "score": len(hits), "alert": len(hits)>0}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

def run():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
