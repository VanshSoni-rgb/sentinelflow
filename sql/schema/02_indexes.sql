SET search_path TO sentinel, public;

CREATE INDEX IF NOT EXISTS ix_fact_ts ON fact_transactions (ts DESC);
CREATE INDEX IF NOT EXISTS ix_fact_customer_ts ON fact_transactions (customer_id, ts DESC);
CREATE INDEX IF NOT EXISTS ix_fact_account_ts ON fact_transactions (account_id, ts DESC);
CREATE INDEX IF NOT EXISTS ix_fact_merchant ON fact_transactions (merchant_id);
CREATE INDEX IF NOT EXISTS ix_fact_fraud ON fact_transactions (is_fraud, ts) WHERE is_fraud = true;
CREATE INDEX IF NOT EXISTS ix_fact_aml ON fact_transactions (aml_flag, ts) WHERE aml_flag = true;
CREATE INDEX IF NOT EXISTS ix_fact_amount ON fact_transactions (amount DESC);
CREATE INDEX IF NOT EXISTS ix_fact_risk ON fact_transactions (transaction_risk_score DESC);
CREATE INDEX IF NOT EXISTS ix_fact_channel ON fact_transactions (channel, ts);
CREATE INDEX IF NOT EXISTS ix_alerts_status ON fact_alerts (status, created_at DESC);
