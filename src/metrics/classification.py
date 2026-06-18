"""Classification metrics for Phase 4 synthetic experiments."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.core.types import console_log


def extract_truth_decision(result: dict[str, Any]) -> tuple[int, bool]:
    truth = int(result["case"]["truth"])
    decision = bool(result["decision"])
    if truth not in (0, 1):
        raise ValueError(f"truth must be 0 or 1, got {truth!r}")
    return truth, decision


def classification_metrics(results: list[dict[str, Any]]) -> dict[str, float | int]:
    if not results:
        raise ValueError("results must be nonempty")
    total = len(results)
    correct = 0
    false_positive = 0
    false_negative = 0
    rejected = 0
    unsafe_acceptance = 0
    unsafe_total = 0
    for result in results:
        truth, decision = extract_truth_decision(result)
        if decision == bool(truth):
            correct += 1
        if truth == 0:
            unsafe_total += 1
            if decision:
                false_positive += 1
                unsafe_acceptance += 1
        if truth == 1 and not decision:
            false_negative += 1
        if not decision:
            rejected += 1
    # console.log: record classification metric computation.
    console_log("metrics.classification", f"computed classification metrics for n={total}")
    return {
        "count": total,
        "accuracy": correct / total,
        "false_positive_count": false_positive,
        "false_positive_rate": false_positive / unsafe_total if unsafe_total else 0.0,
        "false_negative_count": false_negative,
        "false_negative_rate": false_negative / (total - unsafe_total) if total != unsafe_total else 0.0,
        "rejection_count": rejected,
        "rejection_rate": rejected / total,
        "unsafe_acceptance_count": unsafe_acceptance,
        "unsafe_acceptance_rate": unsafe_acceptance / total,
    }


def classification_by_system(records: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["system"]].append(record["result"])
    # console.log: record classification grouping by comparison system.
    console_log("metrics.classification_by_system", f"grouped {len(records)} records")
    return {
        system: classification_metrics(system_results)
        for system, system_results in sorted(grouped.items())
    }

