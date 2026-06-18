# Baseline Definitions

## Purpose

This document defines the Phase 3 comparison systems. These systems are baselines for later controlled synthetic experiments. They are not claims of superiority and they are not substitutes for the MAVS-GC formal pipeline.

## Shared Inputs

All baselines use the same all-speak specialist outputs produced by the Phase 1 specialist framework:

- `specialist_scores`: calibrated specialist scores in `[0, 1]`;
- `supports`: support values computed as `r_i = 2s_i - 1`;
- `truth`: synthetic ground truth carried by the case;
- `case` metadata: corruption, disagreement regime, mitigation hint, and edge condition.

Baselines emit baseline traces. A baseline trace is intentionally smaller than a full MAVS-GC trace and must not be interpreted as containing governed severity, rebalanced trust, bounded mitigation, governed thresholding, or governed consensus unless explicitly stated.

## Mean Ensemble

System id: `mean_ensemble`

Decision rule:

```text
score = mean(specialist_scores)
decision = score >= 0.5
```

The cutoff is fixed at `0.5`. This baseline performs static averaging only. It does not use diagnostics, severity, rebalancing, organs, threshold policy, hard veto, or governed consensus.

## Static Weighted Ensemble

System id: `static_weighted_ensemble`

Default static weights:

```text
accurate = 0.95
noisy = 0.82
overconfident = 0.74
fragile = 0.70
adversarial = 0.35
```

Decision rule:

```text
score = sum_i(static_weight_i * specialist_score_i) / sum_i(static_weight_i)
decision = score >= 0.5
```

The cutoff is fixed at `0.5`. Weights are fixed before execution and do not depend on diagnostics, case context, or flags. This baseline does not use severity, rebalancing, organs, threshold policy, hard veto, or governed consensus.

## Veto MAVS

System id: `veto_mavs`

Decision rule:

```text
score = mean(specialist_scores)
red_flags = {
  disagreement,
  corruption,
  overconfidence,
  inconsistency
}
veto_active = max(red_flags) >= veto_threshold
decision = score >= 0.5 and not veto_active
```

Default `veto_threshold`: `0.85`.

This baseline uses direct red-flag veto behavior only. It does not aggregate flags into MAVS-GC severity, does not rebalance specialist weights, does not use mitigation organs, does not compute a governed threshold, and does not compute governed consensus `R`.

## Pure MAVS-GC

System id: `pure_mavs_gc`

The pure MAVS-GC comparison uses the Phase 2 full governance pipeline:

```text
specialists -> supports -> diagnostics -> severity -> rebalancing -> mitigation -> threshold -> consensus -> decision -> full trace
```

This is the only comparison system in Phase 3 that emits a full MAVS-GC trace with diagnostics `z`, severity `a`, weights `w`, mitigation `m`, threshold `theta`, consensus `R`, decision, and policy metadata.

## Trace Boundary

Baseline traces include enough fields for reproducible comparison:

- system id;
- trace id;
- config id and seed;
- case metadata;
- specialist scores;
- supports;
- baseline score;
- decision cutoff;
- decision;
- baseline metadata.

Veto MAVS additionally records direct red flags and whether the veto fired.

Pure MAVS-GC uses the Phase 2 full trace schema and should not be collapsed into a baseline trace.

