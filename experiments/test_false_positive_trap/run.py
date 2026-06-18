"""Synthetic Test 2: false positive trap."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from statistics import mean
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
EXPERIMENT_NAME = "test_false_positive_trap"


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    # console.log: record false-positive experiment config load.
    console_log("experiment.false_positive.config", f"loaded config from {path}")
    return config


def _record(experiment: str, case: SyntheticCase, system: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment": experiment,
        "system": system,
        "case_id": result["case"]["case_id"],
        "truth": result["case"]["truth"],
        "decision": result["decision"],
        "case_metadata": {
            "trap_type": "unsafe_high_confidence_consensus",
            "disagreement_regime": case.disagreement_regime,
            "corruption": case.corruption,
            "mitigation_level": case.mitigation_level,
            "edge_condition": case.edge_condition,
        },
        "result": result,
    }


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    # console.log: record false-positive trace output write.
    console_log("experiment.false_positive.traces", f"wrote {len(records)} records to {path}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    # console.log: record false-positive metric output write.
    console_log("experiment.false_positive.metrics", f"wrote metrics to {path}")


def build_cases(config: dict[str, Any]) -> list[SyntheticCase]:
    cases: list[SyntheticCase] = []
    seed = int(config["seed"])
    for index in range(int(config["case_count"])):
        rng = random.Random(stable_hash_int(seed, EXPERIMENT_NAME, index))
        corruption = rng.uniform(float(config["corruption_min"]), float(config["corruption_max"]))
        signal_strength = rng.uniform(float(config["signal_min"]), float(config["signal_max"]))
        mitigation = rng.uniform(0.0, 0.35)
        cases.append(
            SyntheticCase(
                case_id=f"false-positive-trap-{index:06d}",
                truth=0,
                corruption=round(corruption, 6),
                disagreement_regime="high",
                mitigation_level=round(mitigation, 6),
                edge_condition="fragility",
                features={
                    "signal_strength": round(signal_strength, 6),
                    "corruption": round(corruption, 6),
                    "mitigation_hint": round(mitigation, 6),
                    "disagreement_code": 2.0,
                },
                metadata={
                    "experiment": EXPERIMENT_NAME,
                    "trap_type": "unsafe_high_confidence_consensus",
                    "case_index": index,
                },
            )
        )
    # console.log: record false-positive case construction.
    console_log("experiment.false_positive.cases", f"built {len(cases)} trap cases")
    return cases


def summarize(records: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    pure_records = [record["result"] for record in records if record["system"] == "pure_mavs_gc"]
    thresholds = [float(result["threshold"]) for result in pure_records]
    metrics = {
        "experiment": EXPERIMENT_NAME,
        "config": config,
        "record_count": len(records),
        "classification_by_system": classification_by_system(records),
        "governance_by_system": governance_by_system(records),
        "stability_by_system": stability_by_system(records),
        "acceptance_by_trap_type": acceptance_by_group(records, "trap_type"),
        "pure_mavs_gc_mean_threshold_escalation": mean(thresholds) if thresholds else None,
    }
    # console.log: record false-positive summary construction.
    console_log("experiment.false_positive.summary", "computed false-positive metrics")
    return metrics


def run_experiment(
    config_path: Path = CONFIG_PATH,
    output_root: Path = ROOT / "results",
) -> dict[str, Any]:
    config = load_config(config_path)
    benchmark_config = BenchmarkConfig(seed=int(config["seed"]), case_count=int(config["case_count"]))
    specialists = build_default_specialists(benchmark_config)
    cases = build_cases(config)
    records: list[dict[str, Any]] = []
    # console.log: record false-positive experiment execution start.
    console_log("experiment.false_positive.start", f"running {len(cases)} trap cases")
    for case in cases:
        results = run_all_systems(benchmark_config, case, specialists)
        for system in ALL_COMPARISON_SYSTEMS:
            records.append(_record(EXPERIMENT_NAME, case, system, results[system]))
    metrics = summarize(records, config)
    trace_path = output_root / "traces" / f"{EXPERIMENT_NAME}.jsonl"
    metrics_path = output_root / "metrics" / f"{EXPERIMENT_NAME}.json"
    _write_jsonl(trace_path, records)
    _write_json(metrics_path, metrics)
    # console.log: record false-positive experiment completion.
    console_log("experiment.false_positive.complete", "experiment completed")
    return {"records": records, "metrics": metrics}


if __name__ == "__main__":
    run_experiment()

