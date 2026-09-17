-- ============================================================
-- SentinelFlow — Financial Crime Intelligence Platform
-- ANALYSES MASTER — ALL 62 QUERIES IN ONE FILE
-- Version: 2.1.0
-- PostgreSQL 16 • schema: sentinel
-- 1,000,000 transactions
-- Generated: 2026-07-11
-- ============================================================
-- Usage:
--   psql postgresql://sentinel:sentinel_dev@localhost:5432/sentinelflow \
--     -v ON_ERROR_STOP=1 -f sql/analyses/analyses.sql
-- ============================================================

SET search_path TO sentinel, public;
SET statement_timeout = '5min';
\timing on

\echo '========================================'
\echo 'SentinelFlow — 62 Analytics — 1M rows'
\echo '========================================'

-- Q001 velocity_24h — Card/account velocity burst 24h
SELECT account_id, DATE_TRUNC('hour', ts) AS hr, COUNT(*) AS txns, SUM(amount) AS vol, SUM(is_fraud::int) fraud_hits
FROM sentinel.fact_transactions
WHERE ts >= now() - INTERVAL '30 days'
GROUP BY 1,2 HAVING COUNT(*) > 5 ORDER BY txns DESC LIMIT 200;

-- Q002 geo_velocity_impossible — Impossible travel
WITH loc AS (
 SELECT transaction_id, customer_id, ts, country,
 LAG(country) OVER (PARTITION BY customer_id ORDER BY ts) prev_country,
 LAG(ts) OVER (PARTITION BY customer_id ORDER BY ts) prev_ts
 FROM sentinel.fact_transactions)
SELECT * FROM loc WHERE country <> prev_country AND EXTRACT(EPOCH FROM ts-prev_ts)/3600 < 3 ORDER BY ts DESC;

-- Q003 amount_zscore — Amount Z-score anomaly per customer
WITH s AS (
 SELECT customer_id, AVG(amount) m, STDDEV(amount) sd FROM sentinel.fact_transactions GROUP BY 1)
SELECT t.transaction_id, t.customer_id, t.amount, (t.amount-s.m)/NULLIF(s.sd,0) z
FROM sentinel.fact_transactions t JOIN s USING(customer_id)
WHERE ABS((t.amount-s.m)/NULLIF(s.sd,0))>4 ORDER BY z DESC LIMIT 500;

-- Q004 bin_attack_detection — BIN attack / card testing
SELECT merchant_id, DATE_TRUNC('hour', ts) hr, COUNT(DISTINCT account_id) cards, COUNT(*) tries,
 SUM(CASE WHEN auth_code='declined' THEN 1 ELSE 0 END)::float/COUNT(*) decline_rate
FROM sentinel.fact_transactions WHERE channel='ecom'
GROUP BY 1,2 HAVING COUNT(*)>25 AND SUM(CASE WHEN auth_code='declined' THEN 1 ELSE 0 END)::float/COUNT(*) >0.6
ORDER BY decline_rate DESC;

-- Q005 merchant_collusion — Merchant collusion risk
SELECT merchant_id, COUNT(*) txns, SUM(is_fraud::int) frauds,
 SUM(is_fraud::int)::float/COUNT(*) fraud_rate, SUM(amount) volume
FROM sentinel.fact_transactions GROUP BY 1 HAVING COUNT(*)>50
ORDER BY fraud_rate DESC LIMIT 100;

-- Q006 account_takeover — ATO signals
SELECT customer_id, COUNT(DISTINCT device_id) devices_7d, COUNT(*) txns
FROM sentinel.fact_transactions WHERE ts > now() - INTERVAL '7 days'
GROUP BY 1 HAVING COUNT(DISTINCT device_id) >=3 ORDER BY devices_7d DESC;

-- Q007 first_party_fraud — First-party / bust-out ramp
SELECT account_id, DATE_TRUNC('week', ts) wk, SUM(amount) spend, COUNT(*) n
FROM sentinel.fact_transactions GROUP BY 1,2 ORDER BY spend DESC LIMIT 200;

-- Q008 cnp_spike — CNP spike ecom
SELECT customer_id, DATE(ts) d, SUM(CASE WHEN channel='ecom' THEN amount ELSE 0 END) ecom_vol
FROM sentinel.fact_transactions GROUP BY 1,2 HAVING SUM(CASE WHEN channel='ecom' THEN amount ELSE 0 END) > 2500;

-- Q009 night_anomaly — Night-time high-risk
SELECT * FROM sentinel.fact_transactions WHERE is_night=1 AND transaction_risk_score>80 ORDER BY amount DESC LIMIT 300;

-- Q010 device_velocity — Device velocity
SELECT device_id, COUNT(DISTINCT account_id) accts, COUNT(*) txns
FROM sentinel.fact_transactions GROUP BY 1 HAVING COUNT(DISTINCT account_id)>4 ORDER BY accts DESC;

-- Q011 refund_fraud — Refund / triangulation
SELECT customer_id, SUM(CASE WHEN amount<0 THEN 1 ELSE 0 END) refunds, COUNT(*) total
FROM sentinel.fact_transactions GROUP BY 1 HAVING SUM(CASE WHEN amount<0 THEN 1 ELSE 0 END) >3;

-- Q012 fraud_by_mcc — Fraud rate by MCC
SELECT mcc, COUNT(*) txns, SUM(is_fraud::int) frauds, SUM(is_fraud::int)::float/COUNT(*) rate
FROM sentinel.fact_transactions GROUP BY 1 ORDER BY rate DESC;

-- Q013 fraud_loss_curve — Cumulative fraud loss
SELECT DATE_TRUNC('week', ts) wk, SUM(CASE WHEN is_fraud THEN amount ELSE 0 END) loss,
 COUNT(*) FILTER (WHERE is_fraud) n FROM sentinel.fact_transactions GROUP BY 1 ORDER BY 1;

-- Q014 velocity_burst — Velocity burst 1h
SELECT account_id, ts, velocity_24h, amount FROM sentinel.fact_transactions WHERE velocity_24h>8 ORDER BY velocity_24h DESC LIMIT 500;

-- Q015 geo_mismatch — Country mismatch cust vs merchant
SELECT * FROM sentinel.fact_transactions WHERE country<>merchant_country AND amount>1000 ORDER BY amount DESC LIMIT 200;

-- Q016 fraud_precision_by_score — Precision by ML score bucket
SELECT WIDTH_BUCKET(COALESCE(ml_score, transaction_risk_score/100.0),0,1,10) bucket,
 COUNT(*) n, SUM(is_fraud::int) frauds, SUM(is_fraud::int)::float/COUNT(*) precision
FROM sentinel.fact_transactions GROUP BY 1 ORDER BY 1 DESC;

-- Q017 new_device_high_amount — New device high amount
SELECT t.* FROM sentinel.fact_transactions t
JOIN (SELECT account_id, MIN(ts) first_seen, device_id FROM sentinel.fact_transactions GROUP BY 1,3) f
 ON t.account_id=f.account_id AND t.device_id=f.device_id
WHERE t.ts < f.first_seen + INTERVAL '24 hours' AND t.amount>1200;

-- Q018 fraud_network_links — Fraud network shared device
SELECT device_id, COUNT(DISTINCT customer_id) customers, SUM(is_fraud::int) frauds
FROM sentinel.fact_transactions GROUP BY 1 HAVING SUM(is_fraud::int)>1 ORDER BY frauds DESC;

-- Q019 structuring_near_10k — Structuring $9.5–9.99k
SELECT customer_id, DATE(ts) d, COUNT(*) n, SUM(amount) total
FROM sentinel.fact_transactions WHERE amount BETWEEN 9500 AND 9999.99
GROUP BY 1,2 HAVING COUNT(*)>=1 ORDER BY total DESC;

-- Q020 smurfing_ring — Smurfing ring detection
SELECT merchant_id, DATE(ts) d, COUNT(DISTINCT account_id) smurfs, SUM(amount) volume
FROM sentinel.fact_transactions WHERE amount BETWEEN 800 AND 3000
GROUP BY 1,2 HAVING COUNT(DISTINCT account_id)>=6 ORDER BY smurfs DESC;

-- Q021 rapid_movement — Rapid movement fan-out 24h
SELECT account_id, DATE_TRUNC('day', ts) day, COUNT(DISTINCT merchant_id) outs, SUM(amount) vol
FROM sentinel.fact_transactions GROUP BY 1,2 HAVING COUNT(DISTINCT merchant_id)>8;

-- Q022 layering_chains — Layering 3+ hops heuristic
SELECT customer_id, COUNT(*) hops, SUM(amount) volume
FROM sentinel.fact_transactions WHERE channel IN ('wire','ach') AND amount>5000
GROUP BY 1 HAVING COUNT(*)>=3 ORDER BY volume DESC;

-- Q023 mule_scoring — Mule account scoring
SELECT account_id, SUM(CASE WHEN amount>0 THEN amount ELSE 0 END) inflow,
 COUNT(*) txns, COUNT(DISTINCT merchant_id) counterparties FROM sentinel.fact_transactions
GROUP BY 1 ORDER BY inflow DESC LIMIT 200;

-- Q024 round_trip — Round-trip same-day
WITH a AS (SELECT account_id, DATE(ts) d, SUM(amount) s FROM sentinel.fact_transactions GROUP BY 1,2)
SELECT * FROM a WHERE s BETWEEN -250 AND 250 AND ABS(s)>0 LIMIT 500;

-- Q025 high_risk_corridor — High-risk jurisdiction corridor
SELECT * FROM sentinel.fact_transactions WHERE merchant_country IN ('CY','VG','PA','IR','KP','MM','SY','LR','AF')
ORDER BY amount DESC LIMIT 500;

-- Q026 pep_proximity — PEP proximity large flows
SELECT t.* FROM sentinel.fact_transactions t JOIN sentinel.dim_customer c USING(customer_id)
WHERE c.pep_flag = true AND t.amount>5000 ORDER BY t.amount DESC;

-- Q027 ctr_aggregation — CTR aggregation >$10k daily
SELECT customer_id, DATE(ts) d, SUM(amount) daily_cash
FROM sentinel.fact_transactions WHERE channel IN ('atm','ach','wire')
GROUP BY 1,2 HAVING SUM(amount)>10000 ORDER BY daily_cash DESC;

-- Q028 tbml_flags — Trade-based ML flags
SELECT * FROM sentinel.fact_transactions WHERE mcc IN ('7399','5999','5122') AND amount BETWEEN 9900 AND 50000 AND merchant_country <> country;

-- Q029 sar_narrative_helper — SAR narrative helper
SELECT customer_id, MIN(ts) first_alert, MAX(ts) last_alert, COUNT(*) alerts,
 SUM(amount) FILTER (WHERE aml_flag) aml_volume, STRING_AGG(DISTINCT aml_typology, ', ') typos
FROM sentinel.fact_transactions WHERE aml_flag=true GROUP BY 1 ORDER BY aml_volume DESC LIMIT 100;

-- Q030 fan_in_fan_out — Fan-in / fan-out
SELECT account_id,
 COUNT(DISTINCT CASE WHEN amount>0 THEN merchant_id END) fan_out,
 SUM(amount) vol FROM sentinel.fact_transactions GROUP BY 1 HAVING COUNT(DISTINCT merchant_id)>10;

-- Q031 aml_risk_tiering — Customer AML risk tiering
SELECT c.customer_id, c.risk_tier, COUNT(*) FILTER (WHERE t.aml_flag) aml_alerts,
 SUM(t.amount) FILTER (WHERE t.aml_flag) aml_vol
FROM sentinel.dim_customer c LEFT JOIN sentinel.fact_transactions t USING(customer_id)
GROUP BY 1,2 ORDER BY aml_alerts DESC NULLS LAST;

-- Q032 wire_burst — Wire burst
SELECT customer_id, DATE_TRUNC('hour', ts) hr, COUNT(*) wires, SUM(amount) vol
FROM sentinel.fact_transactions WHERE channel='wire' GROUP BY 1,2 HAVING COUNT(*)>2;

-- Q033 mule_community — Mule community detection prep
SELECT a.account_id, b.account_id AS linked_account, COUNT(*) shared_merchant
FROM sentinel.fact_transactions a JOIN sentinel.fact_transactions b ON a.merchant_id=b.merchant_id AND a.account_id < b.account_id
GROUP BY 1,2 HAVING COUNT(*)>=3 LIMIT 1000;

-- Q034 aml_alert_queue — AML alert queue prioritized
SELECT transaction_id, customer_id, aml_typology, amount, transaction_risk_score,
 ROW_NUMBER() OVER (ORDER BY transaction_risk_score DESC, amount DESC) priority
FROM sentinel.fact_transactions WHERE aml_flag=true ORDER BY priority LIMIT 200;

-- Q035 auth_rates — Authorization rates
SELECT channel, COUNT(*) n, AVG((auth_code='approved')::int) auth_rate FROM sentinel.fact_transactions GROUP BY 1;

-- Q036 fraud_rate_timeseries — Fraud rate timeseries
SELECT DATE_TRUNC('day', ts) d,
 COUNT(*) vol, SUM(is_fraud::int)::float/COUNT(*) fraud_rate, SUM(CASE WHEN is_fraud THEN amount ELSE 0 END) loss
FROM sentinel.fact_transactions GROUP BY 1 ORDER BY 1;

-- Q037 loss_prevented — Loss prevented estimate
SELECT SUM(amount) FILTER (WHERE COALESCE(ml_decision,'review')='decline' AND is_fraud) prevented_loss
FROM sentinel.fact_transactions;

-- Q038 false_positive_cost — False positive cost
SELECT COUNT(*) FILTER (WHERE ml_decision='decline' AND NOT is_fraud) fp,
 COUNT(*) FILTER (WHERE ml_decision='decline') total_declines FROM sentinel.fact_transactions;

-- Q039 channel_performance — Channel performance
SELECT channel, COUNT(*) txns, SUM(amount) volume,
 SUM(is_fraud::int)::float/COUNT(*) fraud_rate FROM sentinel.fact_transactions GROUP BY 1;

-- Q040 top_merchants_volume — Top merchants
SELECT merchant_id, SUM(amount) vol, COUNT(*) txns FROM sentinel.fact_transactions GROUP BY 1 ORDER BY vol DESC LIMIT 50;

-- Q041 customer_lifetime_value — CLV risk adjusted
SELECT customer_id, SUM(amount) gross, SUM(CASE WHEN is_fraud THEN amount ELSE 0 END) fraud_loss
FROM sentinel.fact_transactions GROUP BY 1 ORDER BY gross DESC LIMIT 100;

-- Q042 alert_precision — Alert precision
SELECT rule_code, COUNT(*) alerts, AVG(score) avg_score FROM sentinel.fact_alerts GROUP BY 1;

-- Q043 sla_investigation — Investigation SLA
SELECT status, AVG(EXTRACT(EPOCH FROM now()-created_at)/3600) hrs_open, COUNT(*) FROM sentinel.fact_alerts GROUP BY 1;

-- Q044 executive_snapshot — Executive snapshot
SELECT 
 COUNT(*) txns, SUM(amount) volume,
 SUM(is_fraud::int) fraud_cases,
 SUM(CASE WHEN is_fraud THEN amount ELSE 0 END) fraud_loss,
 SUM(aml_flag::int) aml_alerts
FROM sentinel.fact_transactions WHERE ts >= CURRENT_DATE - INTERVAL '30 days';

-- Q045 exposure_by_mcc — Exposure by MCC
SELECT mcc, SUM(amount) exposure, SUM(is_fraud::int)::float/COUNT(*) fraud_rate FROM sentinel.fact_transactions GROUP BY 1 ORDER BY exposure DESC;

-- Q046 customer_risk_migration — Customer risk migration
SELECT risk_tier, COUNT(DISTINCT customer_id) customers, 
 AVG(t.transaction_risk_score) avg_score FROM sentinel.dim_customer c JOIN sentinel.fact_transactions t USING(customer_id)
GROUP BY 1;

-- Q047 device_risk — Device risk leaderboard
SELECT device_id, COUNT(*) txns, SUM(is_fraud::int) frauds,
 SUM(is_fraud::int)::float/NULLIF(COUNT(*),0) rate FROM sentinel.fact_transactions GROUP BY 1 ORDER BY rate DESC NULLS LAST LIMIT 100;

-- Q048 geo_risk_heatmap — Geo risk heatmap
SELECT country, merchant_country, COUNT(*) n, SUM(is_fraud::int) frauds
FROM sentinel.fact_transactions GROUP BY 1,2 ORDER BY frauds DESC LIMIT 100;

-- Q049 velocity_risk_matrix — Velocity vs amount matrix
SELECT WIDTH_BUCKET(velocity_24h,0,20,5) v_bucket, WIDTH_BUCKET(amount::int,0,5000,5) a_bucket,
 COUNT(*), SUM(is_fraud::int) frauds FROM sentinel.fact_transactions GROUP BY 1,2 ORDER BY 1,2;

-- Q050 account_health — Account health score
SELECT account_id, AVG(transaction_risk_score) avg_risk, COUNT(*) FILTER (WHERE is_fraud) frauds,
 MAX(ts) last_tx FROM sentinel.fact_transactions GROUP BY 1 ORDER BY avg_risk DESC LIMIT 200;

-- Q051 concentration_risk — Concentration risk
SELECT customer_id, SUM(amount) total, 
 MAX(amount)/NULLIF(SUM(amount),0) concentration FROM sentinel.fact_transactions GROUP BY 1 HAVING SUM(amount)>50000 ORDER BY concentration DESC;

-- Q052 chargeback_exposure — Chargeback exposure
SELECT DATE_TRUNC('month', ts) mon, SUM(CASE WHEN is_fraud THEN amount ELSE 0 END) exp
FROM sentinel.fact_transactions GROUP BY 1 ORDER BY 1;

-- Q053 kpi_risk_appetite — Risk appetite breach
SELECT DATE(ts) d, SUM(is_fraud::int)::float/COUNT(*) rate FROM sentinel.fact_transactions
GROUP BY 1 HAVING SUM(is_fraud::int)::float/COUNT(*) > 0.012 ORDER BY d;

-- Q054 bipartite_customer_merchant — Bipartite graph extract
SELECT customer_id, merchant_id, COUNT(*) weight, SUM(amount) volume
FROM sentinel.fact_transactions GROUP BY 1,2 HAVING COUNT(*)>=2 LIMIT 5000;

-- Q055 mule_communities — Mule community edges
SELECT t1.account_id AS src, t2.account_id AS dst, COUNT(*) shared
FROM sentinel.fact_transactions t1 JOIN sentinel.fact_transactions t2 
 ON t1.merchant_id=t2.merchant_id AND t1.account_id < t2.account_id
GROUP BY 1,2 HAVING COUNT(*)>=2 LIMIT 2000;

-- Q056 circular_payments — Circular payment heuristic
SELECT customer_id, COUNT(DISTINCT merchant_id) merchants, SUM(amount) vol
FROM sentinel.fact_transactions WHERE channel='p2p' GROUP BY 1 HAVING COUNT(DISTINCT merchant_id)>5;

-- Q057 pagerank_seeds — PageRank seed accounts
SELECT account_id, COUNT(*) degree, SUM(amount) strength
FROM sentinel.fact_transactions GROUP BY 1 ORDER BY strength DESC LIMIT 500;

-- Q058 shared_device_network — Shared device network
SELECT device_id, ARRAY_AGG(DISTINCT customer_id) customers, COUNT(*) txns
FROM sentinel.fact_transactions GROUP BY 1 HAVING COUNT(DISTINCT customer_id)>1 LIMIT 500;

-- Q059 ctr_report — CTR report $10k+
SELECT customer_id, DATE(ts) AS activity_date, SUM(amount) AS cash_total,
 COUNT(*) AS txns FROM sentinel.fact_transactions WHERE channel IN ('atm','ach','wire')
GROUP BY 1,2 HAVING SUM(amount)>=10000 ORDER BY cash_total DESC;

-- Q060 sar_draft — SAR draft extract
SELECT customer_id, STRING_AGG(DISTINCT aml_typology, '; ') AS typologies,
 MIN(ts) AS start_date, MAX(ts) AS end_date, SUM(amount) FILTER (WHERE aml_flag) AS suspicious_amount,
 COUNT(*) FILTER (WHERE aml_flag) AS alert_count
FROM sentinel.fact_transactions WHERE aml_flag=true GROUP BY 1 HAVING COUNT(*) FILTER (WHERE aml_flag) >=3;

-- Q061 ofac_fuzzy — OFAC fuzzy screening helper
SELECT customer_id, full_name, country FROM sentinel.dim_customer
WHERE country IN ('IR','KP','SY','CU') OR pep_flag = true;

-- Q062 314a_lookup — 314(a) lookup template
-- Parameterize :search_name
SELECT c.customer_id, c.full_name, SUM(t.amount) total_12m, COUNT(*) txns
FROM sentinel.dim_customer c JOIN sentinel.fact_transactions t USING(customer_id)
WHERE c.full_name ILIKE '%SEARCH_TERM%' AND t.ts > now() - INTERVAL '12 months'
GROUP BY 1,2;

-- ==================== SentinelFlow Summary ====================
SELECT 
  'fact_transactions' as table_name,
  COUNT(*) as rows,
  SUM(is_fraud::int) as fraud_cases,
  ROUND(100.0*SUM(is_fraud::int)/COUNT(*),3) as fraud_rate_pct,
  SUM(aml_flag::int) as aml_alerts,
  SUM(CASE WHEN is_fraud THEN amount ELSE 0 END) as fraud_loss
FROM sentinel.fact_transactions;

SELECT fraud_typology, COUNT(*) n 
FROM sentinel.fact_transactions 
WHERE is_fraud 
GROUP BY 1 ORDER BY 2 DESC LIMIT 5;

SELECT aml_typology, COUNT(*) n
FROM sentinel.fact_transactions
WHERE aml_flag
GROUP BY 1 ORDER BY 2 DESC LIMIT 5;

\echo '================ SentinelFlow — 62 Queries Complete ================'
\echo '1,000,000 transactions • v2.1.0'
