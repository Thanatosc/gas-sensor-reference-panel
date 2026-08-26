"""Generate publication-oriented figures for the frozen confirmation analysis.

The numerical source and all transformations are explicit.  If matplotlib is
not installed, ``--spec-only`` (or the automatic fallback) still writes the
figure package, captions, LaTeX snippets, and trace manifest without silently
creating placeholder images.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


CB = {
    "frozen": "#0077BB",
    "calibrator_update": "#EE7733",
    "full_retrain": "#009988",
    "high": "#0077BB",
    "low": "#EE7733",
    "intermediate": "#666666",
}


def package_specs() -> list[dict[str, str]]:
    return [
        {
            "id": "fig-1",
            "title": "Leakage-controlled temporal evaluation and reference-budget workflow",
            "caption": "Figure 1. Leakage-controlled temporal evaluation and reference-budget workflow. The first three batches are used for source fitting; each later target window is split into a labeled reference panel and a held-out test set before any recalibration is fitted. The primary absolute reference budgets are 0, 2, 5, 10, 20, and 50 observations.",
            "claim": "The protocol preserves temporal order and selects reference observations before evaluating the held-out target set.",
            "limitations": "The diagram describes the analysis protocol and does not establish a physical cause for temporal change.",
            "latex": r"\includegraphics[width=\columnwidth]{figures/figure_01_workflow.pdf}",
        },
        {
            "id": "fig-2",
            "title": "nRMSE across absolute reference budgets",
            "caption": "Figure 2. Median held-out nRMSE across absolute reference budgets for each analyte and model. Lines show the frozen source model, lightweight output calibration, and full retraining; ribbons show the interquartile range across target windows. The nRMSE axis is logarithmic so that the complete two-reference instability remains visible without compressing the other budgets. Lower nRMSE is better. Models and analytes are displayed in separate panels and are not pooled as independent replicates.",
            "claim": "Performance changes with reference budget are heterogeneous across analytes and model classes.",
            "limitations": "The interquartile ranges summarize four target windows in the six-day primary analysis and are not confidence intervals.",
            "latex": r"\includegraphics[width=\textwidth]{figures/figure_02_budget_curves.pdf}",
        },
        {
            "id": "fig-3",
            "title": "Absolute nRMSE changes and lightweight decision categories at five references",
            "caption": "Figure 3. Target-window-specific change in nRMSE after lightweight calibration at the five-reference budget. Negative values indicate improvement relative to the frozen source model; positive values indicate worsening. Filled circles mark windows with recovery ≥0.50, filled triangles mark recovery <0.20, and open circles mark intermediate recovery. A black outline flags the descriptive small-denominator warning; no observations were excluded.",
            "claim": "At the primary budget, lightweight output calibration contains both useful and inadequate target-window/model regimes.",
            "limitations": "Recovery categories use the pre-specified ratio but the plotted effect is absolute nRMSE change because the ratio is unstable for small oracle denominators.",
            "latex": r"\includegraphics[width=\textwidth]{figures/figure_03_primary_heterogeneity.pdf}",
        },
        {
            "id": "fig-4",
            "title": "Sensitivity of the decision boundary",
            "caption": "Figure 4. Proportion of all evaluable target-window/model sequences jointly meeting the temporal-increase and recovery gates under the six-day primary analysis, the three-day-window sensitivity analysis, and the alternative reference-panel seed. Labels show numerator/denominator counts. The heterogeneous boundary is retained in both sensitivity analyses.",
            "claim": "The presence of a heterogeneous lightweight boundary is stable to temporal-window width and reference-panel seed, while counts and regime medians vary.",
            "limitations": "The sensitivity analyses are descriptive and use the same Wörner evidence family; they do not provide an independent external validation corpus.",
            "latex": r"\includegraphics[width=\columnwidth]{figures/figure_04_sensitivity.pdf}",
        },
    ]


def script_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_package(out_dir: Path, package_path: Path, source: Path, rendered: bool) -> None:
    script = Path(__file__).resolve()
    traces = []
    for spec in package_specs():
        traces.append(
            {
                "artifact_id": spec["id"],
                "source_data": {"dataset_id": "worner_zenodo_15681119_confirmation", "file": str(source)},
                "transformation": {"script": str(script), "sha256": script_hash(script)},
                "caption_claim": spec["claim"],
                "supported_manuscript_claims": [{"claim": spec["claim"], "locator": "Results/Figures"}],
                "limitations": [spec["limitations"]],
                "rendered_status": "PASS" if rendered else "PENDING_MATPLOTLIB",
            }
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "figure_table_trace.json").write_text(json.dumps(traces, indent=2), encoding="utf-8")
    lines = [
        "# Figure package",
        "",
        f"Source: `{source}`  ",
        f"Transformation script SHA-256: `{script_hash(script)}`  ",
        f"Rendering status: **{'PASS' if rendered else 'PENDING_MATPLOTLIB'}**",
        "",
        "Figures use a colorblind-safe categorical palette, 300-dpi output, and separate analyte/model panels. Figure 3 uses absolute nRMSE change for the visual effect; the recovery ratio is retained in the tables with denominator diagnostics.",
        "",
    ]
    for i, spec in enumerate(package_specs(), start=1):
        lines.extend([
            f"## Figure {i}",
            "",
            f"**Caption.** {spec['caption']}",
            "",
            f"**LaTeX.** `{spec['latex']}`",
            "",
            f"**Trace claim.** {spec['claim']}",
            "",
        ])
    package_path.parent.mkdir(parents=True, exist_ok=True)
    package_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def setup_matplotlib():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    return matplotlib, plt, Line2D, FancyArrowPatch, FancyBboxPatch


def render_workflow(plt, FancyArrowPatch, FancyBboxPatch, out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.5, 0.94, "Leakage-controlled temporal evaluation", ha="center", va="center", fontsize=12, weight="bold")
    boxes = [
        (0.04, 0.54, 0.25, 0.22, "Source fitting\nBatches 1–3\n18 days; 216 rows", "#D9EAF7"),
        (0.38, 0.54, 0.25, 0.22, "Target evaluation\nBatches 4–7\n4 windows; 252 rows", "#FCE4D6"),
        (0.71, 0.54, 0.25, 0.22, "Reference-budget\ncomparison\n0, 2, 5, 10, 20, 50", "#DDEBF7"),
    ]
    for x, y, w, h, label, color in boxes:
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012", facecolor=color, edgecolor="#333333", linewidth=0.9)
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=9)
    for x1, x2 in [(0.29, 0.38), (0.63, 0.71)]:
        ax.add_patch(FancyArrowPatch((x1, 0.65), (x2, 0.65), arrowstyle="-|>", mutation_scale=13, linewidth=1.1, color="#333333"))
    ax.text(0.5, 0.39, "For each target window: select labeled references first → freeze the held-out test set", ha="center", fontsize=8.5)
    ax.text(0.5, 0.25, "Strategies: frozen source model  |  lightweight output calibration  |  full retraining", ha="center", fontsize=8.5)
    ax.text(0.5, 0.12, "468 concentration-bearing records • 7 total temporal windows • 252 finite sensor features", ha="center", fontsize=8.2, color="#444444")
    fig.tight_layout()
    fig.savefig(out_dir / "figure_01_workflow.pdf", bbox_inches="tight")
    fig.savefig(out_dir / "figure_01_workflow.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def render_budget_curves(plt, frame: pd.DataFrame, out_dir: Path) -> None:
    strategies = ["frozen", "calibrator_update", "full_retrain"]
    labels = {"frozen": "Frozen", "calibrator_update": "Lightweight calibration", "full_retrain": "Full retraining"}
    markers = {"frozen": "o", "calibrator_update": "s", "full_retrain": "^"}
    fig, axes = plt.subplots(2, 3, figsize=(7.2, 5.7), sharex=True)
    for ax, (gas, model) in zip(axes.flat, [(g, m) for g in sorted(frame.gas_id.unique()) for m in sorted(frame.model.unique())]):
        sub = frame[(frame.gas_id == gas) & (frame.model == model) & frame.strategy.isin(strategies)]
        for strategy in strategies:
            agg = sub[sub.strategy == strategy].groupby("budget")["nrmse"].agg(["median", lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)]).reset_index()
            agg.columns = ["budget", "median", "q1", "q3"]
            ax.plot(agg.budget, agg["median"], marker=markers[strategy], color=CB[strategy], linewidth=1.5, markersize=4, label=labels[strategy])
            if strategy != "frozen":
                ax.fill_between(agg.budget, agg.q1, agg.q3, color=CB[strategy], alpha=0.12, linewidth=0)
        ax.set_title(f"{gas} — {model}", fontsize=9.5)
        ax.set_yscale("log")
        ax.set_ylabel("Held-out nRMSE (log scale)")
        ax.grid(axis="y", alpha=0.18, linewidth=0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    for ax in axes[1, :]:
        ax.set_xlabel("Absolute reference observations")
    axes[0, 0].legend(frameon=False, fontsize=7.5, loc="upper right")
    fig.tight_layout()
    fig.savefig(out_dir / "figure_02_budget_curves.pdf", bbox_inches="tight")
    fig.savefig(out_dir / "figure_02_budget_curves.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def render_primary_heterogeneity(plt, Line2D, frame: pd.DataFrame, out_dir: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(7.2, 5.4), sharey=False)
    for ax, (gas, model) in zip(axes.flat, [(g, m) for g in sorted(frame.gas_id.unique()) for m in sorted(frame.model.unique())]):
        sub = frame[(frame.gas_id == gas) & (frame.model == model) & (frame.strategy == "calibrator_update") & (frame.budget == 5)].sort_values("target_batch").copy()
        sub["delta"] = sub["nrmse"] - sub["frozen_nrmse"]
        sub["category"] = np.where(sub.recovered_loss >= 0.50, "high", np.where(sub.recovered_loss < 0.20, "low", "intermediate"))
        for _, row in sub.iterrows():
            marker = "o" if row.category == "high" else ("^" if row.category == "low" else "o")
            face = CB[row.category] if row.category != "intermediate" else "white"
            edge = "black" if row.oracle_denominator < 0.05 else CB[row.category]
            ax.scatter(row.target_batch, row.delta, marker=marker, s=46, facecolor=face, edgecolor=edge, linewidth=1.0, zorder=3)
        ax.axhline(0, color="#333333", linewidth=0.8)
        ax.set_xticks(sorted(sub.target_batch.tolist()))
        ax.set_xlabel("Target window")
        ax.set_ylabel("Δ nRMSE (updated − frozen)")
        ax.set_title(f"{gas} — {model}", fontsize=9.5)
        ax.grid(axis="y", alpha=0.18, linewidth=0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    legend = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=CB["high"], markeredgecolor=CB["high"], label="Recovery ≥0.50", markersize=6),
        Line2D([0], [0], marker="^", color="none", markerfacecolor=CB["low"], markeredgecolor=CB["low"], label="Recovery <0.20", markersize=6),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="white", markeredgecolor="#666666", label="Intermediate recovery", markersize=6),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="white", markeredgecolor="black", label="Small denominator warning", markersize=6),
    ]
    axes[0, 0].legend(handles=legend, frameon=False, fontsize=7.0, loc="best")
    fig.tight_layout()
    fig.savefig(out_dir / "figure_03_primary_heterogeneity.pdf", bbox_inches="tight")
    fig.savefig(out_dir / "figure_03_primary_heterogeneity.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def render_sensitivity(plt, sensitivity: pd.DataFrame, out_dir: Path) -> None:
    analyses = sensitivity["analysis"].tolist()
    labels = {"six_day_primary": "Six-day\nprimary", "three_day_windows": "Three-day\nwindows", "alternative_reference_seed": "Alternative\nseed"}
    metrics = [
        ("light_drift_conditioned_recovery_ge_50", "Drift + light ≥0.50", CB["high"]),
        ("light_drift_conditioned_recovery_lt_20", "Drift + light <0.20", CB["low"]),
        ("full_retrain_joint_hits", "Drift + full retrain ≥0.50", CB["full_retrain"]),
    ]
    fig, ax = plt.subplots(figsize=(6.9, 4.0))
    x = np.arange(len(analyses))
    width = 0.23
    for j, (column, label, color) in enumerate(metrics):
        values = []
        texts = []
        for analysis in analyses:
            row = sensitivity[sensitivity.analysis == analysis].iloc[0]
            denom = int(row.light_rows)
            numerator = int(row[column])
            values.append(100 * numerator / denom)
            texts.append(f"{numerator}/{denom}")
        bars = ax.bar(x + (j - 1) * width, values, width, color=color, label=label, edgecolor="black", linewidth=0.4)
        for bar, txt in zip(bars, texts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2, txt, ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels([labels[a] for a in analyses])
    ax.set_ylabel("Sequences meeting gate (%)")
    ax.set_ylim(0, 100)
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis="y", alpha=0.18, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_dir / "figure_04_sensitivity.pdf", bbox_inches="tight")
    fig.savefig(out_dir / "figure_04_sensitivity.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("results/confirmation_worner_v1/tables/benchmark_results.csv"))
    parser.add_argument("--sensitivity", type=Path, default=Path("results/tables/confirmation_sensitivity_summary.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/figures"))
    parser.add_argument("--package", type=Path, default=Path("artifacts/FIGURE_PACKAGE.md"))
    parser.add_argument("--spec-only", action="store_true")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    try:
        matplotlib, plt, Line2D, FancyArrowPatch, FancyBboxPatch = setup_matplotlib()
    except ImportError:
        write_package(args.out_dir, args.package, args.results, rendered=False)
        print("matplotlib is not installed; wrote figure specifications and trace manifest only")
        return 0
    if args.spec_only:
        write_package(args.out_dir, args.package, args.results, rendered=False)
        print("spec-only requested; no images rendered")
        return 0
    frame = pd.read_csv(args.results)
    frame["delta_nrmse"] = frame["nrmse"] - frame["frozen_nrmse"]
    frame["oracle_denominator"] = frame["frozen_nrmse"] - frame["oracle_nrmse"]
    sensitivity = pd.read_csv(args.sensitivity)
    render_workflow(plt, FancyArrowPatch, FancyBboxPatch, args.out_dir)
    render_budget_curves(plt, frame, args.out_dir)
    render_primary_heterogeneity(plt, Line2D, frame, args.out_dir)
    render_sensitivity(plt, sensitivity, args.out_dir)
    write_package(args.out_dir, args.package, args.results, rendered=True)
    print("rendered four confirmation figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
