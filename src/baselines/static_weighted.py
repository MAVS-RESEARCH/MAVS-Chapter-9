"""Static weighted ensemble baseline for Phase 3."""

from __future__ import annotations

from typing import Any

from src.core.config import BenchmarkConfig
from src.core.types import SpecialistOutput, SyntheticCase, console_log, ensure_finite

STATIC_WEIGHTED_DECISION_CUTOFF = 0.5
DEFAULT_STATIC_WEIGHTS = {
    "accurate": 0.95,
    "noisy": 0.82,
    "overconfident": 0.74,
    "fragile": 0.70,
    "adversarial": 0.35,
}


def run_static_weighted_ensemble(
    config: BenchmarkConfig,
    case: SyntheticCase,
    outputs: list[SpecialistOutput],
    weights: dict[str, float] | None = None,
    cutoff: float = STATIC_WEIGHTED_DECISION_CUTOFF,
) -> dict[str, Any]:
    if not outputs:
        raise ValueError("outputs must be nonempty")
    effective_weights = weights or DEFAULT_STATIC_WEIGHTS
    missing = {output.specialist_name for output in outputs} - set(effective_weights)
    if missing:
        raise ValueError(f"missing static weights for specialists: {sorted(missing)}")
    numerator = 0.0
    denominator = 0.0
    used_weights: dict[str, float] = {}
    for output in outputs:
        weight = ensure_finite(float(effective_weights[output.specialist_name]), "static_weight")
        if weight < 0.0:
            raise ValueError("static weights must be nonnegative")
        numerator += weight * output.score
        denominator += weight
        used_weights[output.specialist_name] = weight
    if denominator <= 0.0:
        raise ValueError("sum of static weights must be positive")
    weighted_score = numerator / denominator
    decision = weighted_score >= cutoff
    # console.log: record static weighted baseline decision.
    console_log(
        "baseline.static_weighted",
        f"{case.case_id} weighted_score={weighted_score:.6f} decision={decision}",
    )
    return {
        "system": "static_weighted_ensemble",
        "trace_id": f"trace-{config.config_id}-{case.case_id}-static-weighted",
        "config": {"config_id": config.config_id, "seed": config.seed},
        "case": {
            "case_id": case.case_id,
            "truth": case.truth,
            "corruption": case.corruption,
            "disagreement_regime": case.disagreement_regime,
            "mitigation_level": case.mitigation_level,
            "edge_condition": case.edge_condition,
        },
        "specialist_scores": {output.specialist_name: output.score for output in outputs},
        "supports": {output.specialist_name: output.support for output in outputs},
        "weights": used_weights,
        "score": weighted_score,
        "cutoff": cutoff,
        "decision": decision,
        "metadata": {
            "phase": 3,
            "baseline_type": "static_weighted_mean",
            "uses_governance": False,
        },
    }

