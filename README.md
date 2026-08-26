# Reference-set size for slope-and-bias recalibration of a drifting gas-sensor array

Analysis code and derived results for the manuscript *The Exactly-Determined
Reference Panel: Why Two-Sample Slope-and-Bias Recalibration Cannot Be Checked,
and Why Larger Panels Are Not Reliably Safe Either* (submitted to *Chemometrics
and Intelligent Laboratory Systems*).

This is an evaluation study, not a new drift-compensation algorithm.

## What the study concludes

Two findings, deliberately reported at different strengths.

**Structural, and draw-invariant.** A two-parameter slope-and-bias correction
fitted on exactly two reference samples has no residual degrees of freedom: it
interpolates both references, so no statistic computed from the panel can reveal
that it has failed. Its coefficient is a ratio of differences whose denominator
is the drifted model's predicted gap over the panel — small precisely when the
model has lost resolution, and able to change sign precisely when the model has
degraded most. Across ten independent reference-panel draws and 900 decision
cells per budget, calibration-slope inversion and error inflation beyond
fivefold occur **at two references and at no other budget**, the worst case
inflating normalised RMSE 44.5-fold through a correction coefficient of −21.3.
Above two references the worst outcome observed anywhere is 4.7-fold.

**A negative result about how the question is usually answered.** A single panel
draw yields an apparently clean threshold at four references. It does not
replicate: across ten draws the budget from which no cell exceeds twice frozen
error takes the values 4, 4, 4, 4, 4, 5, 6, 8, 20, 20 — mode 4, range 4 to 20.
It also moves with the criterion (three references at a threefold tolerance) and
with the error metric (eight on MAE). **We retract the threshold and report a
bound instead.** No small panel is reliably safe: failures above twice frozen
error persist to ten references and clear in every draw only at twenty.

An earlier version of this work reported the four-reference floor as a result.
That claim was withdrawn by our own robustness analysis; the record is in
`artifacts/UCI360_DRAW_SENSITIVITY.md`.

## Corpus

Primary: De Vito air-quality array, five metal-oxide channels co-located with
reference analysers over 389 days, UCI Machine Learning Repository,
DOI [10.24432/C59K5F](https://doi.org/10.24432/C59K5F). Three analytes (CO, NO2,
NOx) against reference-analyser values, 40–478 distinct values per 30-day window.

Contrast only: Wörner et al. one-year electronic-nose archive,
DOI [10.5281/zenodo.15681119](https://doi.org/10.5281/zenodo.15681119). Two
nominal concentration levels per analyte, which is why it cannot express a
reference-count effect (Section 4.9 of the manuscript).

**Raw data are not redistributed here.** Provenance JSON with checksums is under
version control in `data/processed/*_provenance.json`; the sources above are
public.

## Archived records

| Record | Version DOI | Concept DOI |
|---|---|---|
| Code and derived results, v2.0.0 | [10.5281/zenodo.22114413](https://doi.org/10.5281/zenodo.22114413) | [10.5281/zenodo.21973116](https://doi.org/10.5281/zenodo.21973116) |
| Row-level benchmark data, v1.0.0 | [10.5281/zenodo.22114399](https://doi.org/10.5281/zenodo.22114399) | [10.5281/zenodo.22114398](https://doi.org/10.5281/zenodo.22114398) |

Version DOIs identify the exact state that produced the manuscript's numbers;
concept DOIs always resolve to the latest version.

`10.5281/zenodo.21973117` (v1.0.0) archives the **withdrawn** analysis, in which
Wörner was treated as the primary corpus. It is retained as the record of that
version and should not be used to reproduce the current manuscript.

The ten row-level benchmark tables (one per panel draw, 1.10 MB each) are
archived in the data record rather than here, following the convention that
large numerical arrays go to a separate `dataset` record. Everything the
manuscript cites — decision cells, pooled summaries, figures, tables — is in
this repository.

## Layout

```text
docs/uci360_primary_protocol.md     protocol, frozen before execution
configs/                            frozen run configurations
src/gasdrift/                       split, recalibration and metric code
scripts/                            runners, analysis, figure/table/LaTeX builds
results/                            derived summaries, figures, tables
artifacts/UCI360_*.md               findings, retraction record, figure package
```

## Environment

Python 3.13 with the pins in `requirements.txt`.

```powershell
uv venv .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
```

## Reproducing

The benchmark needs the normalised corpus, which is rebuilt from the public raw
archive:

```powershell
.\.venv\Scripts\python.exe scripts\fetch_uci.py --dataset air_quality --out-dir data\raw
.\.venv\Scripts\python.exe scripts\normalize_uci360_rewindowed.py `
  --input data\raw\air_quality_features.csv `
  --output data\processed\uci360_rewindowed.csv `
  --provenance data\processed\uci360_rewindowed_provenance.json
.\.venv\Scripts\python.exe scripts\audit_dataset.py --config configs\primary_uci360_rewindowed.json --input data\processed\uci360_rewindowed.csv --report results\logs\uci360_rewindowed_audit.json
```

The re-windowing defaults to 30-day windows over the full 389-day span; the
withdrawn analysis truncated at `batch_id <= 3` and discarded 119 days.

Pre-specified primary run and its hypothesis tests:

```powershell
.\.venv\Scripts\python.exe scripts\run_benchmark.py --config configs\primary_uci360_rewindowed.json --input data\processed\uci360_rewindowed.csv --out-dir results\primary_uci360_rewindowed
.\.venv\Scripts\python.exe scripts\analyze_decision_rule.py --config configs\primary_uci360_rewindowed.json --results results\primary_uci360_rewindowed\tables\benchmark_results.csv --out-dir results\primary_uci360_rewindowed\decision_rule
```

Dense budget grid, then the ten-draw replication that overturned the threshold
(about 8–14 minutes per draw; existing draws are reused):

```powershell
.\.venv\Scripts\python.exe scripts\run_benchmark.py --config configs\sensitivity_uci360_floor_grid.json --input data\processed\uci360_rewindowed.csv --out-dir results\sensitivity_uci360_floor_grid
.\.venv\Scripts\python.exe scripts\run_seed_sensitivity.py --seeds 11 22 33 44 55 66 77 88 99
.\.venv\Scripts\python.exe scripts\summarize_seed_sensitivity.py
```

Mechanism analysis, figures and tables:

```powershell
.\.venv\Scripts\python.exe scripts\analyze_open_items.py --conditioning-budgets 2 3 4 5 6 8
.\.venv\Scripts\python.exe scripts\generate_uci360_figures.py
.\.venv\Scripts\python.exe scripts\generate_uci360_tables.py
```

`generate_uci360_tables.py` writes to `manuscript/uci360_tables.md`, creating the
directory if needed. The manuscript itself is not part of this repository (see
below).

## Verification

```powershell
.\.venv\Scripts\python.exe scripts\verify_draft_numbers.py   # 141 numeric claims
```

Every quantitative claim in the manuscript is restated here as a literal and
recomputed from the frozen result files; the script exits non-zero on any
mismatch. It needs no manuscript file, so it runs against this repository alone
and is the check that matters for reproduction. Its draw-replication section
hardcodes the ten-draw values, so it is *expected* to fail if the draw count
changes — that failure is the reminder to update the corresponding sentences.

## Reproducibility notes

- The benchmark was run twice from the same configuration and seed in separate
  output directories. Maximum absolute numerical difference across all numeric
  columns: 2.487 × 10⁻¹³. All three pre-specified verdicts reproduce exactly.
- Figures regenerate byte-identically; jitter uses a fixed seed.
- The decision unit is the (analyte, window, model) cell; cells share source
  fits and target windows and are not independent replicates.
- Two disclosures carried in the manuscript: the diagnostic hypothesis is
  exploratory in origin (windows 4–9 overlap the span that generated it, windows
  10–13 are the confirmation set), and the diagnostic shares a reference panel
  with the correction it informs.
- Temporal change is not attributed to physical sensor drift, and predictive
  error is not measurement uncertainty.

## Licensing

Source code under `scripts/`, `src/` and `configs/`: MIT.
Derived tables, figures, protocol documents and reports: CC BY 4.0.

## Older frozen runs

Retained for provenance and not part of the current claim:
`results/kill_test*`, `results/repro_uci*`, `results/confirmation_worner_v1`,
`results/repro_worner_v1`, `results/sensitivity_worner_*`, `results/figures/`.

## What is deliberately not here

The manuscript, its LaTeX build, and the manuscript-production scripts are not
released in this repository. Double-anonymised review requires that
reviewer-visible material not be linkable to author identity, and this repository
is public under a named account; shipping the manuscript would defeat that. The
v1.0.0 Zenodo code record likewise contained no manuscript. Everything the
manuscript cites is regenerable from the code and results that are here.

Also excluded: raw and normalised corpora (public sources, provenance JSON with
checksums retained), the row-level benchmark tables for the ten draws (separate
dataset record), third-party PDFs, and material from the withdrawn *Measurement*
submission.
