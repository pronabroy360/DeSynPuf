from __future__ import annotations

import argparse
from pathlib import Path

try:
    from src.transform.common import DEFAULT_DB_PATH, connect, create_silver_prescription_events
except ModuleNotFoundError:
    from common import DEFAULT_DB_PATH, connect, create_silver_prescription_events


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create silver_prescription_events from Bronze PDE data.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    con = connect(args.db)
    create_silver_prescription_events(con)
    rows = con.execute("SELECT COUNT(*) FROM silver_prescription_events").fetchone()[0]
    print(f"silver_prescription_events: {rows:,} rows")


if __name__ == "__main__":
    main()
