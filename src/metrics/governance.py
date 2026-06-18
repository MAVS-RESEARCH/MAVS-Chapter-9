"""Governance-oriented metrics for Phase 4 synthetic experiments."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any

from src.core.types import console_log


def _numeric_summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
        }
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": mean(values),
    }


def governance_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    severities = [float(result["severity"]) for result in results if result.get("severity") is not None]
    thresholds = [float(result["threshold"]) for result in results if result.get("threshold") is not None]
    mitigations = [float(result["mitigation"]) for result in results if result.get("mitigation") is not None]
    consensuses = [float(result["consensus"]) for result in results if result.get("consensus") is not None]
    hard_veto_count = sum(1 for result in results if result.get("metadata", {}).get("hard_veto_active"))
    # console.log: record governance metric computation.
    console_log("metrics.governance", f"computed governance metrics for n={len(results)}")
    return {
        "severity_distribution": _numeric_summary(severities),
        "threshold_distribution": _numeric_summary(thresholds),
        "mitigation_distribution": _numeric_summary(mitigations),
        "consensus_distribution": _numeric_summary(consensuses),
        "hard_veto_count": hard_veto_count,
        "hard_veto_rate": hard_veto_count / len(results) if results else 0.0,
    }


def governance_by_system(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["system"]].append(record["result"])
    # console.log: record governance grouping by comparison system.
    console_log("metrics.governance_by_system", f"grouped {len(records)} records")
    return {
        system: governance_summary(system_results)
        for system, system_results in sorted(grouped.items())
    }


def acceptance_by_group(records: list[dict[str, Any]], group_key: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record["case_metadata"].get(group_key))].append(record)
    output: dict[str, dict[str, Any]] = {}
    for group, group_records in sorted(grouped.items()):
        system_counts: dict[str, dict[str, int | float]] = {}
        by_system: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in group_records:
            by_system[record["system"]].append(record["result"])
        for system, results in sorted(by_system.items()):
            accepted = sum(1 for result in results if result["decision"])
            system_counts[system] = {
                "count": len(results),
                "accepted": accepted,
                "acceptance_rate": accepted / len(results) if results else 0.0,
            }
        output[group] = system_counts
    # console.log: record grouped acceptance metric computation.
    console_log("metrics.acceptance_by_group", f"grouped by {group_key}")
    return output

