"""Threshold policy and hard-veto evaluation for MAVS-GC Phase 2."""

from __future__ import annotations

from dataclasses import dataclass

from src.core.config import BenchmarkConfig
from src.core.types import console_log, ensure_finite, ensure_unit_interval


@dataclass(frozen=True)
class PolicyResult:
    threshold: float
    hard_veto_active: bool
    decision: bool
    reason: str


def compute_threshold(config: BenchmarkConfig, severity: float, mitigation: float) -> float:
    severity = ensure_finite(severity, "severity")
    if severity < 0.0:
        raise ValueError("severity must be nonnegative")
    mitigation = ensure_unit_interval(mitigation, "mitigation")
    threshold = (
        config.governance.theta_0
        + config.governance.lambda_severity * severity
        - config.governance.delta_mitigation * mitigation
    )
    # console.log: record governed threshold computation.
    console_log("governance.policy.threshold", f"theta={threshold:.6f}")
    return threshold


def evaluate_policy(
    config: BenchmarkConfig,
    severity: float,
    mitigation: float,
    consensus: float,
) -> PolicyResult:
    threshold = compute_threshold(config, severity, mitigation)
    hard_veto_active = severity >= config.governance.tau_hard
    if hard_veto_active:
        # console.log: record hard-veto dominance.
        console_log("governance.policy.hard_veto", "hard veto forced rejection")
        return PolicyResult(
            threshold=threshold,
            hard_veto_active=True,
            decision=False,
            reason="hard_veto",
        )
    decision = consensus >= threshold
    # console.log: record ordinary policy decision.
    console_log("governance.policy.decision", f"decision={decision} from R={consensus:.6f}")
    return PolicyResult(
        threshold=threshold,
        hard_veto_active=False,
        decision=decision,
        reason="threshold_accept" if decision else "threshold_reject",
    )

