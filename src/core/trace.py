"""Trace construction and validation for MAVS-GC Phase 1."""

from __future__ import annotations

from src.core.config import BenchmarkConfig
from src.core.types import ConfigReference, SpecialistOutput, SyntheticCase, Trace, console_log

PHASE1_REQUIRED_TRACE_FIELDS = (
    "trace_id",
    "config",
    "case",
    "specialist_scores",
    "supports",
)


def build_phase1_trace(
    config: BenchmarkConfig,
    case: SyntheticCase,
    outputs: list[SpecialistOutput],
) -> Trace:
    if not outputs:
        raise ValueError("outputs must be nonempty")
    specialist_scores = {output.specialist_name: output.score for output in outputs}
    supports = {output.specialist_name: output.support for output in outputs}
    if len(specialist_scores) != len(outputs):
        raise ValueError("specialist names must be unique within a trace")
    # console.log: record trace assembly from specialist outputs.
    console_log("trace.build", f"building trace for {case.case_id} with {len(outputs)} specialists")
    trace = Trace(
        trace_id=f"trace-{config.config_id}-{case.case_id}",
        config=ConfigReference(config_id=str(config.config_id), seed=config.seed),
        case=case,
        specialist_scores=specialist_scores,
        supports=supports,
        metadata={
            "phase": 1,
            "scope": "core infrastructure",
            "governance_status": "not_evaluated_in_phase_1",
        },
    )
    validate_phase1_trace(trace)
    return trace


def validate_phase1_trace(trace: Trace) -> None:
    missing = [field for field in PHASE1_REQUIRED_TRACE_FIELDS if getattr(trace, field) is None]
    if missing:
        raise ValueError(f"trace missing required Phase 1 fields: {missing}")
    if trace.case.truth not in (0, 1):
        raise ValueError("trace case truth must be 0 or 1")
    if not trace.specialist_scores:
        raise ValueError("trace must include specialist scores")
    if set(trace.specialist_scores) != set(trace.supports):
        raise ValueError("trace scores and supports must use the same specialist names")
    # console.log: record trace validation success.
    console_log("trace.validate", f"{trace.trace_id} passed Phase 1 trace validation")

