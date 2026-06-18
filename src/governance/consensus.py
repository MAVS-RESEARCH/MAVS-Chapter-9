"""Governed consensus operator for MAVS-GC Phase 2."""

from __future__ import annotations

from src.core.types import SpecialistOutput, console_log, ensure_finite


def governed_sum(outputs: list[SpecialistOutput], weights: dict[str, float]) -> float:
    if not outputs:
        raise ValueError("outputs must be nonempty")
    if set(weights) != {output.specialist_name for output in outputs}:
        raise ValueError("weights must be provided for exactly the specialist outputs")
    consensus = 0.0
    for output in outputs:
        weight = ensure_finite(weights[output.specialist_name], f"weights[{output.specialist_name}]")
        consensus += weight * output.support
    # console.log: record governed consensus computation.
    console_log("governance.consensus", f"R={consensus:.6f}")
    return consensus

