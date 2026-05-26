PYTHON ?= python3
RAW_DIR ?= data/raw
DB ?= data/processed/desynpuf.duckdb

.PHONY: install demo-data demo-smoke demo-train demo-explain demo-all ingest transform validate features train explain dashboard api test clean

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
		--evaluation-out data/processed/demo_model_evaluation.json \
		--comparison-out data/processed/demo_model_comparison.json \
		--report-md docs/demo_model_report.md \
		--comparison-report-md docs/demo_model_comparison_report.md

demo-explain:
	$(PYTHON) -m src.llm.generate_explanation_report \
		--db data/processed/demo_desynpuf.duckdb \
		--json-out data/processed/demo_llm_explanation_examples.json \
		--report-md docs/demo_llm_explanation_report.md \
		--limit 5

demo-all: demo-smoke demo-train demo-explain

ingest:
	$(PYTHON) -m src.ingest.load_raw_files --raw-dir $(RAW_DIR) --db $(DB)

transform:
	$(PYTHON) -m src.transform.build_claims_mart --db $(DB)

validate:
	$(PYTHON) -m src.quality.validate_warehouse --db $(DB)

features: transform

train:
	$(PYTHON) -m src.models.train_high_cost_model --db $(DB)

explain:
	$(PYTHON) -m src.llm.generate_explanation_report --db $(DB)

dashboard:
	streamlit run dashboard/streamlit_app.py

api:
	uvicorn src.api.main:app --reload

test:
	pytest -q

clean:
	rm -f $(DB) $(DB).wal data/processed/demo_desynpuf.duckdb data/processed/demo_desynpuf.duckdb.wal data/processed/demo_model_evaluation.json data/processed/model_evaluation.json data/processed/demo_model_comparison.json data/processed/model_comparison.json
