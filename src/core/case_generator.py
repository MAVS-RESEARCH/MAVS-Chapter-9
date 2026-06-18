"""Deterministic synthetic case generation for Phase 1."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable

from src.core.config import BenchmarkConfig
from src.core.types import SyntheticCase, console_log, stable_hash_int

REGIMES = ("low", "medium", "high")


@dataclass(frozen=True)
class SyntheticCaseGenerator:
    config: BenchmarkConfig

    def __post_init__(self) -> None:
        # console.log: record case generator readiness.
        console_log(
            "case_generator.ready",
            f"seed={self.config.seed}, planned_cases={self.config.case_count}",
        )

    def generate_case(self, index: int, regime: str | None = None) -> SyntheticCase:
        if index < 0:
            raise ValueError("index must be nonnegative")
        selected_regime = regime or REGIMES[index % len(REGIMES)]
        if selected_regime not in REGIMES:
            raise ValueError(f"unknown disagreement regime {selected_regime!r}")

        rng = random.Random(stable_hash_int(self.config.seed, "case", index, selected_regime))
        truth = int(rng.random() >= 0.5)
        corruption = self._draw_corruption(rng, selected_regime)
        mitigation_level = round(rng.uniform(0.0, 1.0), 6)
        signal_strength = self._draw_signal_strength(rng, truth, corruption)
        edge_condition = self._edge_condition(corruption, selected_regime)
        case = SyntheticCase(
            case_id=f"case-{index:06d}-{selected_regime}",
            truth=truth,
            corruption=round(corruption, 6),
            disagreement_regime=selected_regime,
            mitigation_level=mitigation_level,
            edge_condition=edge_condition,
            features={
                "signal_strength": round(signal_strength, 6),
                "corruption": round(corruption, 6),
                "mitigation_hint": mitigation_level,
                "disagreement_code": float(REGIMES.index(selected_regime)),
            },
            metadata={
                "generator": "SyntheticCaseGenerator",
                "case_index": index,
                "seed": self.config.seed,
            },
        )
        # console.log: record deterministic synthetic case emission.
        console_log("case_generator.case", f"{case.case_id} emitted with truth={case.truth}")
        return case

    def generate_batch(
        self,
        count: int | None = None,
        regimes: Iterable[str] | None = None,
    ) -> list[SyntheticCase]:
        case_count = count or self.config.case_count
        if case_count <= 0:
            raise ValueError("count must be positive")
        regime_list = tuple(regimes) if regimes is not None else REGIMES
        if not regime_list:
            raise ValueError("regimes must be nonempty")
        # console.log: record deterministic batch generation.
        console_log("case_generator.batch", f"generating {case_count} synthetic cases")
        return [
            self.generate_case(index, regime_list[index % len(regime_list)])
            for index in range(case_count)
        ]

    @staticmethod
    def _draw_corruption(rng: random.Random, regime: str) -> float:
        if regime == "low":
            return rng.uniform(0.0, 0.2)
        if regime == "medium":
            return rng.uniform(0.25, 0.6)
        return rng.uniform(0.65, 1.0)

    @staticmethod
    def _draw_signal_strength(rng: random.Random, truth: int, corruption: float) -> float:
        clean_signal = rng.uniform(0.62, 0.98) if truth == 1 else rng.uniform(0.02, 0.38)
        drift = (rng.random() - 0.5) * corruption
        return max(0.0, min(1.0, clean_signal + drift))

    @staticmethod
    def _edge_condition(corruption: float, regime: str) -> str:
        if corruption >= 0.82:
            return "fragility"
        if regime == "high":
            return "high_disagreement"
        return "nominal"

