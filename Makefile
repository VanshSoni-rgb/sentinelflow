.PHONY: setup db-init generate-full etl-load sql-all ml-train api ui test lint clean

setup:
	python -m pip install -e ".[dev]"
	pre-commit install || true

db-init:
	psql postgresql://sentinel:sentinel_dev@localhost:5432/sentinelflow -f sql/schema/00_init.sql
	psql postgresql://sentinel:sentinel_dev@localhost:5432/sentinelflow -f sql/schema/01_schema.sql
	psql postgresql://sentinel:sentinel_dev@localhost:5432/sentinelflow -f sql/schema/02_indexes.sql

generate-full:
	python -m sentinelflow.generator.transactions --rows 1000000 --seed 42 --output data/transactions_1m.parquet
	python -m sentinelflow.generator.transactions --rows 1000 --seed 42 --output data/samples/transactions_sample_1k.csv --csv

generate-smoke:
	python -m sentinelflow.generator.transactions --rows 50000 --seed 42 --output data/transactions_smoke.parquet

etl-load:
	python -m sentinelflow.etl.load --input data/transactions_1m.parquet

sql-all:
	@for f in sql/analyses/*/*.sql; do echo "→ $$f"; psql postgresql://sentinel:sentinel_dev@localhost:5432/sentinelflow -f $$f -q -o exports/$$(basename $$f .sql).csv --csv; done

ml-train:
	python -m sentinelflow.ml.train_fraud --input postgres --output models/fraud_xgb_v21.json

api:
	uvicorn sentinelflow.api.main:app --reload --port 8000

ui:
	streamlit run dashboard/streamlit_app.py

test:
	pytest -q --cov=sentinelflow

lint:
	ruff check src
	mypy src/sentinelflow

powerbi-export:
	python -m sentinelflow.etl.transform --powerbi --output powerbi/

clean:
	rm -rf data/transactions_1m.* exports/* models/*.json
