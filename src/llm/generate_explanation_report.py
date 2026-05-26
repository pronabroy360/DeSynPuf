from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import duckdb

from src.llm.patient_risk_explainer import explain_patient_year


DEFAULT_DB_PATH = Path("data/processed/desynpuf.duckdb")
DEFAULT_JSON_PATH = Path("data/processed/llm_explanation_examples.json")
DEFAULT_REPORT_PATH = Path("docs/latest_llm_explanation_report.md")


SAFE_FEATURE_COLUMNS = [
    "beneficiary_id",
    "year",
    "age",
    "sex_code",
    "race_code",
    "state_code",
    "chronic_condition_count",
    "inpatient_claims_count",
    "outpatient_claims_count",
    "carrier_claims_count",
    "prescription_events_count",
    "inpatient_total_paid",
    "outpatient_total_paid",
    "carrier_total_paid",
    "prescription_total_cost",
    "total_synthetic_cost",
    "unique_diagnosis_codes",
    "unique_procedure_codes",
    "any_inpatient",
    "repeated_inpatient",
    "alzheimers",
    "heart_failure",
    "kidney_disease",
    "cancer",
    "copd",
    "depression",
    "diabetes",
    "ischemic_heart",
    "osteoporosis",
    "rheumatoid_arthritis",
    "stroke_tia",
]


def _jsonable(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def load_example_features(db_path: Path, limit: int) -> list[dict[str, Any]]:
    if not db_path.exists():
        raise FileNotFoundError(f"DuckDB database not found: {db_path}")

    columns = ", ".join(f'"{column}"' for column in SAFE_FEATURE_COLUMNS)
    con = duckdb.connect(str(db_path), read_only=True)
    rows = con.execute(
        f"""
        WITH ranked AS (
            SELECT
                {columns},
                CUME_DIST() OVER (
                    PARTITION BY year
                    ORDER BY total_synthetic_cost
                ) AS risk_percentile_raw
            FROM gold_patient_year_summary
        )
        SELECT
            *,
            CAST(ROUND(risk_percentile_raw * 100, 0) AS INTEGER) AS risk_percentile
        FROM ranked
        ORDER BY total_synthetic_cost DESC, beneficiary_id, year
        LIMIT ?
        """,
        [limit],
    ).fetchall()
    names = [description[0] for description in con.description]
    return [
        {name: _jsonable(value) for name, value in zip(names, row)}
        for row in rows
    ]


def build_explanation_examples(db_path: Path, limit: int) -> list[dict[str, Any]]:
    examples = []
    for features in load_example_features(db_path, limit):
        examples.append(
            {
                "beneficiary_id": features.get("beneficiary_id"),
                "year": features.get("year"),
                "features": features,
                "explanation": explain_patient_year(features),
            }
        )
    return examples


def write_markdown_report(examples: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# LLM Claims Explanation Examples",
        "",
        "These examples are generated from synthetic CMS DE-SynPUF-style beneficiary-year features.",
        "They are safe, non-diagnostic explanations for portfolio demonstration only.",
        "",
        "Guardrails:",
        "",
        "- Use only structured synthetic or aggregate fields.",
        "- Do not infer real patient facts.",
        "- Do not diagnose or recommend treatment.",
        "- State that the explanation is not clinical advice.",
        "",
    ]

    for idx, example in enumerate(examples, start=1):
        features = example["features"]
        lines.extend(
            [
                f"## Example {idx}: `{example['beneficiary_id']}` in {example['year']}",
                "",
                "| Field | Value |",
                "| --- | ---: |",
                f"| `age` | {features.get('age')} |",
                f"| `chronic_condition_count` | {features.get('chronic_condition_count')} |",
                f"| `inpatient_claims_count` | {features.get('inpatient_claims_count')} |",
                f"| `outpatient_claims_count` | {features.get('outpatient_claims_count')} |",
                f"| `carrier_claims_count` | {features.get('carrier_claims_count')} |",
                f"| `prescription_events_count` | {features.get('prescription_events_count')} |",
                f"| `total_synthetic_cost` | ${float(features.get('total_synthetic_cost') or 0):,.0f} |",
                f"| `risk_percentile` | {features.get('risk_percentile')} |",
                "",
                "**Explanation**",
                "",
                str(example["explanation"]),
                "",
            ]
        )
    output_path.write_text("\n".join(lines))


def generate_explanation_report(
    db_path: Path = DEFAULT_DB_PATH,
    json_out: Path = DEFAULT_JSON_PATH,
    report_md: Path = DEFAULT_REPORT_PATH,
    limit: int = 5,
) -> list[dict[str, Any]]:
    examples = build_explanation_examples(db_path, limit)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(examples, indent=2, sort_keys=True))
    write_markdown_report(examples, report_md)
    print(f"Generated {len(examples)} explanation examples")
    print(f"JSON examples: {json_out}")
    print(f"Markdown report: {report_md}")
    return examples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate safe synthetic claims explanation examples.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--limit", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_explanation_report(
        db_path=args.db,
        json_out=args.json_out,
        report_md=args.report_md,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
