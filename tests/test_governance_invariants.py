import contextlib
import io
import unittest

from src.core.case_generator import SyntheticCaseGenerator
from src.core.config import BenchmarkConfig, GovernanceConfig
from src.core.types import SyntheticCase
from src.governance.aggregator import max_aggregator, weighted_sum_aggregator
from src.governance.consensus import governed_sum
from src.governance.pipeline import compute_diagnostics, run_mavs_gc_pipeline, validate_full_trace
from src.governance.policy import compute_threshold, evaluate_policy
from src.governance.rebalancer import compute_weights, weights_within_bounds
from src.specialists.base import evaluate_all
from src.specialists.synthetic import build_default_specialists


class GovernanceInvariantTests(unittest.TestCase):
    def setUp(self):
        self.config = BenchmarkConfig.default()
        self.generator = SyntheticCaseGenerator(self.config)
        self.specialists = build_default_specialists(self.config)

    def test_diagnostics_are_nonnegative(self):
        case = self.generator.generate_case(2, "high")
        outputs = evaluate_all(self.specialists, case)
        diagnostics = compute_diagnostics(case, outputs)
        self.assertEqual(
            set(diagnostics),
            {"disagreement", "corruption", "overconfidence", "inconsistency"},
        )
        self.assertTrue(all(value >= 0.0 for value in diagnostics.values()))

    def test_weighted_sum_severity_is_monotone(self):
        base = {
            "disagreement": 0.1,
            "corruption": 0.2,
            "overconfidence": 0.3,
            "inconsistency": 0.4,
        }
        increased = dict(base)
        increased["corruption"] = 0.7
        self.assertGreaterEqual(
            weighted_sum_aggregator(increased, self.config.governance.diagnostic_weights),
            weighted_sum_aggregator(base, self.config.governance.diagnostic_weights),
        )

    def test_max_aggregator_is_monotone(self):
        base = {"a": 0.2, "b": 0.3}
        increased = {"a": 0.2, "b": 0.5}
        self.assertGreaterEqual(max_aggregator(increased), max_aggregator(base))

    def test_threshold_is_monotone_in_severity(self):
        low = compute_threshold(self.config, severity=0.2, mitigation=0.4)
        high = compute_threshold(self.config, severity=0.9, mitigation=0.4)
        self.assertGreaterEqual(high, low)

    def test_threshold_is_nonincreasing_in_mitigation(self):
        low_mitigation = compute_threshold(self.config, severity=0.8, mitigation=0.1)
        high_mitigation = compute_threshold(self.config, severity=0.8, mitigation=0.9)
        self.assertLessEqual(high_mitigation, low_mitigation)

    def test_hard_veto_dominates_mitigation_and_consensus(self):
        policy = evaluate_policy(
            self.config,
            severity=self.config.governance.tau_hard,
            mitigation=1.0,
            consensus=999.0,
        )
        self.assertTrue(policy.hard_veto_active)
        self.assertFalse(policy.decision)
        self.assertEqual(policy.reason, "hard_veto")

    def test_policy_accepts_without_hard_veto_when_consensus_meets_threshold(self):
        policy = evaluate_policy(
            self.config,
            severity=0.1,
            mitigation=0.0,
            consensus=0.5,
        )
        self.assertFalse(policy.hard_veto_active)
        self.assertTrue(policy.decision)
        self.assertEqual(policy.reason, "threshold_accept")

    def test_rebalancer_weights_are_bounded(self):
        case = self.generator.generate_case(7, "medium")
        outputs = evaluate_all(self.specialists, case)
        diagnostics = compute_diagnostics(case, outputs)
        weights = compute_weights(self.config, case, outputs, diagnostics)
        self.assertEqual(set(weights), {output.specialist_name for output in outputs})
        self.assertTrue(weights_within_bounds(self.config, weights))

    def test_consensus_matches_governed_sum_formula(self):
        case = self.generator.generate_case(3, "low")
        outputs = evaluate_all(self.specialists, case)
        diagnostics = compute_diagnostics(case, outputs)
        weights = compute_weights(self.config, case, outputs, diagnostics)
        consensus = governed_sum(outputs, weights)
        expected = sum(weights[output.specialist_name] * output.support for output in outputs)
        self.assertAlmostEqual(consensus, expected)

    def test_full_pipeline_trace_is_complete(self):
        case = self.generator.generate_case(11, "high")
        trace = run_mavs_gc_pipeline(self.config, case, self.specialists)
        validate_full_trace(self.config, trace)
        self.assertEqual(trace.metadata["phase"], 2)
        self.assertIsNotNone(trace.severity)
        self.assertIsNotNone(trace.mitigation)
        self.assertIsNotNone(trace.threshold)
        self.assertIsNotNone(trace.consensus)
        self.assertIsInstance(trace.decision, bool)

    def test_full_pipeline_trace_is_deterministic(self):
        case = self.generator.generate_case(12, "medium")
        first = run_mavs_gc_pipeline(self.config, case, self.specialists).to_dict()

        second_config = BenchmarkConfig.default()
        second_case = SyntheticCaseGenerator(second_config).generate_case(12, "medium")
        second_specialists = build_default_specialists(second_config)
        second = run_mavs_gc_pipeline(second_config, second_case, second_specialists).to_dict()

        self.assertEqual(first, second)

    def test_pipeline_hard_veto_trace_rejects(self):
        hard_config = BenchmarkConfig(
            governance=GovernanceConfig(
                theta_0=0.0,
                lambda_severity=1.0,
                delta_mitigation=1.0,
                tau_hard=0.25,
                w_min=0.0,
                w_max=1.0,
            )
        )
        case = SyntheticCase(
            case_id="hard-veto-case",
            truth=1,
            corruption=1.0,
            disagreement_regime="high",
            mitigation_level=1.0,
            edge_condition="fragility",
            features={
                "signal_strength": 0.95,
                "corruption": 1.0,
                "mitigation_hint": 1.0,
                "disagreement_code": 2.0,
            },
        )
        trace = run_mavs_gc_pipeline(hard_config, case, build_default_specialists(hard_config))
        self.assertTrue(trace.metadata["hard_veto_active"])
        self.assertFalse(trace.decision)

    def test_pipeline_stress_sample_without_stdout_noise(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            config = BenchmarkConfig(seed=20260618, case_count=250)
            generator = SyntheticCaseGenerator(config)
            specialists = build_default_specialists(config)
            traces = [
                run_mavs_gc_pipeline(config, case, specialists)
                for case in generator.generate_batch(count=250)
            ]
        self.assertEqual(len(traces), 250)
        self.assertEqual(len({trace.trace_id for trace in traces}), 250)
        self.assertTrue(all(isinstance(trace.decision, bool) for trace in traces))
        self.assertGreater(len(buffer.getvalue().splitlines()), 0)


if __name__ == "__main__":
    unittest.main()
