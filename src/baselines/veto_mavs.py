"""Veto MAVS baseline for Phase 3.

This baseline is intentionally not the full MAVS-GC pipeline. It uses mean
ensemble scoring plus a direct red-flag veto and does not aggregate severity,
rebalance weights, use organs, compute a governed threshold, or compute R.
"""

from __future__ import annotations

from typing import Any

from src.core.config import BenchmarkConfig
from src.core.types import SpecialistOutput, SyntheticCase, console_log
from src.diagnostics.corruption import corruption_flag
from src.diagnostics.disagreement import disagreement_flag
from src.diagnostics.inconsistency import inconsistency_flag
from src.diagnostics.overconfidence import overconfidence_flag

VETO_MAVS_DECISION_CUTOFF = 0.5
VETO_FLAG_THRESHOLD = 0.85


def compute_red_flags(case: SyntheticCase, outputs: list[SpecialistOutput]) -> dict[str, float]:
    flags = {
        "disagreement": disagreement_flag(outputs),
        "corruption": corruption_flag(case),
        "overconfidence": overconfidence_flag(case, outputs),
        "inconsistency": inconsistency_flag(outputs),
    }
    # console.log: record Veto MAVS red-flag vector construction.
    console_log("baseline.veto.flags", f"{case.case_id} flags={flags}")
    return flags


def run_veto_mavs(
    config: BenchmarkConfig,
    case: SyntheticCase,
    outputs: list[SpecialistOutput],
    cutoff: float = VETO_MAVS_DECISION_CUTOFF,
    veto_threshold: float = VETO_FLAG_THRESHOLD,
) -> dict[str, Any]:
    if not outputs:
        raise ValueError("outputs must be nonempty")
    mean_score = sum(output.score for output in outputs) / len(outputs)
    flags = compute_red_flags(case, outputs)
    max_flag = max(flags.values())
    veto_active = max_flag >= veto_threshold
    decision = mean_score >= cutoff and not veto_active
    # console.log: record Veto MAVS baseline decision.
    console_log(
        "baseline.veto.decision",
        f"{case.case_id} mean_score={mean_score:.6f} veto={veto_active} decision={decision}",
    )
    return {
        "system": "veto_mavs",
        "trace_id": f"trace-{config.config_id}-{case.case_id}-veto-mavs",
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
        "diagnostics": flags,
        "score": mean_score,
        "cutoff": cutoff,
        "veto_threshold": veto_threshold,
        "veto_active": veto_active,
        "decision": decision,
        "metadata": {
            "phase": 3,
            "baseline_type": "mean_plus_red_flag_veto",
            "uses_governance": False,
            "uses_red_flags": True,
        },
    }

