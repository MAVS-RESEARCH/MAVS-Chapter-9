"""Bounded contextual rebalancer W for MAVS-GC Phase 2."""

from __future__ import annotations

from src.core.config import BenchmarkConfig
from src.core.types import SpecialistOutput, SyntheticCase, clamp_unit_interval, console_log

RELIABILITY_PRIORS = {
    "accurate": 0.95,
    "noisy": 0.82,
    "overconfident": 0.74,
    "fragile": 0.70,
    "adversarial": 0.35,
}


def _clip_weight(config: BenchmarkConfig, value: float) -> float:
    lower = config.governance.w_min
    upper = config.governance.w_max
    return max(lower, min(upper, value))


def compute_weights(
    config: BenchmarkConfig,
    case: SyntheticCase,
    outputs: list[SpecialistOutput],
    diagnostics: dict[str, float],
) -> dict[str, float]:
    if not outputs:
        raise ValueError("outputs must be nonempty")
    # console.log: record rebalancer execution start.
    console_log("governance.rebalancer.start", f"computing weights for {case.case_id}")
    weights: dict[str, float] = {}
    disagreement = diagnostics.get("disagreement", 0.0)
    corruption = diagnostics.get("corruption", 0.0)
    overconfidence = diagnostics.get("overconfidence", 0.0)
    inconsistency = diagnostics.get("inconsistency", 0.0)
    for output in outputs:
        base = RELIABILITY_PRIORS.get(output.specialist_name, 0.6)
        penalty = 0.10 * disagreement + 0.08 * corruption + 0.07 * inconsistency
        bonus = 0.0
        if output.specialist_name == "accurate":
            bonus += 0.04 * (1.0 - corruption)
        elif output.specialist_name == "noisy":
            penalty += 0.10 * corruption
        elif output.specialist_name == "overconfident":
            penalty += 0.18 * overconfidence
        elif output.specialist_name == "fragile":
            penalty += 0.16 * corruption
        elif output.specialist_name == "adversarial":
            penalty += 0.20 * (disagreement + inconsistency)
        weight = _clip_weight(config, base + bonus - penalty)
        weights[output.specialist_name] = weight
        # console.log: record each bounded specialist weight.
        console_log("governance.rebalancer.weight", f"{output.specialist_name} weight={weight:.6f}")
    return weights


def weights_within_bounds(config: BenchmarkConfig, weights: dict[str, float]) -> bool:
    lower = config.governance.w_min
    upper = config.governance.w_max
    return all(lower <= value <= upper for value in weights.values())

