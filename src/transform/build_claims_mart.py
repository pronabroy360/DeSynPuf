from __future__ import annotations

import argparse
from pathlib import Path

try:
    from src.transform.common import DEFAULT_DB_PATH, connect, run_gold_transforms, run_silver_transforms
except ModuleNotFoundError:
    from common import DEFAULT_DB_PATH, connect, run_gold_transforms, run_silver_transforms


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Silver and Gold CMS DE-SynPUF claims marts.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--silver-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    con = connect(args.db)

    print("Building Silver tables...")
    run_silver_transforms(con)

    if not args.silver_only:
        print("Building Gold tables...")
        run_gold_transforms(con)

    tables = con.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND (table_name LIKE 'silver_%' OR table_name LIKE 'gold_%')
        ORDER BY table_name
        """
    ).fetchall()
    for (table_name,) in tables:
        rows = con.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
        print(f"{table_name}: {rows:,} rows")


if __name__ == "__main__":
    main()
