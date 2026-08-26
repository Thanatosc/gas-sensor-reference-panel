"""Pool the panel draws and state what survives across them.

The primary analysis used one reference-panel draw. Because a two-sample panel is
exactly determined, whether its pathological case materialises depends on which
two rows are drawn, so a single draw can neither establish nor refute a floor.
This script pools the draws and reports:

- the worst outcome observed at each budget across all draws;
- how often catastrophic outcomes (inversion, order-of-magnitude inflation) occur,
  and at which budgets they are possible at all;
- the budget from which no draw produced a failure, which is the only form of
  floor statement the data support.

**Status: post-hoc robustness analysis.** Changes no hypothesis, threshold, or
verdict of the frozen protocol.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PRIMARY_SEED = 20260826
PRIMARY = Path("results/sensitivity_uci360_floor_grid/tables/benchmark_results.csv")
ROOT = Path("results/seed_sensitivity")


def cells_of(path: Path, seed: int) -> pd.DataFrame:
    raw = pd.read_csv(path)
    key = ["gas_id", "target_batch", "model", "budget"]
    frozen = raw[raw.strategy == "frozen"].set_index(key)
    light = raw[raw.strategy == "calibrator_update"].set_index(key)
    common = frozen.index.intersection(light.index)
    cells = pd.DataFrame(
        {
            "frozen_nrmse": frozen.loc[common, "nrmse"],
            "light_nrmse": light.loc[common, "nrmse"],
            "mae_f": frozen.loc[common, "mae"],
            "mae_l": light.loc[common, "mae"],
            "slope": light.loc[common, "calibration_slope"],
            "d_ref": frozen.loc[common, "d_ref"],
        }
    ).reset_index()
    cells["seed"] = seed
    cells["ratio"] = cells.light_nrmse / cells.frozen_nrmse
    cells["mae_ratio"] = cells.mae_l / cells.mae_f
    return cells


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "pooled_summary.md")
    args = parser.parse_args()

    frames = [cells_of(PRIMARY, PRIMARY_SEED)]
    seeds = [PRIMARY_SEED]
    for directory in sorted(ROOT.glob("seed_*")):
        path = directory / "tables" / "benchmark_results.csv"
        if path.exists():
            seed = int(directory.name.split("_")[1])
            frames.append(cells_of(path, seed))
            seeds.append(seed)
    pooled = pd.concat(frames, ignore_index=True)
    pooled.to_csv(ROOT / "pooled_cells.csv", index=False)

    pd.set_option("display.width", 220)
    print(f"draws pooled: {len(seeds)}  seeds: {seeds}")
    print(f"cells per budget per draw: {int(len(pooled) / len(seeds) / pooled.budget.nunique())}")
    print(f"cells per budget pooled  : {int(len(pooled) / pooled.budget.nunique())}")

    budgets = sorted(pooled.budget.unique())
    rows = []
    for budget in budgets:
        part = pooled[pooled.budget == budget]
        rows.append(
            {
                "N": int(budget),
                "cells": len(part),
                "worst_nrmse_ratio": float(part.ratio.max()),
                "worst_mae_ratio": float(part.mae_ratio.max()),
                "inverted": int((part.slope < 0).sum()),
                "gt5x": int((part.ratio > 5).sum()),
                "gt3x": int((part.ratio > 3).sum()),
                "gt2x": int((part.ratio > 2).sum()),
                "gt2x_mae": int((part.mae_ratio > 2).sum()),
                "mean_ratio": float(part.ratio.mean()),
                "median_ratio": float(part.ratio.median()),
            }
        )
    table = pd.DataFrame(rows).set_index("N")
    print("\n=== pooled across draws ===")
    print(table.to_string(float_format=lambda v: f"{v:.3f}"))

    print("\n=== per draw: worst ratio, inversions, 2x count ===")
    per_draw = pooled.groupby(["seed", "budget"]).agg(
        worst=("ratio", "max"), inv=("slope", lambda s: int((s < 0).sum())),
        gt2=("ratio", lambda s: int((s > 2).sum())),
    ).reset_index()
    for metric, label in [("worst", "worst nRMSE ratio"), ("inv", "inverted slopes"),
                          ("gt2", "cells above 2x")]:
        print(f"\n{label}:")
        print(per_draw.pivot(index="seed", columns="budget", values=metric)
              .to_string(float_format=lambda v: f"{v:.2f}"))

    def first_clean(column: str, threshold: float) -> int | None:
        for i, budget in enumerate(budgets):
            if budget == 0:
                continue
            if all(
                int((pooled[(pooled.budget == later)][column] > threshold).sum()) == 0
                for later in budgets[i:]
            ):
                return int(budget)
        return None

    print("\n=== pooled floor by endpoint and threshold ===")
    floors = {}
    for column, label in [("ratio", "nRMSE"), ("mae_ratio", "MAE")]:
        for threshold in (1.5, 2.0, 3.0, 5.0):
            floor = first_clean(column, threshold)
            floors[f"{label}>{threshold}x"] = floor
            print(f"  no draw exceeds {threshold:>4}x {label:5} from N = {floor}")

    inversion_budgets = sorted(
        int(b) for b in budgets if int((pooled[pooled.budget == b].slope < 0).sum()) > 0
    )
    print(f"\nbudgets at which any draw inverted the slope: {inversion_budgets}")
    print(f"budgets at which any draw exceeded 5x        : "
          f"{sorted(int(b) for b in budgets if int((pooled[pooled.budget == b].ratio > 5).sum()) > 0)}")

    summary = {
        "draws": len(seeds),
        "seeds": seeds,
        "cells_per_budget_pooled": int(len(pooled) / pooled.budget.nunique()),
        "pooled_floors": floors,
        "inversion_budgets": inversion_budgets,
        "per_draw_floor_2x_nrmse": {
            int(seed): next(
                (int(b) for i, b in enumerate(budgets) if b != 0 and all(
                    int((pooled[(pooled.seed == seed) & (pooled.budget == later)].ratio > 2).sum()) == 0
                    for later in budgets[i:]))
                , None)
            for seed in seeds
        },
    }
    (ROOT / "pooled_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# Panel-draw sensitivity of the reference-count floor",
        "",
        f"Draws pooled: **{len(seeds)}** (seeds {seeds}, primary {PRIMARY_SEED}).  ",
        f"Cells per budget per draw: 90. Pooled: "
        f"**{int(len(pooled) / pooled.budget.nunique())}**.",
        "",
        "Post-hoc robustness analysis. No hypothesis, threshold, or verdict of the "
        "frozen protocol is changed.",
        "",
        "## Pooled over all draws",
        "",
        "| N | cells | worst nRMSE ratio | worst MAE ratio | inverted | >5× | >3× | >2× | >2× MAE | mean ratio | median ratio |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for n, row in table.iterrows():
        lines.append(
            f"| {n} | {int(row.cells)} | {row.worst_nrmse_ratio:.2f} | "
            f"{row.worst_mae_ratio:.2f} | {int(row.inverted)} | {int(row.gt5x)} | "
            f"{int(row.gt3x)} | {int(row.gt2x)} | {int(row.gt2x_mae)} | "
            f"{row.mean_ratio:.3f} | {row.median_ratio:.3f} |"
        )
    lines += [
        "",
        "## Per-draw floor, 2× nRMSE",
        "",
        "| seed | floor N |",
        "|---|---:|",
    ]
    for seed, floor in summary["per_draw_floor_2x_nrmse"].items():
        mark = " (primary)" if seed == PRIMARY_SEED else ""
        lines.append(f"| {seed}{mark} | {floor} |")
    lines += ["", "## Pooled floor by endpoint and threshold", "",
              "| endpoint and threshold | no draw exceeds it from |", "|---|---:|"]
    for label, floor in floors.items():
        lines.append(f"| {label} | N = {floor} |")
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
