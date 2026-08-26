## Material Passport

- Origin Skill: academic-research-suite / academic-paper
- Origin Mode: plan
- Origin Date: 2026-08-14
- Verification Status: UNVERIFIED
- Version Label: paper_positioning_v1

## Paper Configuration Record

- **Target journal**: Measurement
- **Article type**: Original research article / benchmarking study, subject to
  confirmation against the current journal guide for authors
- **Language**: English
- **Working format**: Markdown during analysis; Elsevier LaTeX at submission
- **Citation style**: Defer to the current Measurement template; do not assume
  a style until the official guide is checked
- **Study status**: Exploratory UCI 270/360 results complete and reproducible;
  untouched confirmation pending

## Working Title

**Budgeted Recalibration of Gas Sensor Arrays under Temporal Shift: When Is
Lightweight Updating Insufficient?**

## Primary Research Question

Under time-ordered sensor-response and environmental distribution shift, how
much target-period reference data is required for lightweight output calibration
to approach full retraining, and under which conditions does lightweight
calibration remain inadequate?

## Thesis

Reference-sample count alone does not determine successful recalibration.
Strategy effectiveness depends on the model, analyte, temporal regime, and
concentration support; a lightweight calibrator can be efficient in some
deployment sequences but can worsen error in others, while full retraining may
recover performance at a higher computational cost.

## Measurement-Facing Contribution

1. A leakage-controlled rolling temporal protocol with fixed evaluation
   holdouts and nested, concentration-spread reference panels.
2. Cost-performance curves comparing no update, lightweight calibration,
   target-only updating, and full retraining.
3. A failure boundary identifying when additional reference samples should not
   be interpreted as sufficient evidence for lightweight recalibration.
4. Cross-corpus evidence that reports heterogeneity rather than averaging it
   away.

## Claims Allowed

- The evaluated strategies differ across datasets, analytes, models, budgets,
  and temporal regimes.
- UCI 270 and UCI 360 provide reproducible exploratory evidence.
- A new untouched corpus can test whether the revised strategy-selection rule
  transfers.

## Claims Prohibited

- Lightweight recalibration is universally effective.
- Temporal error changes are caused solely by physical sensor drift.
- The benchmark directly measures replacement cost or the performance of a new
  sensor when no replacement observation exists.
- UCI 224 and UCI 270 are independent evidence families.
- Post-hoc v0-v2 results are confirmatory evidence.

## Submission Gate

Do not draft the final Results or Discussion as a Measurement submission until
the untouched confirmation protocol is frozen, the new dataset passes schema
and provenance audit, and the confirmation run is reproduced.
