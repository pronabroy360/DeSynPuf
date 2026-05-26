PYTHON ?= python3
RAW_DIR ?= data/raw
DB ?= data/processed/desynpuf.duckdb

.PHONY: install demo-data demo-smoke demo-train ingest transform validate features train dashboard api test clean

install:
	$(PYTHON) -m pip install -r requirements.txt

demo-data:
	$(PYTHON) -m src.demo.create_demo_raw_files --output-dir data/raw/demo_sample

demo-smoke:
	$(PYTHON) -m src.demo.smoke_test_pipeline --raw-dir data/raw/demo_sample --db data/processed/demo_desynpuf.duckdb

demo-train:
	$(PYTHON) -m src.models.train_high_cost_model \
		--db data/processed/demo_desynpuf.duckdb \
		--model-out data/processed/demo_high_cost_model.joblib \
		--metrics-out data/processed/demo_model_metrics.json \
		--feature-importance-out data/processed/demo_model_feature_importance.json \
		--report-md docs/demo_model_report.md

ingest:
	$(PYTHON) -m src.ingest.load_raw_files --raw-dir $(RAW_DIR) --db $(DB)

transform:
	$(PYTHON) -m src.transform.build_claims_mart --db $(DB)

validate:
	$(PYTHON) -m src.quality.validate_warehouse --db $(DB)

features: transform

train:
	$(PYTHON) -m src.models.train_high_cost_model --db $(DB)

dashboard:
	streamlit run dashboard/streamlit_app.py

api:
	uvicorn src.api.main:app --reload

test:
	pytest -q

clean:
	rm -f $(DB) $(DB).wal data/processed/demo_desynpuf.duckdb data/processed/demo_desynpuf.duckdb.wal
