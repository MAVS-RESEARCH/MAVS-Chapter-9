# MAVS-GC Synthetic Benchmarks

This repository implements the Chapter 9 synthetic benchmark program for MAVS-GC.

The benchmark is designed to test whether explicit output governance behavior can be implemented, traced, and evaluated under controlled synthetic conditions. The current implementation includes deterministic core infrastructure, the MAVS-GC governance pipeline, comparison baselines, synthetic experiments, generated trace and metric outputs, and the Phase 5 analysis report.

## Source Hierarchy

Implementation decisions follow this order:

1. MAVS-GC Formal Definition: architecture, invariants, operators, governance behavior, and trace semantics.
2. Foundation Arc Chapters 1-8: research objective, claim control, theorem backlog, governance metrics, and evidence discipline.
3. Chapter 9 Synthetic Benchmark Program: repository structure, synthetic benchmark scope, baselines, experiments, metrics, and reporting.

## Phase 1 Scope

Phase 1 includes:

- deterministic synthetic case generation;
- specialist protocol with `predict(case) -> score`;
- accurate, noisy, overconfident, fragile, and adversarial synthetic specialists;
- score bounds in `[0, 1]`;
- support transform `r_i = 2s_i - 1`;
- trace scaffolding for truth, specialist scores, supports, case metadata, and configuration identifiers.

## Phase 2 Scope

Phase 2 includes:

- disagreement, corruption, overconfidence, and inconsistency diagnostics;
- weighted-sum and max severity aggregation;
- bounded contextual rebalancing;
- one synthetic mitigation organ;
- threshold policy `theta = theta_0 + lambda * a - delta * m`;
- hard-veto handling;
- governed consensus `R = sum_i(w_i * r_i)`;
- final MAVS-GC decision execution;
- complete full-pipeline trace emission.

## Phase 3 Scope

Phase 3 includes:

- mean ensemble baseline;
- static weighted ensemble baseline;
- Veto MAVS baseline;
- shared runner for the three baselines and pure MAVS-GC;
- baseline decision-rule documentation.

## Phase 4 Scope

Phase 4 includes:

- specialist disagreement experiment;
- false positive trap experiment;
- mitigation versus hard-veto experiment;
- automatic metric generation;
- JSONL trace output under `results/traces/`;
- JSON metric summaries under `results/metrics/`.

## Phase 5 Scope

Phase 5 includes:

- summary tables under `results/tables/`;
- deterministic SVG figures under `results/figures/`;
- an automated Markdown report at `docs/chapter_9_report.md`;
- a reproducibility manifest at `results/run_manifest.json`;
- report-generation tests for source provenance, metric-definition coverage, trace completeness, and deterministic replay.

Regenerate the Phase 5 report with:

```powershell
python scripts\generate_report.py
```

## Verification

Run the Phase 1 tests with:

```powershell
python -m unittest discover -s tests
```

The tests verify:

- all required specialists are available;
- specialist scores remain bounded;
- specialist behavior is deterministic under fixed seeds;
- all-speak evaluation returns every specialist output;
- generated cases are deterministic;
- Phase 1 traces contain required fields and are reproducible;
- Phase 2 diagnostics are nonnegative;
- severity and threshold monotonicity hold under the configured policy;
- mitigation lowers or preserves threshold pressure;
- hard veto dominates mitigation and consensus;
- full MAVS-GC traces are complete and deterministic;
- baseline outputs are reproducible;
- baseline decision rules are documented;
- baselines do not emit full MAVS-GC governance fields;
- experiments are reproducible from configuration alone;
- metric summaries are generated automatically;
- experiment trace outputs are deterministic;
- report tables and figures are generated from stored experiment outputs;
- report generation is deterministic across temporary output roots;
- reported metrics have definitions and source references.

## Claim Control

This repository does not claim performance superiority. The implementation establishes deterministic infrastructure, governance-core behavior, comparison baselines, synthetic experiment outputs, and controlled reporting artifacts for bounded synthetic evidence analysis.
