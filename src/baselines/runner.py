"""Shared baseline execution interface for Phase 3."""

from __future__ import annotations

from typing import Any, Sequence

from src.baselines.mean import run_mean_ensemble
from src.baselines.static_weighted import run_static_weighted_ensemble
from src.baselines.veto_mavs import run_veto_mavs
from src.core.config import BenchmarkConfig
from src.core.types import SyntheticCase, console_log
from src.governance.pipeline import run_mavs_gc_pipeline
from src.specialists.base import Specialist, evaluate_all
from src.specialists.synthetic import build_default_specialists

BASELINE_SYSTEMS = ("mean_ensemble", "static_weighted_ensemble", "veto_mavs")
ALL_COMPARISON_SYSTEMS = (*BASELINE_SYSTEMS, "pure_mavs_gc")


def run_baselines(
    config: BenchmarkConfig,
    case: SyntheticCase,
    specialists: Sequence[Specialist] | None = None,
) -> dict[str, dict[str, Any]]:
    active_specialists = list(specialists) if specialists is not None else build_default_specialists(config)
    # console.log: record shared baseline specialist evaluation.
    console_log("baseline.runner.evaluate", f"evaluating baselines for {case.case_id}")
    outputs = evaluate_all(active_specialists, case)
    results = {
        "mean_ensemble": run_mean_ensemble(config, case, outputs),
        "static_weighted_ensemble": run_static_weighted_ensemble(config, case, outputs),
        "veto_mavs": run_veto_mavs(config, case, outputs),
    }
    # console.log: record baseline-only execution completion.
    console_log("baseline.runner.complete", f"{case.case_id} baseline systems completed")
    return results


def run_all_systems(
    config: BenchmarkConfig,
    case: SyntheticCase,
    specialists: Sequence[Specialist] | None = None,
) -> dict[str, dict[str, Any]]:
    active_specialists = list(specialists) if specialists is not None else build_default_specialists(config)
    # console.log: record full comparison execution start.
    console_log("baseline.runner.all_start", f"running all comparison systems for {case.case_id}")
    results = run_baselines(config, case, active_specialists)
    pure_trace = run_mavs_gc_pipeline(config, case, active_specialists)
    results["pure_mavs_gc"] = pure_trace.to_dict()
    # console.log: record full comparison execution completion.
    console_log("baseline.runner.all_complete", f"{case.case_id} all comparison systems completed")
    return results


def validate_baseline_result(result: dict[str, Any]) -> None:
    required = {
        "system",
        "trace_id",
        "config",
        "case",
        "specialist_scores",
        "supports",
        "score",
        "cutoff",
        "decision",
        "metadata",
    }
    missing = sorted(required - set(result))
    if missing:
        raise ValueError(f"baseline result missing fields: {missing}")
    if result["metadata"].get("uses_governance"):
        raise ValueError("baseline result must not claim full MAVS-GC governance")
    if result["system"] not in BASELINE_SYSTEMS:
        raise ValueError(f"unknown baseline system {result['system']!r}")
    if set(result["specialist_scores"]) != set(result["supports"]):
        raise ValueError("baseline scores and supports must align")
    # console.log: record baseline result validation.
    console_log("baseline.runner.validate", f"{result['trace_id']} baseline trace validated")

