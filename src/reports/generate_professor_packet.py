from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_PATH = Path("docs/latest_professor_packet.md")
DEFAULT_CONTEXT = "real"

REPORT_PATHS = {
    "real": {
        "quality_json": Path("data/processed/quality_report.json"),
        "quality_md": Path("docs/latest_quality_report.md"),
        "model_metrics_json": Path("data/processed/model_metrics.json"),
        "model_eval_json": Path("data/processed/model_evaluation.json"),
        "model_comparison_json": Path("data/processed/model_comparison.json"),
        "model_report_md": Path("docs/latest_model_report.md"),
        "model_comparison_md": Path("docs/latest_model_comparison_report.md"),
        "llm_examples_json": Path("data/processed/llm_explanation_examples.json"),
        "llm_report_md": Path("docs/latest_llm_explanation_report.md"),
    },
    "demo": {
        "quality_json": Path("data/processed/demo_quality_report.json"),
        "quality_md": Path("docs/demo_quality_report.md"),
        "model_metrics_json": Path("data/processed/demo_model_metrics.json"),
        "model_eval_json": Path("data/processed/demo_model_evaluation.json"),
        "model_comparison_json": Path("data/processed/demo_model_comparison.json"),
        "model_report_md": Path("docs/demo_model_report.md"),
        "model_comparison_md": Path("docs/demo_model_comparison_report.md"),
        "llm_examples_json": Path("data/processed/demo_llm_explanation_examples.json"),
        "llm_report_md": Path("docs/demo_llm_explanation_report.md"),
    },
}


def load_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def link_line(path: Path) -> str:
    if path.exists():
        return f"- Available: `{path}`"
    return f"- Missing: `{path}`"


def summarize_quality(quality_json: dict[str, Any] | None) -> list[str]:
    if not quality_json:
        return ["- Quality report JSON not found."]
    checks = quality_json.get("checks", [])
    failed_checks = 0
    if isinstance(checks, list):
        failed_checks = sum(
            1
            for row in checks
            if isinstance(row, dict) and str(row.get("status", "")).lower() != "pass"
        )
    status = str(quality_json.get("status", "unknown")).upper()
    return [
        f"- Overall quality status: **{status}**",
        f"- Failed checks: **{failed_checks}**",
    ]


def summarize_model(
    metrics_json: dict[str, Any] | None,
    comparison_json: list[dict[str, Any]] | None,
) -> list[str]:
    lines: list[str] = []
    if not metrics_json:
        return ["- Model metrics JSON not found."]
    dataset = metrics_json.get("dataset", {})
    best_model = (metrics_json.get("best_model") or {}).get("name", "unknown")
    if isinstance(dataset, dict):
        lines.append(f"- Modeling rows: **{dataset.get('rows', 'N/A')}**")
        lines.append(f"- Train rows: **{dataset.get('train_rows', 'N/A')}**")
        lines.append(f"- Test rows: **{dataset.get('test_rows', 'N/A')}**")
    lines.append(f"- Best model by AUPRC selection rule: **{best_model}**")
    if comparison_json and isinstance(comparison_json, list):
        top_rows = sorted(
            comparison_json,
            key=lambda row: float(row.get("precision_at_10_percent") or 0.0),
            reverse=True,
        )[:2]
        for row in top_rows:
            lines.append(
                "- "
                + f"{row.get('model')}: "
                + f"F1@0.50={row.get('f1_at_0_5')}, "
                + f"Precision@10%={row.get('precision_at_10_percent')}, "
                + f"Brier={row.get('brier_score')}"
            )
    return lines


def summarize_llm(llm_examples_json: list[dict[str, Any]] | None) -> list[str]:
    if not llm_examples_json or not isinstance(llm_examples_json, list):
        return ["- LLM explanation examples JSON not found."]
    return [
        f"- Explanation examples generated: **{len(llm_examples_json)}**",
        "- Explanations are explicitly non-diagnostic and synthetic-data-only.",
    ]


def generate_professor_packet(output_path: Path, context: str) -> Path:
    if context not in REPORT_PATHS:
        raise ValueError(f"Unsupported context: {context}")
    paths = REPORT_PATHS[context]

    quality_json = load_json(paths["quality_json"])
    metrics_json = load_json(paths["model_metrics_json"])
    model_eval_json = load_json(paths["model_eval_json"])
    comparison_json = load_json(paths["model_comparison_json"])
    llm_examples_json = load_json(paths["llm_examples_json"])

    title_suffix = "Demo" if context == "demo" else "Sample 1"
    lines = [
        f"# Professor Packet ({title_suffix})",
        "",
        "This packet summarizes the latest reproducible pipeline outputs for outreach and review.",
        "All metrics and explanations are based on synthetic CMS DE-SynPUF-style data workflows.",
        "",
        "## Snapshot",
        "",
        *summarize_quality(quality_json if isinstance(quality_json, dict) else None),
        *summarize_model(
            metrics_json if isinstance(metrics_json, dict) else None,
            comparison_json if isinstance(comparison_json, list) else None,
        ),
        *summarize_llm(llm_examples_json if isinstance(llm_examples_json, list) else None),
        "",
        "## Linked Reports",
        "",
        "### Quality",
        link_line(paths["quality_json"]),
        link_line(paths["quality_md"]),
        "",
        "### Modeling",
        link_line(paths["model_metrics_json"]),
        link_line(paths["model_eval_json"]),
        link_line(paths["model_comparison_json"]),
        link_line(paths["model_report_md"]),
        link_line(paths["model_comparison_md"]),
        "",
        "### LLM Explainer",
        link_line(paths["llm_examples_json"]),
        link_line(paths["llm_report_md"]),
        "",
        "## Responsible Use",
        "",
        "- This project demonstrates claims data engineering and analytics pipeline design.",
        "- DE-SynPUF is synthetic; outputs should not be interpreted as clinical evidence.",
        "- LLM explanations are non-diagnostic and are not medical advice.",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n")
    print(f"Generated professor packet: {output_path}")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a professor-facing packet from latest reports.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--context", choices=sorted(REPORT_PATHS.keys()), default=DEFAULT_CONTEXT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_professor_packet(output_path=args.output, context=args.context)


if __name__ == "__main__":
    main()
