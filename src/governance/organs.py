"""Synthetic mitigation organ for MAVS-GC Phase 2."""

from __future__ import annotations

from src.core.types import SyntheticCase, clamp_unit_interval, console_log


def synthetic_mitigation(case: SyntheticCase, diagnostics: dict[str, float]) -> float:
    corruption = diagnostics.get("corruption", 0.0)
    inconsistency = diagnostics.get("inconsistency", 0.0)
    credibility_discount = clamp_unit_interval(0.30 * corruption + 0.20 * inconsistency)
    mitigation = clamp_unit_interval(case.mitigation_level * (1.0 - credibility_discount))
    # console.log: record bounded synthetic organ mitigation.
    console_log("governance.organ.synthetic", f"{case.case_id} mitigation={mitigation:.6f}")
    return mitigation

