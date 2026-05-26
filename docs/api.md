# FastAPI Service

This project includes a local FastAPI service on top of the DuckDB warehouse for lightweight portfolio demos and integration testing.

Run:

```bash
make api
```

Or:

```bash
uvicorn src.api.main:app --reload
```

## Core Endpoints

- `GET /health`: service status and active DuckDB path.
- `GET /overview/metrics`: aggregate beneficiary-year and cost overview.
- `GET /analytics/cost-summary`: yearly cost summary table.
- `GET /analytics/utilization-summary`: yearly utilization summary table.
- `GET /analytics/chronic-conditions`: chronic-condition summary (optional `?year=2009`).
- `GET /patient-year/{beneficiary_id}/{year}`: one synthetic beneficiary-year feature row.
- `GET /patient-year/{beneficiary_id}/{year}/explain`: non-diagnostic plain-language explanation.
- `GET /model/metrics`: latest model metrics artifact JSON.
- `GET /model/comparison`: latest model-comparison artifact JSON.
- `GET /quality/report`: latest warehouse quality report JSON.

## Example Requests

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/overview/metrics
curl -s http://127.0.0.1:8000/analytics/cost-summary
curl -s http://127.0.0.1:8000/patient-year/B1/2008
```

## Notes

- The API serves synthetic DE-SynPUF-derived outputs only.
- Responses should be treated as engineering artifacts, not clinical evidence.
