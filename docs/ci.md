# Continuous Integration

GitHub Actions runs the reproducible demo pipeline on every push and pull request to `main`.

Workflow file:

```text
.github/workflows/ci.yml
```

## What CI Checks

- Installs lightweight core dependencies from `requirements-ci.txt`.
- Compiles Python modules.
- Runs the tiny demo warehouse pipeline with `make demo-smoke`.
- Trains demo high-cost models with `make demo-train`.
- Generates demo LLM explanation examples with `make demo-explain`.
- Runs the pytest suite.

## Why CI Uses `requirements-ci.txt`

The full `requirements.txt` includes optional portfolio extensions such as SHAP, XGBoost, Streamlit, and FastAPI. CI focuses on the reproducible core pipeline to keep checks fast and stable.

## Local Equivalent

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-ci.txt
make demo-all
pytest -q
```
