## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: plan
- Origin Date: 2026-08-14
- Verification Status: UNVERIFIED
- Version Label: measurement_protocol_v1

## Protocol Role Separation

- **Exploratory evidence**: UCI 270 Kill Test v2 and UCI 360 Kill Test v1.
- **Untouched confirmation**: Wörner et al. 2025 one-year electronic-nose
  dataset, DOI `10.5281/zenodo.15681119`, if schema audit shows that the data can
  support the revised RQ.
- Exploratory outputs may motivate the revised RQ but cannot be pooled with the
  confirmation corpus as if all analyses had been pre-specified together.

## Frozen Decisions Before Confirmation Data Inspection

1. Evaluate each analyte and temporal deployment sequence separately.
2. Preserve temporal order; no random row split across time.
3. Freeze an evaluation holdout before selecting target references.
4. Use nested reference panels ordered to span the available concentration
   range.
5. Compare `frozen`, `calibrator_update`, `target_finetune`, and
   `full_retrain` under identical references.
6. Treat `calibrator_update` as the lightweight strategy.
7. Use nRMSE, MAE, calibration slope, and `recovered_loss`; leave recovery
   undefined when the oracle denominator is non-positive.
8. Make the temporal sequence, not individual sensor rows or model instances,
   the inferential unit.
9. Report every analyte/model direction and every excluded sequence.
10. Do not interpret temporal shift as physical sensor drift unless the dataset
    provides evidence that separates drift from environment, maintenance, and
    concentration-distribution change.

## Reference-Budget Plan

- Primary cost axis: absolute number of labeled reference observations per
  target window: 0, 2, 5, 10, 20, and 50, capped by the available reference
  pool.
- Secondary axis: target-window fractions 0%, 1%, 2%, 5%, 10%, and 20% for
  comparability with the exploratory analyses.
- Monetary cost is out of scope unless the source provides defensible sampling
  or laboratory cost metadata.

## Confirmation Dataset Audit Status

- Wörner Zenodo record metadata: verified against DOI `10.5281/zenodo.15681119`.
- Archive MD5: verified locally as `9937678cac4118c53287276009172a74`.
- Raw archive schema: passes the concentration-label and temporal-order gate;
  see `docs/worner_schema_audit.md` and `docs/worner_data_contract.md`.
- The normalized table is generated from raw files, not the incomplete
  624-row pre-extracted feature table.

Sensitivity configurations for three-day windows and an alternative reference
panel seed are frozen in `configs/confirmation_worner_window3.json` and
`configs/confirmation_worner_seed20260816.json`; they are not to be used to
change the primary six-day-window conclusion.

## Confirmation Outcomes

- **Supports transfer**: at least one lightweight strategy/model regime reaches
  `recovered_loss >= 0.50`, while at least one other defensible regime remains
  below `0.20`, demonstrating a reproducible decision boundary rather than a
  universal winner.
- **Supports retraining-only pivot**: lightweight recovery remains below `0.20`
  across eligible sequences but full retraining exceeds `0.50` in multiple
  independent temporal sequences.
- **No support**: neither lightweight calibration nor full retraining produces
  a stable direction across eligible temporal sequences, or the dataset cannot
  separate target/reference measurements sufficiently to answer the RQ.

These outcomes are descriptive decision gates, not p-value thresholds.

## Mandatory Sensitivity Analyses

- Alternative temporal-window widths.
- Common concentration support versus observed-range support.
- Complete-case versus missingness-aware analysis when applicable.
- Reference-panel seed or panel-design sensitivity.
- Model-specific results without aggregation across models.

## Next Gate

Read official Zenodo metadata and archive structure only. Do not train or tune a
model until a dataset-specific normalization contract and temporal split are
written and audited.
