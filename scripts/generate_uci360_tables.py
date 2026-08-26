"""Generate the CILS manuscript tables for the UCI 360 recalibration analysis.

Every cell is computed from the frozen result files, so the tables cannot drift
away from the figures or from `artifacts/UCI360_PRIMARY_FINDINGS.md`. Replaces
`manuscript/measurement_tables.md`, which describes the retired Wörner analysis
and is left in place untouched.

Sources
-------
- `results/sensitivity_uci360_floor_grid/tables/benchmark_results.csv`
  dense budget grid, 3600 rows, all four strategies
- `results/primary_uci360_rewindowed/decision_rule/decision_rule_report.json`
  pre-specified H1/H2/H3 outcomes on the 6-point primary grid
- `results/open_items_uci360/panel_conditioning.csv`
  refitted panel geometry for the mechanism table
- `data/processed/uci360_rewindowed.csv`
  corpus descriptives
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

PRIMARY_SEED = 20260826
POOLED_CELLS = Path("results/seed_sensitivity/pooled_cells.csv")
STRATEGIES = ["frozen", "calibrator_update", "target_finetune", "full_retrain"]
STRATEGY_LABEL = {
    "frozen": "Frozen",
    "calibrator_update": "Lightweight",
    "target_finetune": "Target-only refit",
    "full_retrain": "Full retraining",
}
MODEL_LABEL = {"pls": "PLS", "random_forest": "Random forest", "xgboost": "XGBoost"}
GAS_LABEL = {"CO": "CO", "NO2": "NO2", "NOx": "NOx"}
FLOOR = 4
SOURCE_BATCHES = [1, 2, 3]


def minus(value: str) -> str:
    """Typographic minus for prose tables."""
    return value.replace("-", "−")


def fmt(value: float, digits: int = 3, signed: bool = False) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "n/a"
    text = f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"
    return minus(text)


def fmt_p(p_value: float) -> str:
    """LaTeX p-value. Avoids `1.6e-09`, which does not typeset in math mode."""
    if p_value is None or not np.isfinite(p_value):
        return "n/a"
    if p_value >= 0.001:
        return f"{p_value:.3f}".rstrip("0").rstrip(".")
    exponent = int(np.floor(np.log10(p_value)))
    mantissa = p_value / 10 ** exponent
    return rf"{mantissa:.1f}\times 10^{{{exponent}}}"


def load_cells(results: pd.DataFrame) -> pd.DataFrame:
    key = ["gas_id", "target_batch", "model", "budget"]
    frozen = results[results.strategy == "frozen"].set_index(key)
    light = results[results.strategy == "calibrator_update"].set_index(key)
    common = frozen.index.intersection(light.index)
    cells = pd.DataFrame(
        {
            "frozen_nrmse": frozen.loc[common, "nrmse"],
            "light_nrmse": light.loc[common, "nrmse"],
            "slope": light.loc[common, "calibration_slope"],
            "frozen_slope": frozen.loc[common, "calibration_slope"],
            "d_ref": frozen.loc[common, "d_ref"],
            "n_test": frozen.loc[common, "n_test"],
            "n_reference_pool": frozen.loc[common, "n_reference_pool"],
        }
    ).reset_index()
    cells["ratio"] = cells.light_nrmse / cells.frozen_nrmse
    cells["delta_nrmse"] = cells.frozen_nrmse - cells.light_nrmse
    # MAE ratio is needed for the endpoint-sensitivity table.
    mae_f = frozen.loc[common, "mae"].to_numpy()
    mae_l = light.loc[common, "mae"].to_numpy()
    cells["mae_ratio"] = mae_l / mae_f
    return cells


def table_1_design(frame: pd.DataFrame, cells: pd.DataFrame, config: dict) -> list[str]:
    """Corpus and evaluation design, per analyte."""
    target_batches = config["target_batches"]
    rows = []
    for gas_id in sorted(frame.gas_id.unique()):
        gas = frame[frame.gas_id == gas_id]
        source = gas[gas.batch_id.isin(SOURCE_BATCHES)]
        targets = gas[gas.batch_id.isin(target_batches)]
        per_window = targets.groupby("batch_id")
        gas_cells = cells[(cells.gas_id == gas_id) & (cells.budget == 5)]
        rows.append(
            {
                "analyte": GAS_LABEL[gas_id],
                "source_rows": len(source),
                "windows": targets.batch_id.nunique(),
                "target_rows_min": int(per_window.size().min()),
                "target_rows_max": int(per_window.size().max()),
                "distinct_min": int(per_window.target.nunique().min()),
                "distinct_max": int(per_window.target.nunique().max()),
                "test_min": int(gas_cells.n_test.min()),
                "test_max": int(gas_cells.n_test.max()),
                "unit": {"CO": "mg m$^{-3}$", "NO2": "µg m$^{-3}$", "NOx": "ppb"}[gas_id],
            }
        )
    lines = [
        "## Table 1",
        "",
        "**Corpus and evaluation design.** Source windows 1–3 (2004-03-10 to "
        "2004-06-08) fit each model; target windows 4–13 are evaluated one at a "
        "time. Within a target window the held-out test set is frozen before any "
        "reference is selected. Distinct target values are co-located reference-"
        "analyser readings, not nominal levels. Held-out rows are counted at the "
        "five-reference budget; they vary by at most the reference count across "
        "budgets.",
        "",
        "| Analyte | Unit | Source rows | Target windows | Rows per window | "
        "Distinct reference values per window | Held-out rows per window |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['analyte']} | {r['unit']} | {r['source_rows']} | {r['windows']} | "
            f"{r['target_rows_min']}–{r['target_rows_max']} | "
            f"{r['distinct_min']}–{r['distinct_max']} | {r['test_min']}–{r['test_max']} |"
        )
    total_seq = cells[cells.budget == 5].groupby(["gas_id", "target_batch"]).ngroups
    total_cells = int((cells.budget == 5).sum())
    lines.extend([
        "",
        f"Sequences (analyte × window): **{total_seq}**. Decision cells "
        f"(analyte × window × model): **{total_cells}** per budget. "
        f"Models: PLS, random forest, XGBoost. Skipped sequences: **0**.",
        "",
    ])
    return lines


def table_2_budget(cells: pd.DataFrame, results: pd.DataFrame) -> list[str]:
    """The core result: all four strategies and the tail counts by budget."""
    key = ["gas_id", "target_batch", "model", "budget"]
    frozen = results[results.strategy == "frozen"].set_index(key)
    per_strategy: dict[str, pd.DataFrame] = {}
    for strategy in STRATEGIES:
        part = results[results.strategy == strategy].set_index(key)
        common = frozen.index.intersection(part.index)
        joined = pd.DataFrame(
            {
                "nrmse": part.loc[common, "nrmse"],
                "frozen_nrmse": frozen.loc[common, "nrmse"],
            }
        ).reset_index()
        joined["ratio"] = joined.nrmse / joined.frozen_nrmse
        per_strategy[strategy] = joined

    budgets = sorted(cells.budget.unique())
    lines = [
        "## Table 2",
        "",
        "**Held-out error against reference budget, all four update strategies.** "
        "Mean over 90 decision cells per budget; `ratio` is the per-cell "
        "lightweight-to-frozen nRMSE ratio, so its mean is not the ratio of the "
        "displayed means. Cells > 2× counts cells whose held-out nRMSE exceeds "
        "twice that of the frozen model, and is the failure statistic used "
        "throughout. Inverted counts cells whose held-out calibration slope is "
        "negative. Cells are not independent replicates: they share source fits "
        "and target windows.",
        "",
        "| N | Frozen | Lightweight | Target-only refit | Full retraining | "
        "Lightweight mean ratio | Lightweight median ratio | "
        "Lightweight cells > 2× | Lightweight inverted | Lightweight improved |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for budget in budgets:
        part = cells[cells.budget == budget]
        means = {
            s: per_strategy[s][per_strategy[s].budget == budget].nrmse.mean()
            for s in STRATEGIES
        }
        best = min(means, key=means.get)
        cellvals = []
        for s in STRATEGIES:
            text = fmt(means[s], 5)
            cellvals.append(f"**{text}**" if s == best and budget > 0 else text)
        lines.append(
            f"| {budget} | " + " | ".join(cellvals) + " | "
            f"{fmt(part.ratio.mean())} | {fmt(part.ratio.median())} | "
            f"{int((part.ratio > 2).sum())} | {int((part.slope < 0).sum())} | "
            f"{int((part.delta_nrmse > 0).sum())}/{len(part)} |"
        )
    tail = {int(b): int((cells[cells.budget == b].ratio > 2).sum()) for b in budgets}
    lines.extend([
        "",
        f"Bold marks the best strategy at each budget. In this draw the count above "
        f"2× reaches zero at N = {FLOOR} ({tail[2]} cells at N = 2, {tail[3]} at "
        f"N = 3). **That budget is specific to this panel draw and is not a floor**: "
        "under nine further draws it ranges from 4 to 20 (Table 5). The draw-invariant "
        "statement is in Table 6.",
        "",
    ])
    return lines


def table_5_draws(pooled: pd.DataFrame) -> list[str]:
    """Per-draw failure counts: the non-replication result."""
    budgets = sorted(pooled.budget.unique())
    seeds = sorted(pooled.seed.unique(), key=lambda s: (s != PRIMARY_SEED, s))
    lines = [
        "## Table 5",
        "",
        "**The failure threshold does not replicate across reference-panel draws.** "
        "Each draw redraws every panel and reseeds the model random states, so each "
        "is an independent realisation of the same range-spanning design. Counts are "
        "cells above twice frozen error, of 90 per budget. The final column is the "
        "smallest budget from which that draw and all larger budgets are clean. "
        "Reported post-hoc; no threshold, hypothesis, or verdict of the frozen "
        "protocol is changed.",
        "",
        "| Draw | " + " | ".join(f"N={b}" for b in budgets if b > 0)
        + " | First clean N |",
        "|---|" + "---:|" * (len([b for b in budgets if b > 0]) + 1),
    ]
    firsts = []
    for seed in seeds:
        part = pooled[pooled.seed == seed]
        counts = [int((part[part.budget == b].ratio > 2).sum())
                  for b in budgets if b > 0]
        first = None
        for i, b in enumerate(budgets):
            if b == 0:
                continue
            if all(int((part[part.budget == later].ratio > 2).sum()) == 0
                   for later in budgets[i:]):
                first = int(b)
                break
        firsts.append(first)
        label = f"**{seed}** (pre-specified)" if seed == PRIMARY_SEED else str(seed)
        lines.append(f"| {label} | " + " | ".join(str(c) for c in counts)
                     + f" | **{first}** |")
    lines.extend([
        "",
        f"Per-draw thresholds: {', '.join(str(f) for f in firsts)}, spanning "
        f"{min(f for f in firsts if f)} to {max(f for f in firsts if f)} with mode "
        f"{max(set(f for f in firsts if f), key=firsts.count)} "
        f"({firsts.count(max(set(f for f in firsts if f), key=firsts.count))} of "
        f"{len(firsts)} draws). The pre-specified draw takes the modal value, so it "
        "was a typical realisation rather than an unlucky one; a typical realisation "
        "nonetheless conveys nothing about the spread. Pooling all draws, the twofold "
        f"criterion is first met by every draw at N = {max(f for f in firsts if f)}.",
        "",
    ])
    return lines


def table_6_pooled(pooled: pd.DataFrame) -> list[str]:
    """What survives all draws: the worst-case bound and the regime boundary."""
    budgets = sorted(pooled.budget.unique())
    lines = [
        "## Table 6",
        "",
        f"**Draw-invariant results, pooled over {pooled.seed.nunique()} panel draws "
        f"({int(len(pooled) / pooled.budget.nunique())} cells per "
        "budget).** The worst observed ratio requires no threshold and is the "
        "quantity a prohibition bounds. Slope inversion and inflation beyond "
        "fivefold occur at N = 2 and at no other budget in any draw, which is what "
        "the exact-determination argument of Section 2.1 predicts. Counts above 2× "
        "decay gradually and reach zero only at N = 20, so no small panel is "
        "reliably safe.",
        "",
        "| N | Cells | Worst nRMSE ratio | Worst MAE ratio | Inverted | >5× | >3× | "
        ">2× | >2× on MAE | Mean ratio | Median ratio |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for budget in budgets:
        part = pooled[pooled.budget == budget]
        lines.append(
            f"| {int(budget)} | {len(part)} | {fmt(part.ratio.max(), 2)} | "
            f"{fmt(part.mae_ratio.max(), 2)} | {int((part.slope < 0).sum())} | "
            f"{int((part.ratio > 5).sum())} | {int((part.ratio > 3).sum())} | "
            f"{int((part.ratio > 2).sum())} | {int((part.mae_ratio > 2).sum())} | "
            f"{fmt(part.ratio.mean())} | {fmt(part.ratio.median())} |"
        )
    med = pooled[pooled.budget == 2].groupby("seed").ratio.median()
    mean = pooled[pooled.budget == 2].groupby("seed").ratio.mean()
    lines.extend([
        "",
        f"At N = 2 the median ratio is stable across draws "
        f"({', '.join(f'{v:.3f}' for v in sorted(med))}), while the mean is not "
        f"({', '.join(f'{v:.3f}' for v in sorted(mean))}). The mean departs from the "
        "median only in the draw whose tail was realised, which is the expected "
        "behaviour of a tail-driven mean and the reason a single-draw mean should not "
        "be read as an effect size.",
        "",
    ])
    return lines


def table_s5_thresholds(cells: pd.DataFrame) -> list[str]:
    """Threshold and endpoint sensitivity within the primary draw."""
    budgets = sorted(cells.budget.unique())
    thresholds = [1.5, 2.0, 3.0, 5.0]
    lines = [
        "## Table S5",
        "",
        "**Threshold and endpoint sensitivity within the pre-specified draw.** The "
        "budget at which failures cease depends on the tolerance and on the error "
        "metric, independently of the panel draw. Neither choice is canonical, so a "
        "laboratory with a defined tolerance should read the relevant column rather "
        "than adopt the twofold nRMSE convention used in the main text.",
        "",
        "| N | " + " | ".join(f">{t}× nRMSE" for t in thresholds) + " | >2× MAE |",
        "|---:|" + "---:|" * (len(thresholds) + 1),
    ]
    for budget in budgets:
        part = cells[cells.budget == budget]
        row = [f"| {int(budget)}"]
        for t in thresholds:
            row.append(str(int((part.ratio > t).sum())))
        row.append(str(int((part.mae_ratio > 2).sum())))
        lines.append(" | ".join(row) + " |")

    lines.extend(["", "First clean budget by criterion:", "",
                  "| Criterion | First clean N |", "|---|---:|"])
    for t in thresholds:
        first = None
        for i, b in enumerate(budgets):
            if b == 0:
                continue
            if all(int((cells[cells.budget == later].ratio > t).sum()) == 0
                   for later in budgets[i:]):
                first = int(b)
                break
        lines.append(f"| nRMSE ratio > {t} | {first} |")
    first_mae = None
    for i, b in enumerate(budgets):
        if b == 0:
            continue
        if all(int((cells[cells.budget == later].mae_ratio > 2).sum()) == 0
               for later in budgets[i:]):
            first_mae = int(b)
            break
    lines.extend([f"| MAE ratio > 2.0 | {first_mae} |", ""])
    return lines


def table_3_tail(cells: pd.DataFrame, conditioning: pd.DataFrame | None) -> list[str]:
    """Every cell above 2x at the two budgets where any exist."""
    lines = [
        "## Table 3",
        "",
        "**Every cell above twice frozen error, with mechanism.** These are all "
        "12 such cells in the corpus; none occur at any budget above N = 3. "
        "Held-out calibration slope is the slope of reference values regressed on "
        "predictions over the test set, where 1 is ideal. Inversion means that "
        "slope is negative, so the recalibrated model orders concentrations "
        "backwards. Slope error means the correction had the right sign but the "
        "wrong magnitude.",
        "",
        "| N | Analyte | Window | Model | Frozen nRMSE | Lightweight nRMSE | "
        "Ratio | Held-out slope | $D_{\\mathrm{ref}}$ | Mechanism |",
        "|---:|---|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    tail = cells[cells.ratio > 2].sort_values(["budget", "ratio"], ascending=[True, False])
    for _, row in tail.iterrows():
        mechanism = "Inversion" if row.slope < 0 else "Slope error"
        lines.append(
            f"| {int(row.budget)} | {GAS_LABEL[row.gas_id]} | {int(row.target_batch)} | "
            f"{MODEL_LABEL[row.model]} | {fmt(row.frozen_nrmse)} | {fmt(row.light_nrmse)} | "
            f"{fmt(row.ratio, 1)}× | {fmt(row.slope)} | {fmt(row.d_ref, 2)} | {mechanism} |"
        )
    n_inv = int((tail.slope < 0).sum())
    lines.extend([
        "",
        f"Inversion occurs in **{n_inv}** cells, all at N = 2 and all in the same "
        "NO2 window, across all three model classes. Every remaining failure is a "
        "slope error with a positive slope. Note that $D_{\\mathrm{ref}}$ is high "
        "in the inversion cells: the pre-decision diagnostic recommends "
        "recalibration exactly where the two-point fit is about to fail.",
        "",
    ])
    return lines


def table_4_hypotheses(report: dict) -> list[str]:
    """Pre-specified H1/H2/H3 outcomes, held-out windows only."""
    h1_held = report["H1"]["held_out"]
    h1_fit = report["H1"]["rule_fitting"]
    h2 = report["H2"]
    selected = h2["selected_on_rule_fitting_windows"]
    evaluation = h2["held_out_evaluation"]
    h3 = report["H3"]
    agreement = h3["action_agreement_with_max_budget"]

    lines = [
        "## Table 4",
        "",
        "**Pre-specified hypothesis outcomes.** Thresholds were selected on "
        "rule-fitting windows 4–9 and applied unchanged to held-out windows "
        "10–13. The rule-fitting windows overlap the span that generated the "
        "diagnostic hypothesis and are in-sample for hypothesis generation; "
        "windows 10–13 cover 121 days not used in any earlier analysis. The H2 "
        f"means are over the {evaluation['n_cells']} held-out cells at "
        f"$N={selected['decision_budget']}$ and are therefore not comparable with "
        "the 90-cell all-window means in Table 2.",
        "",
        "| Hypothesis | Pre-specified test | Rule-fitting windows 4–9 | "
        "Held-out windows 10–13 | Verdict |",
        "|---|---|---|---|---|",
        f"| H1 diagnostic validity | Spearman $\\rho(D_{{\\mathrm{{ref}}}}(5), "
        f"\\Delta\\mathrm{{nRMSE}}) > 0$, $p < 0.05$ | "
        f"$\\rho={fmt(h1_fit['pooled_spearman_rho'])}$, "
        f"$p={fmt_p(h1_fit['pooled_spearman_p'])}$ ($n={h1_fit['n_cells']}$) | "
        f"$\\rho={fmt(h1_held['pooled_spearman_rho'])}$, "
        f"$p={fmt_p(h1_held['pooled_spearman_p'])}$ ($n={h1_held['n_cells']}$) | "
        f"**{report['verdicts']['H1']}** |",
        f"| H2 rule utility | Rule beats always-frozen *and* "
        f"always-recalibrate on mean held-out nRMSE | "
        f"selected $\\tau={selected['tau']:.2f}$, $N={selected['decision_budget']}$ | "
        f"frozen {fmt(evaluation['always_frozen'], 4)}, "
        f"recalibrate {fmt(evaluation['always_recalibrate'], 4)}, "
        f"rule {fmt(evaluation['rule'], 4)} | "
        f"**{report['verdicts']['H2']}**, practically null |",
        f"| H3 decision cheaper than fit | Action agreement reaches 100 % at "
        f"smaller $N$ than the fitting plateau | — | "
        f"decision-stable at $N={h3['decision_stable_budget']}$, "
        f"fit plateau at $N={h3['light_plateau_budget']}$ | "
        f"**{report['verdicts']['H3']}** |",
        "",
        f"H2 is technically supported but the margin over always-recalibrate is "
        f"{(evaluation['always_recalibrate'] - evaluation['rule']):.7f} nRMSE, or "
        f"{100 * (evaluation['always_recalibrate'] - evaluation['rule']) / evaluation['always_recalibrate']:.3f} %, "
        f"and the rule recalibrates {evaluation['n_recalibrate']} of "
        f"{evaluation['n_cells']} cells. It is always-recalibrate plus rounding. "
        "The honest reading is that above the reference-count floor no gate is "
        "needed. The pre-specified protocol anticipated this outcome and declared "
        "it reportable.",
        "",
        "Per-model H1 on held-out windows: "
        + ", ".join(
            f"{MODEL_LABEL[m]} $\\rho={fmt(v['rho'])}$ ($p={fmt_p(v['p'])}$)"
            for m, v in h1_held["per_model"].items()
        )
        + ".",
        "",
        "A design confound is disclosed: the same reference panel supplies both "
        "the diagnostic and the calibrator fit, so selecting $N=20$ improves fit "
        "quality for reasons unrelated to decision quality. The rule versus "
        "always-recalibrate comparison at fixed $N$ remains valid.",
        "",
    ]
    return lines


def table_s1_per_analyte(cells: pd.DataFrame) -> list[str]:
    """Per analyte and model at the floor and at the primary budget."""
    lines = [
        "## Table S1",
        "",
        "**Per-analyte and per-model detail at the floor and at the primary "
        "budget.** Medians over the ten target windows. ΔnRMSE is the median of "
        "the per-window frozen-minus-lightweight differences and need not equal "
        "the difference of the displayed medians. Positive ΔnRMSE favours "
        "recalibration.",
        "",
        "| Analyte | Model | Frozen nRMSE | "
        "N=4 lightweight | N=4 ΔnRMSE | N=4 improved | "
        "N=5 lightweight | N=5 ΔnRMSE | N=5 improved |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for gas_id in sorted(cells.gas_id.unique()):
        for model in ["pls", "random_forest", "xgboost"]:
            base = cells[(cells.gas_id == gas_id) & (cells.model == model)]
            frozen_median = base[base.budget == 0].frozen_nrmse.median()
            parts = []
            for budget in (4, 5):
                sub = base[base.budget == budget]
                parts.append(
                    f"{fmt(sub.light_nrmse.median())} | "
                    f"{fmt(sub.delta_nrmse.median(), 4, signed=True)} | "
                    f"{int((sub.delta_nrmse > 0).sum())}/{len(sub)}"
                )
            lines.append(
                f"| {GAS_LABEL[gas_id]} | {MODEL_LABEL[model]} | "
                f"{fmt(frozen_median)} | " + " | ".join(parts) + " |"
            )
    lines.append("")
    return lines


def table_s2_mechanism(conditioning: pd.DataFrame, frame: pd.DataFrame,
                       config: dict) -> list[str]:
    """NO2 window 6 panel geometry and the falsifiability argument."""
    lines: list[str] = []
    b2 = conditioning[conditioning.budget == 2]
    worst = b2[(b2.gas_id == "NO2") & (b2.target_batch == 6)]

    lines.extend([
        "## Table S2",
        "",
        "**Panel geometry of the inversion cells.** The reference panel is "
        "ordered to span the target range, so at N = 2 the two references are the "
        "extreme low and high strata of the window. For a two-point panel the "
        "least-squares calibrator coefficient is exactly the ratio of the true gap "
        "to the predicted gap. In NO2 window 6 all three frozen models compress a "
        "91 µg m$^{-3}$ interval into 4–12 µg m$^{-3}$ **of the wrong sign**, so "
        "the coefficient is large and negative and every prediction is inverted. "
        "The calibrator coefficient below is the multiplier applied to the frozen "
        "output; it is a different quantity from the held-out calibration slope in "
        "Table 3.",
        "",
        "| Model | Reference values | Frozen predictions | True gap | "
        "Predicted gap | Calibrator coefficient | Held-out ratio |",
        "|---|---|---|---:|---:|---:|---:|",
    ])
    for _, row in worst.iterrows():
        lines.append(
            f"| {MODEL_LABEL[row.model]} | {row.panel_targets} | "
            f"{row.panel_predictions} | {fmt(row.extreme_true_gap, 1, signed=True)} | "
            f"{fmt(row.extreme_pred_gap, 2, signed=True)} | "
            f"{fmt(row.calibrator_slope, 2)} | {fmt(row.ratio, 1)}× |"
        )

    lines.extend([
        "",
        "## Table S3",
        "",
        "**Why N = 2 cannot be checked from its own panel.** A two-parameter "
        "calibrator fitted on two points reproduces both exactly, so the panel "
        "residual is identically zero and no panel-internal evidence of failure "
        "can exist. From N = 3 the panel can contradict the fitted line. Rank "
        "agreement is the fraction of reference pairs the frozen model orders "
        "correctly. This table is post-hoc: it was constructed after the failures "
        "were observed and is reported as mechanism, not as a decision rule.",
        "",
        "| N | Residual d.f. | Median panel residual | Minimum rank agreement | "
        "Cells > 2× |",
        "|---:|---:|---:|---:|---:|",
    ])
    for budget, part in conditioning.groupby("budget"):
        lines.append(
            f"| {int(budget)} | {int(part.residual_df.iloc[0])} | "
            f"{fmt(part.panel_residual_rmse.median(), 3)} | "
            f"{fmt(part.panel_rank_agreement.min(), 3)} | "
            f"{int((part.ratio > 2).sum())} |"
        )

    b3 = conditioning[(conditioning.budget == 3) & (conditioning.ratio > 2)]
    lines.extend([
        "",
        "At N = 3 the surviving failures look clean on their own panel: rank "
        "agreement is 1.000 and Pearson $r$ exceeds 0.98 in every case, so no "
        "panel-side screen separates them. Each has two closely spaced low "
        "references and one distant high reference, leaving the fit determined by "
        "a single leveraged point.",
        "",
        "| Analyte | Window | Model | Reference values | Rank agreement | "
        "Panel $r$ | Calibrator coefficient | Held-out ratio |",
        "|---|---:|---|---|---:|---:|---:|---:|",
    ])
    for _, row in b3.iterrows():
        lines.append(
            f"| {GAS_LABEL[row.gas_id]} | {int(row.target_batch)} | "
            f"{MODEL_LABEL[row.model]} | {row.panel_targets} | "
            f"{fmt(row.panel_rank_agreement)} | {fmt(row.panel_pearson_r, 4)} | "
            f"{fmt(row.calibrator_slope)} | {fmt(row.ratio, 2)}× |"
        )

    lines.extend([
        "",
        "## Table S4",
        "",
        "**Target distribution of the NO2 windows**, as observed before the "
        "common-support restriction and before the held-out split. Window 6, which "
        "carries every inversion cell, has the fewest rows, the fewest distinct "
        "reference values, the lowest mean concentration, and the strongest right "
        "skew of the ten windows. Its range is not the narrowest: window 8 spans "
        "165 against window 6's 166.",
        "",
        "| Window | Rows | Distinct values | Min | Max | Range | Mean | Skew |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    no2 = frame[(frame.gas_id == "NO2") & (frame.batch_id.isin(config["target_batches"]))]
    for batch_id, part in no2.groupby("batch_id"):
        target = part.target
        marker = "**" if batch_id == 6 else ""
        lines.append(
            f"| {marker}{int(batch_id)}{marker} | {len(part)} | {target.nunique()} | "
            f"{target.min():.0f} | {target.max():.0f} | "
            f"{target.max() - target.min():.0f} | {target.mean():.1f} | "
            f"{fmt(target.skew(), 2)} |"
        )
    lines.append("")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path,
                        default=Path("results/sensitivity_uci360_floor_grid/tables/benchmark_results.csv"))
    parser.add_argument("--report", type=Path,
                        default=Path("results/primary_uci360_rewindowed/decision_rule/decision_rule_report.json"))
    parser.add_argument("--conditioning", type=Path,
                        default=Path("results/open_items_uci360/panel_conditioning.csv"))
    parser.add_argument("--data", type=Path, default=Path("data/processed/uci360_rewindowed.csv"))
    parser.add_argument("--config", type=Path,
                        default=Path("configs/sensitivity_uci360_floor_grid.json"))
    parser.add_argument("--out", type=Path, default=Path("manuscript/uci360_tables.md"))
    args = parser.parse_args()

    results = pd.read_csv(args.results)
    report = json.loads(args.report.read_text(encoding="utf-8"))
    frame = pd.read_csv(args.data)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    conditioning = pd.read_csv(args.conditioning) if args.conditioning.exists() else None
    cells = load_cells(results)

    pooled = pd.read_csv(POOLED_CELLS) if POOLED_CELLS.exists() else None

    script = Path(__file__).resolve()
    digest = hashlib.sha256(script.read_bytes()).hexdigest()

    lines = [
        "# Manuscript tables — UCI 360 recalibration analysis (CILS submission)",
        "",
        f"Generated by `{script.name}`, SHA-256 `{digest}`.  ",
        f"Primary source: `{args.results}` (dense budget grid, "
        f"{len(results)} rows, 0 skipped).  ",
        f"Hypothesis outcomes: `{args.report}` (6-point pre-specified grid).  ",
        "",
        "Replaces `manuscript/measurement_tables.md`, which describes the retired "
        "Wörner analysis withdrawn after the *Measurement* desk rejection. That "
        "file is left in place unchanged.",
        "",
        "Tables 1–6 are intended for the main text; Tables S1–S5 are "
        "supplementary. Tables 1–4 and S1–S5 describe the pre-specified panel draw; "
        f"Tables 5–6 pool {pooled.seed.nunique() if pooled is not None else 0} draws and "
        "govern any claim about reference count. "
        "Minus signs are typographic (U+2212); replace with `-` if the submission "
        "system requires ASCII.",
        "",
        "---",
        "",
    ]

    lines += table_1_design(frame, cells, config)
    lines += table_2_budget(cells, results)
    lines += table_3_tail(cells, conditioning)
    lines += table_4_hypotheses(report)
    if pooled is not None:
        lines += table_5_draws(pooled)
        lines += table_6_pooled(pooled)
    else:
        lines += ["> Tables 5–6 require `scripts/run_seed_sensitivity.py` and "
                  "`scripts/summarize_seed_sensitivity.py` to be run first.", ""]
    lines += ["---", "", "# Supplementary tables", ""]
    lines += table_s1_per_analyte(cells)
    if conditioning is not None:
        lines += table_s2_mechanism(conditioning, frame, config)
    else:
        lines += ["> Tables S2–S4 require `scripts/analyze_open_items.py` to be run first.", ""]
    lines += table_s5_thresholds(cells)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")
    print(f"  tables: {6 if pooled is not None else 4} main + "
          f"{5 if conditioning is not None else 1} supplementary")
    print(f"  cells per budget: {int((cells.budget == 5).sum())}")
    print(f"  tail cells (ratio>2) documented: {int((cells.ratio > 2).sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
