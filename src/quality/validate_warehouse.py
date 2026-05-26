from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import duckdb


DEFAULT_DB_PATH = Path("data/processed/desynpuf.duckdb")
DEFAULT_REPORT_JSON = Path("data/processed/quality_report.json")
DEFAULT_REPORT_MD = Path("docs/latest_quality_report.md")

REQUIRED_TABLES = [
    "silver_beneficiaries",
    "silver_inpatient_claims",
    "silver_outpatient_claims",
    "silver_carrier_claims",
    "silver_prescription_events",
    "silver_diagnosis_codes",
    "silver_procedure_codes",
    "gold_patient_year_summary",
    "gold_patient_utilization_summary",
    "gold_patient_cost_summary",
    "gold_patient_chronic_condition_summary",
    "gold_high_cost_prediction_dataset",
]

REQUIRED_GOLD_COLUMNS = [
    "beneficiary_id",
    "year",
    "age",
    "chronic_condition_count",
    "inpatient_claims_count",
    "outpatient_claims_count",
    "carrier_claims_count",
    "prescription_events_count",
    "total_synthetic_cost",
    "unique_diagnosis_codes",
    "unique_procedure_codes",
]


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    observed: int | float | str | None
    expectation: str
    details: str = ""


def table_exists(con: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    result = con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND table_name = ?
        """,
        [table_name],
    ).fetchone()
    return bool(result and result[0])


def table_columns(con: duckdb.DuckDBPyConnection, table_name: str) -> set[str]:
    if not table_exists(con, table_name):
        return set()
    return {row[1] for row in con.execute(f'PRAGMA table_info("{table_name}")').fetchall()}


def scalar(con: duckdb.DuckDBPyConnection, sql: str) -> int | float | str | None:
    result = con.execute(sql).fetchone()
    return result[0] if result else None


def pass_fail(condition: bool) -> str:
    return "pass" if condition else "fail"


def validate_required_tables(con: duckdb.DuckDBPyConnection) -> list[CheckResult]:
    checks = []
    for table_name in REQUIRED_TABLES:
        exists = table_exists(con, table_name)
        row_count = scalar(con, f'SELECT COUNT(*) FROM "{table_name}"') if exists else None
        checks.append(
            CheckResult(
                name=f"table_exists:{table_name}",
                status=pass_fail(exists),
                observed=row_count,
                expectation="table exists and is queryable",
            )
        )
    return checks


def validate_gold_schema(con: duckdb.DuckDBPyConnection) -> list[CheckResult]:
    columns = table_columns(con, "gold_patient_year_summary")
    checks = []
    for column in REQUIRED_GOLD_COLUMNS:
        checks.append(
            CheckResult(
                name=f"gold_column:{column}",
                status=pass_fail(column in columns),
                observed="present" if column in columns else "missing",
                expectation="required Gold patient-year column is present",
            )
        )
    return checks


def validate_patient_year_integrity(con: duckdb.DuckDBPyConnection) -> list[CheckResult]:
    if not table_exists(con, "gold_patient_year_summary"):
        return [
            CheckResult(
                name="patient_year_integrity",
                status="fail",
                observed="missing table",
                expectation="gold_patient_year_summary exists",
            )
        ]

    duplicate_rows = scalar(
        con,
        """
        SELECT COUNT(*)
        FROM (
            SELECT beneficiary_id, year, COUNT(*) AS rows
            FROM gold_patient_year_summary
            GROUP BY beneficiary_id, year
            HAVING COUNT(*) > 1
        )
        """,
    )
    null_key_rows = scalar(
        con,
        """
        SELECT COUNT(*)
        FROM gold_patient_year_summary
        WHERE beneficiary_id IS NULL
           OR year IS NULL
        """,
    )
    out_of_range_years = scalar(
        con,
        """
        SELECT COUNT(*)
        FROM gold_patient_year_summary
        WHERE year NOT BETWEEN 2008 AND 2010
        """,
    )
    negative_cost_rows = scalar(
        con,
        """
        SELECT COUNT(*)
        FROM gold_patient_year_summary
        WHERE total_synthetic_cost < 0
           OR inpatient_total_paid < 0
           OR outpatient_total_paid < 0
           OR carrier_total_paid < 0
           OR prescription_total_cost < 0
        """,
    )
    negative_count_rows = scalar(
        con,
        """
        SELECT COUNT(*)
        FROM gold_patient_year_summary
        WHERE inpatient_claims_count < 0
           OR outpatient_claims_count < 0
           OR carrier_claims_count < 0
           OR prescription_events_count < 0
        """,
    )

    return [
        CheckResult(
            name="patient_year_unique_grain",
            status=pass_fail(int(duplicate_rows or 0) == 0),
            observed=duplicate_rows,
            expectation="0 duplicate beneficiary_id/year grains",
        ),
        CheckResult(
            name="patient_year_non_null_keys",
            status=pass_fail(int(null_key_rows or 0) == 0),
            observed=null_key_rows,
            expectation="0 rows with null beneficiary_id or year",
        ),
        CheckResult(
            name="patient_year_valid_years",
            status=pass_fail(int(out_of_range_years or 0) == 0),
            observed=out_of_range_years,
            expectation="0 rows outside 2008-2010",
        ),
        CheckResult(
            name="patient_year_nonnegative_costs",
            status=pass_fail(int(negative_cost_rows or 0) == 0),
            observed=negative_cost_rows,
            expectation="0 rows with negative cost values",
        ),
        CheckResult(
            name="patient_year_nonnegative_counts",
            status=pass_fail(int(negative_count_rows or 0) == 0),
            observed=negative_count_rows,
            expectation="0 rows with negative utilization counts",
        ),
    ]


def validate_model_dataset(con: duckdb.DuckDBPyConnection) -> list[CheckResult]:
    if not table_exists(con, "gold_high_cost_prediction_dataset"):
        return [
            CheckResult(
                name="model_dataset_exists",
                status="fail",
                observed="missing table",
                expectation="gold_high_cost_prediction_dataset exists",
            )
        ]

    rows = scalar(con, "SELECT COUNT(*) FROM gold_high_cost_prediction_dataset")
    null_labels = scalar(
        con,
        """
        SELECT COUNT(*)
        FROM gold_high_cost_prediction_dataset
        WHERE high_cost_next_year IS NULL
        """,
    )
    bad_year_pairs = scalar(
        con,
        """
        SELECT COUNT(*)
        FROM gold_high_cost_prediction_dataset
        WHERE target_year != input_year + 1
        """,
    )
    positive_labels = scalar(
        con,
        """
        SELECT COUNT(*)
        FROM gold_high_cost_prediction_dataset
        WHERE high_cost_next_year = 1
        """,
    )

    return [
        CheckResult(
            name="model_dataset_has_rows",
            status=pass_fail(int(rows or 0) > 0),
            observed=rows,
            expectation="at least 1 modeling row",
        ),
        CheckResult(
            name="model_dataset_non_null_labels",
            status=pass_fail(int(null_labels or 0) == 0),
            observed=null_labels,
            expectation="0 null high-cost labels",
        ),
        CheckResult(
            name="model_dataset_next_year_pairs",
            status=pass_fail(int(bad_year_pairs or 0) == 0),
            observed=bad_year_pairs,
            expectation="target_year equals input_year + 1",
        ),
        CheckResult(
            name="model_dataset_positive_labels",
            status=pass_fail(int(positive_labels or 0) > 0),
            observed=positive_labels,
            expectation="at least 1 high-cost positive label",
            details="Small demo datasets should still include at least one positive label.",
        ),
    ]


def summarize_tables(con: duckdb.DuckDBPyConnection) -> list[dict[str, int | str]]:
    rows = con.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND (
              table_name LIKE 'bronze_%'
              OR table_name LIKE 'silver_%'
              OR table_name LIKE 'gold_%'
          )
        ORDER BY table_name
        """
    ).fetchall()
    return [
        {
            "table_name": table_name,
            "row_count": int(scalar(con, f'SELECT COUNT(*) FROM "{table_name}"') or 0),
        }
        for (table_name,) in rows
    ]


def build_report(con: duckdb.DuckDBPyConnection) -> dict[str, object]:
    checks = [
        *validate_required_tables(con),
        *validate_gold_schema(con),
        *validate_patient_year_integrity(con),
        *validate_model_dataset(con),
    ]
    failed = [check for check in checks if check.status != "pass"]
    return {
        "status": "pass" if not failed else "fail",
        "table_summary": summarize_tables(con),
        "checks": [asdict(check) for check in checks],
    }


def write_markdown_report(report: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    checks = report["checks"]
    table_summary = report["table_summary"]
    lines = [
        "# Latest Warehouse Quality Report",
        "",
        f"Overall status: **{str(report['status']).upper()}**",
        "",
        "This report is generated from the local DuckDB warehouse. It contains aggregate validation results only.",
        "",
        "## Table Summary",
        "",
        "| Table | Rows |",
        "| --- | ---: |",
    ]
    for table in table_summary:
        lines.append(f"| `{table['table_name']}` | {int(table['row_count']):,} |")

    lines.extend(
        [
            "",
            "## Checks",
            "",
            "| Check | Status | Observed | Expectation |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for check in checks:
        lines.append(
            f"| `{check['name']}` | {str(check['status']).upper()} | "
            f"{check['observed']} | {check['expectation']} |"
        )

    output_path.write_text("\n".join(lines) + "\n")


def validate_warehouse(
    db_path: Path = DEFAULT_DB_PATH,
    report_json: Path = DEFAULT_REPORT_JSON,
    report_md: Path = DEFAULT_REPORT_MD,
    fail_on_error: bool = True,
    con: duckdb.DuckDBPyConnection | None = None,
) -> dict[str, object]:
    if con is None and not db_path.exists():
        raise FileNotFoundError(f"DuckDB database not found: {db_path}")

    active_con = con or duckdb.connect(str(db_path), read_only=True)
    report = build_report(active_con)

    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True))
    write_markdown_report(report, report_md)

    print(f"Quality status: {str(report['status']).upper()}")
    print(f"JSON report: {report_json}")
    print(f"Markdown report: {report_md}")

    if fail_on_error and report["status"] != "pass":
        raise SystemExit(1)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the CMS DE-SynPUF DuckDB warehouse.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--no-fail", action="store_true", help="Write reports without returning a failing exit code.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    validate_warehouse(
        db_path=args.db,
        report_json=args.report_json,
        report_md=args.report_md,
        fail_on_error=not args.no_fail,
    )


if __name__ == "__main__":
    main()
