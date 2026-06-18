import unittest

from src.core.case_generator import SyntheticCaseGenerator
from src.core.config import BenchmarkConfig
from src.core.trace import build_phase1_trace, validate_phase1_trace
from src.specialists.base import evaluate_all
from src.specialists.synthetic import build_default_specialists


class TracePhase1Tests(unittest.TestCase):
    def setUp(self):
        self.config = BenchmarkConfig.default()
        self.generator = SyntheticCaseGenerator(self.config)
        self.specialists = build_default_specialists(self.config)

    def test_phase1_trace_contains_required_core_fields(self):
        case = self.generator.generate_case(0, "medium")
        outputs = evaluate_all(self.specialists, case)
        trace = build_phase1_trace(self.config, case, outputs)
        self.assertTrue(trace.trace_id.startswith("trace-"))
        self.assertEqual(trace.config.config_id, self.config.config_id)
        self.assertEqual(trace.case.case_id, case.case_id)
        self.assertEqual(set(trace.specialist_scores), set(trace.supports))
        self.assertEqual(len(trace.specialist_scores), 5)
        self.assertEqual(trace.metadata["phase"], 1)
        validate_phase1_trace(trace)

    def test_phase1_trace_is_deterministic(self):
        case = self.generator.generate_case(2, "high")
        outputs = evaluate_all(self.specialists, case)
        first = build_phase1_trace(self.config, case, outputs).to_dict()

        second_config = BenchmarkConfig.default()
        second_case = SyntheticCaseGenerator(second_config).generate_case(2, "high")
        second_outputs = evaluate_all(build_default_specialists(second_config), second_case)
        second = build_phase1_trace(second_config, second_case, second_outputs).to_dict()

        self.assertEqual(first, second)

    def test_phase1_trace_rejects_empty_outputs(self):
        case = self.generator.generate_case(0, "low")
        with self.assertRaises(ValueError):
            build_phase1_trace(self.config, case, [])

    def test_phase1_trace_rejects_duplicate_specialist_names(self):
        case = self.generator.generate_case(0, "low")
        outputs = evaluate_all(self.specialists, case)
        duplicated = [outputs[0], outputs[0]]
        with self.assertRaises(ValueError):
            build_phase1_trace(self.config, case, duplicated)


if __name__ == "__main__":
    unittest.main()

