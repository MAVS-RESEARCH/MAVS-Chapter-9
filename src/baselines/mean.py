"""Mean ensemble baseline for Phase 3."""

from __future__ import annotations

from typing import Any

from src.core.config import BenchmarkConfig
from src.core.types import SpecialistOutput, SyntheticCase, console_log

MEAN_DECISION_CUTOFF = 0.5


def run_mean_ensemble(
    config: BenchmarkConfig,
    case: SyntheticCase,
    outputs: list[SpecialistOutput],
    cutoff: float = MEAN_DECISION_CUTOFF,
) -> dict[str, Any]:
    if not outputs:
        raise ValueError("outputs must be nonempty")
    mean_score = sum(output.score for output in outputs) / len(outputs)
    decision = mean_score >= cutoff
    # console.log: record mean ensemble baseline decision.
    console_log("baseline.mean", f"{case.case_id} mean_score={mean_score:.6f} decision={decision}")
    return {
        "system": "mean_ensemble",
        "trace_id": f"trace-{config.config_id}-{case.case_id}-mean-ensemble",
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
        "score": mean_score,
        "cutoff": cutoff,
        "decision": decision,
        "metadata": {
            "phase": 3,
            "baseline_type": "static_mean",
            "uses_governance": False,
        },
    }

