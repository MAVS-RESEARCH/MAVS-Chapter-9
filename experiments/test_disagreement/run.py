"""Synthetic Test 1: specialist disagreement."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.baselines.runner import ALL_COMPARISON_SYSTEMS, run_all_systems
from src.core.case_generator import SyntheticCaseGenerator
from src.core.config import BenchmarkConfig
from src.core.types import SyntheticCase, console_log
from src.metrics.classification import classification_by_system
from src.metrics.governance import acceptance_by_group, governance_by_system
from src.metrics.stability import stability_by_system
from src.specialists.synthetic import build_default_specialists

CONFIG_PATH = Path(__file__).with_name("config.yaml")
EXPERIMENT_NAME = "test_disagreement"


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    # console.log: record disagreement experiment config load.
    console_log("experiment.disagreement.config", f"loaded config from {path}")
    return config


def _record(experiment: str, case: SyntheticCase, system: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment": experiment,
        "system": system,
        "case_id": result["case"]["case_id"],
        "truth": result["case"]["truth"],
        "decision": result["decision"],
        "case_metadata": {
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
    # console.log: record disagreement trace output write.
    console_log("experiment.disagreement.traces", f"wrote {len(records)} records to {path}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    # console.log: record disagreement metric output write.
    console_log("experiment.disagreement.metrics", f"wrote metrics to {path}")


def build_cases(config: dict[str, Any], benchmark_config: BenchmarkConfig) -> list[SyntheticCase]:
    generator = SyntheticCaseGenerator(benchmark_config)
    count_per_regime = int(config["count_per_regime"])
    regimes = list(config["regimes"])
    cases: list[SyntheticCase] = []
    index = 0
    for regime in regimes:
        for _ in range(count_per_regime):
            cases.append(generator.generate_case(index, regime))
            index += 1
    # console.log: record disagreement case construction.
    console_log("experiment.disagreement.cases", f"built {len(cases)} cases")
    return cases


def summarize(records: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    metrics = {
        "experiment": EXPERIMENT_NAME,
        "config": config,
        "record_count": len(records),
        "classification_by_system": classification_by_system(records),
        "governance_by_system": governance_by_system(records),
        "stability_by_system": stability_by_system(records),
        "acceptance_by_disagreement_regime": acceptance_by_group(records, "disagreement_regime"),
    }
    # console.log: record disagreement summary construction.
    console_log("experiment.disagreement.summary", "computed disagreement experiment metrics")
    return metrics


def run_experiment(
    config_path: Path = CONFIG_PATH,
    output_root: Path = ROOT / "results",
) -> dict[str, Any]:
    config = load_config(config_path)
    case_count = int(config["count_per_regime"]) * len(config["regimes"])
    benchmark_config = BenchmarkConfig(seed=int(config["seed"]), case_count=case_count)
    specialists = build_default_specialists(benchmark_config)
    cases = build_cases(config, benchmark_config)
    records: list[dict[str, Any]] = []
    # console.log: record disagreement experiment execution start.
    console_log("experiment.disagreement.start", f"running {len(cases)} cases")
    for case in cases:
        results = run_all_systems(benchmark_config, case, specialists)
        for system in ALL_COMPARISON_SYSTEMS:
            records.append(_record(EXPERIMENT_NAME, case, system, results[system]))
    metrics = summarize(records, config)
    trace_path = output_root / "traces" / f"{EXPERIMENT_NAME}.jsonl"
    metrics_path = output_root / "metrics" / f"{EXPERIMENT_NAME}.json"
    _write_jsonl(trace_path, records)
    _write_json(metrics_path, metrics)
    # console.log: record disagreement experiment completion.
    console_log("experiment.disagreement.complete", "experiment completed")
    return {"records": records, "metrics": metrics}


if __name__ == "__main__":
    run_experiment()

