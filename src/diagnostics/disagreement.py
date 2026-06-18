"""Disagreement diagnostic for MAVS-GC Phase 2."""

from __future__ import annotations

from src.core.types import SpecialistOutput, clamp_unit_interval, console_log


def disagreement_flag(outputs: list[SpecialistOutput]) -> float:
    if not outputs:
        raise ValueError("outputs must be nonempty")
    scores = [output.score for output in outputs]
    mean_score = sum(scores) / len(scores)
    variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
    flag = clamp_unit_interval(4.0 * variance)
    # console.log: record disagreement diagnostic emission.
    console_log("diagnostic.disagreement", f"flag={flag:.6f} from {len(outputs)} specialists")
    return flag

