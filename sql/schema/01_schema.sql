-- SentinelFlow Core Schema — PostgreSQL 16
SET search_path TO sentinel, public;

-- Dimensions
CREATE TABLE IF NOT EXISTS dim_customer (
  customer_id VARCHAR(32) PRIMARY KEY,
  full_name VARCHAR(120),
  country CHAR(2),
  risk_tier VARCHAR(16),
  pep_flag BOOLEAN,
  kyc_date DATE,
  age INT,
  occupation_risk INT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dim_merchant (
  merchant_id VARCHAR(32) PRIMARY KEY,
  mcc VARCHAR(8),
  mcc_desc VARCHAR(64),
  mcc_risk INT,
  merchant_country CHAR(2),
  high_risk_merchant BOOLEAN
);

CREATE TABLE IF NOT EXISTS dim_account (
  account_id VARCHAR(32) PRIMARY KEY,
  customer_id VARCHAR(32) REFERENCES dim_customer(customer_id),
  account_type VARCHAR(24),
  open_date DATE,
  account_risk_score NUMERIC(5,1)
);

CREATE TABLE IF NOT EXISTS dim_device (
  device_id VARCHAR(32) PRIMARY KEY,
  device_type VARCHAR(16),
  device_risk NUMERIC(5,3)
);

CREATE TABLE IF NOT EXISTS dim_date (
  date_key INT PRIMARY KEY,
  full_date DATE,
  year INT, quarter INT, month INT, dow INT,
  is_weekend BOOLEAN
);

-- Fact table partitioned monthly
CREATE TABLE IF NOT EXISTS fact_transactions (
  transaction_id VARCHAR(32) PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL,
  account_id VARCHAR(32),
  customer_id VARCHAR(32),
  merchant_id VARCHAR(32),
  device_id VARCHAR(32),
  channel VARCHAR(24),
  mcc VARCHAR(8),
  amount NUMERIC(14,2),
  currency CHAR(3),
  country CHAR(2),
  merchant_country CHAR(2),
  auth_code VARCHAR(24),
  is_fraud BOOLEAN,
  fraud_typology VARCHAR(40),
  fraud_reported_at TIMESTAMPTZ,
  aml_flag BOOLEAN,
  aml_typology VARCHAR(40),
  transaction_risk_score NUMERIC(5,1),
  velocity_24h INT,
  seconds_since_last NUMERIC,
  is_night INT,
  is_weekend INT,
  is_high_risk INT,
  ml_score NUMERIC(6,4),
  ml_decision VARCHAR(16)
) PARTITION BY RANGE (ts);

-- Monthly partitions Jan 2023 – Jun 2024
CREATE TABLE fact_transactions_2023_01 PARTITION OF fact_transactions FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');
CREATE TABLE fact_transactions_2023_02 PARTITION OF fact_transactions FOR VALUES FROM ('2023-02-01') TO ('2023-03-01');
CREATE TABLE fact_transactions_2023_03 PARTITION OF fact_transactions FOR VALUES FROM ('2023-03-01') TO ('2023-04-01');
CREATE TABLE fact_transactions_2023_04 PARTITION OF fact_transactions FOR VALUES FROM ('2023-04-01') TO ('2023-05-01');
CREATE TABLE fact_transactions_2023_05 PARTITION OF fact_transactions FOR VALUES FROM ('2023-05-01') TO ('2023-06-01');
CREATE TABLE fact_transactions_2023_06 PARTITION OF fact_transactions FOR VALUES FROM ('2023-06-01') TO ('2023-07-01');
CREATE TABLE fact_transactions_2023_07 PARTITION OF fact_transactions FOR VALUES FROM ('2023-07-01') TO ('2023-08-01');
CREATE TABLE fact_transactions_2023_08 PARTITION OF fact_transactions FOR VALUES FROM ('2023-08-01') TO ('2023-09-01');
CREATE TABLE fact_transactions_2023_09 PARTITION OF fact_transactions FOR VALUES FROM ('2023-09-01') TO ('2023-10-01');
CREATE TABLE fact_transactions_2023_10 PARTITION OF fact_transactions FOR VALUES FROM ('2023-10-01') TO ('2023-11-01');
CREATE TABLE fact_transactions_2023_11 PARTITION OF fact_transactions FOR VALUES FROM ('2023-11-01') TO ('2023-12-01');
CREATE TABLE fact_transactions_2023_12 PARTITION OF fact_transactions FOR VALUES FROM ('2023-12-01') TO ('2024-01-01');
CREATE TABLE fact_transactions_2024_01 PARTITION OF fact_transactions FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE fact_transactions_2024_02 PARTITION OF fact_transactions FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
CREATE TABLE fact_transactions_2024_03 PARTITION OF fact_transactions FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');
CREATE TABLE fact_transactions_2024_04 PARTITION OF fact_transactions FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');
CREATE TABLE fact_transactions_2024_05 PARTITION OF fact_transactions FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');
CREATE TABLE fact_transactions_2024_06 PARTITION OF fact_transactions FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');

CREATE TABLE IF NOT EXISTS fact_alerts (
  alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id VARCHAR(32),
  customer_id VARCHAR(32),
  alert_type VARCHAR(32),
  rule_code VARCHAR(32),
  score NUMERIC(6,4),
  status VARCHAR(24) DEFAULT 'open',
  created_at TIMESTAMPTZ DEFAULT now(),
  investigator VARCHAR(80),
  sar_filed BOOLEAN DEFAULT false
);

CREATE TABLE IF NOT EXISTS audit_log (
  log_id BIGSERIAL PRIMARY KEY,
  entity_type VARCHAR(40),
  entity_id VARCHAR(64),
  action VARCHAR(40),
  actor VARCHAR(80),
  ts TIMESTAMPTZ DEFAULT now(),
  details JSONB
);

-- Views for Power BI
CREATE OR REPLACE VIEW vw_fact_transactions_enriched AS
SELECT t.*, c.risk_tier, c.pep_flag, m.mcc_desc, a.account_type
FROM fact_transactions t
LEFT JOIN dim_customer c USING (customer_id)
LEFT JOIN dim_merchant m USING (merchant_id)
LEFT JOIN dim_account a USING (account_id);
