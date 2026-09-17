from fastapi.testclient import TestClient
from sentinelflow.api.main import app
client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code==200
    assert r.json()["status"]=="ok"

def test_score():
    r = client.post("/score", json={"amount":2400,"channel":"wire","mcc":"6012","mcc_risk":5,"merchant_country":"CY","customer_risk_tier":"high","velocity_24h":3})
    assert r.status_code==200
    assert "fraud_score" in r.json()
