"""Build the Phase 5 MAVS-GC synthetic benchmark report."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.types import console_log
from src.metrics.plots import write_phase5_figures
from src.metrics.summaries import (
    EXPERIMENT_LABELS,
    EXPERIMENT_ORDER,
    SYSTEM_LABELS,
    SYSTEM_ORDER,
    build_headline_findings,
    build_summary_tables,
    hash_file,
    relative_path,
    source_artifact_inventory,
    write_summary_tables,
)

REPORT_FILENAME = "chapter_9_report.md"
MANIFEST_FILENAME = "run_manifest.json"
CHART_MAP_COLUMNS = [
    "figure_id",
    "title",
    "path",
    "source_table",
    "source_fields",
    "question",
    "takeaway",
]


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _number(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _common_artifact_root(output_root: Path, docs_dir: Path, repo_root: Path) -> Path:
    try:
        import os

        paths = [str(output_root.resolve()), str(docs_dir.resolve())]
        if all(path.lower().startswith(str(repo_root.resolve()).lower()) for path in paths):
            return repo_root.resolve()
        return Path(os.path.commonpath(paths))
    except ValueError:
        return output_root.resolve().parent


def _link_from_docs(target: Path, docs_dir: Path) -> str:
    try:
        return target.resolve().relative_to(docs_dir.resolve()).as_posix()
    except ValueError:
        import os

        return Path(os.path.relpath(target.resolve(), docs_dir.resolve())).as_posix()


def _markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(key, "")) for key, _ in columns) + " |")
    return "\n".join([header, divider, *body])


def _classification_rows_for_report(tables: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for row in tables["classification_summary"]:
        rows.append(
            {
                "Experiment": row["experiment_label"],
                "System": row["system_label"],
                "Accuracy": _percent(float(row["accuracy"])),
                "Rejection": _percent(float(row["rejection_rate"])),
                "Unsafe acceptance": _percent(float(row["unsafe_acceptance_rate"])),
            }
        )
    return rows


def _governance_rows_for_report(tables: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for row in tables["governance_summary"]:
        if row["system"] != "pure_mavs_gc":
            continue
        rows.append(
            {
                "Experiment": row["experiment_label"],
                "Severity mean": _number(row["severity_mean"]),
                "Threshold mean": _number(row["threshold_mean"]),
                "Consensus mean": _number(row["consensus_mean"]),
                "Mitigation mean": _number(row["mitigation_mean"]),
                "Hard veto rate": _percent(float(row["hard_veto_rate"])),
            }
        )
    return rows


def write_chart_map(figures: list[dict[str, Any]], tables_dir: Path, artifact_root: Path) -> Path:
    path = tables_dir / "chart_map.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CHART_MAP_COLUMNS)
        writer.writeheader()
        for figure in figures:
            row = dict(figure)
            row["path"] = relative_path(Path(row["path"]), artifact_root)
            writer.writerow(row)
    # console.log: record Phase 5 chart-map artifact write.
    console_log("report.chart_map.write", f"wrote chart map to {path}")
    return path


def build_report_markdown(
    tables: dict[str, list[dict[str, Any]]],
    figures: list[dict[str, Any]],
    table_paths: dict[str, Path],
    chart_map_path: Path,
    manifest_path: Path,
    docs_dir: Path,
) -> str:
    findings = build_headline_findings(tables)
    trap = findings["false_positive_trap"]
    veto = findings["mitigation_veto"]
    traceability = findings["traceability"]
    figure_by_id = {figure["figure_id"]: figure for figure in figures}

    def figure_markdown(figure_id: str) -> str:
        figure = figure_by_id[figure_id]
        link = _link_from_docs(Path(figure["path"]), docs_dir)
        return f"![{figure['title']}]({link})"

    classification_table = _markdown_table(
        _classification_rows_for_report(tables),
        [
            ("Experiment", "Experiment"),
            ("System", "System"),
            ("Accuracy", "Accuracy"),
            ("Rejection", "Rejection"),
            ("Unsafe acceptance", "Unsafe acceptance"),
        ],
    )
    governance_table = _markdown_table(
        _governance_rows_for_report(tables),
        [
            ("Experiment", "Experiment"),
            ("Severity mean", "Severity mean"),
            ("Threshold mean", "Threshold mean"),
            ("Consensus mean", "Consensus mean"),
            ("Mitigation mean", "Mitigation mean"),
            ("Hard veto rate", "Hard veto rate"),
        ],
    )

    table_links = {
        name: _link_from_docs(path, docs_dir)
        for name, path in sorted(table_paths.items())
    }
    chart_map_link = _link_from_docs(chart_map_path, docs_dir)
    manifest_link = _link_from_docs(manifest_path, docs_dir)

    # console.log: record Phase 5 report markdown rendering.
    console_log("report.markdown.render", "rendered report markdown from generated tables")
    return f"""# Chapter 9 Synthetic Benchmark Report

## Technical Summary

This report summarizes the deterministic synthetic benchmark outputs generated for the MAVS-GC Chapter 9 program. The evidence is bounded to synthetic specialists, synthetic cases, and the configured comparison systems; it does not establish real-world model performance.

- In the false-positive trap, pure MAVS-GC accepted {_percent(float(trap['pure_mavs_gc_unsafe_acceptance_rate']))} of unsafe records, compared with {_percent(float(trap['mean_unsafe_acceptance_rate']))} for the mean ensemble and {_percent(float(trap['static_weighted_unsafe_acceptance_rate']))} for the static weighted ensemble. Veto MAVS accepted {_percent(float(trap['veto_mavs_unsafe_acceptance_rate']))} under its direct red-flag rule.
- Pure MAVS-GC hard-veto behavior rejected {veto['hard_veto_rejection_count']} of {veto['hard_veto_count']} hard-veto-active mitigation-veto traces, a {_percent(float(veto['hard_veto_compliance_rate']))} compliance rate in the generated evidence.
- Trace completeness is {_percent(float(traceability['minimum_trace_completeness_rate']))} across {traceability['total_trace_records']} generated trace records, using full MAVS-GC field requirements for pure MAVS-GC and explicit reduced trace requirements for baselines.
- The classification results show a safety-pressure tradeoff in the synthetic program: governance-heavy systems reduce unsafe acceptance in trap conditions but reject more truth=1 cases in mitigation-veto settings.

## Key Findings With Visual Evidence

### Acceptance and rejection behavior separate the comparison systems

The acceptance-rate chart shows how often each system accepted records under the three synthetic tests. This is a descriptive comparison of configured systems under controlled synthetic inputs, not a claim about deployment performance.

{figure_markdown('acceptance_rate_by_experiment')}

### Unsafe acceptance concentrates in the false-positive trap

The unsafe-acceptance chart isolates truth=0 cases accepted by each system. In the false-positive trap, the mean and static weighted ensembles accept many unsafe high-confidence cases, while pure MAVS-GC escalates threshold pressure and Veto MAVS applies a direct red-flag rejection rule.

{figure_markdown('unsafe_acceptance_by_experiment')}

### Pure MAVS-GC exposes governance pressure as traceable quantities

The governance-pressure chart reports mean severity, threshold, consensus, and mitigation for pure MAVS-GC. These quantities correspond to the formal trace semantics: diagnostics feed severity, severity and mitigation determine threshold pressure, and consensus remains separately auditable.

{figure_markdown('pure_mavs_gc_governance_pressure')}

### Decision variance distinguishes mixed behavior from consistent rejection

Decision variance is highest when a system has mixed accept/reject behavior and lower when decisions concentrate on one outcome. This metric supports stability inspection, but it is not a quality score by itself.

{figure_markdown('decision_variance_by_experiment')}

### Hard-veto-active traces reject under the generated evidence

The hard-veto chart compares hard-veto-active pure MAVS-GC records with the number rejected. Matching bars indicate that the hard-veto dominance invariant is preserved in these generated traces.

{figure_markdown('hard_veto_compliance')}

## Scope, Data, and Metric Definitions

The benchmark uses three deterministic synthetic experiments:

- Specialist disagreement: low, medium, and high disagreement regimes.
- False positive trap: unsafe high-confidence consensus cases.
- Mitigation versus hard veto: corruption and mitigation grid cases with hard-veto boundary pressure.

Comparison systems are mean ensemble, static weighted ensemble, Veto MAVS, and pure MAVS-GC. Pure MAVS-GC is the only system that emits the full governance trace containing diagnostics, severity, weights, mitigation, threshold, consensus, policy reason, hard-veto status, and final decision.

Metric definitions are generated in [{table_links['metric_definitions']}]({table_links['metric_definitions']}), and all result tables are generated from `results/metrics/*.json` and `results/traces/*.jsonl`.

## Results Tables

### Classification Summary

{classification_table}

Source table: [{table_links['classification_summary']}]({table_links['classification_summary']}).

### Pure MAVS-GC Governance Summary

{governance_table}

Source table: [{table_links['governance_summary']}]({table_links['governance_summary']}).

Additional generated tables:

- Grouped acceptance: [{table_links['grouped_acceptance']}]({table_links['grouped_acceptance']}).
- Stability summary: [{table_links['stability_summary']}]({table_links['stability_summary']}).
- Hard-veto compliance: [{table_links['hard_veto_compliance']}]({table_links['hard_veto_compliance']}).
- Trace completeness: [{table_links['trace_completeness']}]({table_links['trace_completeness']}).
- Reproducibility: [{table_links['reproducibility']}]({table_links['reproducibility']}).
- Chart map: [{chart_map_link}]({chart_map_link}).

## Methodology and Traceability

Each experiment is generated from its configuration file and fixed seed. Every comparison system evaluates the same synthetic cases and the same all-speak specialist outputs. Baseline traces intentionally remain reduced to their stated decision rules, while pure MAVS-GC traces include the full governance state required by the formal definition.

The run manifest records source hashes, generated artifacts, source hierarchy, seeds, table paths, figure paths, and report-generation scope: [{manifest_link}]({manifest_link}).

## Limitations, Uncertainty, and Robustness Checks

The specialists, case distributions, corruption levels, and mitigation levels are synthetic. The benchmark is appropriate for checking implementation semantics, reproducibility, trace completeness, and controlled failure-mode behavior. It is not evidence that any system will perform better on real-world tasks.

The current experiments also use fixed decision thresholds and fixed synthetic specialist definitions. Future runs should vary governance constants, specialist reliability priors, corruption distributions, and mitigation reliability to test sensitivity before making broader claims.

Robustness checks performed in this phase include automatic report regeneration, source-data checks for every table and figure, metric-definition coverage, trace-completeness checks, and deterministic stress replay of the report builder.

## Recommended Next Steps

1. Add parameter sweeps for `theta_0`, `lambda`, `delta`, and `tau_hard` to test governance sensitivity.
2. Add ablations for each diagnostic flag to measure which governance components drive threshold pressure.
3. Extend the report generator with optional appendix tables once larger stress outputs are promoted from temporary artifacts to stored benchmark outputs.

## Further Questions

- Which diagnostic flags dominate severity under each synthetic failure mode?
- How sensitive are false positives and false negatives to the hard-veto boundary?
- How should synthetic mitigation reliability be varied to separate useful mitigation from unsafe threshold relaxation?
"""


def _validate_metric_definitions(tables: dict[str, list[dict[str, Any]]]) -> None:
    defined = {row["metric"] for row in tables["metric_definitions"]}
    required = {
        "accuracy",
        "false_positive_rate",
        "false_negative_rate",
        "rejection_rate",
        "unsafe_acceptance_rate",
        "severity_mean",
        "threshold_mean",
        "mitigation_mean",
        "consensus_mean",
        "decision_variance",
        "hard_veto_compliance_rate",
        "trace_completeness_rate",
    }
    missing = sorted(required - defined)
    if missing:
        raise ValueError(f"missing metric definitions: {missing}")
    # console.log: record metric-definition coverage validation.
    console_log("report.metrics.validate", f"validated {len(required)} metric definitions")


def validate_report(report_path: Path, figures: list[dict[str, Any]], table_paths: dict[str, Path]) -> None:
    text = report_path.read_text(encoding="utf-8")
    required_sections = [
        "## Technical Summary",
        "## Key Findings With Visual Evidence",
        "## Scope, Data, and Metric Definitions",
        "## Results Tables",
        "## Methodology and Traceability",
        "## Limitations, Uncertainty, and Robustness Checks",
        "## Recommended Next Steps",
        "## Further Questions",
    ]
    missing_sections = [section for section in required_sections if section not in text]
    if missing_sections:
        raise ValueError(f"report missing sections: {missing_sections}")
    prohibited = ["proves superiority", "real-world superiority", "guarantees superior"]
    found = [phrase for phrase in prohibited if phrase in text.lower()]
    if found:
        raise ValueError(f"unsupported claim phrase found: {found}")
    for figure in figures:
        if not Path(figure["path"]).exists():
            raise FileNotFoundError(figure["path"])
    for path in table_paths.values():
        if not path.exists():
            raise FileNotFoundError(path)
    # console.log: record final report validation.
    console_log("report.validate", f"validated report {report_path}")


def _generated_file_records(
    files: list[Path],
    artifact_root: Path,
) -> list[dict[str, Any]]:
    records = []
    for path in sorted(files, key=lambda candidate: str(candidate)):
        records.append(
            {
                "path": relative_path(path, artifact_root),
                "sha256": hash_file(path),
                "bytes": path.stat().st_size,
            }
        )
    return records


def write_manifest(
    manifest_path: Path,
    report_path: Path,
    table_paths: dict[str, Path],
    figures: list[dict[str, Any]],
    chart_map_path: Path,
    source_results_root: Path,
    repo_root: Path,
    artifact_root: Path,
) -> dict[str, Any]:
    generated_files = [report_path, chart_map_path, *table_paths.values()]
    generated_files.extend(Path(figure["path"]) for figure in figures)
    manifest = {
        "manifest_version": "phase5.v1",
        "generated_date": "2026-06-18",
        "scope": "controlled synthetic benchmark report generation",
        "source_hierarchy": [
            "MAVS-GC Formal Definition",
            "Foundation Arc Chapters 1-8",
            "Chapter 9 Synthetic Benchmark Program",
        ],
        "source_results_root": relative_path(source_results_root, repo_root),
        "report_path": relative_path(report_path, artifact_root),
        "generated_files": _generated_file_records(generated_files, artifact_root),
        "source_artifacts": source_artifact_inventory(repo_root),
        "tables": {
            name: relative_path(path, artifact_root)
            for name, path in sorted(table_paths.items())
        },
        "figures": [
            {
                **figure,
                "path": relative_path(Path(figure["path"]), artifact_root),
            }
            for figure in figures
        ],
        "claim_boundary": "Results are controlled synthetic evidence only.",
        "reproducibility_command": "python scripts/generate_report.py",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    # console.log: record Phase 5 manifest write.
    console_log("report.manifest.write", f"wrote run manifest to {manifest_path}")
    return manifest


def generate_report(
    source_results_root: Path = ROOT / "results",
    output_root: Path = ROOT / "results",
    docs_dir: Path = ROOT / "docs",
    repo_root: Path = ROOT,
) -> dict[str, Any]:
    # console.log: record Phase 5 report generation start.
    console_log("report.start", "starting Phase 5 report generation")
    artifact_root = _common_artifact_root(output_root, docs_dir, repo_root)
    tables = build_summary_tables(source_results_root, repo_root)
    _validate_metric_definitions(tables)
    table_paths = write_summary_tables(tables, output_root / "tables")
    figures = write_phase5_figures(tables, output_root / "figures")
    chart_map_path = write_chart_map(figures, output_root / "tables", artifact_root)
    manifest_path = output_root / MANIFEST_FILENAME
    docs_dir.mkdir(parents=True, exist_ok=True)
    report_path = docs_dir / REPORT_FILENAME
    report_path.write_text(
        build_report_markdown(tables, figures, table_paths, chart_map_path, manifest_path, docs_dir),
        encoding="utf-8",
    )
    # console.log: record Phase 5 report artifact write.
    console_log("report.write", f"wrote report to {report_path}")
    manifest = write_manifest(
        manifest_path,
        report_path,
        table_paths,
        figures,
        chart_map_path,
        source_results_root,
        repo_root,
        artifact_root,
    )
    validate_report(report_path, figures, table_paths)
    # console.log: record Phase 5 report generation completion.
    console_log("report.complete", "completed Phase 5 report generation")
    return {
        "report_path": report_path,
        "manifest_path": manifest_path,
        "table_paths": table_paths,
        "figures": figures,
        "chart_map_path": chart_map_path,
        "manifest": manifest,
    }


if __name__ == "__main__":
    generate_report()
