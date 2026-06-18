import contextlib
import io
import unittest
from pathlib import Path

from src.baselines.mean import MEAN_DECISION_CUTOFF, run_mean_ensemble
from src.baselines.runner import (
    ALL_COMPARISON_SYSTEMS,
    BASELINE_SYSTEMS,
    run_all_systems,
    run_baselines,
    validate_baseline_result,
)
from src.baselines.static_weighted import DEFAULT_STATIC_WEIGHTS, run_static_weighted_ensemble
from src.baselines.veto_mavs import VETO_FLAG_THRESHOLD, run_veto_mavs
from src.core.case_generator import SyntheticCaseGenerator
from src.core.config import BenchmarkConfig
from src.core.types import SpecialistOutput, SyntheticCase
from src.specialists.base import evaluate_all
from src.specialists.synthetic import build_default_specialists


class BaselinePhase3Tests(unittest.TestCase):
    def setUp(self):
        self.config = BenchmarkConfig.default()
        self.generator = SyntheticCaseGenerator(self.config)
        self.specialists = build_default_specialists(self.config)

    def test_mean_ensemble_decision_rule(self):
        case = self.generator.generate_case(0, "low")
        outputs = [
            SpecialistOutput.from_score("a", 0.6),
            SpecialistOutput.from_score("b", 0.8),
            SpecialistOutput.from_score("c", 0.4),
        ]
        result = run_mean_ensemble(self.config, case, outputs)
        self.assertAlmostEqual(result["score"], 0.6)
        self.assertEqual(result["cutoff"], MEAN_DECISION_CUTOFF)
        self.assertTrue(result["decision"])
        validate_baseline_result(result)

    def test_static_weighted_ensemble_decision_rule(self):
        case = self.generator.generate_case(1, "medium")
        outputs = [
            SpecialistOutput.from_score("accurate", 0.9),
            SpecialistOutput.from_score("noisy", 0.1),
            SpecialistOutput.from_score("overconfident", 0.5),
            SpecialistOutput.from_score("fragile", 0.5),
            SpecialistOutput.from_score("adversarial", 0.0),
        ]
        result = run_static_weighted_ensemble(self.config, case, outputs)
        expected = sum(
            DEFAULT_STATIC_WEIGHTS[output.specialist_name] * output.score for output in outputs
        ) / sum(DEFAULT_STATIC_WEIGHTS[output.specialist_name] for output in outputs)
        self.assertAlmostEqual(result["score"], expected)
        self.assertEqual(result["weights"], DEFAULT_STATIC_WEIGHTS)
        validate_baseline_result(result)

    def test_veto_mavs_rejects_high_red_flag_even_when_mean_accepts(self):
        case = SyntheticCase(
            case_id="veto-test",
            truth=1,
            corruption=1.0,
            disagreement_regime="high",
            mitigation_level=1.0,
            edge_condition="fragility",
            features={
                "signal_strength": 0.9,
                "corruption": 1.0,
                "mitigation_hint": 1.0,
                "disagreement_code": 2.0,
            },
        )
        outputs = [
            SpecialistOutput.from_score("accurate", 0.95),
            SpecialistOutput.from_score("noisy", 0.9),
            SpecialistOutput.from_score("overconfident", 0.99),
            SpecialistOutput.from_score("fragile", 0.88),
            SpecialistOutput.from_score("adversarial", 0.9),
        ]
        result = run_veto_mavs(self.config, case, outputs)
        self.assertGreaterEqual(result["score"], 0.5)
        self.assertGreaterEqual(max(result["diagnostics"].values()), VETO_FLAG_THRESHOLD)
        self.assertTrue(result["veto_active"])
        self.assertFalse(result["decision"])
        validate_baseline_result(result)

    def test_run_baselines_returns_all_baseline_systems(self):
        case = self.generator.generate_case(2, "high")
        results = run_baselines(self.config, case, self.specialists)
        self.assertEqual(set(results), set(BASELINE_SYSTEMS))
        for result in results.values():
            validate_baseline_result(result)

    def test_run_all_systems_includes_pure_mavs_gc(self):
        case = self.generator.generate_case(3, "low")
        results = run_all_systems(self.config, case, self.specialists)
        self.assertEqual(set(results), set(ALL_COMPARISON_SYSTEMS))
        for system in BASELINE_SYSTEMS:
            validate_baseline_result(results[system])
        self.assertIn("severity", results["pure_mavs_gc"])
        self.assertIn("threshold", results["pure_mavs_gc"])
        self.assertIn("consensus", results["pure_mavs_gc"])

    def test_baseline_outputs_are_reproducible(self):
        case = self.generator.generate_case(11, "medium")
        first = run_all_systems(self.config, case, self.specialists)

        second_config = BenchmarkConfig.default()
        second_case = SyntheticCaseGenerator(second_config).generate_case(11, "medium")
        second_specialists = build_default_specialists(second_config)
        second = run_all_systems(second_config, second_case, second_specialists)

        self.assertEqual(first, second)

    def test_baselines_do_not_emit_full_governance_fields(self):
        case = self.generator.generate_case(4, "medium")
        results = run_baselines(self.config, case, self.specialists)
        forbidden = {"severity", "mitigation", "threshold", "consensus"}
        for result in results.values():
            self.assertTrue(forbidden.isdisjoint(result))
            self.assertFalse(result["metadata"]["uses_governance"])

    def test_baseline_documentation_records_decision_rules(self):
        docs = Path("docs/baseline_definitions.md").read_text(encoding="utf-8")
        self.assertIn("score = mean(specialist_scores)", docs)
        self.assertIn("decision = score >= 0.5", docs)
        self.assertIn("Default `veto_threshold`: `0.85`", docs)
        self.assertIn("pure_mavs_gc", docs)

    def test_baseline_stress_sample_without_stdout_noise(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            config = BenchmarkConfig(seed=20260618, case_count=200)
            generator = SyntheticCaseGenerator(config)
            specialists = build_default_specialists(config)
            cases = generator.generate_batch(count=200)
            results = [run_all_systems(config, case, specialists) for case in cases]
        self.assertEqual(len(results), 200)
        for result in results:
            self.assertEqual(set(result), set(ALL_COMPARISON_SYSTEMS))
            for system in BASELINE_SYSTEMS:
                validate_baseline_result(result[system])
        self.assertGreater(len(buffer.getvalue().splitlines()), 0)

    def test_runner_uses_all_speak_outputs_for_baselines(self):
        case = self.generator.generate_case(6, "low")
        outputs = evaluate_all(self.specialists, case)
        results = run_baselines(self.config, case, self.specialists)
        expected_names = {output.specialist_name for output in outputs}
        for result in results.values():
            self.assertEqual(set(result["specialist_scores"]), expected_names)


if __name__ == "__main__":
    unittest.main()

