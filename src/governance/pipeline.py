"""End-to-end MAVS-GC Phase 2 governance pipeline."""

from __future__ import annotations

from typing import Sequence

from src.core.config import BenchmarkConfig
from src.core.types import ConfigReference, SpecialistOutput, SyntheticCase, Trace, console_log
from src.diagnostics.corruption import corruption_flag
from src.diagnostics.disagreement import disagreement_flag
from src.diagnostics.inconsistency import inconsistency_flag
from src.diagnostics.overconfidence import overconfidence_flag
from src.governance.aggregator import weighted_sum_aggregator
from src.governance.consensus import governed_sum
from src.governance.organs import synthetic_mitigation
from src.governance.policy import PolicyResult, evaluate_policy
from src.governance.rebalancer import compute_weights, weights_within_bounds
from src.specialists.base import Specialist, evaluate_all
from src.specialists.synthetic import build_default_specialists

FULL_TRACE_FIELDS = (
    "diagnostics",
    "severity",
    "weights",
    "mitigation",
    "threshold",
    "consensus",
    "decision",
)


def compute_diagnostics(case: SyntheticCase, outputs: list[SpecialistOutput]) -> dict[str, float]:
    diagnostics = {
        "disagreement": disagreement_flag(outputs),
        "corruption": corruption_flag(case),
        "overconfidence": overconfidence_flag(case, outputs),
        "inconsistency": inconsistency_flag(outputs),
    }
    # console.log: record complete diagnostic vector construction.
    console_log("pipeline.diagnostics", f"{case.case_id} diagnostics={diagnostics}")
    return diagnostics


def run_mavs_gc_pipeline(
    config: BenchmarkConfig,
    case: SyntheticCase,
    specialists: Sequence[Specialist] | None = None,
) -> Trace:
    active_specialists = list(specialists) if specialists is not None else build_default_specialists(config)
    # console.log: record MAVS-GC pipeline start.
    console_log("pipeline.start", f"running full governance pipeline for {case.case_id}")
    outputs = evaluate_all(active_specialists, case)
    diagnostics = compute_diagnostics(case, outputs)
    severity = weighted_sum_aggregator(diagnostics, config.governance.diagnostic_weights)
    weights = compute_weights(config, case, outputs, diagnostics)
    if not weights_within_bounds(config, weights):
        raise ValueError("rebalancer produced weights outside configured bounds")
    mitigation = synthetic_mitigation(case, diagnostics)
    consensus = governed_sum(outputs, weights)
    policy = evaluate_policy(config, severity, mitigation, consensus)
    trace = _build_full_trace(
        config=config,
        case=case,
        outputs=outputs,
        diagnostics=diagnostics,
        severity=severity,
        weights=weights,
        mitigation=mitigation,
        consensus=consensus,
        policy=policy,
    )
    validate_full_trace(config, trace)
    # console.log: record MAVS-GC pipeline completion.
    console_log("pipeline.complete", f"{trace.trace_id} decision={trace.decision}")
    return trace


def _build_full_trace(
    config: BenchmarkConfig,
    case: SyntheticCase,
    outputs: list[SpecialistOutput],
    diagnostics: dict[str, float],
    severity: float,
    weights: dict[str, float],
    mitigation: float,
    consensus: float,
    policy: PolicyResult,
) -> Trace:
    specialist_scores = {output.specialist_name: output.score for output in outputs}
    supports = {output.specialist_name: output.support for output in outputs}
    # console.log: record full trace materialization.
    console_log("pipeline.trace", f"materializing full trace for {case.case_id}")
    return Trace(
        trace_id=f"trace-{config.config_id}-{case.case_id}-mavs-gc",
        config=ConfigReference(config_id=str(config.config_id), seed=config.seed),
        case=case,
        specialist_scores=specialist_scores,
        supports=supports,
        diagnostics=diagnostics,
        severity=severity,
        weights=weights,
        mitigation=mitigation,
        threshold=policy.threshold,
        consensus=consensus,
        decision=policy.decision,
        metadata={
            "phase": 2,
            "scope": "governance core",
            "policy_reason": policy.reason,
            "hard_veto_active": policy.hard_veto_active,
        },
    )


def validate_full_trace(config: BenchmarkConfig, trace: Trace) -> None:
    for field_name in FULL_TRACE_FIELDS:
        value = getattr(trace, field_name)
        if value is None:
            raise ValueError(f"full MAVS-GC trace missing {field_name}")
        if isinstance(value, dict) and not value:
            raise ValueError(f"full MAVS-GC trace has empty {field_name}")
    if set(trace.specialist_scores) != set(trace.supports):
        raise ValueError("trace scores and supports must align")
    if set(trace.specialist_scores) != set(trace.weights):
        raise ValueError("trace scores and weights must align")
    if not weights_within_bounds(config, trace.weights):
        raise ValueError("trace weights are outside configured bounds")
    if trace.metadata.get("hard_veto_active") and trace.decision is not False:
        raise ValueError("hard veto traces must reject")
    # console.log: record full trace validation success.
    console_log("pipeline.validate", f"{trace.trace_id} passed full trace validation")

