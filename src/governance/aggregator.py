"""Severity aggregation operators for MAVS-GC Phase 2."""

from __future__ import annotations

from src.core.types import console_log, ensure_finite


def _ensure_nonnegative_mapping(values: dict[str, float], label: str) -> None:
    if not values:
        raise ValueError(f"{label} must be nonempty")
    for name, value in values.items():
        value = ensure_finite(float(value), f"{label}[{name}]")
        if value < 0.0:
            raise ValueError(f"{label}[{name}] must be nonnegative")


def weighted_sum_aggregator(
    diagnostics: dict[str, float],
    weights: dict[str, float] | None = None,
) -> float:
    _ensure_nonnegative_mapping(diagnostics, "diagnostics")
    effective_weights = weights or {}
    for name, weight in effective_weights.items():
        weight = ensure_finite(float(weight), f"weights[{name}]")
        if weight < 0.0:
            raise ValueError(f"weights[{name}] must be nonnegative")
    severity = sum(value * effective_weights.get(name, 1.0) for name, value in diagnostics.items())
    # console.log: record weighted severity aggregation.
    console_log("governance.aggregator.weighted_sum", f"severity={severity:.6f}")
    return severity


def max_aggregator(diagnostics: dict[str, float]) -> float:
    _ensure_nonnegative_mapping(diagnostics, "diagnostics")
    severity = max(diagnostics.values())
    # console.log: record max severity aggregation.
    console_log("governance.aggregator.max", f"severity={severity:.6f}")
    return severity

