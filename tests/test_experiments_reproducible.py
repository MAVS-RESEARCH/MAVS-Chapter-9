import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from experiments.test_disagreement.run import EXPERIMENT_NAME as DISAGREEMENT_NAME
from experiments.test_disagreement.run import run_experiment as run_disagreement
from experiments.test_false_positive_trap.run import EXPERIMENT_NAME as FALSE_POSITIVE_NAME
from experiments.test_false_positive_trap.run import run_experiment as run_false_positive
from experiments.test_mitigation_veto.run import EXPERIMENT_NAME as MITIGATION_VETO_NAME
from experiments.test_mitigation_veto.run import run_experiment as run_mitigation_veto


class ExperimentReproducibilityTests(unittest.TestCase):
    def _run_quietly(self, runner, output_root: Path):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            payload = runner(output_root=output_root)
        self.assertGreater(len(buffer.getvalue().splitlines()), 0)
        return payload

    def _assert_output_files(self, output_root: Path, experiment_name: str, expected_records: int):
        trace_path = output_root / "traces" / f"{experiment_name}.jsonl"
        metrics_path = output_root / "metrics" / f"{experiment_name}.json"
        self.assertTrue(trace_path.exists())
        self.assertTrue(metrics_path.exists())
        trace_lines = trace_path.read_text(encoding="utf-8").splitlines()
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        self.assertEqual(len(trace_lines), expected_records)
        self.assertEqual(metrics["record_count"], expected_records)
        return trace_lines, metrics

    def test_disagreement_experiment_is_reproducible(self):
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first_root = Path(first_dir)
            second_root = Path(second_dir)
            first = self._run_quietly(run_disagreement, first_root)
            second = self._run_quietly(run_disagreement, second_root)
            self.assertEqual(first["records"], second["records"])
            self.assertEqual(first["metrics"], second["metrics"])
            first_lines, first_metrics = self._assert_output_files(first_root, DISAGREEMENT_NAME, 360)
            second_lines, second_metrics = self._assert_output_files(second_root, DISAGREEMENT_NAME, 360)
            self.assertEqual(first_lines, second_lines)
            self.assertEqual(first_metrics, second_metrics)
            self.assertIn("acceptance_by_disagreement_regime", first_metrics)

    def test_false_positive_experiment_is_reproducible(self):
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first_root = Path(first_dir)
            second_root = Path(second_dir)
            first = self._run_quietly(run_false_positive, first_root)
            second = self._run_quietly(run_false_positive, second_root)
            self.assertEqual(first["records"], second["records"])
            self.assertEqual(first["metrics"], second["metrics"])
            first_lines, first_metrics = self._assert_output_files(first_root, FALSE_POSITIVE_NAME, 480)
            second_lines, second_metrics = self._assert_output_files(second_root, FALSE_POSITIVE_NAME, 480)
            self.assertEqual(first_lines, second_lines)
            self.assertEqual(first_metrics, second_metrics)
            self.assertIn("acceptance_by_trap_type", first_metrics)
            self.assertIn("pure_mavs_gc_mean_threshold_escalation", first_metrics)

    def test_mitigation_veto_experiment_is_reproducible(self):
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first_root = Path(first_dir)
            second_root = Path(second_dir)
            first = self._run_quietly(run_mitigation_veto, first_root)
            second = self._run_quietly(run_mitigation_veto, second_root)
            self.assertEqual(first["records"], second["records"])
            self.assertEqual(first["metrics"], second["metrics"])
            first_lines, first_metrics = self._assert_output_files(first_root, MITIGATION_VETO_NAME, 400)
            second_lines, second_metrics = self._assert_output_files(second_root, MITIGATION_VETO_NAME, 400)
            self.assertEqual(first_lines, second_lines)
            self.assertEqual(first_metrics, second_metrics)
            self.assertIn("acceptance_by_mitigation_level", first_metrics)
            self.assertIn("acceptance_by_corruption_level", first_metrics)
            compliance = first_metrics["pure_mavs_gc_hard_veto_compliance"]
            self.assertEqual(compliance["hard_veto_count"], compliance["hard_veto_rejection_count"])

    def test_metrics_include_required_phase4_sections(self):
        with tempfile.TemporaryDirectory() as output_dir:
            payload = self._run_quietly(run_disagreement, Path(output_dir))
            metrics = payload["metrics"]
            self.assertIn("classification_by_system", metrics)
            self.assertIn("governance_by_system", metrics)
            self.assertIn("stability_by_system", metrics)
            for system_metrics in metrics["classification_by_system"].values():
                self.assertIn("accuracy", system_metrics)
                self.assertIn("false_positive_rate", system_metrics)
                self.assertIn("false_negative_rate", system_metrics)
                self.assertIn("rejection_rate", system_metrics)
                self.assertIn("unsafe_acceptance_rate", system_metrics)


if __name__ == "__main__":
    unittest.main()

