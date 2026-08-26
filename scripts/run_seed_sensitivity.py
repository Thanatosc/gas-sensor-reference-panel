"""Seed sensitivity of the reference-count floor.

The floor of N = 4 in the primary analysis rests on one reference-panel draw. The
seed governs both the panel draw and the model random states, so re-running the
dense budget grid under additional seeds asks the operationally relevant question:
would a different deployment have found the tail closing somewhere else?

**Status: post-hoc robustness analysis.** It is not part of the frozen protocol
and it changes no threshold, hypothesis, or verdict. It tests whether a
descriptive finding survives a nuisance parameter.

Usage:
    python scripts/run_seed_sensitivity.py --seeds 11 22 33 44
    python scripts/run_seed_sensitivity.py --summarize-only
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

BASE_CONFIG = Path("configs/sensitivity_uci360_floor_grid.json")
DATA = Path("data/processed/uci360_rewindowed.csv")
ROOT = Path("results/seed_sensitivity")
PRIMARY_SEED = 20260826
PRIMARY_RESULTS = Path(
    "results/sensitivity_uci360_floor_grid/tables/benchmark_results.csv"
)


def tail_profile(results_path: Path, seed: int) -> pd.DataFrame:
    """Per-budget tail statistics for one run."""
    raw = pd.read_csv(results_path)
    key = ["gas_id", "target_batch", "model", "budget"]
    frozen = raw[raw.strategy == "frozen"].set_index(key)
    light = raw[raw.strategy == "calibrator_update"].set_index(key)
    common = frozen.index.intersection(light.index)
    cells = pd.DataFrame(
        {
            "frozen": frozen.loc[common, "nrmse"],
            "light": light.loc[common, "nrmse"],
            "slope": light.loc[common, "calibration_slope"],
        }
    ).reset_index()
    cells["ratio"] = cells.light / cells.frozen
    rows = []
    for budget, part in cells.groupby("budget"):
        rows.append(
            {
                "seed": seed,
                "budget": int(budget),
                "n_cells": len(part),
                "mean_ratio": float(part.ratio.mean()),
                "median_ratio": float(part.ratio.median()),
                "max_ratio": float(part.ratio.max()),
                "cells_gt2": int((part.ratio > 2).sum()),
                "cells_negative_slope": int((part.slope < 0).sum()),
                "mean_nrmse": float(part.light.mean()),
            }
        )
    return pd.DataFrame(rows)


def floor_of(profile: pd.DataFrame) -> int | None:
    """Smallest budget from which no larger budget has any cell above 2x."""
    budgets = sorted(profile.budget.unique())
    for i, budget in enumerate(budgets):
        if budget == 0:
            continue
        if all(
            int(profile.loc[profile.budget == later, "cells_gt2"].iloc[0]) == 0
            for later in budgets[i:]
        ):
            return int(budget)
    return None


def run_seed(seed: int) -> Path:
    config = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    config["random_seed"] = seed
    config["corpus_role"] = "sensitivity"
    config["refinement_note"] = (
        "Post-hoc seed sensitivity of the reference-count floor. Changes no "
        "hypothesis, threshold, or verdict; the primary seed is 20260826."
    )
    out_dir = ROOT / f"seed_{seed}"
    out_dir.mkdir(parents=True, exist_ok=True)
    config_path = out_dir / "config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    results = out_dir / "tables" / "benchmark_results.csv"
    if results.exists():
        print(f"  seed {seed}: reusing existing {results}")
        return results
    print(f"  seed {seed}: running benchmark ...", flush=True)
    completed = subprocess.run(
        [sys.executable, "scripts/run_benchmark.py",
         "--config", str(config_path), "--input", str(DATA),
         "--out-dir", str(out_dir)],
        capture_output=True, text=True,
    )
    if completed.returncode != 0:
        print(completed.stdout[-2000:])
        print(completed.stderr[-2000:], file=sys.stderr)
        raise SystemExit(f"benchmark failed for seed {seed}")
    manifest = json.loads((out_dir / "logs" / "run_manifest.json").read_text(encoding="utf-8"))
    print(f"  seed {seed}: {manifest['result_rows']} rows, "
          f"{len(manifest['skipped_sequences'])} skipped")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[11, 22, 33, 44])
    parser.add_argument("--summarize-only", action="store_true")
    args = parser.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)

    profiles = [tail_profile(PRIMARY_RESULTS, PRIMARY_SEED)]
    for seed in args.seeds:
        path = ROOT / f"seed_{seed}" / "tables" / "benchmark_results.csv"
        if not args.summarize_only:
            path = run_seed(seed)
        if path.exists():
            profiles.append(tail_profile(path, seed))
        else:
            print(f"  seed {seed}: no results, skipping")

    combined = pd.concat(profiles, ignore_index=True)
    combined.to_csv(ROOT / "tail_profiles.csv", index=False)

    pd.set_option("display.width", 200)
    print("\n=== cells above 2x frozen error, by seed and budget ===")
    pivot = combined.pivot(index="seed", columns="budget", values="cells_gt2")
    print(pivot.to_string())

    print("\n=== inverted slopes, by seed and budget ===")
    print(combined.pivot(index="seed", columns="budget",
                         values="cells_negative_slope").to_string())

    print("\n=== worst ratio, by seed and budget ===")
    print(combined.pivot(index="seed", columns="budget", values="max_ratio")
          .to_string(float_format=lambda v: f"{v:.2f}"))

    print("\n=== floor per seed (smallest N with no failures at or above it) ===")
    floors = {}
    for seed, part in combined.groupby("seed"):
        floors[int(seed)] = floor_of(part)
        print(f"  seed {seed:>9}: floor N = {floors[int(seed)]}")

    print("\n=== mean / median ratio at N=2 and N=4, by seed ===")
    small = combined[combined.budget.isin([2, 3, 4])]
    print(small.pivot(index="seed", columns="budget",
                      values=["mean_ratio", "median_ratio"])
          .to_string(float_format=lambda v: f"{v:.3f}"))

    values = [v for v in floors.values() if v is not None]
    agree = len(set(values)) == 1
    print(f"\nfloors: {floors}")
    print(f"all seeds agree: {agree}"
          + (f" (N = {values[0]})" if agree and values else ""))
    (ROOT / "floor_summary.json").write_text(
        json.dumps({"floors": floors, "all_agree": agree,
                    "primary_seed": PRIMARY_SEED}, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
