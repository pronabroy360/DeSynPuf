PYTHON ?= python3
RAW_DIR ?= data/raw
DB ?= data/processed/desynpuf.duckdb

.PHONY: install ingest transform features train dashboard api test clean

install:
	$(PYTHON) -m pip install -r requirements.txt

ingest:
	$(PYTHON) -m src.ingest.load_raw_files --raw-dir $(RAW_DIR) --db $(DB)

transform:
	$(PYTHON) -m src.transform.build_claims_mart --db $(DB)

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
	rm -f $(DB) $(DB).wal
