from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from src.demo.create_demo_raw_files import create_demo_raw_files
from src.ingest.load_raw_files import load_raw_files
from src.transform.common import run_gold_transforms, run_silver_transforms


DEFAULT_RAW_DIR = Path("data/raw/demo_sample")
DEFAULT_DB_PATH = Path("data/processed/demo_desynpuf.duckdb")


def smoke_test_pipeline(raw_dir: Path = DEFAULT_RAW_DIR, db_path: Path = DEFAULT_DB_PATH) -> None:
    create_demo_raw_files(raw_dir)
    load_raw_files(raw_dir=raw_dir, db_path=db_path, replace_existing=True)

    con = duckdb.connect(str(db_path))
    run_silver_transforms(con)
    run_gold_transforms(con)

    checks = {
        "silver_beneficiaries": 9,
        "silver_inpatient_claims": 2,
        "silver_outpatient_claims": 2,
        "silver_carrier_claims": 3,
        "silver_prescription_events": 3,
        "gold_patient_year_summary": 9,
        "gold_high_cost_prediction_dataset": 6,
    }
    for table_name, minimum_rows in checks.items():
        row_count = con.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
        if row_count < minimum_rows:
            raise AssertionError(f"{table_name} expected at least {minimum_rows} rows, found {row_count}")
        print(f"{table_name}: {row_count:,} rows")

    high_cost_rows = con.execute(
        """
        SELECT COUNT(*)
        FROM gold_high_cost_prediction_dataset
        WHERE high_cost_next_year = 1
        """
    ).fetchone()[0]
    if high_cost_rows == 0:
        raise AssertionError("Expected at least one high-cost target label in demo data")

    print(f"Smoke test complete: {db_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny end-to-end pipeline smoke test.")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    smoke_test_pipeline(raw_dir=args.raw_dir, db_path=args.db)


if __name__ == "__main__":
    main()
