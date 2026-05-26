from __future__ import annotations

import argparse
from pathlib import Path

try:
    from src.transform.common import DEFAULT_DB_PATH, connect, create_silver_outpatient_claims
except ModuleNotFoundError:
    from common import DEFAULT_DB_PATH, connect, create_silver_outpatient_claims


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create silver_outpatient_claims from Bronze outpatient data.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    con = connect(args.db)
    create_silver_outpatient_claims(con)
    rows = con.execute("SELECT COUNT(*) FROM silver_outpatient_claims").fetchone()[0]
    print(f"silver_outpatient_claims: {rows:,} rows")


if __name__ == "__main__":
    main()
