"""Phase 5 summary tables and reproducibility helpers."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Any

from src.core.types import console_log

EXPERIMENT_ORDER = [
    "test_disagreement",
    "test_false_positive_trap",
    "test_mitigation_veto",
]

EXPERIMENT_LABELS = {
    "test_disagreement": "Specialist disagreement",
    "test_false_positive_trap": "False positive trap",
    "test_mitigation_veto": "Mitigation versus hard veto",
}

SYSTEM_ORDER = [
    "mean_ensemble",
    "static_weighted_ensemble",
    "veto_mavs",
    "pure_mavs_gc",
]

SYSTEM_LABELS = {
    "mean_ensemble": "Mean ensemble",
    "static_weighted_ensemble": "Static weighted ensemble",
    "veto_mavs": "Veto MAVS",
    "pure_mavs_gc": "Pure MAVS-GC",
}

METRIC_DEFINITIONS = [
    {
        "metric": "accuracy",
        "definition": "Share of records where the binary decision equals the synthetic truth label.",
        "denominator": "Records for one experiment and one comparison system.",
    },
    {
        "metric": "false_positive_rate",
        "definition": "Share of unsafe truth=0 cases that were accepted.",
        "denominator": "Unsafe truth=0 records for one experiment and one comparison system.",
    },
    {
        "metric": "false_negative_rate",
        "definition": "Share of safe truth=1 cases that were rejected.",
        "denominator": "Safe truth=1 records for one experiment and one comparison system.",
    },
    {
        "metric": "rejection_rate",
        "definition": "Share of records rejected by the system.",
        "denominator": "Records for one experiment and one comparison system.",
    },
    {
        "metric": "unsafe_acceptance_rate",
        "definition": "Share of all records where an unsafe truth=0 case was accepted.",
        "denominator": "Records for one experiment and one comparison system.",
    },
    {
        "metric": "severity_mean",
        "definition": "Mean MAVS-GC diagnostic severity after aggregating nonnegative diagnostic flags.",
        "denominator": "Pure MAVS-GC records with severity fields.",
    },
    {
        "metric": "threshold_mean",
        "definition": "Mean governed threshold after severity pressure and mitigation evidence are applied.",
        "denominator": "Pure MAVS-GC records with threshold fields.",
    },
    {
        "metric": "mitigation_mean",
        "definition": "Mean bounded mitigation evidence emitted by the synthetic organ.",
        "denominator": "Pure MAVS-GC records with mitigation fields.",
    },
    {
        "metric": "consensus_mean",
        "definition": "Mean governed consensus R=sum_i(w_i*r_i).",
        "denominator": "Pure MAVS-GC records with consensus fields.",
    },
    {
        "metric": "decision_variance",
        "definition": "Bernoulli variance of accept/reject decisions for one system.",
        "denominator": "Records for one experiment and one comparison system.",
    },
    {
        "metric": "hard_veto_compliance_rate",
        "definition": "Share of hard-veto-active pure MAVS-GC records that were rejected.",
        "denominator": "Pure MAVS-GC records with hard_veto_active=true.",
    },
    {
        "metric": "trace_completeness_rate",
        "definition": "Share of trace records containing the fields required for that system type.",
        "denominator": "Trace records for one experiment and one comparison system.",
    },
]

TABLE_COLUMNS = {
    "classification_summary": [
        "experiment",
        "experiment_label",
        "system",
        "system_label",
        "count",
        "accuracy",
        "false_positive_rate",
        "false_negative_rate",
        "rejection_rate",
        "acceptance_rate",
        "unsafe_acceptance_rate",
        "source_metric_file",
        "source_metric_key",
    ],
    "governance_summary": [
        "experiment",
        "experiment_label",
        "system",
        "system_label",
        "severity_mean",
        "severity_min",
        "severity_max",
        "threshold_mean",
        "threshold_min",
        "threshold_max",
        "mitigation_mean",
        "consensus_mean",
        "hard_veto_count",
        "hard_veto_rate",
        "source_metric_file",
        "source_metric_key",
    ],
    "stability_summary": [
        "experiment",
        "experiment_label",
        "system",
        "system_label",
        "decision_variance",
        "score_or_consensus_stddev",
        "score_or_consensus_range",
        "consensus_stability_index",
        "source_metric_file",
        "source_metric_key",
    ],
    "grouped_acceptance": [
        "experiment",
        "experiment_label",
        "grouping",
        "group_value",
        "system",
        "system_label",
        "count",
        "accepted",
        "acceptance_rate",
        "source_metric_file",
        "source_metric_key",
    ],
    "hard_veto_compliance": [
        "experiment",
        "experiment_label",
        "hard_veto_count",
        "hard_veto_rejection_count",
        "hard_veto_compliance_rate",
        "source_trace_file",
        "source_trace_key",
    ],
    "trace_completeness": [
        "experiment",
        "experiment_label",
        "system",
        "system_label",
        "record_count",
        "complete_count",
        "incomplete_count",
        "trace_completeness_rate",
        "missing_field_counts",
        "source_trace_file",
        "source_trace_key",
    ],
    "reproducibility": [
        "experiment",
        "experiment_label",
        "seed",
        "config_path",
        "metric_path",
        "trace_path",
        "metric_sha256",
        "trace_sha256",
        "record_count",
        "systems",
    ],
    "metric_definitions": [
        "metric",
        "definition",
        "denominator",
    ],
}


def relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_metrics(metrics_dir: Path, repo_root: Path) -> dict[str, dict[str, Any]]:
    metrics: dict[str, dict[str, Any]] = {}
    for path in sorted(metrics_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        experiment = str(payload["experiment"])
        payload["_source_metric_file"] = relative_path(path, repo_root)
        payload["_source_metric_hash"] = hash_file(path)
        metrics[experiment] = payload
    missing = [name for name in EXPERIMENT_ORDER if name not in metrics]
    if missing:
        raise FileNotFoundError(f"missing metric outputs: {missing}")
    # console.log: record Phase 5 metric-source loading.
    console_log("summary.metrics.load", f"loaded {len(metrics)} metric files")
    return {name: metrics[name] for name in EXPERIMENT_ORDER}


def load_traces(traces_dir: Path, repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    traces: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(traces_dir.glob("*.jsonl")):
        experiment = path.stem
        records = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for record in records:
            record["_source_trace_file"] = relative_path(path, repo_root)
            record["_source_trace_hash"] = hash_file(path)
        traces[experiment] = records
    missing = [name for name in EXPERIMENT_ORDER if name not in traces]
    if missing:
        raise FileNotFoundError(f"missing trace outputs: {missing}")
    # console.log: record Phase 5 trace-source loading.
    console_log("summary.traces.load", f"loaded {len(traces)} trace files")
    return {name: traces[name] for name in EXPERIMENT_ORDER}


def _value_at(payload: dict[str, Any], dotted_key: str) -> Any:
    current: Any = payload
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _distribution_value(metrics: dict[str, Any], system: str, distribution: str, field: str) -> Any:
    return metrics["governance_by_system"][system][distribution].get(field)


def build_classification_table(metrics_by_experiment: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for experiment, metrics in metrics_by_experiment.items():
        for system in SYSTEM_ORDER:
            summary = metrics["classification_by_system"][system]
            rows.append(
                {
                    "experiment": experiment,
                    "experiment_label": EXPERIMENT_LABELS[experiment],
                    "system": system,
                    "system_label": SYSTEM_LABELS[system],
                    "count": summary["count"],
                    "accuracy": summary["accuracy"],
                    "false_positive_rate": summary["false_positive_rate"],
                    "false_negative_rate": summary["false_negative_rate"],
                    "rejection_rate": summary["rejection_rate"],
                    "acceptance_rate": 1.0 - float(summary["rejection_rate"]),
                    "unsafe_acceptance_rate": summary["unsafe_acceptance_rate"],
                    "source_metric_file": metrics["_source_metric_file"],
                    "source_metric_key": f"classification_by_system.{system}",
                }
            )
    # console.log: record Phase 5 classification table construction.
    console_log("summary.table.classification", f"built {len(rows)} rows")
    return rows


def build_governance_table(metrics_by_experiment: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for experiment, metrics in metrics_by_experiment.items():
        for system in SYSTEM_ORDER:
            rows.append(
                {
                    "experiment": experiment,
                    "experiment_label": EXPERIMENT_LABELS[experiment],
                    "system": system,
                    "system_label": SYSTEM_LABELS[system],
                    "severity_mean": _distribution_value(metrics, system, "severity_distribution", "mean"),
                    "severity_min": _distribution_value(metrics, system, "severity_distribution", "min"),
                    "severity_max": _distribution_value(metrics, system, "severity_distribution", "max"),
                    "threshold_mean": _distribution_value(metrics, system, "threshold_distribution", "mean"),
                    "threshold_min": _distribution_value(metrics, system, "threshold_distribution", "min"),
                    "threshold_max": _distribution_value(metrics, system, "threshold_distribution", "max"),
                    "mitigation_mean": _distribution_value(metrics, system, "mitigation_distribution", "mean"),
                    "consensus_mean": _distribution_value(metrics, system, "consensus_distribution", "mean"),
                    "hard_veto_count": metrics["governance_by_system"][system]["hard_veto_count"],
                    "hard_veto_rate": metrics["governance_by_system"][system]["hard_veto_rate"],
                    "source_metric_file": metrics["_source_metric_file"],
                    "source_metric_key": f"governance_by_system.{system}",
                }
            )
    # console.log: record Phase 5 governance table construction.
    console_log("summary.table.governance", f"built {len(rows)} rows")
    return rows


def build_stability_table(metrics_by_experiment: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for experiment, metrics in metrics_by_experiment.items():
        for system in SYSTEM_ORDER:
            summary = metrics["stability_by_system"][system]
            rows.append(
                {
                    "experiment": experiment,
                    "experiment_label": EXPERIMENT_LABELS[experiment],
                    "system": system,
                    "system_label": SYSTEM_LABELS[system],
                    "decision_variance": summary["decision_variance"],
                    "score_or_consensus_stddev": summary["score_or_consensus_stddev"],
                    "score_or_consensus_range": summary["score_or_consensus_range"],
                    "consensus_stability_index": summary["consensus_stability_index"],
                    "source_metric_file": metrics["_source_metric_file"],
                    "source_metric_key": f"stability_by_system.{system}",
                }
            )
    # console.log: record Phase 5 stability table construction.
    console_log("summary.table.stability", f"built {len(rows)} rows")
    return rows


def _group_metric_names(metrics: dict[str, Any]) -> list[str]:
    return sorted(
        key
        for key, value in metrics.items()
        if key.startswith("acceptance_by_") and isinstance(value, dict)
    )


def build_grouped_acceptance_table(metrics_by_experiment: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for experiment, metrics in metrics_by_experiment.items():
        for metric_name in _group_metric_names(metrics):
            grouping = metric_name.removeprefix("acceptance_by_")
            for group_value, by_system in sorted(metrics[metric_name].items()):
                for system in SYSTEM_ORDER:
                    if system not in by_system:
                        continue
                    summary = by_system[system]
                    rows.append(
                        {
                            "experiment": experiment,
                            "experiment_label": EXPERIMENT_LABELS[experiment],
                            "grouping": grouping,
                            "group_value": group_value,
                            "system": system,
                            "system_label": SYSTEM_LABELS[system],
                            "count": summary["count"],
                            "accepted": summary["accepted"],
                            "acceptance_rate": summary["acceptance_rate"],
                            "source_metric_file": metrics["_source_metric_file"],
                            "source_metric_key": f"{metric_name}.{group_value}.{system}",
                        }
                    )
    # console.log: record Phase 5 grouped acceptance table construction.
    console_log("summary.table.grouped_acceptance", f"built {len(rows)} rows")
    return rows


def _required_trace_fields(system: str) -> list[str]:
    required = [
        "experiment",
        "system",
        "case_id",
        "truth",
        "decision",
        "case_metadata",
        "result.trace_id",
        "result.case",
        "result.config",
        "result.specialist_scores",
        "result.supports",
        "result.decision",
    ]
    if system == "pure_mavs_gc":
        required.extend(
            [
                "result.diagnostics",
                "result.severity",
                "result.weights",
                "result.mitigation",
                "result.threshold",
                "result.consensus",
                "result.metadata",
            ]
        )
    else:
        required.extend(["result.score", "result.cutoff", "result.metadata"])
    return required


def _missing_trace_fields(record: dict[str, Any], system: str) -> list[str]:
    missing: list[str] = []
    for field in _required_trace_fields(system):
        if _value_at(record, field) is None:
            missing.append(field)
    return missing


def build_trace_completeness_table(traces_by_experiment: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for experiment, records in traces_by_experiment.items():
        by_system: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            by_system[str(record["system"])].append(record)
        for system in SYSTEM_ORDER:
            system_records = by_system[system]
            missing_counts: dict[str, int] = defaultdict(int)
            complete_count = 0
            for record in system_records:
                missing = _missing_trace_fields(record, system)
                if missing:
                    for field in missing:
                        missing_counts[field] += 1
                else:
                    complete_count += 1
            missing_field_counts = "; ".join(
                f"{field}:{count}" for field, count in sorted(missing_counts.items())
            )
            source_file = system_records[0]["_source_trace_file"] if system_records else ""
            rows.append(
                {
                    "experiment": experiment,
                    "experiment_label": EXPERIMENT_LABELS[experiment],
                    "system": system,
                    "system_label": SYSTEM_LABELS[system],
                    "record_count": len(system_records),
                    "complete_count": complete_count,
                    "incomplete_count": len(system_records) - complete_count,
                    "trace_completeness_rate": complete_count / len(system_records) if system_records else 0.0,
                    "missing_field_counts": missing_field_counts,
                    "source_trace_file": source_file,
                    "source_trace_key": f"{experiment}.{system}",
                }
            )
    # console.log: record Phase 5 trace-completeness table construction.
    console_log("summary.table.trace_completeness", f"built {len(rows)} rows")
    return rows


def build_hard_veto_compliance_table(traces_by_experiment: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for experiment, records in traces_by_experiment.items():
        pure_records = [record for record in records if record["system"] == "pure_mavs_gc"]
        hard_veto_records = [
            record
            for record in pure_records
            if record["result"].get("metadata", {}).get("hard_veto_active")
        ]
        rejection_count = sum(1 for record in hard_veto_records if not record["result"]["decision"])
        source_file = pure_records[0]["_source_trace_file"] if pure_records else ""
        rows.append(
            {
                "experiment": experiment,
                "experiment_label": EXPERIMENT_LABELS[experiment],
                "hard_veto_count": len(hard_veto_records),
                "hard_veto_rejection_count": rejection_count,
                "hard_veto_compliance_rate": rejection_count / len(hard_veto_records)
                if hard_veto_records
                else 1.0,
                "source_trace_file": source_file,
                "source_trace_key": f"{experiment}.pure_mavs_gc.metadata.hard_veto_active",
            }
        )
    # console.log: record Phase 5 hard-veto compliance table construction.
    console_log("summary.table.hard_veto", f"built {len(rows)} rows")
    return rows


def build_reproducibility_table(
    metrics_by_experiment: dict[str, dict[str, Any]],
    traces_by_experiment: dict[str, list[dict[str, Any]]],
    repo_root: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for experiment, metrics in metrics_by_experiment.items():
        config_path = Path("experiments") / experiment / "config.yaml"
        source_trace_file = traces_by_experiment[experiment][0]["_source_trace_file"]
        rows.append(
            {
                "experiment": experiment,
                "experiment_label": EXPERIMENT_LABELS[experiment],
                "seed": metrics["config"].get("seed"),
                "config_path": config_path.as_posix(),
                "metric_path": metrics["_source_metric_file"],
                "trace_path": source_trace_file,
                "metric_sha256": metrics["_source_metric_hash"],
                "trace_sha256": hash_file(repo_root / source_trace_file),
                "record_count": metrics["record_count"],
                "systems": ",".join(SYSTEM_ORDER),
            }
        )
    # console.log: record Phase 5 reproducibility table construction.
    console_log("summary.table.reproducibility", f"built {len(rows)} rows")
    return rows


def build_metric_definition_table() -> list[dict[str, Any]]:
    rows = [dict(row) for row in METRIC_DEFINITIONS]
    # console.log: record Phase 5 metric-definition table construction.
    console_log("summary.table.metric_definitions", f"built {len(rows)} rows")
    return rows


def build_summary_tables(source_results_root: Path, repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    metrics = load_metrics(source_results_root / "metrics", repo_root)
    traces = load_traces(source_results_root / "traces", repo_root)
    tables = {
        "classification_summary": build_classification_table(metrics),
        "governance_summary": build_governance_table(metrics),
        "stability_summary": build_stability_table(metrics),
        "grouped_acceptance": build_grouped_acceptance_table(metrics),
        "hard_veto_compliance": build_hard_veto_compliance_table(traces),
        "trace_completeness": build_trace_completeness_table(traces),
        "reproducibility": build_reproducibility_table(metrics, traces, repo_root),
        "metric_definitions": build_metric_definition_table(),
    }
    validate_summary_tables(tables)
    # console.log: record Phase 5 complete summary table construction.
    console_log("summary.tables.complete", f"built {len(tables)} summary tables")
    return tables


def validate_summary_tables(tables: dict[str, list[dict[str, Any]]]) -> None:
    for table_name, rows in tables.items():
        if not rows:
            raise ValueError(f"{table_name} must be nonempty")
        expected_columns = TABLE_COLUMNS[table_name]
        for index, row in enumerate(rows):
            missing = [column for column in expected_columns if column not in row]
            if missing:
                raise ValueError(f"{table_name}[{index}] missing columns: {missing}")
            has_source_reference = any(
                key.startswith("source_") and str(row.get(key, "")).strip()
                for key in row
            )
            if table_name == "reproducibility":
                has_source_reference = bool(row.get("metric_path")) and bool(row.get("trace_path"))
            if table_name != "metric_definitions" and not has_source_reference:
                raise ValueError(f"{table_name}[{index}] has no source reference")
    # console.log: record Phase 5 table provenance validation.
    console_log("summary.tables.validate", f"validated {len(tables)} tables")


def write_summary_tables(tables: dict[str, list[dict[str, Any]]], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for table_name, rows in tables.items():
        path = output_dir / f"{table_name}.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=TABLE_COLUMNS[table_name], extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        paths[table_name] = path
    json_path = output_dir / "summary_tables.json"
    json_path.write_text(json.dumps(tables, indent=2, sort_keys=True), encoding="utf-8")
    paths["summary_tables"] = json_path
    # console.log: record Phase 5 table artifact writes.
    console_log("summary.tables.write", f"wrote {len(paths)} table artifacts to {output_dir}")
    return paths


def build_headline_findings(tables: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    classification = {
        (row["experiment"], row["system"]): row
        for row in tables["classification_summary"]
    }
    governance = {
        (row["experiment"], row["system"]): row
        for row in tables["governance_summary"]
    }
    trace_rows = tables["trace_completeness"]
    hard_veto = {
        row["experiment"]: row
        for row in tables["hard_veto_compliance"]
    }
    false_positive_key = ("test_false_positive_trap", "pure_mavs_gc")
    mean_false_positive_key = ("test_false_positive_trap", "mean_ensemble")
    static_false_positive_key = ("test_false_positive_trap", "static_weighted_ensemble")
    veto_false_positive_key = ("test_false_positive_trap", "veto_mavs")
    findings = {
        "false_positive_trap": {
            "pure_mavs_gc_unsafe_acceptance_rate": classification[false_positive_key]["unsafe_acceptance_rate"],
            "mean_unsafe_acceptance_rate": classification[mean_false_positive_key]["unsafe_acceptance_rate"],
            "static_weighted_unsafe_acceptance_rate": classification[static_false_positive_key]["unsafe_acceptance_rate"],
            "veto_mavs_unsafe_acceptance_rate": classification[veto_false_positive_key]["unsafe_acceptance_rate"],
            "pure_mavs_gc_mean_threshold": governance[false_positive_key]["threshold_mean"],
        },
        "mitigation_veto": {
            "hard_veto_count": hard_veto["test_mitigation_veto"]["hard_veto_count"],
            "hard_veto_rejection_count": hard_veto["test_mitigation_veto"]["hard_veto_rejection_count"],
            "hard_veto_compliance_rate": hard_veto["test_mitigation_veto"]["hard_veto_compliance_rate"],
        },
        "traceability": {
            "total_trace_records": sum(int(row["record_count"]) for row in trace_rows),
            "minimum_trace_completeness_rate": min(float(row["trace_completeness_rate"]) for row in trace_rows),
        },
        "classification": {
            experiment: {
                system: classification[(experiment, system)]["accuracy"]
                for system in SYSTEM_ORDER
            }
            for experiment in EXPERIMENT_ORDER
        },
    }
    # console.log: record Phase 5 headline finding derivation.
    console_log("summary.findings", "derived headline findings from summary tables")
    return findings


def source_artifact_inventory(repo_root: Path) -> list[dict[str, Any]]:
    source_paths = [
        Path("Workplan.md"),
        Path("Path.md"),
        Path("README.md"),
        Path("docs/baseline_definitions.md"),
        Path("experiments/test_disagreement/config.yaml"),
        Path("experiments/test_false_positive_trap/config.yaml"),
        Path("experiments/test_mitigation_veto/config.yaml"),
        Path("results/metrics/test_disagreement.json"),
        Path("results/metrics/test_false_positive_trap.json"),
        Path("results/metrics/test_mitigation_veto.json"),
        Path("results/traces/test_disagreement.jsonl"),
        Path("results/traces/test_false_positive_trap.jsonl"),
        Path("results/traces/test_mitigation_veto.jsonl"),
    ]
    inventory = []
    for path in source_paths:
        absolute_path = repo_root / path
        inventory.append(
            {
                "path": path.as_posix(),
                "sha256": hash_file(absolute_path) if absolute_path.exists() else None,
                "exists": absolute_path.exists(),
            }
        )
    # console.log: record Phase 5 source artifact inventory.
    console_log("summary.inventory", f"inventoried {len(inventory)} source artifacts")
    return inventory
