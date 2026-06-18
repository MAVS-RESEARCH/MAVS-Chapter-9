"""Synthetic corruption diagnostic for MAVS-GC Phase 2."""

from __future__ import annotations

from src.core.types import SyntheticCase, clamp_unit_interval, console_log


def corruption_flag(case: SyntheticCase) -> float:
    flag = clamp_unit_interval(case.corruption)
    # console.log: record corruption diagnostic emission.
    console_log("diagnostic.corruption", f"{case.case_id} corruption flag={flag:.6f}")
    return flag

