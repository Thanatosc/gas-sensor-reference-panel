# Method Changelog

## 2026-08-26: Reference-panel diagnostic added to `run_benchmark.py`

- Added three output columns: `reference_frozen_nrmse`, `d_ref`, computed from
  the deployed frozen model scored on the labelled reference panel, against the
  existing `preceding_source_error`.
- No existing column, split, model, strategy, or metric was changed. The edit is
  purely additive; re-running any earlier config reproduces its previous values
  and gains the new columns.

Reason: the existing `frozen_nrmse_relative_increase` is computed from the frozen
test holdout, so it is not observable when the recalibration decision has to be
made and cannot drive an operational rule. `d_ref` uses only the reference panel
and source-validation error, both available before the decision. Specified in
`docs/uci360_primary_protocol.md`.

## 2026-08-26: UCI 360 promoted to primary confirmation corpus

- New normalizer `scripts/normalize_uci360_rewindowed.py` removes the
  `batch_id <= 3` truncation of `scripts/normalize_uci360.py`, which discarded
  119 of 389 available days, and takes window width as a parameter.
- Window width 30 days, 13 windows, source 1–3, target 4–13. 30 sequences
  against 3 in the previous UCI 360 run.
- `scripts/normalize_uci360.py` and all prior outputs are left untouched.

Reason: post-rejection audit found the evidence hierarchy inverted. The Wörner
confirmation corpus carries two nominal concentration levels per analyte and
6–12 held-out rows per sequence, which cannot support a calibration claim. UCI
360 carries 90–751 distinct reference-analyser values and 107–207 held-out rows.
The original Kill Test FAIL verdict was produced by a gate requiring joint hits
in two corpora, written for the retired claim and never re-specified after the
research question changed.

Known artefact: 42 sklearn `y residual is constant` warnings from PLS at small
reference budgets, where the reference panel target values do not vary enough to
identify a component. These cells are part of the reference-budget floor result
and are not suppressed.

## 2026-08-14: Kill Test v0 to v1

- Split regression by gas identity and target batch instead of pooling them.
- Added a fixed 30% target holdout and nested reference budgets.
- Restricted evaluation to common source/target concentration support.
- Added a rolling source-period nRMSE reference and explicit sequence skips.

Reason: the initial implementation changed the evaluation set across budgets,
pooled incomparable gases, and emitted undefined nRMSE for single-concentration
target batches.

## 2026-08-14: Kill Test v1 to v2

- Changed nested reference ordering from concentration-blocked to a low/high
  alternating design.
- Defined `calibrator_update` as the only lightweight strategy for the Kill Test.
- When reference concentration has no variation, the calibrator can estimate an
  intercept correction only; target-only fine-tuning falls back to frozen.

Reason: v1's blocked ordering made the 5% reference prefix single-concentration,
so calibration slope was structurally unidentifiable. This is an exploratory
method correction made before preregistration; v0/v1 outputs remain archived and
must not be combined with v2.
