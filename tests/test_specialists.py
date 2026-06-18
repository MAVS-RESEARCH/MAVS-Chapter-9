import unittest

from src.core.case_generator import SyntheticCaseGenerator
from src.core.config import BenchmarkConfig
from src.core.types import score_to_support
from src.specialists.base import evaluate_all
from src.specialists.synthetic import build_default_specialists


class SpecialistPhase1Tests(unittest.TestCase):
    def setUp(self):
        self.config = BenchmarkConfig.default()
        self.generator = SyntheticCaseGenerator(self.config)
        self.specialists = build_default_specialists(self.config)

    def test_required_specialists_are_available(self):
        names = {specialist.name for specialist in self.specialists}
        self.assertEqual(
            names,
            {"accurate", "noisy", "overconfident", "fragile", "adversarial"},
        )

    def test_all_speak_evaluation_returns_every_specialist(self):
        case = self.generator.generate_case(0, "low")
        outputs = evaluate_all(self.specialists, case)
        self.assertEqual(len(outputs), len(self.specialists))
        self.assertEqual(
            {output.specialist_name for output in outputs},
            {specialist.name for specialist in self.specialists},
        )

    def test_specialist_scores_and_supports_are_bounded(self):
        cases = self.generator.generate_batch(count=120)
        for case in cases:
            for output in evaluate_all(self.specialists, case):
                self.assertGreaterEqual(output.score, 0.0)
                self.assertLessEqual(output.score, 1.0)
                self.assertGreaterEqual(output.support, -1.0)
                self.assertLessEqual(output.support, 1.0)
                self.assertAlmostEqual(output.support, score_to_support(output.score))

    def test_specialists_are_deterministic_under_fixed_seed(self):
        cases = self.generator.generate_batch(count=30)
        first = [
            [(output.specialist_name, output.score, output.support) for output in evaluate_all(self.specialists, case)]
            for case in cases
        ]
        second_specialists = build_default_specialists(BenchmarkConfig.default())
        second = [
            [(output.specialist_name, output.score, output.support) for output in evaluate_all(second_specialists, case)]
            for case in cases
        ]
        self.assertEqual(first, second)

    def test_case_generator_is_deterministic(self):
        first = self.generator.generate_batch(count=15)
        second = SyntheticCaseGenerator(BenchmarkConfig.default()).generate_batch(count=15)
        self.assertEqual(first, second)

    def test_case_generator_regime_corruption_ranges(self):
        low = self.generator.generate_case(1, "low")
        medium = self.generator.generate_case(1, "medium")
        high = self.generator.generate_case(1, "high")
        self.assertGreaterEqual(low.corruption, 0.0)
        self.assertLessEqual(low.corruption, 0.2)
        self.assertGreaterEqual(medium.corruption, 0.25)
        self.assertLessEqual(medium.corruption, 0.6)
        self.assertGreaterEqual(high.corruption, 0.65)
        self.assertLessEqual(high.corruption, 1.0)


if __name__ == "__main__":
    unittest.main()

