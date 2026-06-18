"""Overconfidence diagnostic for MAVS-GC Phase 2."""

from __future__ import annotations

from src.core.types import SpecialistOutput, SyntheticCase, clamp_unit_interval, console_log


def overconfidence_flag(case: SyntheticCase, outputs: list[SpecialistOutput]) -> float:
    if not outputs:
        raise ValueError("outputs must be nonempty")
    scores = [output.score for output in outputs]
    confidence = max(abs(score - 0.5) * 2.0 for score in scores)
    spread = max(scores) - min(scores)
    flag = clamp_unit_interval(confidence * max(case.corruption, spread))
    # console.log: record overconfidence diagnostic emission.
    console_log("diagnostic.overconfidence", f"{case.case_id} overconfidence flag={flag:.6f}")
    return flag

