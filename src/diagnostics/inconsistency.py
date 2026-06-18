"""Contradictory specialist behavior diagnostic for MAVS-GC Phase 2."""

from __future__ import annotations

from src.core.types import SpecialistOutput, clamp_unit_interval, console_log


def inconsistency_flag(outputs: list[SpecialistOutput]) -> float:
    if not outputs:
        raise ValueError("outputs must be nonempty")
    supports = [output.support for output in outputs]
    strongest_positive = max(supports)
    strongest_negative = min(supports)
    if strongest_positive <= 0.0 or strongest_negative >= 0.0:
        flag = 0.0
    else:
        flag = clamp_unit_interval((strongest_positive - strongest_negative) / 2.0)
    # console.log: record inconsistency diagnostic emission.
    console_log("diagnostic.inconsistency", f"flag={flag:.6f} from opposing supports")
    return flag

