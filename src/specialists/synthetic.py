"""Synthetic specialists required by the Chapter 9 Phase 1 specification."""

from __future__ import annotations

import random
from dataclasses import dataclass

from src.core.config import BenchmarkConfig
from src.core.types import SyntheticCase, clamp_unit_interval, console_log, stable_hash_int


@dataclass(frozen=True)
class SyntheticSpecialistBase:
    name: str
    seed: int

    def _rng(self, case: SyntheticCase) -> random.Random:
        return random.Random(stable_hash_int(self.seed, self.name, case.case_id))

    @staticmethod
    def _truth_aligned_score(truth: int, confidence: float) -> float:
        confidence = clamp_unit_interval(confidence)
        return confidence if truth == 1 else 1.0 - confidence


@dataclass(frozen=True)
class AccurateSpecialist(SyntheticSpecialistBase):
    accuracy: float = 0.92

    def predict(self, case: SyntheticCase) -> float:
        rng = self._rng(case)
        effective_accuracy = max(0.55, self.accuracy - 0.25 * case.corruption)
        correct = rng.random() < effective_accuracy
        confidence = rng.uniform(0.78, 0.96)
        score = self._truth_aligned_score(case.truth if correct else 1 - case.truth, confidence)
        # console.log: record accurate specialist prediction path.
        console_log("specialist.accurate", f"{case.case_id} scored by accurate specialist")
        return clamp_unit_interval(score)


@dataclass(frozen=True)
class NoisySpecialist(SyntheticSpecialistBase):
    noise_amplitude: float = 0.18

    def predict(self, case: SyntheticCase) -> float:
        rng = self._rng(case)
        base = case.features.get("signal_strength", 0.5)
        perturbation = rng.uniform(-self.noise_amplitude, self.noise_amplitude)
        corruption_drift = rng.uniform(-case.corruption, case.corruption) * 0.15
        # console.log: record noisy specialist perturbation path.
        console_log("specialist.noisy", f"{case.case_id} scored with synthetic perturbation")
        return clamp_unit_interval(base + perturbation + corruption_drift)


@dataclass(frozen=True)
class OverconfidentSpecialist(SyntheticSpecialistBase):
    error_rate: float = 0.18

    def predict(self, case: SyntheticCase) -> float:
        rng = self._rng(case)
        error_pressure = self.error_rate + 0.35 * case.corruption
        wrong = rng.random() < min(0.85, error_pressure)
        asserted_truth = 1 - case.truth if wrong else case.truth
        confidence = rng.uniform(0.91, 0.995)
        # console.log: record overconfident specialist extreme-confidence path.
        console_log("specialist.overconfident", f"{case.case_id} scored with high confidence")
        return clamp_unit_interval(self._truth_aligned_score(asserted_truth, confidence))


@dataclass(frozen=True)
class FragileSpecialist(SyntheticSpecialistBase):
    fragility_threshold: float = 0.72

    def predict(self, case: SyntheticCase) -> float:
        rng = self._rng(case)
        fragile_failure = (
            case.edge_condition == "fragility"
            or case.corruption >= self.fragility_threshold
            or (case.disagreement_regime == "high" and rng.random() < 0.35)
        )
        asserted_truth = 1 - case.truth if fragile_failure else case.truth
        confidence = rng.uniform(0.65, 0.9)
        # console.log: record fragile specialist edge-condition path.
        console_log("specialist.fragile", f"{case.case_id} scored under {case.edge_condition}")
        return clamp_unit_interval(self._truth_aligned_score(asserted_truth, confidence))


@dataclass(frozen=True)
class AdversarialSpecialist(SyntheticSpecialistBase):
    adversarial_strength: float = 0.88

    def predict(self, case: SyntheticCase) -> float:
        rng = self._rng(case)
        confidence = rng.uniform(self.adversarial_strength, 0.99)
        asserted_truth = 1 - case.truth
        # console.log: record adversarial specialist misleading path.
        console_log("specialist.adversarial", f"{case.case_id} scored against truth")
        return clamp_unit_interval(self._truth_aligned_score(asserted_truth, confidence))


def build_default_specialists(config: BenchmarkConfig) -> list[SyntheticSpecialistBase]:
    specialist_config = config.specialist
    specialists: list[SyntheticSpecialistBase] = [
        AccurateSpecialist(
            name="accurate",
            seed=config.seed + 11,
            accuracy=specialist_config.accuracy,
        ),
        NoisySpecialist(
            name="noisy",
            seed=config.seed + 23,
            noise_amplitude=specialist_config.noise_amplitude,
        ),
        OverconfidentSpecialist(
            name="overconfident",
            seed=config.seed + 37,
            error_rate=specialist_config.overconfidence_error_rate,
        ),
        FragileSpecialist(
            name="fragile",
            seed=config.seed + 41,
            fragility_threshold=specialist_config.fragility_threshold,
        ),
        AdversarialSpecialist(
            name="adversarial",
            seed=config.seed + 53,
            adversarial_strength=specialist_config.adversarial_strength,
        ),
    ]
    # console.log: record required synthetic specialist construction.
    console_log("specialists.default", "built five required synthetic specialists")
    return specialists

