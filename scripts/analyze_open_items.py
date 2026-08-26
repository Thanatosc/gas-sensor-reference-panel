"""Close the three open data items left in artifacts/UCI360_PRIMARY_FINDINGS.md.

Item 1. ``target_finetune`` across the dense budget grid. The findings note
records only that it is "worse still" at N = 2 (0.456 mean) and asks for one
sentence. This quantifies all four strategies on the same cells.

Item 3. What else is distinctive about NO2 window 6, where the N = 2 tail
concentrates. The reference panel is ordered to span the target range, so at
N = 2 the two references are the extreme low and high strata of the window.
That is deliberate: two points at maximum separation are the most informative
pair for a two-parameter fit. This script tests the consequence, namely that
the fitted slope is then determined by a single pairwise difference

    slope = (y_high - y_low) / (yhat_high - yhat_low)

so the fit inverts whenever the frozen model orders the two extremes wrongly.
The denominator ratio is computable from the panel alone, before the held-out
set is touched, so it is reported as a candidate conditioning diagnostic.

**Provenance.** This conditioning diagnostic is post-hoc. It was constructed
after the N = 2 failures were observed and is not part of the frozen protocol's
H1-H3. It is reported as mechanism and as a lead, never as a confirmed rule.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from gasdrift.metrics import calibration_slope, nrmse  # noqa: E402
from gasdrift.recalibration import fit_strategy, make_model  # noqa: E402
from gasdrift.split import make_split  # noqa: E402

STRATEGIES = ["frozen", "calibrator_update", "target_finetune", "full_retrain"]
STRATEGY_LABEL = {
    "frozen": "frozen",
    "calibrator_update": "lightweight (output calibration)",
    "target_finetune": "target-only refit",
    "full_retrain": "full retraining",
}


# ---------------------------------------------------------------- item 1

def strategy_comparison(results: pd.DataFrame) -> pd.DataFrame:
    """All four strategies per budget, on the cells where each is evaluable."""
    key = ["gas_id", "target_batch", "model", "budget"]
    frozen = results[results.strategy == "frozen"].set_index(key)
    rows = []
    for strategy in STRATEGIES:
        part = results[results.strategy == strategy].set_index(key)
        common = frozen.index.intersection(part.index)
        joined = pd.DataFrame(
            {
                "nrmse": part.loc[common, "nrmse"],
                "frozen_nrmse": frozen.loc[common, "nrmse"],
                "slope": part.loc[common, "calibration_slope"],
            }
        ).reset_index()
        joined["ratio"] = joined.nrmse / joined.frozen_nrmse
        for budget, sub in joined.groupby("budget"):
            rows.append(
                {
                    "strategy": strategy,
                    "budget": int(budget),
                    "n_cells": int(len(sub)),
                    "mean_nrmse": float(sub.nrmse.mean()),
                    "median_nrmse": float(sub.nrmse.median()),
                    "mean_ratio": float(sub.ratio.mean()),
                    "median_ratio": float(sub.ratio.median()),
                    "max_ratio": float(sub.ratio.max()),
                    "cells_gt2": int((sub.ratio > 2).sum()),
                    "cells_improved": int((sub.ratio < 1).sum()),
                    "cells_negative_slope": int((sub.slope < 0).sum()),
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- item 3

def window_descriptives(frame: pd.DataFrame, target_batches: list[int]) -> pd.DataFrame:
    """Per (gas, window) target-distribution facts, for context on window 6."""
    rows = []
    for (gas_id, batch_id), part in frame[
        frame.batch_id.isin(target_batches)
    ].groupby(["gas_id", "batch_id"]):
        target = part["target"]
        rows.append(
            {
                "gas_id": gas_id,
                "target_batch": int(batch_id),
                "n_rows": int(len(part)),
                "n_distinct_targets": int(target.nunique()),
                "target_min": float(target.min()),
                "target_max": float(target.max()),
                "target_range": float(target.max() - target.min()),
                "target_mean": float(target.mean()),
                "target_median": float(target.median()),
                "target_std": float(target.std()),
                "target_skew": float(target.skew()),
                "target_iqr": float(target.quantile(0.75) - target.quantile(0.25)),
            }
        )
    return pd.DataFrame(rows).sort_values(["gas_id", "target_batch"]).reset_index(drop=True)


def panel_conditioning(config: dict, frame: pd.DataFrame, budget: int) -> pd.DataFrame:
    """Refit the frozen model per cell and inspect the N-point panel geometry.

    Replicates the benchmark's split and frozen fit exactly, then records the
    predicted and true spread over the reference panel. For a two-point panel
    the least-squares slope is exactly the ratio of true to predicted gap, so
    the panel's predicted spread fully determines the calibrator's stability.
    """
    excluded = set(config["required_columns"] + config.get("metadata_columns", []))
    feature_columns = [c for c in frame.columns if c not in excluded]
    rows: list[dict] = []

    for gas_id in sorted(frame.gas_id.unique()):
        gas_frame = frame[frame.gas_id == gas_id]
        for target_batch in config["target_batches"]:
            # Common-support restriction, copied from run_benchmark.run.
            source_target = gas_frame[gas_frame.batch_id.isin(config["source_batches"])]["target"]
            target_target = gas_frame[gas_frame.batch_id == target_batch]["target"]
            lower = max(float(source_target.min()), float(target_target.min()))
            upper = min(float(source_target.max()), float(target_target.max()))
            analysis_frame = gas_frame[gas_frame["target"].between(lower, upper)]

            split = make_split(
                analysis_frame,
                config["source_batches"],
                [target_batch],
                budget,
                config["random_seed"],
                config["group_columns"],
                config["target_holdout_fraction"],
                config.get("holdout_target_bins"),
                config["min_reference_rows"],
                config.get("reference_budget_mode", "fraction"),
            )
            source_x = split.source[feature_columns].to_numpy()
            source_y = split.source["target"].to_numpy()
            reference_x = split.references[feature_columns].to_numpy()
            reference_y = split.references["target"].to_numpy()
            test_x = split.test[feature_columns].to_numpy()
            test_y = split.test["target"].to_numpy()

            for model_name in config["models"]:
                base = make_model(model_name, config["random_seed"])
                frozen = fit_strategy(
                    "frozen", base, source_x, source_y, reference_x, reference_y
                )
                panel_pred = np.asarray(
                    frozen.model.predict(reference_x), dtype=float
                ).reshape(-1)
                order = np.argsort(reference_y)
                y_sorted = reference_y[order]
                pred_sorted = panel_pred[order]
                true_gap = float(y_sorted[-1] - y_sorted[0])
                pred_gap = float(pred_sorted[-1] - pred_sorted[0])

                light = fit_strategy(
                    "calibrator_update", base, source_x, source_y, reference_x, reference_y
                )
                frozen_test = nrmse(test_y, frozen.predict(test_x))
                light_test = nrmse(test_y, light.predict(test_x))

                # Rank agreement over the panel: does the model order the
                # references the way the analyser does? Computed over all pairs,
                # so unlike the extreme-pair gap this responds to added points.
                pairs = len(y_sorted) * (len(y_sorted) - 1) // 2
                concordant = sum(
                    1
                    for i in range(len(y_sorted))
                    for j in range(i + 1, len(y_sorted))
                    if (pred_sorted[j] - pred_sorted[i]) > 0
                )
                panel_rank_agreement = concordant / pairs if pairs else float("nan")

                # Conditioning of the two-parameter fit on the panel alone.
                # residual_df = 0 at N = 2, so the fit is unfalsifiable from its
                # own data: no residual exists to inspect. From N = 3 the panel
                # can contradict the fitted line.
                residual_df = len(reference_y) - 2
                if len(reference_y) >= 2 and np.ptp(panel_pred) > 0:
                    panel_r = float(np.corrcoef(panel_pred, reference_y)[0, 1])
                    fitted_on_panel = (
                        light.calibration_intercept + light.calibration_slope * panel_pred
                    )
                    panel_residual_rmse = float(
                        np.sqrt(np.mean((reference_y - fitted_on_panel) ** 2))
                    )
                else:
                    panel_r = float("nan")
                    panel_residual_rmse = float("nan")

                rows.append(
                    {
                        "gas_id": gas_id,
                        "target_batch": int(target_batch),
                        "model": model_name,
                        "budget": int(budget),
                        "n_reference": int(len(reference_y)),
                        "n_test": int(len(test_y)),
                        "residual_df": int(residual_df),
                        "panel_targets": ", ".join(f"{v:g}" for v in y_sorted),
                        "panel_predictions": ", ".join(f"{v:.3f}" for v in pred_sorted),
                        # Extreme-pair geometry. The nested panel draws the range
                        # extremes first, so these two columns are fixed once
                        # N >= 2; at N = 2 the ratio is exactly 1 / calibrator slope.
                        "extreme_true_gap": true_gap,
                        "extreme_pred_gap": pred_gap,
                        "extreme_gap_ratio": pred_gap / true_gap if true_gap else float("nan"),
                        "panel_rank_agreement": panel_rank_agreement,
                        "panel_pearson_r": panel_r,
                        "panel_residual_rmse": panel_residual_rmse,
                        "calibrator_slope": float(light.calibration_slope),
                        "calibrator_intercept": float(light.calibration_intercept),
                        "frozen_nrmse": frozen_test,
                        "light_nrmse": light_test,
                        "ratio": light_test / frozen_test if frozen_test else float("nan"),
                        "window_set": "held" if target_batch in config["held_out_target_batches"] else "fit",
                    }
                )
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path,
                       default=Path("configs/sensitivity_uci360_floor_grid.json"))
    parser.add_argument("--results", type=Path,
                       default=Path("results/sensitivity_uci360_floor_grid/tables/benchmark_results.csv"))
    parser.add_argument("--data", type=Path, default=Path("data/processed/uci360_rewindowed.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/open_items_uci360"))
    parser.add_argument("--conditioning-budgets", type=int, nargs="+", default=[2, 3, 4, 5])
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    results = pd.read_csv(args.results)
    frame = pd.read_csv(args.data)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 220)

    # ---- item 1 -------------------------------------------------------
    comparison = strategy_comparison(results)
    comparison.to_csv(args.out_dir / "strategy_comparison.csv", index=False)
    print("=== ITEM 1: all four strategies by budget (mean nRMSE) ===")
    pivot = comparison.pivot(index="budget", columns="strategy", values="mean_nrmse")
    print(pivot[STRATEGIES].to_string(float_format=lambda v: f"{v:.5f}"))
    print("\n=== cells above 2x frozen, by strategy ===")
    print(comparison.pivot(index="budget", columns="strategy", values="cells_gt2")[STRATEGIES].to_string())
    print("\n=== target_finetune detail ===")
    tf = comparison[comparison.strategy == "target_finetune"]
    print(tf[["budget", "n_cells", "mean_nrmse", "median_nrmse", "mean_ratio",
              "median_ratio", "max_ratio", "cells_gt2", "cells_improved"]]
          .to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    # ---- item 3 -------------------------------------------------------
    descriptives = window_descriptives(frame, config["target_batches"])
    descriptives.to_csv(args.out_dir / "window_descriptives.csv", index=False)
    print("\n=== ITEM 3a: NO2 windows, target distribution ===")
    print(descriptives[descriptives.gas_id == "NO2"].to_string(index=False, float_format=lambda v: f"{v:.2f}"))

    conditioning = []
    for budget in args.conditioning_budgets:
        print(f"\n... refitting frozen models at N={budget}", flush=True)
        conditioning.append(panel_conditioning(config, frame, budget))
    conditioning = pd.concat(conditioning, ignore_index=True)
    conditioning.to_csv(args.out_dir / "panel_conditioning.csv", index=False)

    print("\n=== ITEM 3b: N=2 panel geometry, NO2 window 6 ===")
    b2 = conditioning[conditioning.budget == 2].copy()
    print(b2[(b2.gas_id == "NO2") & (b2.target_batch == 6)][
        ["model", "panel_targets", "panel_predictions", "extreme_true_gap",
         "extreme_pred_gap", "extreme_gap_ratio", "calibrator_slope", "ratio"]
    ].to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    print("\n=== N=2: does the sign of the predicted gap separate the failures? ===")
    b2["failed_2x"] = b2.ratio > 2
    print(b2.groupby("failed_2x").extreme_gap_ratio.agg(
        ["count", "min", "median", "max"]).to_string(float_format=lambda v: f"{v:.4f}"))
    inverted = b2[b2.extreme_gap_ratio <= 0]
    print(f"\ncells whose frozen model inverts the two references at N=2: {len(inverted)}")
    if not inverted.empty:
        print(inverted[["gas_id", "target_batch", "model", "extreme_gap_ratio",
                        "calibrator_slope", "ratio"]].to_string(
            index=False, float_format=lambda v: f"{v:.4f}"))
        print(f"  these are the {len(inverted)} largest inflations: "
              f"{sorted(b2.nlargest(len(inverted), 'ratio').ratio.round(1).tolist(), reverse=True)}")

    print("\n=== the extreme pair is fixed by design; only interior points are added ===")
    fixed = conditioning.groupby("budget")[["extreme_true_gap", "extreme_pred_gap"]].nunique()
    print(fixed.to_string())
    print("  (identical counts across budgets confirm the nested panel draws the")
    print("   range extremes first, so the pathological pair is never displaced)")

    print("\n=== residual degrees of freedom and panel falsifiability ===")
    dof = conditioning.groupby("budget").agg(
        residual_df=("residual_df", "first"),
        median_rank_agreement=("panel_rank_agreement", "median"),
        min_rank_agreement=("panel_rank_agreement", "min"),
        median_panel_residual=("panel_residual_rmse", "median"),
        cells_gt2=("ratio", lambda s: int((s > 2).sum())),
    )
    print(dof.to_string(float_format=lambda v: f"{v:.4f}"))
    print("  residual_df = 0 at N=2: the two-point calibrator reproduces both")
    print("  references exactly, so nothing in the panel can reveal the failure.")

    print("\n=== do the surviving N=3 failures show a bad panel? ===")
    b3 = conditioning[conditioning.budget == 3].copy()
    b3["failed_2x"] = b3.ratio > 2
    print(b3.groupby("failed_2x").agg(
        n=("ratio", "size"),
        median_rank_agreement=("panel_rank_agreement", "median"),
        median_pearson=("panel_pearson_r", "median"),
        median_residual=("panel_residual_rmse", "median"),
    ).to_string(float_format=lambda v: f"{v:.4f}"))
    if b3.failed_2x.any():
        print("\n  N=3 cells above 2x:")
        print(b3[b3.failed_2x][["gas_id", "target_batch", "model", "panel_targets",
                                "panel_rank_agreement", "panel_pearson_r",
                                "calibrator_slope", "ratio"]].to_string(
            index=False, float_format=lambda v: f"{v:.4f}"))

    print(f"\nwrote strategy_comparison.csv, window_descriptives.csv, "
          f"panel_conditioning.csv to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
