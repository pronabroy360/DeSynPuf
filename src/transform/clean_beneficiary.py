from __future__ import annotations

import argparse
from pathlib import Path

try:
    from src.transform.common import DEFAULT_DB_PATH, connect, create_silver_beneficiaries
except ModuleNotFoundError:
    from common import DEFAULT_DB_PATH, connect, create_silver_beneficiaries


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create silver_beneficiaries from Bronze beneficiary tables.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    con = connect(args.db)
    create_silver_beneficiaries(con)
    rows = con.execute("SELECT COUNT(*) FROM silver_beneficiaries").fetchone()[0]
    print(f"silver_beneficiaries: {rows:,} rows")


if __name__ == "__main__":
    main()
