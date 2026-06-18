"""Tests for Phase 5 report generation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.generate_report import generate_report
from src.metrics.summaries import build_summary_tables

ROOT = Path(__file__).resolve().parents[1]


class ReportGenerationTests(unittest.TestCase):
    def test_report_generation_creates_required_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            result = generate_report(
                source_results_root=ROOT / "results",
                output_root=tmp / "results",
                docs_dir=tmp / "docs",
                repo_root=ROOT,
            )
            self.assertTrue(result["report_path"].exists())
            self.assertTrue(result["manifest_path"].exists())
            self.assertTrue(result["chart_map_path"].exists())
            self.assertIn("Technical Summary", result["report_path"].read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(result["figures"]), 5)
            for path in result["table_paths"].values():
                self.assertTrue(path.exists())
            for figure in result["figures"]:
                self.assertTrue(Path(figure["path"]).exists())

    def test_summary_tables_have_sources_and_complete_traces(self) -> None:
        tables = build_summary_tables(ROOT / "results", ROOT)
        for table_name, rows in tables.items():
            self.assertGreater(len(rows), 0, table_name)
            if table_name == "metric_definitions":
                continue
            for row in rows:
                has_source = any(key.startswith("source_") and str(value) for key, value in row.items())
                if table_name == "reproducibility":
                    has_source = bool(row.get("metric_path")) and bool(row.get("trace_path"))
                self.assertTrue(has_source, f"{table_name} row lacks source reference")
        for row in tables["trace_completeness"]:
            self.assertEqual(row["trace_completeness_rate"], 1.0)
            self.assertEqual(row["incomplete_count"], 0)

    def test_report_manifest_records_generated_file_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            result = generate_report(
                source_results_root=ROOT / "results",
                output_root=tmp / "results",
                docs_dir=tmp / "docs",
                repo_root=ROOT,
            )
            manifest = json.loads(result["manifest_path"].read_text(encoding="utf-8"))
            self.assertEqual(manifest["manifest_version"], "phase5.v1")
            self.assertEqual(manifest["claim_boundary"], "Results are controlled synthetic evidence only.")
            self.assertGreater(len(manifest["generated_files"]), 5)
            for record in manifest["generated_files"]:
                self.assertRegex(record["sha256"], r"^[0-9a-f]{64}$")
                self.assertGreater(record["bytes"], 0)

    def test_report_generation_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = Path(first_dir)
            second = Path(second_dir)
            first_result = generate_report(
                source_results_root=ROOT / "results",
                output_root=first / "results",
                docs_dir=first / "docs",
                repo_root=ROOT,
            )
            second_result = generate_report(
                source_results_root=ROOT / "results",
                output_root=second / "results",
                docs_dir=second / "docs",
                repo_root=ROOT,
            )
            self.assertEqual(
                first_result["report_path"].read_text(encoding="utf-8"),
                second_result["report_path"].read_text(encoding="utf-8"),
            )
            self.assertEqual(
                first_result["manifest_path"].read_text(encoding="utf-8"),
                second_result["manifest_path"].read_text(encoding="utf-8"),
            )
            first_tables = (first / "results" / "tables" / "summary_tables.json").read_text(encoding="utf-8")
            second_tables = (second / "results" / "tables" / "summary_tables.json").read_text(encoding="utf-8")
            self.assertEqual(first_tables, second_tables)

    def test_report_avoids_unsupported_superiority_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            result = generate_report(
                source_results_root=ROOT / "results",
                output_root=tmp / "results",
                docs_dir=tmp / "docs",
                repo_root=ROOT,
            )
            text = result["report_path"].read_text(encoding="utf-8").lower()
            self.assertNotIn("proves superiority", text)
            self.assertNotIn("real-world superiority", text)
            self.assertIn("controlled synthetic", text)


if __name__ == "__main__":
    unittest.main()
