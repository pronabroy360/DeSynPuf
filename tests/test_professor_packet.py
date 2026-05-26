from __future__ import annotations

import json
from pathlib import Path

from src.reports import generate_professor_packet as packet_module


def test_generate_professor_packet_demo_context(tmp_path):
    quality_json = tmp_path / "quality.json"
    quality_md = tmp_path / "quality.md"
    model_metrics_json = tmp_path / "model_metrics.json"
    model_eval_json = tmp_path / "model_eval.json"
    model_comparison_json = tmp_path / "model_comparison.json"
    model_report_md = tmp_path / "model_report.md"
    model_comparison_md = tmp_path / "model_comparison.md"
    llm_examples_json = tmp_path / "llm_examples.json"
    llm_report_md = tmp_path / "llm_report.md"

    quality_json.write_text(json.dumps({"status": "pass", "checks": [{"status": "pass"}]}))
    quality_md.write_text("# quality\n")
    model_metrics_json.write_text(
        json.dumps(
            {
                "best_model": {"name": "logistic_regression"},
                "dataset": {"rows": 10, "train_rows": 6, "test_rows": 4},
                "logistic_regression": {"f1": 0.6, "precision_at_10_percent": 0.7},
            }
        )
    )
    model_eval_json.write_text(json.dumps({"best_model": "logistic_regression", "models": {}}))
    model_comparison_json.write_text(
        json.dumps([{"model": "logistic_regression", "f1_at_0_5": 0.6, "precision_at_10_percent": 0.7}])
    )
    model_report_md.write_text("# model\n")
    model_comparison_md.write_text("# model comparison\n")
    llm_examples_json.write_text(json.dumps([{"beneficiary_id": "B1", "year": 2009, "explanation": "synthetic"}]))
    llm_report_md.write_text("# llm\n")

    original_paths = dict(packet_module.REPORT_PATHS)
    packet_module.REPORT_PATHS = {
        **original_paths,
        "demo": {
            "quality_json": quality_json,
            "quality_md": quality_md,
            "model_metrics_json": model_metrics_json,
            "model_eval_json": model_eval_json,
            "model_comparison_json": model_comparison_json,
            "model_report_md": model_report_md,
            "model_comparison_md": model_comparison_md,
            "llm_examples_json": llm_examples_json,
            "llm_report_md": llm_report_md,
        },
    }
    try:
        out_path = tmp_path / "packet.md"
        packet_module.generate_professor_packet(output_path=out_path, context="demo")
        text = out_path.read_text()
        assert "Professor Packet (Demo)" in text
        assert "Overall quality status: **PASS**" in text
        assert "Best model by AUPRC selection rule: **logistic_regression**" in text
        assert "Explanation examples generated: **1**" in text
    finally:
        packet_module.REPORT_PATHS = original_paths
