# MAVS-GC Synthetic Benchmark Workplan

## Goal

Build a controlled synthetic benchmark repository that tests whether the governance mechanisms defined by MAVS-GC behave according to their formal semantics. The implementation will isolate governance behavior from trained-model effects by using synthetic specialists, deterministic case generation, explicit diagnostics, bounded mitigation, governed thresholding, complete traces, and reproducible experiments.

The work is organized into five phases. Each phase has a defined scope, planned file inventory, verification requirements, and exit criteria.

## Source Hierarchy

When sources conflict, implementation decisions follow this order:

1. MAVS-GC Formal Definition: source of truth for architecture, invariants, operators, governance behavior, and trace semantics.
2. Foundation Arc Chapters 1-8: source of truth for mission, thesis, theorem backlog, governance metrics, evidence requirements, and claim discipline.
3. Chapter 9 Synthetic Benchmark Program: source of truth for repository structure, synthetic benchmark scope, baseline systems, experiments, and reporting artifacts.

## Governing Requirements

All implementation work must preserve the following requirements:

- All-speak evaluation: every specialist evaluates every input; no router may eliminate a specialist.
- Bounded scores and supports: specialist scores are in `[0, 1]`; supports are computed as `r_i = 2s_i - 1` and remain in `[-1, 1]`.
- Nonnegative diagnostics: diagnostic flags `z` are nonnegative.
- Monotone severity: the aggregator `A` maps flags to severity `a` without reducing severity when any flag increases.
- Bounded weights: the rebalancer `W` emits weights inside configured `[w_min, w_max]` bounds.
- Bounded mitigation: organs emit mitigation evidence `m` in `[0, 1]`.
- Governed threshold: `Theta(a, m) = theta_0 + lambda * a - delta * m`, with `lambda >= 0` and `delta >= 0`.
- Hard veto dominance: if configured and `a >= tau_hard`, rejection occurs regardless of consensus or mitigation.
- Governed consensus: `R = sum_i(w_i * r_i)`.
- Decision rule: `Pi(R, theta) = 1[R >= theta]`, except when a hard veto is active.
- Trace completeness: every execution emits `truth`, specialist scores, supports `r`, diagnostics `z`, severity `a`, weights `w`, mitigation `m`, threshold `theta`, consensus `R`, decision, and configuration identifiers.
- Claim control: results must be reported as controlled synthetic evidence, not as broad empirical superiority.

## Target Repository Structure

The repository will satisfy the Chapter 9 structure while allowing a small verification layer:

```text
README.md
Workplan.md
Path.md
src/
  core/
  specialists/
  diagnostics/
  governance/
  baselines/
  metrics/
experiments/
  test_disagreement/
  test_false_positive_trap/
  test_mitigation_veto/
results/
docs/
  chapter_9_report.md
tests/
```

## Phase 1 - Core Infrastructure

### Objective

Establish deterministic data structures, synthetic case generation, specialist interfaces, synthetic specialists, and trace scaffolding.

### Planned Files

- `README.md`: project purpose, source hierarchy, setup, run commands, and claim-control statement.
- `src/core/types.py`: typed records for synthetic cases, specialist outputs, traces, decisions, metrics inputs, and configuration references.
- `src/core/config.py`: configuration schema for seeds, specialist parameters, governance constants, weight bounds, diagnostic weights, and hard-veto settings.
- `src/core/case_generator.py`: deterministic generator for truth labels, corruption levels, disagreement regimes, mitigation regimes, and edge-case flags.
- `src/core/trace.py`: trace builder and validation helpers for required MAVS-GC trace fields.
- `src/specialists/base.py`: specialist protocol with `predict(case) -> score`.
- `src/specialists/synthetic.py`: accurate, noisy, overconfident, fragile, and adversarial specialists.
- `tests/test_trace.py`: trace field completeness and deterministic trace construction tests.
- `tests/test_specialists.py`: seeded specialist behavior and score-bound tests.

### Scope

- Implement no trained machine learning models.
- Ensure every specialist exposes a uniform `predict(case)` interface returning a score in `[0, 1]`.
- Convert scores to supports only through the formal support transform.
- Preserve deterministic outputs under fixed seeds and fixed configuration.

### Verification

- Trace generation works for a complete synthetic case.
- Specialist outputs are bounded.
- Specialist outputs are deterministic when seeded.
- All required specialist classes are available.

### Exit Criteria

Phase 1 is complete when synthetic specialists produce bounded scores and the trace system can record specialist scores, supports, truth, case metadata, and configuration identifiers.

## Phase 2 - Governance Core

### Objective

Implement the full MAVS-GC governance pipeline: diagnostics, severity aggregation, rebalancing, organs, policy, consensus, decision, hard veto, and complete trace emission.

### Planned Files

- `src/diagnostics/disagreement.py`: variance or dispersion-based disagreement flag.
- `src/diagnostics/corruption.py`: synthetic corruption severity flag.
- `src/diagnostics/overconfidence.py`: unjustified confidence flag.
- `src/diagnostics/inconsistency.py`: contradictory specialist behavior flag.
- `src/governance/aggregator.py`: weighted-sum aggregator and optional max aggregator.
- `src/governance/rebalancer.py`: bounded contextual weight function `W`.
- `src/governance/organs.py`: synthetic mitigation organ producing `m in [0, 1]`.
- `src/governance/policy.py`: threshold policy and hard-veto evaluation.
- `src/governance/consensus.py`: governed sum `R = sum_i(w_i * r_i)`.
- `src/governance/pipeline.py`: end-to-end MAVS-GC execution.
- `tests/test_governance_invariants.py`: monotonicity, mitigation, hard-veto, boundedness, and trace determinism tests.

### Scope

- Implement diagnostics as governance signals, not as specialist replacements.
- Ensure severity responds monotonically to diagnostic flags.
- Ensure mitigation can lower the threshold only within policy constraints.
- Ensure hard veto overrides ordinary threshold acceptance.
- Emit full traces for every pipeline execution.

### Verification

- Increasing any diagnostic flag does not lower severity.
- Increasing severity does not lower the governed threshold when mitigation is fixed.
- Increasing mitigation does not raise the governed threshold when severity is fixed.
- Hard veto rejects even when mitigation is maximal.
- Trace content is deterministic under fixed `Phi`, `F`, `G`, `A`, `W`, `P`, `Theta`, and `Pi`.

### Exit Criteria

Phase 2 is complete when the full MAVS-GC pipeline runs end-to-end and satisfies all formal invariants required by the source hierarchy.

## Phase 3 - Baselines

### Objective

Implement comparison systems required by Chapter 9 and document their behavior relative to MAVS-GC.

### Planned Files

- `src/baselines/mean.py`: mean ensemble baseline.
- `src/baselines/static_weighted.py`: static weighted ensemble baseline.
- `src/baselines/veto_mavs.py`: mean ensemble with red-flag veto.
- `src/baselines/runner.py`: shared baseline execution interface.
- `tests/test_baselines.py`: reproducibility and expected-behavior tests.
- `docs/baseline_definitions.md`: exact decision rules, thresholds, and trace fields for each baseline.

### Scope

- Implement four systems for comparison: mean ensemble, static weighted ensemble, veto MAVS, and pure MAVS-GC.
- Keep baseline decision rules explicit and reproducible.
- Use baseline traces sufficient for comparison without misrepresenting them as full MAVS-GC traces.
- Document the decision cutoff for mean and static weighted ensembles.

### Verification

- Baseline outputs are reproducible under fixed seeds.
- Baseline decision rules are documented.
- Baselines do not use MAVS-GC components beyond their stated definitions.
- Pure MAVS-GC remains the only full governance pipeline.

### Exit Criteria

Phase 3 is complete when all comparison systems are runnable through a common interface and their behavior is documented without unsupported claims.

## Phase 4 - Synthetic Experiments

### Objective

Implement the three required synthetic benchmark experiments and automated metric generation.

### Planned Files

- `experiments/test_disagreement/run.py`: experiment driver for low, medium, and high specialist disagreement.
- `experiments/test_disagreement/config.yaml`: seeds, case counts, disagreement parameters, and governance configuration.
- `experiments/test_false_positive_trap/run.py`: experiment driver for unsafe high-confidence consensus cases.
- `experiments/test_false_positive_trap/config.yaml`: seeds, confidence regimes, inconsistency settings, and diagnostic settings.
- `experiments/test_mitigation_veto/run.py`: experiment driver for mitigation levels and hard-veto boundary cases.
- `experiments/test_mitigation_veto/config.yaml`: severity grid, mitigation grid, and hard-veto settings.
- `src/metrics/classification.py`: accuracy, false positive rate, false negative rate, rejection rate, and unsafe acceptance rate.
- `src/metrics/governance.py`: severity distribution, threshold distribution, governance pressure, and mitigation effect.
- `src/metrics/stability.py`: consensus stability and decision variance.
- `tests/test_experiments_reproducible.py`: deterministic experiment output tests.
- `results/traces/`: trace outputs by experiment and system.
- `results/metrics/`: metric summaries by experiment and system.

### Scope

- Synthetic Test 1: specialist disagreement.
- Synthetic Test 2: false positive trap.
- Synthetic Test 3: mitigation versus hard veto.
- Generate metrics automatically for all four comparison systems.
- Preserve full trace reproducibility for pure MAVS-GC.

### Verification

- Experiments are reproducible from configuration alone.
- Metrics are generated automatically.
- Disagreement regimes produce distinct diagnostic pressure.
- False positive trap cases expose unsafe consensus conditions.
- Mitigation effects and hard-veto compliance are measured separately.

### Exit Criteria

Phase 4 is complete when all required experiments run end-to-end and produce traces plus metric summaries for every comparison system.

## Phase 5 - Analysis and Reporting

### Objective

Generate the final Chapter 9 artifact: charts, tables, summary statistics, reproducibility notes, and a disciplined interpretation of synthetic benchmark evidence.

### Planned Files

- `src/metrics/summaries.py`: tabular summaries for experiment outputs.
- `src/metrics/plots.py`: chart generation for acceptance rate, severity, threshold, consensus, decision variance, and hard-veto compliance.
- `scripts/generate_report.py`: reproducible report builder.
- `docs/chapter_9_report.md`: final report with purpose, methods, metrics, results, traceability, limitations, and conclusion.
- `results/figures/`: generated charts.
- `results/tables/`: generated tables.
- `results/run_manifest.json`: source configuration, seeds, generated files, and reproducibility metadata.

### Scope

- Report only controlled synthetic evidence.
- Keep proposed governance metrics distinct from validated empirical conclusions.
- Include limitations for synthetic specialists and non-real-world data.
- Document trace completeness and reproducibility.
- Include complexity observations only when measured or clearly marked as symbolic.

### Verification

- Report is generated automatically from experiment outputs.
- All metrics used in the report are defined.
- All charts and tables have corresponding source data.
- Trace reproducibility is documented.
- No unsupported superiority claims are introduced.

### Exit Criteria

Phase 5 is complete when the repository can generate the complete Chapter 9 artifact from deterministic experiment configurations and all findings are stated within the evidence boundaries set by the source hierarchy.

