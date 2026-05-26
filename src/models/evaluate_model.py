from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_METRICS_PATH = Path("data/processed/model_metrics.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print saved high-cost model metrics.")
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.metrics.exists():
        raise SystemExit(f"No metrics found at {args.metrics}. Run train_high_cost_model.py first.")
    metrics = json.loads(args.metrics.read_text())
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
