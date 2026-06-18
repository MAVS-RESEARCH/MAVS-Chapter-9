"""Deterministic SVG figures for the Phase 5 report."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from src.core.types import console_log
from src.metrics.summaries import EXPERIMENT_LABELS, EXPERIMENT_ORDER, SYSTEM_LABELS, SYSTEM_ORDER

PALETTE = {
    "mean_ensemble": "#2f5f8f",
    "static_weighted_ensemble": "#b17818",
    "veto_mavs": "#7c8f2f",
    "pure_mavs_gc": "#9b4f7f",
    "severity_mean": "#2f5f8f",
    "threshold_mean": "#b17818",
    "consensus_mean": "#7c8f2f",
    "mitigation_mean": "#9b4f7f",
    "hard_veto_count": "#2f5f8f",
    "hard_veto_rejection_count": "#7c8f2f",
}


def _format_number(value: float, percent: bool = False) -> str:
    if percent:
        return f"{value * 100:.0f}%"
    if abs(value) >= 10:
        return f"{value:.0f}"
    return f"{value:.2f}"


def _ordered_unique(values: list[str], preferred_order: list[str] | None = None) -> list[str]:
    seen = set()
    ordered = []
    if preferred_order:
        for value in preferred_order:
            if value in values and value not in seen:
                ordered.append(value)
                seen.add(value)
    for value in values:
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def _svg_text(x: float, y: float, text: str, size: int = 13, anchor: str = "start", weight: str = "400") -> str:
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="#1f2933">'
        f"{escape(text)}</text>"
    )


def _grouped_bar_svg(
    rows: list[dict[str, Any]],
    category_field: str,
    series_field: str,
    value_field: str,
    title: str,
    subtitle: str,
    y_label: str,
    category_order: list[str],
    series_order: list[str],
    category_labels: dict[str, str],
    series_labels: dict[str, str],
    percent: bool = False,
) -> str:
    if not rows:
        raise ValueError("chart rows must be nonempty")
    categories = _ordered_unique([str(row[category_field]) for row in rows], category_order)
    series = _ordered_unique([str(row[series_field]) for row in rows], series_order)
    values = {
        (str(row[category_field]), str(row[series_field])): float(row[value_field])
        for row in rows
        if row.get(value_field) is not None
    }
    if not values:
        raise ValueError(f"chart value field {value_field!r} has no numeric values")
    width = 1120
    height = 660
    left = 96
    right = 48
    top = 112
    bottom = 128
    chart_width = width - left - right
    chart_height = height - top - bottom
    max_value = max(values.values())
    y_max = 1.0 if percent else max(1.0, max_value * 1.15)
    tick_count = 5
    group_width = chart_width / max(len(categories), 1)
    bar_width = min(44.0, (group_width * 0.72) / max(len(series), 1))
    group_inner_width = bar_width * len(series)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        _svg_text(left, 42, title, size=24, weight="700"),
        _svg_text(left, 70, subtitle, size=14),
        _svg_text(22, top + chart_height / 2, y_label, size=13, anchor="middle"),
    ]
    for tick in range(tick_count + 1):
        value = y_max * tick / tick_count
        y = top + chart_height - (value / y_max) * chart_height
        parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{width - right}" y2="{y:.2f}" stroke="#e5e7eb" stroke-width="1"/>')
        parts.append(_svg_text(left - 12, y + 4, _format_number(value, percent), size=12, anchor="end"))
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_height}" stroke="#425466" stroke-width="1.2"/>')
    parts.append(f'<line x1="{left}" y1="{top + chart_height}" x2="{width - right}" y2="{top + chart_height}" stroke="#425466" stroke-width="1.2"/>')
    for category_index, category in enumerate(categories):
        group_x = left + category_index * group_width + (group_width - group_inner_width) / 2
        for series_index, series_name in enumerate(series):
            value = values.get((category, series_name), 0.0)
            bar_height = 0.0 if y_max == 0 else (value / y_max) * chart_height
            x = group_x + series_index * bar_width
            y = top + chart_height - bar_height
            color = PALETTE.get(series_name, "#2f5f8f")
            parts.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width - 4:.2f}" '
                f'height="{bar_height:.2f}" fill="{color}" rx="2"/>'
            )
            if bar_height > 18:
                parts.append(_svg_text(x + (bar_width - 4) / 2, y - 6, _format_number(value, percent), size=11, anchor="middle"))
        label = category_labels.get(category, category)
        parts.append(_svg_text(left + category_index * group_width + group_width / 2, top + chart_height + 30, label, size=12, anchor="middle"))
    legend_x = left
    legend_y = height - 56
    for index, series_name in enumerate(series):
        x = legend_x + index * 245
        color = PALETTE.get(series_name, "#2f5f8f")
        parts.append(f'<rect x="{x}" y="{legend_y - 12}" width="14" height="14" fill="{color}" rx="2"/>')
        parts.append(_svg_text(x + 22, legend_y, series_labels.get(series_name, series_name), size=12))
    parts.append("</svg>")
    return "\n".join(parts)


def _write_svg(path: Path, svg: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
    # console.log: record deterministic SVG artifact write.
    console_log("plots.write_svg", f"wrote {path}")


def _validate_figure_record(record: dict[str, Any]) -> None:
    required = ["figure_id", "title", "path", "source_table", "source_fields", "question", "takeaway"]
    missing = [field for field in required if not record.get(field)]
    if missing:
        raise ValueError(f"figure record missing fields: {missing}")
    if not Path(record["path"]).exists():
        raise FileNotFoundError(record["path"])
    # console.log: record chart-source validation for a generated figure.
    console_log("plots.figure.validate", f"validated {record['figure_id']}")


def write_phase5_figures(tables: dict[str, list[dict[str, Any]]], figures_dir: Path) -> list[dict[str, Any]]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    classification_rows = tables["classification_summary"]
    governance_rows = [row for row in tables["governance_summary"] if row["system"] == "pure_mavs_gc"]
    stability_rows = tables["stability_summary"]
    hard_veto_rows = tables["hard_veto_compliance"]

    acceptance_rows = [
        {
            "experiment": row["experiment"],
            "system": row["system"],
            "acceptance_rate": row["acceptance_rate"],
        }
        for row in classification_rows
    ]
    acceptance_path = figures_dir / "acceptance_rate_by_experiment.svg"
    _write_svg(
        acceptance_path,
        _grouped_bar_svg(
            acceptance_rows,
            "experiment",
            "system",
            "acceptance_rate",
            "Acceptance rate by experiment",
            "Accepted records divided by records for each system and synthetic test.",
            "Acceptance rate",
            EXPERIMENT_ORDER,
            SYSTEM_ORDER,
            EXPERIMENT_LABELS,
            SYSTEM_LABELS,
            percent=True,
        ),
    )

    unsafe_rows = [
        {
            "experiment": row["experiment"],
            "system": row["system"],
            "unsafe_acceptance_rate": row["unsafe_acceptance_rate"],
        }
        for row in classification_rows
    ]
    unsafe_path = figures_dir / "unsafe_acceptance_by_experiment.svg"
    _write_svg(
        unsafe_path,
        _grouped_bar_svg(
            unsafe_rows,
            "experiment",
            "system",
            "unsafe_acceptance_rate",
            "Unsafe acceptance by experiment",
            "Unsafe truth=0 acceptances divided by all records for each system and synthetic test.",
            "Unsafe acceptance",
            EXPERIMENT_ORDER,
            SYSTEM_ORDER,
            EXPERIMENT_LABELS,
            SYSTEM_LABELS,
            percent=True,
        ),
    )

    pressure_rows: list[dict[str, Any]] = []
    for row in governance_rows:
        for metric in ["severity_mean", "threshold_mean", "consensus_mean", "mitigation_mean"]:
            pressure_rows.append(
                {
                    "experiment": row["experiment"],
                    "metric": metric,
                    "value": row[metric],
                }
            )
    pressure_path = figures_dir / "pure_mavs_gc_governance_pressure.svg"
    _write_svg(
        pressure_path,
        _grouped_bar_svg(
            pressure_rows,
            "experiment",
            "metric",
            "value",
            "Pure MAVS-GC governance pressure",
            "Mean severity, governed threshold, consensus, and mitigation across synthetic tests.",
            "Mean value",
            EXPERIMENT_ORDER,
            ["severity_mean", "threshold_mean", "consensus_mean", "mitigation_mean"],
            EXPERIMENT_LABELS,
            {
                "severity_mean": "Severity",
                "threshold_mean": "Threshold",
                "consensus_mean": "Consensus",
                "mitigation_mean": "Mitigation",
            },
        ),
    )

    variance_rows = [
        {
            "experiment": row["experiment"],
            "system": row["system"],
            "decision_variance": row["decision_variance"],
        }
        for row in stability_rows
    ]
    variance_path = figures_dir / "decision_variance_by_experiment.svg"
    _write_svg(
        variance_path,
        _grouped_bar_svg(
            variance_rows,
            "experiment",
            "system",
            "decision_variance",
            "Decision variance by experiment",
            "Bernoulli variance of accept/reject outcomes for each comparison system.",
            "Decision variance",
            EXPERIMENT_ORDER,
            SYSTEM_ORDER,
            EXPERIMENT_LABELS,
            SYSTEM_LABELS,
        ),
    )

    hard_rows: list[dict[str, Any]] = []
    for row in hard_veto_rows:
        for metric in ["hard_veto_count", "hard_veto_rejection_count"]:
            hard_rows.append(
                {
                    "experiment": row["experiment"],
                    "metric": metric,
                    "value": row[metric],
                }
            )
    hard_veto_path = figures_dir / "hard_veto_compliance.svg"
    _write_svg(
        hard_veto_path,
        _grouped_bar_svg(
            hard_rows,
            "experiment",
            "metric",
            "value",
            "Hard-veto compliance",
            "Hard-veto-active pure MAVS-GC records compared with resulting rejections.",
            "Record count",
            EXPERIMENT_ORDER,
            ["hard_veto_count", "hard_veto_rejection_count"],
            EXPERIMENT_LABELS,
            {
                "hard_veto_count": "Hard veto active",
                "hard_veto_rejection_count": "Rejected under veto",
            },
        ),
    )

    figures = [
        {
            "figure_id": "acceptance_rate_by_experiment",
            "title": "Acceptance rate by experiment",
            "path": str(acceptance_path),
            "source_table": "classification_summary",
            "source_fields": "experiment,system,acceptance_rate",
            "question": "How often did each comparison system accept records in each synthetic test?",
            "takeaway": "Acceptance rates separate permissive ensemble behavior from governance-heavy rejection behavior.",
        },
        {
            "figure_id": "unsafe_acceptance_by_experiment",
            "title": "Unsafe acceptance by experiment",
            "path": str(unsafe_path),
            "source_table": "classification_summary",
            "source_fields": "experiment,system,unsafe_acceptance_rate",
            "question": "How often did each system accept unsafe truth=0 records?",
            "takeaway": "The false-positive trap exposes unsafe acceptance pressure under high-confidence unsafe cases.",
        },
        {
            "figure_id": "pure_mavs_gc_governance_pressure",
            "title": "Pure MAVS-GC governance pressure",
            "path": str(pressure_path),
            "source_table": "governance_summary",
            "source_fields": "experiment,severity_mean,threshold_mean,consensus_mean,mitigation_mean",
            "question": "How did severity, threshold, mitigation, and consensus vary for pure MAVS-GC?",
            "takeaway": "Governance pressure is traceable through severity aggregation, threshold movement, mitigation, and consensus.",
        },
        {
            "figure_id": "decision_variance_by_experiment",
            "title": "Decision variance by experiment",
            "path": str(variance_path),
            "source_table": "stability_summary",
            "source_fields": "experiment,system,decision_variance",
            "question": "How variable were binary decisions by system and synthetic test?",
            "takeaway": "Decision variance distinguishes systems that consistently reject from systems with mixed acceptance behavior.",
        },
        {
            "figure_id": "hard_veto_compliance",
            "title": "Hard-veto compliance",
            "path": str(hard_veto_path),
            "source_table": "hard_veto_compliance",
            "source_fields": "experiment,hard_veto_count,hard_veto_rejection_count",
            "question": "Did hard-veto-active pure MAVS-GC traces reject as required?",
            "takeaway": "Hard-veto-active traces reject in the generated evidence, satisfying the dominance invariant.",
        },
    ]
    for record in figures:
        _validate_figure_record(record)
    # console.log: record Phase 5 figure generation completion.
    console_log("plots.phase5.complete", f"generated {len(figures)} figures")
    return figures
