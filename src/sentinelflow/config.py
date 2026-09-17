import os
from dataclasses import dataclass

@dataclass
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://sentinel:sentinel_dev@localhost:5432/sentinelflow")
    model_path: str = os.getenv("MODEL_PATH", "models/fraud_xgb_v21.json")
    seed: int = int(os.getenv("SENTINEL_SEED", "42"))
    fraud_rate_target: float = 0.0087
    # Generator scale
    n_customers: int = 50_000
    n_merchants: int = 12_500
    n_accounts: int = 250_000
    n_transactions: int = 1_000_000

settings = Settings()
