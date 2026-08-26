# UCI 360 Primary Confirmation — Findings

- Date: 2026-08-26
- Protocol: `docs/uci360_primary_protocol.md` (frozen before execution)
- Config: `configs/primary_uci360_rewindowed.json`, seed 20260826
- Data: `data/processed/uci360_rewindowed.csv`
- Results: `results/primary_uci360_rewindowed/`
- Verification Status: **VERIFIED — REPRODUCIBLE**

## Reproduction

Independent re-run to `results/repro_primary_uci360_rewindowed/`, same config
and seed:

- Row keys identical, 2160 × 22 both runs.
- Maximum absolute numeric difference **2.487e-13** (column `recovered_loss`),
  i.e. floating-point accumulation only.
- NaN patterns identical in every numeric column; non-numeric columns identical.
- All three verdicts identical. Every H2 held-out figure, the H1 held-out rho
  (0.813900), and both H3 budgets reproduce with absolute difference 0.
- CSV SHA-256 differs only through float repr formatting.

## Run Scale

| | Rejected study (Wörner primary) | This run (UCI 360 primary) |
|---|---|---|
| Sequences | 8 | **30** |
| Decision cells per budget | 24 | **90** |
| Held-out test rows per sequence | 6–12 | **107–207** |
| Distinct reference values per analyte | 2 | **90 / 238 / 751** |
| Target values | nominal labels | **co-located reference analyser** |
| Result rows | 576 | **2160** |
| Skipped sequences | — | **0** |

Held-out windows 10–13 span 2004-12-05 to 2005-04-04, i.e. 121 days that no
prior analysis in this project had touched.

## H1 — Diagnostic Validity: SUPPORTED

Spearman association between `d_ref(5)` and absolute lightweight benefit
`ΔnRMSE = nRMSE_frozen − nRMSE_calibrator_update`:

| Window set | n cells | rho | p |
|---|---|---|---|
| Rule-fitting (4–9) | 54 | 0.348 | 0.010 |
| **Held-out (10–13)** | 36 | **0.814** | **1.58e-09** |

Per model on held-out windows: PLS 0.832 (p=7.9e-04), random forest 0.902
(p=6.0e-05), XGBoost 0.881 (p=1.5e-04).

The reference-panel diagnostic predicts the **magnitude** of lightweight
benefit using only quantities available before the decision. This is the
positive contribution the rejected manuscript lacked.

## H2 — Rule Utility: TECHNICALLY SUPPORTED, PRACTICALLY NULL

Selected on rule-fitting windows only: `tau = 0.10`, decision budget `N = 20`.
Applied unchanged to held-out windows 10–13 (36 cells):

| Baseline | Mean test nRMSE |
|---|---|
| `always_frozen` | 0.241234 |
| `always_recalibrate` | 0.117631 |
| `rule(tau=0.10, N=20)` | 0.117582 |
| `oracle_action` (unattainable) | 0.117511 |

The rule beats `always_recalibrate` by **0.0000486 nRMSE, or 0.041 %**. It
recalibrates 35 of 36 cells. The rule is `always_recalibrate` plus rounding.

The pre-specified verdict rule ("H2 refuted if `always_recalibrate` is at least
as good as `rule`") is not literally triggered, but reporting this as a win
would be misleading. **The honest reading is that no gate is needed above the
reference-count floor**, because at N ≥ 5 almost every cell benefits. The
protocol anticipated this outcome and declared it publishable.

A design confound is disclosed: the same reference panel serves both the
diagnostic and the calibrator fit, so selecting N = 20 improves the fit quality
for reasons unrelated to decision quality. The `rule` vs `always_recalibrate`
comparison at fixed N remains valid; the choice of N = 20 does not isolate
diagnostic value.

## H3 — Decision Cheaper Than Fitting: SUPPORTED

Action agreement with `d_ref(50)` at tau = 0.10 on held-out windows: N=2 → 94.4 %,
N=5 → 94.4 %, N=10 → **100 %**, N=20 → 100 %.

Lightweight mean nRMSE by budget (held-out): N=2 0.1828, N=5 0.1430,
N=10 0.1224, N=20 0.1176, N=50 0.1154. Plateau within 5 % tolerance at N = 20.

Decision-stable at **N = 10**, fitting plateau at **N = 20**. Deciding whether
to recalibrate is cheaper than recalibrating well.

## The Actual Headline: A Tail-Risk Floor, Not a Mean-Shift Floor

Dense budget grid, `configs/sensitivity_uci360_floor_grid.json`,
`results/sensitivity_uci360_floor_grid/`, 3600 rows, 0 skipped. All 10 target
windows, 90 cells per budget. `ratio = nRMSE_lightweight / nRMSE_frozen`.

| N | mean nRMSE | mean ratio | **median ratio** | cells ratio>2 | neg. slope | improve / worsen |
|---|---|---|---|---|---|---|
| 0 | 0.18414 | 1.000 | 1.000 | 0 | 0 | 0 / 90 |
| **2** | 0.29585 | **2.005** | **1.009** | **8** | **3** | 44 / 46 |
| **3** | 0.15913 | 1.035 | 0.992 | **4** | 0 | 45 / 45 |
| **4** | 0.13608 | 0.906 | 0.899 | **0** | 0 | 55 / 35 |
| 5 | 0.12930 | 0.877 | 0.857 | 0 | 0 | 59 / 31 |
| 6 | 0.12218 | 0.841 | 0.858 | 0 | 0 | 61 / 29 |
| 8 | 0.11446 | 0.793 | 0.837 | 0 | 0 | 62 / 28 |
| 10 | 0.11223 | 0.779 | 0.826 | 0 | 0 | 63 / 27 |
| 20 | 0.10857 | 0.757 | 0.834 | 0 | 0 | 70 / 20 |
| 50 | 0.10563 | 0.729 | 0.816 | 0 | 0 | 83 / 7 |

The refined reading, which supersedes a simple "harmful below 5" statement:

- At **N = 2 the typical cell is neutral** (median ratio 1.009). The mean ratio
  of 2.005 is produced entirely by **8 of 90 cells**. Excluding those 8, N = 2
  gives frozen 0.19097 → lightweight 0.16131, ratio **0.845**, i.e. beneficial.
- The failure is therefore a **heavy right tail**, not a shift of the whole
  distribution. This matters operationally: the risk is not that a small panel
  gives slightly worse calibration on average, it is that a small panel
  occasionally destroys the measurement.
- **Slope inversion occurs only at N = 2** (3 cells; minimum slope −0.120). From
  N = 3 the minimum slope is +0.354 and no inversion occurs at any budget.
- Cells worse than 2× frozen: 8 at N=2, 4 at N=3, **0 from N=4 onward**.
- **The tail closes at N = 4.** That is the operational floor.

The eight N=2 tail cells, ordered by inflation:

| cell | ratio | slope | mechanism |
|---|---|---|---|
| NO2 w6 PLS | **44.5×** | −0.050 | inversion |
| NO2 w6 random forest | 23.8× | −0.102 | inversion |
| NO2 w6 XGBoost | 19.8× | −0.120 | inversion |
| NO2 w9 PLS | 2.34× | + | slope error |
| NOx w5 PLS | 2.32× | + | slope error |
| NOx w4 random forest | 2.22× | + | slope error |
| NOx w4 XGBoost | 2.10× | + | slope error |
| CO w13 XGBoost | 2.09× | + | slope error |

On held-out windows 10–13 alone, N = 2 is already beneficial (ratio 0.758,
25 improve / 11 worsen). The N = 2 tail concentrates in the rule-fitting
windows, chiefly NO2 window 6. The tail risk is real but not uniform across the
corpus, and this must be stated rather than smoothed over.

### Mechanism: slope inversion on a two-point fit (N = 2 only)

`calibration_slope` distribution by budget (all windows):

| N | mean | std | min | max | \|slope−1\|>1 |
|---|---|---|---|---|---|
| 2 | 0.759 | 0.240 | **−0.120** | 1.156 | 3 / 90 |
| 5 | 0.884 | 0.261 | 0.504 | 2.186 | 2 / 90 |
| 20 | 0.983 | 0.126 | 0.699 | 1.392 | 0 / 90 |
| 50 | 0.982 | 0.088 | 0.731 | 1.200 | 0 / 90 |

Worst cell, NO2 window 6, N=2. The two references carry targets 118.0 and 27.0
µg/m³. The frozen model orders these two points inversely to their true values,
so the least-squares calibrator returns a **negative slope** and inverts every
prediction:

| model | slope | frozen nRMSE | lightweight nRMSE | inflation |
|---|---|---|---|---|
| PLS | −0.050 | 0.1456 | 6.4846 | **44.5×** |
| random forest | −0.102 | 0.1292 | 3.0700 | 23.8× |
| XGBoost | −0.120 | 0.1378 | 2.7320 | 19.8× |

`d_ref` for these cells is 5.15–5.94, i.e. **very high**. A gate keyed on high
`d_ref` therefore *recommends recalibration exactly where the two-point
calibrator is about to fail*. The diagnostic's meaning is budget-dependent:
above the floor, high `d_ref` means "recalibrate, expect large gains"; at the
floor it cannot separate "the model has drifted" from "the panel is too small
to fit a calibrator". This is a substantive result, not a defect.

## Contrast With the Two-Level Corpus

Identical protocol, identical strategy, 5-reference budget:

| Corpus | Reference structure | improve / worsen |
|---|---|---|
| Wörner et al. 2025 | 2 nominal levels, 6–12 test rows | **12 / 12** |
| UCI 360 re-windowed | 90–751 analyser values, 107–207 test rows | **59 / 31** |

The rejected manuscript concluded that "reference count alone is not a
sufficient recalibration rule". On a corpus with genuine reference-analyser
values and working range, **reference count is the dominant variable**, with a
sharp safety floor between 2 and 5. The heterogeneity reported in the rejected
paper is better explained by the two-level reference structure of its
confirmation corpus than by an intrinsic property of lightweight recalibration.

## Revised Paper Claim

> Lightweight output recalibration of a gas-sensor array under temporal shift
> carries a **tail risk that closes at four labelled references**, not a gradual
> accuracy penalty. With two references the median sequence is unaffected, but
> the least-squares calibrator can invert its slope and inflate error by up to
> 44×. With four or more references no sequence in a 389-day reference-analyser
> corpus exceeds twice its frozen error, and lightweight updating then improves
> monotonically. A reference-panel diagnostic computed before the decision
> predicts how much will be recovered (Spearman 0.81 on held-out windows) but
> cannot protect against the two-reference tail, because it is highest exactly
> where the two-point fit fails. The decision of whether to recalibrate
> stabilises at a smaller panel than the calibration fit requires.

Deliverable procedure, every step using only pre-decision quantities:

1. Refuse lightweight output calibration below **four** labelled target-period
   references. A hard floor, justified by tail risk rather than mean error.
2. At or above the floor, compute `D_ref` on the panel and expect recovery
   proportional to it.
3. Budget the decision separately from the fit: the action stabilises at N ≈ 10
   while the fit keeps improving to N ≈ 20.

## Open Items — all closed 2026-08-26

Details in `artifacts/UCI360_OPEN_ITEMS_RESOLVED.md`.

1. **CLOSED.** `target_finetune` at N=2: mean 0.456, worst ratio 40.5×, **35 of
   90** cells above 2× frozen against 8 for lightweight. Its tail does not close
   until **N=8**, twice the lightweight floor; its mean nRMSE dips below frozen at
   N=4 but its mean *ratio* not until N=8, and it only overtakes lightweight at
   N=50. Full retraining never exceeds 2× at any
   budget but recovers least from N=5 onward. This bounds the floor claim:
   **N=4 is the floor for output recalibration specifically**, not a universal
   minimum reference count.
2. **CLOSED.** Figures: `results/figures_uci360_cils/` (4 vector PDFs) with
   `artifacts/UCI360_FIGURE_PACKAGE.md`. Tables: `manuscript/uci360_tables.md`
   (4 main + 4 supplementary). Retired Wörner figures and
   `manuscript/measurement_tables.md` left untouched.
3. **CLOSED.** NO2 window 6 has the fewest rows (362), fewest distinct reference
   values (106), lowest mean concentration (66.0), and strongest right skew
   (0.60); its range is *not* the narrowest (window 8 spans 165 vs 166). The
   panel draws one row from the lowest and one from the highest quantile
   stratum, here 27.0 and 118.0 µg/m³. All three frozen models compress that
   +91 interval into −4.3 / −9.7 / −11.7, i.e. **the wrong sign**, so the
   two-point calibrator coefficient is −21.3 / −9.4 / −7.8 and every prediction
   inverts. **Why N=2 is uniquely dangerous**: residual d.f. = 0, the panel
   residual is identically zero, so no panel-internal evidence of failure can
   exist. A post-hoc guard was tested and **rejected**: the sign of the
   predicted gap catches all 3 inversions but none of the other 5 N=2 failures,
   and the 4 surviving N=3 failures have rank agreement 1.000 and panel
   r > 0.98. This strengthens the hard-floor conclusion rather than replacing it.
4. **CLOSED.** Venue: Chemometrics and Intelligent Laboratory Systems (hybrid,
   free subscription route). Backup IEEE Sensors Journal.
5. **CLOSED as tracked.** Both disclosures are carried in the figure-package
   caption/limitation fields and in Table 4's header note. Still to be written
   into the manuscript body.

### Correction to this document

The `calibration_slope` column reported above and plotted in Figure 3 is the
slope of reference values regressed on predictions over the **held-out test
set**, where 1 is ideal — not the calibrator's fitted coefficient. Both are
negative for the NO2 window 6 cells, so the mechanism claim is unchanged, but the
two quantities differ by an order of magnitude (−0.050 vs −21.3 for PLS) and must
not be conflated.
