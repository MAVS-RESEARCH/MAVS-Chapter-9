"""Stability metrics for Phase 4 synthetic experiments."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean, pstdev
from typing import Any

from src.core.types import console_log


def _score_or_consensus(result: dict[str, Any]) -> float | None:
    if result.get("consensus") is not None:
        return float(result["consensus"])
    if result.get("score") is not None:
        return float(result["score"])
    return None


def stability_summary(results: list[dict[str, Any]]) -> dict[str, float | int | None]:
    values = [value for result in results if (value := _score_or_consensus(result)) is not None]
    decisions = [1.0 if result["decision"] else 0.0 for result in results]
    if not values:
        consensus_stddev = None
        consensus_range = None
        stability_index = None
    else:
        consensus_stddev = pstdev(values) if len(values) > 1 else 0.0
        consensus_range = max(values) - min(values)
        stability_index = 1.0 / (1.0 + consensus_stddev)
    decision_mean = mean(decisions) if decisions else 0.0
    decision_variance = decision_mean * (1.0 - decision_mean)
    # console.log: record stability metric computation.
    console_log("metrics.stability", f"computed stability metrics for n={len(results)}")
    return {
        "count": len(results),
        "score_or_consensus_stddev": consensus_stddev,
        "score_or_consensus_range": consensus_range,
        "consensus_stability_index": stability_index,
        "decision_variance": decision_variance,
    }


def stability_by_system(records: list[dict[str, Any]]) -> dict[str, dict[str, float | int | None]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["system"]].append(record["result"])
    # console.log: record stability grouping by comparison system.
    console_log("metrics.stability_by_system", f"grouped {len(records)} records")
    return {
        system: stability_summary(system_results)
        for system, system_results in sorted(grouped.items())
    }

