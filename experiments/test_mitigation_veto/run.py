"""Synthetic Test 3: mitigation versus hard veto."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.baselines.runner import ALL_COMPARISON_SYSTEMS, run_all_systems
from src.core.config import BenchmarkConfig
from src.core.types import SyntheticCase, console_log, stable_hash_int
from src.metrics.classification import classification_by_system
from src.metrics.governance import acceptance_by_group, governance_by_system
from src.metrics.stability import stability_by_system
from src.specialists.synthetic import build_default_specialists

CONFIG_PATH = Path(__file__).with_name("config.yaml")
EXPERIMENT_NAME = "test_mitigation_veto"


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    # console.log: record mitigation-veto experiment config load.
    console_log("experiment.mitigation_veto.config", f"loaded config from {path}")
    return config


def _record(experiment: str, case: SyntheticCase, system: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment": experiment,
        "system": system,
        "case_id": result["case"]["case_id"],
        "truth": result["case"]["truth"],
        "decision": result["decision"],
        "case_metadata": {
            "corruption_level": case.metadata["corruption_level"],
            "mitigation_level": case.metadata["mitigation_level"],
            "disagreement_regime": case.disagreement_regime,
            "corruption": case.corruption,
            "edge_condition": case.edge_condition,
        },
        "result": result,
    }


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    # console.log: record mitigation-veto trace output write.
    console_log("experiment.mitigation_veto.traces", f"wrote {len(records)} records to {path}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    # console.log: record mitigation-veto metric output write.
    console_log("experiment.mitigation_veto.metrics", f"wrote metrics to {path}")


def _regime_for_corruption(corruption: float) -> str:
    if corruption < 0.25:
        return "low"
    if corruption < 0.65:
        return "medium"
    return "high"


def build_cases(config: dict[str, Any]) -> list[SyntheticCase]:
    cases: list[SyntheticCase] = []
    seed = int(config["seed"])
    index = 0
    for corruption in config["corruption_levels"]:
        for mitigation in config["mitigation_levels"]:
            for replicate in range(int(config["replicates"])):
                rng = random.Random(stable_hash_int(seed, EXPERIMENT_NAME, corruption, mitigation, replicate))
                jittered_corruption = max(0.0, min(1.0, float(corruption) + rng.uniform(-0.015, 0.015)))
                signal_strength = rng.uniform(0.78, 0.98)
                regime = _regime_for_corruption(jittered_corruption)
                edge_condition = "fragility" if jittered_corruption >= 0.82 else ("high_disagreement" if regime == "high" else "nominal")
                cases.append(
                    SyntheticCase(
                        case_id=f"mitigation-veto-{index:06d}",
                        truth=1,
                        corruption=round(jittered_corruption, 6),
                        disagreement_regime=regime,
                        mitigation_level=round(float(mitigation), 6),
                        edge_condition=edge_condition,
                        features={
                            "signal_strength": round(signal_strength, 6),
                            "corruption": round(jittered_corruption, 6),
                            "mitigation_hint": round(float(mitigation), 6),
                            "disagreement_code": float({"low": 0, "medium": 1, "high": 2}[regime]),
                        },
                        metadata={
                            "experiment": EXPERIMENT_NAME,
                            "case_index": index,
                            "corruption_level": f"{float(corruption):.2f}",
                            "mitigation_level": f"{float(mitigation):.2f}",
                            "replicate": replicate,
                        },
                    )
                )
                index += 1
    # console.log: record mitigation-veto case construction.
    console_log("experiment.mitigation_veto.cases", f"built {len(cases)} grid cases")
    return cases


def summarize(records: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    pure_records = [record["result"] for record in records if record["system"] == "pure_mavs_gc"]
    hard_veto_count = sum(1 for result in pure_records if result.get("metadata", {}).get("hard_veto_active"))
    metrics = {
        "experiment": EXPERIMENT_NAME,
        "config": config,
        "record_count": len(records),
        "classification_by_system": classification_by_system(records),
        "governance_by_system": governance_by_system(records),
        "stability_by_system": stability_by_system(records),
        "acceptance_by_mitigation_level": acceptance_by_group(records, "mitigation_level"),
        "acceptance_by_corruption_level": acceptance_by_group(records, "corruption_level"),
        "pure_mavs_gc_hard_veto_compliance": {
            "hard_veto_count": hard_veto_count,
            "hard_veto_rejection_count": sum(
                1
                for result in pure_records
                if result.get("metadata", {}).get("hard_veto_active") and not result["decision"]
            ),
        },
    }
    # console.log: record mitigation-veto summary construction.
    console_log("experiment.mitigation_veto.summary", "computed mitigation-veto metrics")
    return metrics


def run_experiment(
    config_path: Path = CONFIG_PATH,
    output_root: Path = ROOT / "results",
) -> dict[str, Any]:
    config = load_config(config_path)
    cases = build_cases(config)
    benchmark_config = BenchmarkConfig(seed=int(config["seed"]), case_count=len(cases))
    specialists = build_default_specialists(benchmark_config)
    records: list[dict[str, Any]] = []
    # console.log: record mitigation-veto experiment execution start.
    console_log("experiment.mitigation_veto.start", f"running {len(cases)} grid cases")
    for case in cases:
        results = run_all_systems(benchmark_config, case, specialists)
        for system in ALL_COMPARISON_SYSTEMS:
            records.append(_record(EXPERIMENT_NAME, case, system, results[system]))
    metrics = summarize(records, config)
    trace_path = output_root / "traces" / f"{EXPERIMENT_NAME}.jsonl"
    metrics_path = output_root / "metrics" / f"{EXPERIMENT_NAME}.json"
    _write_jsonl(trace_path, records)
    _write_json(metrics_path, metrics)
    # console.log: record mitigation-veto experiment completion.
    console_log("experiment.mitigation_veto.complete", "experiment completed")
    return {"records": records, "metrics": metrics}


if __name__ == "__main__":
    run_experiment()

