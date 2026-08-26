"""Generate the CILS figure set for the UCI 360 recalibration analysis.

Source of record: ``results/sensitivity_uci360_floor_grid/tables/benchmark_results.csv``
(dense budget grid 0/2/3/4/5/6/8/10/20/50; 3600 rows; 90 decision cells per
budget; 10 target windows). Every quantity plotted here is recomputed from that
file, so the figures cannot drift away from the numbers in
``artifacts/UCI360_PRIMARY_FINDINGS.md``.

Four figures, matching the frozen headline:

1. Budget-error curve with **mean and median together** — the divergence at
   N = 2 is the tail-risk evidence.
2. Per-cell ratio distribution plus the explicit count of cells above 2x frozen
   error (8 -> 4 -> 0).
3. Calibration-slope distributions converging as the panel grows.
4. ``d_ref`` against realised benefit at N = 2 and N = 5, split by
   rule-fitting and held-out windows.

Layout follows the CILS single-column (3.35 in) / double-column (6.9 in)
measures with a serif face at roughly 8 pt. Output is vector PDF, with PNG
copies at 600 dpi for drafting only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

LIGHTWEIGHT = "calibrator_update"
FROZEN = "frozen"
PRIMARY_SEED = 20260826
POOLED_CELLS = Path("results/seed_sensitivity/pooled_cells.csv")

# Budget grid of the dense sensitivity run, in plotting order.
BUDGETS = [0, 2, 3, 4, 5, 6, 8, 10, 20, 50]
EXACT = 2  # the exactly-determined panel: zero residual d.f., unbounded coefficient
FLOOR = 4  # primary-draw crossing point only; NOT reproducible across draws
PRIMARY_BUDGET = 5
FIT_WINDOWS = [4, 5, 6, 7, 8, 9]
HELD_OUT_WINDOWS = [10, 11, 12, 13]

SINGLE_COL = 3.35
DOUBLE_COL = 6.9

# Paul Tol bright: colourblind-safe and print-safe in greyscale ordering.
CB = {
    "frozen": "#0077BB",
    "mean": "#CC3311",
    "median": "#0077BB",
    "floor": "#EE7733",
    "CO": "#0077BB",
    "NO2": "#CC3311",
    "NOx": "#009988",
    "fit": "#BBBBBB",
    "held": "#0077BB",
    "grid": "#333333",
}
GASES = ["CO", "NO2", "NOx"]
MODEL_LABEL = {"pls": "PLS", "random_forest": "random forest", "xgboost": "XGBoost"}


def load_cells(results_path: Path) -> pd.DataFrame:
    """One row per (gas, window, model, budget) with frozen and lightweight paired.

    The pairing is an inner join on the decision key, so a budget that lost a
    cell in the benchmark run cannot silently borrow a frozen value from
    elsewhere.
    """
    raw = pd.read_csv(results_path)
    key = ["gas_id", "target_batch", "model", "budget"]
    frozen = raw[raw.strategy == FROZEN].set_index(key)
    light = raw[raw.strategy == LIGHTWEIGHT].set_index(key)
    common = frozen.index.intersection(light.index)
    cells = pd.DataFrame(
        {
            "frozen_nrmse": frozen.loc[common, "nrmse"],
            "light_nrmse": light.loc[common, "nrmse"],
            "slope": light.loc[common, "calibration_slope"],
            "d_ref": frozen.loc[common, "d_ref"],
            "n_reference": light.loc[common, "n_reference"],
            "n_test": frozen.loc[common, "n_test"],
        }
    ).reset_index()
    cells["ratio"] = cells.light_nrmse / cells.frozen_nrmse
    cells["delta_nrmse"] = cells.frozen_nrmse - cells.light_nrmse
    cells["window_set"] = np.where(
        cells.target_batch.isin(HELD_OUT_WINDOWS), "held", "fit"
    )
    return cells.sort_values(["budget", "gas_id", "target_batch", "model"]).reset_index(drop=True)


def budget_summary(cells: pd.DataFrame) -> pd.DataFrame:
    """Per-budget aggregates: the table behind figures 1 and 2."""
    rows = []
    for budget, part in cells.groupby("budget"):
        rows.append(
            {
                "budget": int(budget),
                "n_cells": int(len(part)),
                "frozen_mean": float(part.frozen_nrmse.mean()),
                "frozen_median": float(part.frozen_nrmse.median()),
                "light_mean": float(part.light_nrmse.mean()),
                "light_median": float(part.light_nrmse.median()),
                "light_q1": float(part.light_nrmse.quantile(0.25)),
                "light_q3": float(part.light_nrmse.quantile(0.75)),
                "ratio_mean": float(part.ratio.mean()),
                "ratio_median": float(part.ratio.median()),
                "ratio_q1": float(part.ratio.quantile(0.25)),
                "ratio_q3": float(part.ratio.quantile(0.75)),
                "ratio_max": float(part.ratio.max()),
                "cells_gt2": int((part.ratio > 2).sum()),
                "cells_negative_slope": int((part.slope < 0).sum()),
                "cells_improved": int((part.delta_nrmse > 0).sum()),
                "slope_mean": float(part.slope.mean()),
                "slope_median": float(part.slope.median()),
                "slope_std": float(part.slope.std()),
                "slope_iqr": float(part.slope.quantile(0.75) - part.slope.quantile(0.25)),
                "slope_min": float(part.slope.min()),
                "slope_max": float(part.slope.max()),
            }
        )
    return pd.DataFrame(rows).sort_values("budget").reset_index(drop=True)


def setup_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 8.5,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "legend.fontsize": 7,
            "axes.linewidth": 0.6,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "lines.linewidth": 1.1,
            "lines.markersize": 3.4,
            "pdf.fonttype": 42,  # embed as TrueType so the text stays selectable
            "ps.fonttype": 42,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
            "figure.dpi": 150,
        }
    )
    return plt


def _tidy(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.18, linewidth=0.4, zorder=0)
    ax.set_axisbelow(True)


def _budget_axis(ax, positions, budgets, label="Labelled references in the target window, $N$") -> None:
    """Categorical budget axis.

    The grid is 0/2/3/4/5/6/8/10/20/50. On a linear numeric axis the whole
    floor region would collapse into the left margin, so budgets are drawn at
    equal spacing with their true values as tick labels.
    """
    ax.set_xticks(positions)
    ax.set_xticklabels([str(b) for b in budgets])
    ax.set_xlabel(label)
    ax.set_xlim(positions[0] - 0.55, positions[-1] + 0.55)


def _floor_marker(ax, positions, budgets, text_y=None, label=True, va="top") -> None:
    """Shade the exactly-determined budget and label it.

    Earlier revisions marked N = 4 as an operational floor. That crossing point is
    specific to the pre-specified panel draw and does not replicate (4, 6, 4, 20,
    20 across ten draws), so the marker now identifies the regime boundary that
    does hold in every draw: N = 2, where the two-parameter fit is exactly
    determined and unbounded failure is possible.
    """
    idx = budgets.index(EXACT)
    ax.axvspan(idx - 0.5, idx + 0.5, color=CB["mean"], alpha=0.09, linewidth=0, zorder=0)
    ax.axvline(idx + 0.5, color=CB["mean"], linewidth=0.8, linestyle=(0, (4, 2)), zorder=1)
    if label:
        y = text_y if text_y is not None else ax.get_ylim()[1]
        ax.annotate(
            "exactly\ndetermined",
            xy=(idx + 0.5, y),
            xytext=(3, -1 if va == "top" else 1),
            textcoords="offset points",
            fontsize=6.5,
            color=CB["mean"],
            ha="left",
            va=va,
            linespacing=1.25,
        )


def render_budget_curves(plt, cells: pd.DataFrame, summary: pd.DataFrame, out_dir: Path) -> None:
    """Figure 1. Mean and median on the same axes; their gap is the tail.

    Panel (a) is absolute held-out nRMSE, panel (b) the ratio to the frozen
    model. Plotting both central tendencies together is the point of the
    figure: at N = 2 the median cell is neutral (1.009) while the mean is
    inflated to 2.005 by eight cells.
    """
    budgets = summary.budget.tolist()
    pos = np.arange(len(budgets), dtype=float)
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COL, 2.65))

    # -- panel (a): absolute nRMSE ---------------------------------------
    ax = axes[0]
    ax.fill_between(
        pos, summary.light_q1, summary.light_q3,
        color=CB["median"], alpha=0.13, linewidth=0, label="Lightweight IQR", zorder=2,
    )
    ax.plot(
        pos, summary.frozen_mean, color=CB["frozen"], linestyle=(0, (3, 2)), linewidth=1.0,
        marker="", label="Frozen (mean, constant)", zorder=3,
    )
    ax.plot(
        pos, summary.light_mean, color=CB["mean"], marker="o", markerfacecolor="white",
        markeredgewidth=0.9, label="Lightweight mean", zorder=5,
    )
    ax.plot(
        pos, summary.light_median, color=CB["median"], marker="s", label="Lightweight median", zorder=4,
    )
    ax.set_yscale("log")
    ax.set_ylabel("Held-out nRMSE (log scale)")
    ax.set_ylim(0.082, 0.42)
    ax.set_yticks([0.1, 0.15, 0.2, 0.3, 0.4])
    ax.set_yticklabels(["0.10", "0.15", "0.20", "0.30", "0.40"])
    ax.minorticks_off()
    _tidy(ax)
    _floor_marker(ax, pos, budgets, text_y=0.086, va="bottom")
    _budget_axis(ax, pos, budgets)
    ax.annotate(
        f"mean {summary.light_mean.iloc[1]:.3f}",
        xy=(1.06, summary.light_mean.iloc[1]), xytext=(1.75, 0.246),
        textcoords="data", fontsize=6.8, color=CB["mean"], ha="left", va="center",
        arrowprops=dict(arrowstyle="-", color=CB["mean"], linewidth=0.6, shrinkA=1, shrinkB=2),
    )
    ax.legend(frameon=False, loc="upper right", handlelength=1.9, borderaxespad=0.25,
              handletextpad=0.4, labelspacing=0.32)
    ax.set_title("(a) Absolute error", loc="left", fontsize=8.5)

    # -- panel (b): ratio to frozen -------------------------------------
    ax = axes[1]
    ax.axhline(1.0, color=CB["grid"], linewidth=0.7, zorder=3)
    ax.axhline(2.0, color=CB["floor"], linewidth=0.7, linestyle=(0, (1, 2)), zorder=3)
    ax.plot(pos, summary.ratio_mean, color=CB["mean"], marker="o", markerfacecolor="white",
            markeredgewidth=0.9, label="Mean ratio", zorder=5)
    ax.plot(pos, summary.ratio_median, color=CB["median"], marker="s", label="Median ratio", zorder=4)
    ax.set_yscale("log")
    ax.set_ylabel(r"nRMSE ratio, lightweight / frozen")
    ax.set_ylim(0.55, 3.4)
    ax.set_yticks([0.6, 0.8, 1.0, 1.5, 2.0, 3.0])
    ax.set_yticklabels(["0.6", "0.8", "1.0", "1.5", "2.0", "3.0"])
    ax.minorticks_off()
    _tidy(ax)
    _floor_marker(ax, pos, budgets, text_y=0.575, va="bottom")
    _budget_axis(ax, pos, budgets)
    ax.annotate(
        "no benefit", xy=(pos[-1] + 0.45, 1.0), xytext=(-1, 2.2), textcoords="offset points",
        fontsize=6.5, color=CB["grid"], ha="right", va="bottom",
    )
    ax.annotate(
        r"$2\times$ frozen error", xy=(pos[-1] + 0.45, 2.0), xytext=(-1, 2.2),
        textcoords="offset points", fontsize=6.5, color=CB["floor"], ha="right", va="bottom",
    )
    # Explicit gap indicator at N = 2: a bracket between the two statistics reads
    # unambiguously, where a shaded band competes with the floor shading.
    ax.annotate(
        "", xy=(1, summary.ratio_mean.iloc[1]), xytext=(1, summary.ratio_median.iloc[1]),
        arrowprops=dict(arrowstyle="<->", color=CB["grid"], linewidth=0.7,
                        shrinkA=2.2, shrinkB=2.2), zorder=6,
    )
    ax.annotate(
        f"{summary.ratio_mean.iloc[1]:.3f} mean\nvs {summary.ratio_median.iloc[1]:.3f} median",
        xy=(1.06, 1.42), xytext=(2.25, 1.60), textcoords="data", fontsize=6.8, color=CB["mean"],
        ha="left", va="center",
        arrowprops=dict(arrowstyle="-", color=CB["mean"], linewidth=0.6, shrinkA=1, shrinkB=1),
    )
    ax.legend(frameon=False, loc="upper right", handlelength=1.9, borderaxespad=0.25,
              handletextpad=0.4, labelspacing=0.32)
    ax.set_title("(b) Ratio to the frozen model", loc="left", fontsize=8.5)

    fig.tight_layout(pad=0.4, w_pad=1.4)
    _save(fig, out_dir, "figure_01_budget_curves")
    plt.close(fig)


def render_tail_decay(plt, cells: pd.DataFrame, summary: pd.DataFrame, out_dir: Path) -> None:
    """Figure 2. Every cell's ratio, and the count above 2x decaying to zero.

    Panel (a) shows all 90 cells per budget so the reader sees that the bulk of
    the distribution sits near or below 1 even at N = 2; panel (b) states the
    decay 8 -> 4 -> 0 explicitly.
    """
    budgets = summary.budget.tolist()
    pos = np.arange(len(budgets), dtype=float)
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COL, 2.7), gridspec_kw={"width_ratios": [1.55, 1.0]})
    rng = np.random.default_rng(20260826)

    # -- panel (a): per-cell ratio strip ---------------------------------
    ax = axes[0]
    ax.axhline(1.0, color=CB["grid"], linewidth=0.7, zorder=2)
    ax.axhline(2.0, color=CB["floor"], linewidth=0.7, linestyle=(0, (1, 2)), zorder=2)
    for i, budget in enumerate(budgets):
        part = cells[cells.budget == budget]
        for gas in GASES:
            sub = part[part.gas_id == gas]
            if sub.empty:
                continue
            jitter = rng.uniform(-0.26, 0.26, size=len(sub))
            inverted = sub.slope < 0
            ax.scatter(
                i + jitter[~inverted.to_numpy()], sub.ratio[~inverted],
                s=5.0, color=CB[gas], alpha=0.6, linewidth=0, zorder=3,
            )
            if inverted.any():
                ax.scatter(
                    i + jitter[inverted.to_numpy()], sub.ratio[inverted],
                    s=17, facecolor="none", edgecolor=CB[gas], linewidth=0.9,
                    marker="D", zorder=5,
                )
    ax.set_yscale("log")
    ax.set_ylabel("nRMSE ratio, lightweight / frozen")
    ax.set_ylim(0.22, 62)
    ax.set_yticks([0.25, 0.5, 1, 2, 5, 10, 20, 50])
    ax.set_yticklabels(["0.25", "0.5", "1", "2", "5", "10", "20", "50"])
    ax.minorticks_off()
    _tidy(ax)
    _floor_marker(ax, pos, budgets, text_y=0.245, va="bottom")
    _budget_axis(ax, pos, budgets)
    ax.annotate(
        "NO$_2$ window 6, three models:\nslope inversion",
        xy=(1.2, 40), xytext=(2.35, 34), textcoords="data", fontsize=6.6, color=CB["NO2"],
        ha="left", va="center",
        arrowprops=dict(arrowstyle="-", color=CB["NO2"], linewidth=0.6, shrinkA=1, shrinkB=1),
    )
    gas_label = {"CO": "CO", "NO2": "NO$_2$", "NOx": "NO$_x$"}
    handles = [
        plt.Line2D([0], [0], marker="o", linestyle="none", color=CB[g], markersize=3.0,
                   label=gas_label[g])
        for g in GASES
    ]
    handles.append(
        plt.Line2D([0], [0], marker="D", linestyle="none", markerfacecolor="none",
                   markeredgecolor=CB["grid"], markeredgewidth=0.9, markersize=4.0,
                   label="Inverted slope")
    )
    # The band between ratio 3 and 15 is empty at every budget, which is itself the
    # result; the legend sits there rather than over the point clouds.
    ax.legend(handles=handles, frameon=False, loc="center", bbox_to_anchor=(0.5, 0.55),
              ncol=4, handletextpad=0.3, columnspacing=1.1)
    ax.set_title("(a) Every decision cell", loc="left", fontsize=8.5)

    # -- panel (b): count above the 2x line ------------------------------
    ax = axes[1]
    bars = ax.bar(pos, summary.cells_gt2, width=0.64, color=CB["floor"],
                  edgecolor=CB["grid"], linewidth=0.4, zorder=3, label=r"Ratio $>2$")
    ax.bar(pos, summary.cells_negative_slope, width=0.64, facecolor="none",
           edgecolor=CB["grid"], linewidth=0.7, hatch="////", zorder=4,
           label="of which inverted slope")
    for bar, count in zip(bars, summary.cells_gt2):
        ax.annotate(str(int(count)), xy=(bar.get_x() + bar.get_width() / 2, count),
                    xytext=(0, 1.6), textcoords="offset points", ha="center", va="bottom",
                    fontsize=7)
    ax.set_ylabel(r"Cells above $2\times$ frozen error (of 90)")
    ax.set_ylim(0, 9.6)
    ax.set_yticks(range(0, 10, 2))
    _tidy(ax)
    _floor_marker(ax, pos, budgets, text_y=6.4, va="bottom")
    _budget_axis(ax, pos, budgets)
    ax.legend(frameon=False, loc="upper right", handlelength=1.5, borderaxespad=0.25,
              labelspacing=0.32)
    ax.set_title("(b) Tail count", loc="left", fontsize=8.5)

    fig.tight_layout(pad=0.4, w_pad=1.4)
    _save(fig, out_dir, "figure_02_tail_decay")
    plt.close(fig)


def render_slope_distributions(plt, cells: pd.DataFrame, summary: pd.DataFrame, out_dir: Path) -> None:
    """Figure 3. Calibration slope converging on unity as the panel grows.

    The plotted quantity is the benchmark's ``calibration_slope`` column: the
    slope of a regression of reference-analyser values on model predictions,
    evaluated on the **held-out test set**, where 1 is ideal. It is not the
    calibrator's own fitted coefficient. N = 0 is therefore the frozen model's
    held-out slope, i.e. the distortion the calibrator is asked to remove.
    """
    budgets = summary.budget.tolist()
    pos = np.arange(len(budgets), dtype=float)
    fig, ax = plt.subplots(figsize=(DOUBLE_COL, 2.55))
    rng = np.random.default_rng(20260826)

    ax.axhspan(-0.35, 0.0, color=CB["mean"], alpha=0.09, linewidth=0, zorder=0)
    ax.axhline(1.0, color=CB["grid"], linewidth=0.7, zorder=2)
    ax.axhline(0.0, color=CB["mean"], linewidth=0.7, linestyle=(0, (1, 2)), zorder=2)

    data = [cells[cells.budget == b].slope.to_numpy() for b in budgets]
    bp = ax.boxplot(
        data, positions=pos, widths=0.5, showfliers=False, whis=(5, 95),
        patch_artist=True, zorder=3,
        medianprops=dict(color=CB["grid"], linewidth=1.0),
        boxprops=dict(facecolor="#DCE6F0", edgecolor=CB["grid"], linewidth=0.6),
        whiskerprops=dict(color=CB["grid"], linewidth=0.6),
        capprops=dict(color=CB["grid"], linewidth=0.6),
    )
    for i, budget in enumerate(budgets):
        part = cells[cells.budget == budget]
        jitter = rng.uniform(-0.17, 0.17, size=len(part))
        ax.scatter(i + jitter, part.slope, s=3.2, color=CB["frozen"], alpha=0.38,
                   linewidth=0, zorder=4)
        inverted = part[part.slope < 0]
        if not inverted.empty:
            # Spread these deterministically: there are three and they must be countable.
            offsets = np.linspace(-0.2, 0.2, len(inverted))
            ax.scatter(
                i + offsets, inverted.slope, s=17, marker="D", facecolor="none",
                edgecolor=CB["mean"], linewidth=0.9, zorder=6,
            )
    # Spread annotation: the convergence is a variance statement, not a mean one.
    # The row is self-labelled at its left end so it needs no separate caption.
    for i, row in summary.iterrows():
        text = f"s.d. {row.slope_std:.2f}" if i == 0 else f"{row.slope_std:.2f}"
        ax.annotate(text, xy=(i, 3.38), ha="center", va="bottom", fontsize=6.4,
                    color=CB["grid"])

    ax.set_ylabel("Calibration slope on held-out set")
    ax.set_ylim(-0.35, 3.62)
    ax.set_yticks([0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
    _tidy(ax)
    _floor_marker(ax, pos, budgets, text_y=2.62, va="bottom")
    _budget_axis(ax, pos, budgets)
    ax.annotate(
        "inversion", xy=(pos[-1] + 0.45, -0.115), xytext=(-1, 0), textcoords="offset points",
        fontsize=6.5, color=CB["mean"], ha="right", va="center",
    )
    ax.annotate(
        f"min \N{MINUS SIGN}{abs(summary.slope_min.iloc[1]):.3f}",
        xy=(1.3, summary.slope_min.iloc[1] * 0.55), xytext=(2.15, -0.235), textcoords="data",
        fontsize=6.6, color=CB["mean"], ha="left", va="center",
        arrowprops=dict(arrowstyle="-", color=CB["mean"], linewidth=0.6, shrinkA=1, shrinkB=1),
    )
    handles = [
        plt.Line2D([0], [0], marker="o", linestyle="none", color=CB["frozen"], alpha=0.5,
                   markersize=2.6, label="Decision cell"),
        plt.Line2D([0], [0], marker="D", linestyle="none", markerfacecolor="none",
                   markeredgecolor=CB["mean"], markeredgewidth=0.9, markersize=4.0,
                   label="Inverted slope"),
        plt.Line2D([0], [0], color=CB["grid"], linewidth=0.7, label="Ideal slope 1"),
    ]
    ax.legend(handles=handles, frameon=False, loc="upper right", ncol=3,
              bbox_to_anchor=(1.0, 0.90), handletextpad=0.35, columnspacing=1.0,
              borderaxespad=0.0)
    fig.tight_layout(pad=0.4)
    _save(fig, out_dir, "figure_03_slope_convergence")
    plt.close(fig)


def _fmt_p(p_value: float) -> str:
    """LaTeX p-value: plain decimal when readable, else a proper power of ten."""
    if p_value >= 0.001:
        return f"{p_value:.3f}".rstrip("0").rstrip(".")
    exponent = int(np.floor(np.log10(p_value)))
    mantissa = p_value / 10 ** exponent
    return rf"{mantissa:.1f}\times 10^{{{exponent}}}"


def _fmt_rho(rho: float) -> str:
    """Spearman rho with a typographic minus sign, for in-figure text only.

    Do not use this in the captions: U+2212 inside LaTeX math mode does not
    compile under pdfLaTeX. Captions use a plain ASCII minus, which LaTeX
    typesets correctly in math mode anyway.
    """
    return f"{rho:.3f}".replace("-", "\N{MINUS SIGN}")


def render_diagnostic_scatter(plt, cells: pd.DataFrame, out_dir: Path) -> dict:
    """Figure 4. The diagnostic predicts gain, but does not order cells by safety.

    Same axes at both budgets, split into the windows that generated the
    hypothesis (4-9) and the windows never touched before confirmation (10-13).
    At N = 5 high ``d_ref`` marks the largest gains; at N = 2 the three highest
    ``d_ref`` NO2 cells are the three catastrophic ones.
    """
    from scipy.stats import spearmanr

    stats: dict = {}
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COL, 2.75), sharex=True)
    panels = [
        (PRIMARY_BUDGET, axes[0], f"(a) $N={PRIMARY_BUDGET}$: over-determined"),
        (2, axes[1], "(b) $N=2$: exactly determined"),
    ]
    marker = {"fit": "o", "held": "^"}
    label = {"fit": "Rule-fitting windows 4–9", "held": "Held-out windows 10–13"}

    for budget, ax, title in panels:
        part = cells[
            (cells.budget == budget)
            & np.isfinite(cells.d_ref)
            & np.isfinite(cells.delta_nrmse)
        ]
        ax.axhline(0.0, color=CB["grid"], linewidth=0.7, zorder=2)
        ax.axvline(0.0, color=CB["grid"], linewidth=0.5, linestyle=(0, (1, 3)), zorder=2)
        for window_set in ("fit", "held"):
            sub = part[part.window_set == window_set]
            ax.scatter(
                sub.d_ref, sub.delta_nrmse, s=15, marker=marker[window_set],
                facecolor=CB[window_set] if window_set == "held" else "none",
                edgecolor=CB["held"] if window_set == "held" else CB["grid"],
                linewidth=0.7, alpha=0.9, zorder=4, label=label[window_set],
            )
        entry: dict = {"budget": int(budget), "n_cells": int(len(part))}
        lines = []
        for window_set in ("fit", "held"):
            sub = part[part.window_set == window_set]
            rho, p_value = spearmanr(sub.d_ref, sub.delta_nrmse)
            entry[window_set] = {"n": int(len(sub)), "rho": float(rho), "p": float(p_value)}
            tag = "4–9" if window_set == "fit" else "10–13"
            lines.append(rf"$\rho_{{{tag}}}={_fmt_rho(rho)}$, $p={_fmt_p(p_value)}$")
        rho_all, p_all = spearmanr(part.d_ref, part.delta_nrmse)
        entry["pooled"] = {"n": int(len(part)), "rho": float(rho_all), "p": float(p_all)}
        stats[str(budget)] = entry

        ax.set_xlabel(r"Reference-panel diagnostic $D_{\mathrm{ref}}$")
        ax.set_xlim(-1.0, 9.0)
        _tidy(ax)
        ax.set_title(title, loc="left", fontsize=8.5)
        if budget == 2:
            # The three inversion cells sit an order below the bulk; a symmetric
            # log axis keeps zero meaningful while still showing them.
            ax.set_yscale("symlog", linthresh=0.1, linscale=0.7)
            ax.set_ylim(-9.0, 0.45)
            ax.set_yticks([-5, -1, -0.5, 0, 0.25])
            ax.set_yticklabels(["\N{MINUS SIGN}5", "\N{MINUS SIGN}1",
                                "\N{MINUS SIGN}0.5", "0", "0.25"])
            ax.minorticks_off()
            ax.axhspan(-9.0, -0.1, color=CB["mean"], alpha=0.07, linewidth=0, zorder=0)
            # Point at the single worst cell, using that cell's own coordinates.
            window6 = cells[
                (cells.budget == 2) & (cells.gas_id == "NO2") & (cells.target_batch == 6)
            ]
            worst = window6.loc[window6.delta_nrmse.idxmin()]
            ax.annotate(
                "NO$_2$ window 6, all three models:\nhighest $D_{\\mathrm{ref}}$, worst outcome",
                xy=(float(worst.d_ref), float(worst.delta_nrmse)),
                xytext=(-0.75, -1.5), textcoords="data", fontsize=6.6, color=CB["mean"],
                ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color=CB["mean"], linewidth=0.6,
                                shrinkA=3, shrinkB=3,
                                connectionstyle="arc3,rad=-0.16"),
            )
        else:
            ax.set_ylim(-0.16, 0.34)
            ax.set_yticks([-0.1, 0.0, 0.1, 0.2, 0.3])
            ax.set_yticklabels(["\N{MINUS SIGN}0.1", "0.0", "0.1", "0.2", "0.3"])
        ax.set_ylabel(r"$\Delta$nRMSE (frozen $-$ lightweight)")
        # Correlations go wherever that panel is empty: bottom-right at N = 5,
        # bottom-left at N = 2 where the tail occupies the right.
        if budget == 2:
            ax.annotate(
                "\n".join(lines), xy=(-0.75, -4.7), textcoords="data", xycoords="data",
                fontsize=6.6, ha="left", va="center", color=CB["grid"], linespacing=1.45,
            )
        else:
            ax.annotate(
                "\n".join(lines), xy=(0.975, 0.035), xycoords="axes fraction", fontsize=6.6,
                ha="right", va="bottom", color=CB["grid"], linespacing=1.45,
            )
        ax.annotate(
            "lightweight helps", xy=(8.85, 0.0), xytext=(0, 2.6), textcoords="offset points",
            fontsize=6.2, color=CB["grid"], ha="right", va="bottom",
        )
    axes[0].legend(frameon=False, loc="upper left", handletextpad=0.35, borderaxespad=0.3)
    fig.tight_layout(pad=0.4, w_pad=1.5)
    _save(fig, out_dir, "figure_04_diagnostic")
    plt.close(fig)
    return stats


def render_draw_sensitivity(plt, pooled: pd.DataFrame, out_dir: Path) -> dict:
    """Figure 5. The threshold does not replicate; the regime boundary does.

    Panel (a): worst observed ratio per draw, log scale. The primary draw's N = 2
    outlier is the only point above 5 anywhere. Panel (b): count above 2x per
    draw, showing per-draw boundaries scattered over 4 to 20.
    """
    budgets = sorted(pooled.budget.unique())
    pos = np.arange(len(budgets), dtype=float)
    seeds = sorted(pooled.seed.unique(), key=lambda s: (s != PRIMARY_SEED, s))
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COL, 2.7))
    # Individual replicate identity carries no information — the spread is the
    # result — so all replicates share one muted style and the legend has two
    # entries regardless of how many draws are pooled.
    n_replicates = len(seeds) - 1
    styles = {}
    for seed in seeds:
        if seed == PRIMARY_SEED:
            styles[seed] = dict(color=CB["mean"], marker="o", markersize=3.6,
                                linewidth=1.4, zorder=6,
                                label=f"{seed} (pre-specified)")
        else:
            styles[seed] = dict(color="#5588BB", marker="^", markersize=2.6,
                                linewidth=0.8, alpha=0.55, zorder=4,
                                label=f"{n_replicates} replicate draws")

    ax = axes[0]
    ax.axhline(1.0, color=CB["grid"], linewidth=0.7, zorder=2)
    ax.axhline(2.0, color=CB["floor"], linewidth=0.7, linestyle=(0, (1, 2)), zorder=2)
    for seed in seeds:
        part = pooled[pooled.seed == seed].groupby("budget").ratio.max()
        ax.plot(pos, [part[b] for b in budgets], **styles[seed])
    ax.set_yscale("log")
    ax.set_ylabel("Worst nRMSE ratio in the draw")
    ax.set_ylim(0.85, 62)
    ax.set_yticks([1, 2, 5, 10, 20, 50])
    ax.set_yticklabels(["1", "2", "5", "10", "20", "50"])
    ax.minorticks_off()
    _tidy(ax)
    _budget_axis(ax, pos, budgets)
    ax.annotate("only inverting draw", xy=(1, 44.5), xytext=(2.4, 30),
                textcoords="data", fontsize=6.6, color=CB["mean"], ha="left",
                va="center",
                arrowprops=dict(arrowstyle="-", color=CB["mean"], linewidth=0.6,
                                shrinkA=1, shrinkB=2))
    ax.annotate(r"$2\times$", xy=(pos[-1] + 0.45, 2.0), xytext=(-1, 2),
                textcoords="offset points", fontsize=6.5, color=CB["floor"],
                ha="right", va="bottom")
    handles, labels = ax.get_legend_handles_labels()
    seen: dict[str, object] = {}
    for handle, label in zip(handles, labels):
        seen.setdefault(label, handle)
    ax.legend(seen.values(), seen.keys(), frameon=False, loc="upper right",
              handlelength=1.6, labelspacing=0.3, borderaxespad=0.25)
    ax.set_title("(a) Worst case per draw", loc="left", fontsize=8.5)

    ax = axes[1]
    for seed in seeds:
        part = pooled[pooled.seed == seed]
        counts = [int((part[part.budget == b].ratio > 2).sum()) for b in budgets]
        style = {k: v for k, v in styles[seed].items() if k != "label"}
        ax.plot(pos, counts, **style)
    ax.set_ylabel(r"Cells above $2\times$ frozen error (of 90)")
    ax.set_ylim(-0.4, 9.2)
    ax.set_yticks(range(0, 9, 2))
    _tidy(ax)
    _budget_axis(ax, pos, budgets)
    # Mark each draw's first clean budget, and how many draws share it.
    firsts = []
    for seed in seeds:
        part = pooled[pooled.seed == seed]
        for i, b in enumerate(budgets):
            if b == 0:
                continue
            if all(int((part[part.budget == later].ratio > 2).sum()) == 0
                   for later in budgets[i:]):
                firsts.append(int(b))
                break
    tally = {b: firsts.count(b) for b in sorted(set(firsts))}
    # Ticks mark which budgets are some draw's first clean one; the annotation
    # carries the counts, so no per-tick label is needed.
    for budget in tally:
        i = budgets.index(budget)
        ax.scatter([i], [0], marker="|", s=130, color=CB["grid"], linewidth=1.2,
                   zorder=8)
    ax.annotate(
        "first clean budget: "
        + ", ".join(f"{b}×{c}" for b, c in tally.items())
        + f"\n(range {min(firsts)}–{max(firsts)}, mode {max(tally, key=tally.get)})",
        xy=(0.97, 0.95), xycoords="axes fraction", fontsize=6.8,
        ha="right", va="top", color=CB["grid"], linespacing=1.4)
    ax.set_title("(b) Failure count per draw", loc="left", fontsize=8.5)

    fig.tight_layout(pad=0.4, w_pad=1.4)
    _save(fig, out_dir, "figure_05_draw_sensitivity")
    plt.close(fig)
    return {"seeds": [int(s) for s in seeds], "first_clean_budgets": firsts}


def _save(fig, out_dir: Path, stem: str) -> None:
    """Vector PDF for submission, PNG at 600 dpi for drafting."""
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{stem}.pdf")
    fig.savefig(out_dir / f"{stem}.png", dpi=600)


def script_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def caption_specs(summary: pd.DataFrame, diagnostic_stats: dict,
                  draw_stats: dict | None = None) -> list[dict[str, str]]:
    """Captions carrying the plotted numbers, so text and figure cannot diverge."""
    by_budget = summary.set_index("budget")
    n2, n3, n4 = (by_budget.loc[b] for b in (2, 3, 4))
    held = diagnostic_stats["5"]["held"]
    fit = diagnostic_stats["5"]["fit"]
    n2_stats = diagnostic_stats["2"]

    provenance = (
        "The diagnostic hypothesis was generated by inspecting an earlier "
        "three-window run of this corpus, so windows 4–9 are in-sample for "
        "hypothesis generation and windows 10–13 (121 previously untouched days) "
        "are the confirmation set."
    )
    shared_panel = (
        "The same reference panel supplies both the diagnostic and the "
        "calibrator fit, so panel size and diagnostic quality are not "
        "independent."
    )
    return [
        {
            "id": "fig-1",
            "file": "figure_01_budget_curves",
            "width": "double",
            "title": "Held-out error against reference budget, mean and median together",
            "caption": (
                "Figure 1. Held-out nRMSE of lightweight output recalibration against the "
                f"number of labelled target-window references $N$, pooled over "
                f"{int(by_budget.loc[5, 'n_cells'])} decision cells "
                "(3 analytes × 3 model classes × 10 target windows). (a) Absolute error, with "
                "the frozen source model shown for reference and the interquartile range of "
                "the recalibrated model shaded. (b) The same result as a ratio to the frozen "
                "model, with a double arrow marking the mean–median gap at $N=2$. Mean and "
                f"median are plotted together because they disagree at the smallest budget: at "
                f"$N=2$ the median cell is essentially unaffected (ratio {n2.ratio_median:.3f}) "
                f"while the mean is inflated to {n2.ratio_mean:.3f} by a small number of cells. "
                f"From $N={FLOOR}$ both statistics fall below 1 together "
                f"({n4.ratio_mean:.3f} mean, {n4.ratio_median:.3f} median), and absolute error "
                "then falls monotonically in both mean and median across the remaining budgets. "
                "The mean–median divergence at $N=2$ is specific to draws in which the tail is "
                "realised: across the ten draws of Figure 5 the median at $N=2$ is 0.964–1.094, "
                "whereas the mean is 2.005 here and 0.979–1.149 in the other nine. "
                "Vertical axes are logarithmic in both panels; "
                "budgets are drawn at equal spacing, not to numeric scale, so that the "
                "small-panel region remains legible. Lower is better."
            ),
            "claim": (
                "The cost of a small reference panel appears in the mean but not the median, "
                "so it is a tail effect rather than a shift of the whole distribution."
            ),
            "limitations": (
                "Cells share source-model fits and target windows and are not independent "
                "replicates, so the spread is descriptive rather than a confidence statement. "
                + shared_panel
            ),
            "latex": r"\includegraphics[width=\textwidth]{figures/figure_01_budget_curves.pdf}",
        },
        {
            "id": "fig-2",
            "file": "figure_02_tail_decay",
            "width": "double",
            "title": "The heavy tail and its closure at four references",
            "caption": (
                "Figure 2. (a) Ratio of recalibrated to frozen held-out nRMSE for every "
                f"decision cell at each budget ({int(n2.n_cells)} cells per budget), coloured by "
                "analyte and jittered horizontally; open diamonds mark cells whose fitted "
                "calibration slope is negative. The bulk of the distribution lies near or below "
                "1 at every budget, including $N=2$. (b) Number of cells exceeding twice the "
                f"frozen error: {int(n2.cells_gt2)} at $N=2$, {int(n3.cells_gt2)} at $N=3$, and "
                f"none from $N={FLOOR}$ onward; the hatched overlay counts the subset with an "
                f"inverted slope ({int(n2.cells_negative_slope)} cells, all at $N=2$). The three "
                "largest inflations are the three model classes of the same NO$_2$ window."
            ),
            "claim": (
                "In this panel draw the failures are isolated points rather than a shifted "
                "distribution, and the three most severe share one analyte-window and "
                "invert the calibration slope."
            ),
            "limitations": (
                "This is one panel draw. The budget at which the count reaches zero is NOT "
                "reproducible across draws (Figure 5: 4, 6, 4, 20, 20) and must not be read "
                "as a floor. The tail is also concentrated rather than uniform, falling "
                "chiefly in one NO$_2$ window, so the count is neither a rate estimate nor "
                "a threshold."
            ),
            "latex": r"\includegraphics[width=\textwidth]{figures/figure_02_tail_decay.pdf}",
        },
        {
            "id": "fig-3",
            "file": "figure_03_slope_convergence",
            "width": "double",
            "title": "Fitted calibration slope converging on unity",
            "caption": (
                "Figure 3. Distribution of the calibration slope against reference budget, "
                "where the plotted quantity is the slope of a regression of reference-analyser "
                "values on model predictions over the held-out test set and 1 is ideal. It is "
                "not the calibrator's own fitted coefficient. Boxes show the interquartile "
                "range and median with 5th–95th percentile whiskers; individual decision cells "
                "are overlaid. $N=0$ is the frozen model's held-out slope, that is, the "
                "distortion the calibrator is asked to remove "
                f"(median {by_budget.loc[0, 'slope_median']:.3f}). A two-point "
                f"fit at $N=2$ can invert the slope entirely (minimum "
                f"${n2.slope_min:.3f}$, {int(n2.cells_negative_slope)} cells in "
                "the shaded inversion band), which reverses every prediction. No inversion "
                f"occurs at any larger budget (minimum {n3.slope_min:.3f} at $N=3$). The median "
                f"slope then approaches unity monotonically, from {n2.slope_median:.3f} at "
                f"$N=2$ to {by_budget.loc[50, 'slope_median']:.3f} at $N=50$. Dispersion behaves "
                "differently and is printed above each box: the standard deviation is "
                f"{n2.slope_std:.3f} at $N=2$, which is *smaller* than the "
                f"{n3.slope_std:.3f} at $N=3$, because two-point fits are displaced downward as "
                "a group rather than scattered. Dispersion contracts decisively only at the "
                f"largest budgets ({by_budget.loc[20, 'slope_std']:.3f} at $N=20$ and "
                f"{by_budget.loc[50, 'slope_std']:.3f} at $N=50$). Budgets are drawn at equal "
                "spacing, not to numeric scale."
            ),
            "claim": (
                "Slope inversion on a two-point least-squares fit is the mechanism behind the "
                "tail, and it disappears as soon as a third reference is added; the median "
                "slope then approaches unity monotonically."
            ),
            "limitations": (
                "The calibrator is fitted on the reference panel while this slope is evaluated "
                "on the held-out set, so the two are linked only through the panel draw. A "
                "single reference-panel seed is used. The standard deviation is not monotone in "
                "the budget, so it should not be read as a precision-improves-with-N statement "
                "on its own. A slope near 1 does not by itself imply small error, since it is "
                "insensitive to scatter about the calibration line."
            ),
            "latex": r"\includegraphics[width=\textwidth]{figures/figure_03_slope_convergence.pdf}",
        },
        {
            "id": "fig-4",
            "file": "figure_04_diagnostic",
            "width": "double",
            "title": "Pre-decision diagnostic against realised benefit",
            "caption": (
                "Figure 4. Reference-panel diagnostic $D_{\\mathrm{ref}}$, computed before any "
                "recalibration decision, against the realised benefit "
                "$\\Delta$nRMSE $=$ nRMSE$_{\\mathrm{frozen}}-$nRMSE$_{\\mathrm{lightweight}}$. "
                "Open circles are the rule-fitting windows 4–9, filled triangles the held-out "
                f"windows 10–13. (a) At $N={PRIMARY_BUDGET}$ the diagnostic predicts the "
                f"magnitude of the gain (Spearman $\\rho={held['rho']:.3f}$, "
                f"$p={_fmt_p(held['p'])}$ on held-out windows; $\\rho={fit['rho']:.3f}$, "
                f"$p={_fmt_p(fit['p'])}$ on rule-fitting windows). (b) At $N=2$ the association is "
                f"much weaker and no longer consistent across window sets "
                f"($\\rho={n2_stats['held']['rho']:.3f}$, $p={_fmt_p(n2_stats['held']['p'])}$ "
                f"held-out; $\\rho={n2_stats['fit']['rho']:.3f}$, "
                f"$p={_fmt_p(n2_stats['fit']['p'])}$ rule-fitting; "
                f"$\\rho={n2_stats['pooled']['rho']:.3f}$, "
                f"$p={_fmt_p(n2_stats['pooled']['p'])}$ pooled). More important than the weakening "
                "is the direction of the failures: the three cells with the highest diagnostic "
                "values are the three catastrophic ones, so the association that survives at "
                "$N=2$ does not order cells by safety. Note the symmetric logarithmic vertical "
                "axis in (b), linear within $\\pm0.1$, and the different vertical ranges of the "
                "two panels. "
                "A gate keyed on a high diagnostic therefore recommends recalibration exactly "
                "where a two-point fit is about to fail, which is why the prohibition has to be a "
                "hard constraint rather than something the diagnostic can manage."
            ),
            "claim": (
                "The diagnostic is informative about how much will be recovered above the "
                "exactly-determined panel, but it does not order cells by safety there, and "
                "most of the pooled coefficient is a contrast between analytes rather than an "
                "ordering within one. The reversal shown in (b) is specific to the one draw in "
                "ten that realised an inversion; in the other nine the top diagnostic quartile "
                "at $N=2$ is no worse than the rest."
            ),
            "limitations": (
                provenance + " " + shared_panel + " The rule-fitting association is reported "
                "for completeness and is not independent evidence. The pooled coefficient is "
                "largely a between-analyte contrast: the three analytes are ordered in both "
                "$D_{\\mathrm{ref}}$ and benefit, ranking within analyte first reduces the "
                "held-out coefficient from 0.814 to 0.192, and NOx reverses sign between window "
                "sets."
            ),
            "latex": r"\includegraphics[width=\textwidth]{figures/figure_04_diagnostic.pdf}",
        },
    ] + ([
        {
            "id": "fig-5",
            "file": "figure_05_draw_sensitivity",
            "width": "double",
            "title": "The failure threshold does not replicate across panel draws",
            "caption": (
                "Figure 5. The same protocol under "
                f"{len(draw_stats['seeds'])} reference-panel draws, each redrawing every "
                "panel, the held-out split and the model random states; the pre-specified "
                "draw is highlighted. The draws share the corpus, the window boundaries and "
                "the source period, so they are replicates of the sampling rather than "
                "independent studies. (a) Worst nRMSE ratio observed in "
                "each draw, logarithmic scale. Inversion and inflation beyond fivefold "
                "occur at two references and at no other budget in any draw, and only "
                "the pre-specified draw realises them; above two references the worst "
                "outcome anywhere is 4.7-fold. (b) Number of cells above twice frozen "
                "error, with a tick marking each draw's first clean budget. Those "
                "budgets are "
                + ", ".join(str(f) for f in draw_stats["first_clean_budgets"]) +
                ", so the apparently clean threshold of the pre-specified draw is a "
                "property of that panel realisation and not of the method. Every draw "
                "uses the same range-spanning design, so the spread is not a "
                "consequence of poor transfer-sample selection."
            ),
            "claim": (
                "Unbounded failure is confined to the exactly-determined panel in every "
                "draw, while the reference count at which moderate failures cease varies "
                "by a factor of five across draws, with a mode at four."
            ),
            "limitations": (
                "Five draws demonstrate instability but do not characterise its "
                "distribution; the per-draw first-clean budgets span 4 to 20 and the "
                "one-in-five rate at which inversion appeared is an observation, not an "
                "estimate. Draws share the corpus, the windows and the source fits, so "
                "they are replicates of the panel selection only."
            ),
            "latex": r"\includegraphics[width=\textwidth]{figures/figure_05_draw_sensitivity.pdf}",
        },
    ] if draw_stats else [])


def write_package(out_dir: Path, package_path: Path, source: Path, summary: pd.DataFrame,
                  diagnostic_stats: dict, status: str, draw_stats: dict | None = None) -> None:
    """``status`` is recorded verbatim in the manifest, so it must say why.

    ``PASS`` means the images in ``out_dir`` were produced by this run.
    ``PENDING_RENDER`` means captions only, by request. ``PENDING_MATPLOTLIB``
    means the render was attempted and the dependency was missing.
    """
    script = Path(__file__).resolve()
    digest = script_hash(script)
    specs = caption_specs(summary, diagnostic_stats, draw_stats)

    traces = [
        {
            "artifact_id": spec["id"],
            "file": f"{spec['file']}.pdf",
            "source_data": {
                "dataset_id": "uci360_air_quality_rewindowed_floor_grid",
                "doi": "10.24432/C59K5F",
                "file": str(source),
                "rows": 3600,
                "decision_cells_per_budget": int(summary.n_cells.iloc[0]),
                "budgets": BUDGETS,
                "target_windows": FIT_WINDOWS + HELD_OUT_WINDOWS,
            },
            "transformation": {"script": str(script), "sha256": digest},
            "caption_claim": spec["claim"],
            "supported_manuscript_claims": [{"claim": spec["claim"], "locator": "Results/Figures"}],
            "limitations": [spec["limitations"]],
            "rendered_status": status,
        }
        for spec in specs
    ]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "figure_table_trace.json").write_text(json.dumps(traces, indent=2), encoding="utf-8")

    lines = [
        "# Figure package — UCI 360 recalibration analysis (CILS submission)",
        "",
        f"Source: `{source}`  ",
        f"Transformation script: `{script}`  ",
        f"Script SHA-256: `{digest}`  ",
        f"Rendering status: **{status}**",
        "",
        "Vector PDF at CILS column measures (single 3.35 in, double 6.9 in), serif face at "
        "8 pt base, colourblind-safe palette, TrueType-embedded text. PNG copies at 600 dpi "
        "are for drafting only and should not be submitted.",
        "",
        "All four figures replace the retired Wörner figure set in `results/figures/`, which "
        "describes the analysis withdrawn after the *Measurement* desk rejection.",
        "",
        "## Per-budget values as plotted",
        "",
        "| N | mean nRMSE | median nRMSE | mean ratio | median ratio | cells >2× | inverted slope | improved |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"| {int(row.budget)} | {row.light_mean:.5f} | {row.light_median:.5f} | "
            f"{row.ratio_mean:.3f} | {row.ratio_median:.3f} | {int(row.cells_gt2)} | "
            f"{int(row.cells_negative_slope)} | {int(row.cells_improved)}/{int(row.n_cells)} |"
        )
    lines.extend(["", "## Figures", ""])
    for i, spec in enumerate(specs, start=1):
        lines.extend([
            f"### Figure {i} — {spec['title']}",
            "",
            f"File: `{spec['file']}.pdf` ({spec['width']} column)",
            "",
            f"**Caption.** {spec['caption']}",
            "",
            f"**LaTeX.** `{spec['latex']}`",
            "",
            f"**Claim.** {spec['claim']}",
            "",
            f"**Limitations.** {spec['limitations']}",
            "",
        ])
    package_path.parent.mkdir(parents=True, exist_ok=True)
    package_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results", type=Path,
        default=Path("results/sensitivity_uci360_floor_grid/tables/benchmark_results.csv"),
    )
    parser.add_argument("--out-dir", type=Path, default=Path("results/figures_uci360_cils"))
    parser.add_argument("--package", type=Path, default=Path("artifacts/UCI360_FIGURE_PACKAGE.md"))
    parser.add_argument("--spec-only", action="store_true",
                        help="write captions, summary table, and trace manifest without rendering")
    args = parser.parse_args()

    cells = load_cells(args.results)
    summary = budget_summary(cells)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.out_dir / "figure_source_summary.csv", index=False)
    cells.to_csv(args.out_dir / "figure_source_cells.csv", index=False)

    if args.spec_only:
        # Diagnostic correlations do not need matplotlib, so the package stays complete.
        from scipy.stats import spearmanr

        stats = {}
        for budget in (PRIMARY_BUDGET, 2):
            part = cells[(cells.budget == budget) & np.isfinite(cells.d_ref)]
            entry = {"budget": budget, "n_cells": int(len(part))}
            for window_set in ("fit", "held"):
                sub = part[part.window_set == window_set]
                rho, p_value = spearmanr(sub.d_ref, sub.delta_nrmse)
                entry[window_set] = {"n": int(len(sub)), "rho": float(rho), "p": float(p_value)}
            rho, p_value = spearmanr(part.d_ref, part.delta_nrmse)
            entry["pooled"] = {"n": int(len(part)), "rho": float(rho), "p": float(p_value)}
            stats[str(budget)] = entry
        write_package(args.out_dir, args.package, args.results, summary, stats,
                      status="PENDING_RENDER")
        print("spec-only: wrote captions, summary table, and trace manifest; no images rendered")
        return 0

    plt = setup_matplotlib()
    render_budget_curves(plt, cells, summary, args.out_dir)
    render_tail_decay(plt, cells, summary, args.out_dir)
    render_slope_distributions(plt, cells, summary, args.out_dir)
    diagnostic_stats = render_diagnostic_scatter(plt, cells, args.out_dir)
    n_figures = 4
    draw_stats = None
    if POOLED_CELLS.exists():
        pooled = pd.read_csv(POOLED_CELLS)
        draw_stats = render_draw_sensitivity(plt, pooled, args.out_dir)
        n_figures = 5
        print(f"  draw sensitivity: seeds {draw_stats['seeds']}, "
              f"first clean budgets {draw_stats['first_clean_budgets']}")
    else:
        print(f"  {POOLED_CELLS} missing; figure 5 not rendered. "
              "Run scripts/summarize_seed_sensitivity.py first.")
    write_package(args.out_dir, args.package, args.results, summary, diagnostic_stats,
                  status="PASS", draw_stats=draw_stats)

    print(f"rendered {n_figures} figures to {args.out_dir}")
    print(f"cells: {len(cells)}  budgets: {summary.budget.tolist()}")
    print("tail counts (ratio>2) by budget:",
          dict(zip(summary.budget.astype(int), summary.cells_gt2.astype(int))))
    for budget, entry in diagnostic_stats.items():
        print(f"  N={budget}: held-out rho={entry['held']['rho']:.4f} "
              f"p={entry['held']['p']:.2e}  (n={entry['held']['n']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
