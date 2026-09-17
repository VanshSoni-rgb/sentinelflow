from pydantic import BaseModel, Field
from typing import Optional, List

class ScoreRequest(BaseModel):
    amount: float = Field(..., gt=0)
    channel: str = "ecom"
    mcc: str = "5812"
    mcc_risk: int = 2
    merchant_country: str = "US"
    customer_risk_tier: str = "low"
    velocity_24h: int = 1
    hour: Optional[int] = 14
    device_type: Optional[str] = "web"

class ScoreResponse(BaseModel):
    fraud_score: float
    decision: str
    rules_triggered: List[str] = []
    risk_band: str

class EntityResponse(BaseModel):
    customer_id: str
    risk_tier: str
    total_volume: float
    fraud_cases: int
