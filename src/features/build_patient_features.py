from __future__ import annotations

import argparse
from pathlib import Path

from src.transform.common import DEFAULT_DB_PATH, connect, run_gold_transforms, run_silver_transforms


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build patient-year feature tables from Silver claims data.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--skip-silver", action="store_true", help="Reuse existing Silver tables.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    con = connect(args.db)
    if not args.skip_silver:
        run_silver_transforms(con)
    run_gold_transforms(con)
    rows = con.execute("SELECT COUNT(*) FROM gold_patient_year_summary").fetchone()[0]
    print(f"gold_patient_year_summary: {rows:,} rows")


if __name__ == "__main__":
    main()
