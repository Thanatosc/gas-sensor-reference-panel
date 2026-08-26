"""Evaluate the pre-specified recalibration decision rule.

Tests H1/H2/H3 of docs/uci360_primary_protocol.md. Thresholds and decision
budgets are read from the config and are selected on the rule-fitting windows
only, then applied unchanged to the held-out windows.

Decision unit: (gas_id, target_batch, model). A measurement team deploys a
specific model, so the action is chosen per model, not per analyte.
Reporting unit for H1: the temporal sequence (gas_id, target_batch), with the
per-model correlation reported separately and the pooled cell-level correlation
reported as secondary.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

LIGHTWEIGHT = "calibrator_update"
FROZEN = "frozen"


def load_cells(results: pd.DataFrame) -> pd.DataFrame:
    """Collapse the long benchmark table into one row per decision cell/budget."""
    rows: list[dict] = []
    grouped = results.groupby(["gas_id", "target_batch", "model", "budget"], sort=True)
    for (gas_id, target_batch, model, budget), part in grouped:
        by_strategy = part.set_index("strategy")
        if FROZEN not in by_strategy.index or LIGHTWEIGHT not in by_strategy.index:
            continue
        frozen_test = float(by_strategy.loc[FROZEN, "nrmse"])
        light_test = float(by_strategy.loc[LIGHTWEIGHT, "nrmse"])
        rows.append(
            {
                "gas_id": gas_id,
                "target_batch": int(target_batch),
                "model": model,
                "budget": int(budget),
                "frozen_nrmse": frozen_test,
                "light_nrmse": light_test,
                "delta_nrmse": frozen_test - light_test,
                "d_ref": float(by_strategy.loc[FROZEN, "d_ref"]),
                "reference_frozen_nrmse": float(
                    by_strategy.loc[FROZEN, "reference_frozen_nrmse"]
                ),
                "drift_increase_test": float(
                    by_strategy.loc[FROZEN, "frozen_nrmse_relative_increase"]
                ),
                "n_reference": int(by_strategy.loc[FROZEN, "n_reference"]),
                "n_test": int(by_strategy.loc[FROZEN, "n_test"]),
            }
        )
    return pd.DataFrame(rows)


def test_h1(cells: pd.DataFrame, budget: int, windows: list[int], label: str) -> dict:
    """Spearman association between d_ref and the absolute lightweight benefit."""
    part = cells[(cells["budget"] == budget) & (cells["target_batch"].isin(windows))]
    part = part[np.isfinite(part["d_ref"]) & np.isfinite(part["delta_nrmse"])]
    out: dict = {"window_set": label, "budget": budget, "n_cells": int(len(part))}
    if len(part) >= 4:
        rho, p_value = spearmanr(part["d_ref"], part["delta_nrmse"])
        out["pooled_spearman_rho"] = float(rho)
        out["pooled_spearman_p"] = float(p_value)
    else:
        out["pooled_spearman_rho"] = None
        out["pooled_spearman_p"] = None
    per_model: dict = {}
    for model, model_part in part.groupby("model"):
        if len(model_part) >= 4:
            rho, p_value = spearmanr(model_part["d_ref"], model_part["delta_nrmse"])
            per_model[model] = {
                "n": int(len(model_part)),
                "rho": float(rho),
                "p": float(p_value),
            }
        else:
            per_model[model] = {"n": int(len(model_part)), "rho": None, "p": None}
    out["per_model"] = per_model
    return out


def score_rule(part: pd.DataFrame, tau: float) -> dict:
    """Score every baseline on one budget/window slice.

    A non-finite d_ref cannot support a decision, so the rule falls back to the
    conservative action (keep frozen, i.e. spend nothing further).
    """
    frozen = part["frozen_nrmse"].to_numpy(dtype=float)
    light = part["light_nrmse"].to_numpy(dtype=float)
    diagnostic = part["d_ref"].to_numpy(dtype=float)
    recalibrate = np.isfinite(diagnostic) & (diagnostic >= tau)
    rule = np.where(recalibrate, light, frozen)
    oracle = np.minimum(frozen, light)
    return {
        "tau": tau,
        "n_cells": int(len(part)),
        "n_recalibrate": int(recalibrate.sum()),
        "always_frozen": float(np.mean(frozen)),
        "always_recalibrate": float(np.mean(light)),
        "rule": float(np.mean(rule)),
        "oracle_action": float(np.mean(oracle)),
        "undecidable_cells": int((~np.isfinite(diagnostic)).sum()),
    }


def select_rule(cells: pd.DataFrame, fit_windows: list[int], taus: list[float],
                budgets: list[int]) -> tuple[dict, list[dict]]:
    """Pick (tau, N) on the rule-fitting windows only. Smallest values break ties."""
    grid: list[dict] = []
    for budget in budgets:
        part = cells[
            (cells["budget"] == budget) & (cells["target_batch"].isin(fit_windows))
        ]
        if part.empty:
            continue
        for tau in taus:
            entry = score_rule(part, tau)
            entry["decision_budget"] = budget
            entry["margin_vs_frozen"] = entry["always_frozen"] - entry["rule"]
            entry["margin_vs_recalibrate"] = entry["always_recalibrate"] - entry["rule"]
            grid.append(entry)
    if not grid:
        raise ValueError("rule-fitting grid is empty")
    best = min(grid, key=lambda e: (e["rule"], e["decision_budget"], e["tau"]))
    return best, grid


def test_h3(cells: pd.DataFrame, tau: float, budgets: list[int], max_budget: int,
            windows: list[int], plateau_tolerance: float = 0.05) -> dict:
    """Compare decision-stability budget against the fitting-performance plateau."""
    reference = cells[
        (cells["budget"] == max_budget) & (cells["target_batch"].isin(windows))
    ]
    key = ["gas_id", "target_batch", "model"]
    reference_action = {
        tuple(row[column] for column in key): bool(
            math.isfinite(row["d_ref"]) and row["d_ref"] >= tau
        )
        for _, row in reference.iterrows()
    }
    agreement: dict = {}
    for budget in budgets:
        part = cells[(cells["budget"] == budget) & (cells["target_batch"].isin(windows))]
        matched = total = 0
        for _, row in part.iterrows():
            cell = tuple(row[column] for column in key)
            if cell not in reference_action:
                continue
            action = bool(math.isfinite(row["d_ref"]) and row["d_ref"] >= tau)
            total += 1
            matched += int(action == reference_action[cell])
        agreement[str(budget)] = {
            "n": total,
            "agreement": (matched / total) if total else None,
        }
    plateau_source = cells[cells["target_batch"].isin(windows)]
    mean_light = {
        int(budget): float(part["light_nrmse"].mean())
        for budget, part in plateau_source.groupby("budget")
        if int(budget) > 0
    }
    best_light = min(mean_light.values()) if mean_light else float("nan")
    plateau_budget = None
    for budget in sorted(mean_light):
        if mean_light[budget] <= best_light * (1.0 + plateau_tolerance):
            plateau_budget = budget
            break
    decision_budget = None
    for budget in sorted(int(k) for k in agreement):
        value = agreement[str(budget)]["agreement"]
        if value is not None and value >= 1.0:
            decision_budget = budget
            break
    return {
        "tau": tau,
        "action_agreement_with_max_budget": agreement,
        "mean_light_nrmse_by_budget": mean_light,
        "plateau_tolerance": plateau_tolerance,
        "light_plateau_budget": plateau_budget,
        "decision_stable_budget": decision_budget,
        "h3_supported": (
            decision_budget is not None
            and plateau_budget is not None
            and decision_budget < plateau_budget
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    rule_config = config["decision_rule"]
    fit_windows = config["rule_fitting_target_batches"]
    held_out_windows = config["held_out_target_batches"]
    taus = rule_config["tau_grid"]
    budgets = rule_config["decision_budget_grid"]
    max_budget = max(config["reference_budgets"])

    results = pd.read_csv(args.results)
    cells = load_cells(results)

    h1 = {
        "primary_budget": 5,
        "rule_fitting": test_h1(cells, 5, fit_windows, "rule_fitting_windows_4_9"),
        "held_out": test_h1(cells, 5, held_out_windows, "held_out_windows_10_13"),
        "by_decision_budget_held_out": {
            str(budget): test_h1(cells, budget, held_out_windows, "held_out")
            for budget in budgets
        },
    }

    selected, grid = select_rule(cells, fit_windows, taus, budgets)
    held_out_part = cells[
        (cells["budget"] == selected["decision_budget"])
        & (cells["target_batch"].isin(held_out_windows))
    ]
    held_out_score = score_rule(held_out_part, selected["tau"])
    held_out_score["decision_budget"] = selected["decision_budget"]
    beats_frozen = held_out_score["rule"] < held_out_score["always_frozen"]
    beats_recalibrate = held_out_score["rule"] < held_out_score["always_recalibrate"]
    per_gas = {}
    for gas_id, gas_part in held_out_part.groupby("gas_id"):
        per_gas[gas_id] = score_rule(gas_part, selected["tau"])

    h2 = {
        "selected_on_rule_fitting_windows": selected,
        "held_out_evaluation": held_out_score,
        "per_gas_held_out": per_gas,
        "beats_always_frozen": bool(beats_frozen),
        "beats_always_recalibrate": bool(beats_recalibrate),
        "h2_supported": bool(beats_frozen and beats_recalibrate),
        "selection_grid": grid,
    }

    h3 = test_h3(cells, selected["tau"], budgets, max_budget, held_out_windows)

    h1_held_out = h1["held_out"]
    h1_supported = (
        h1_held_out["pooled_spearman_rho"] is not None
        and h1_held_out["pooled_spearman_rho"] > 0
        and h1_held_out["pooled_spearman_p"] is not None
        and h1_held_out["pooled_spearman_p"] < 0.05
    )

    report = {
        "status": "UNVERIFIED",
        "protocol": "docs/uci360_primary_protocol.md",
        "hypothesis_provenance": rule_config["provenance"],
        "results_input": str(args.results),
        "n_sequences": int(cells.groupby(["gas_id", "target_batch"]).ngroups),
        "n_decision_cells_per_budget": int(
            cells[cells["budget"] == budgets[0]].shape[0]
        ),
        "rule_fitting_windows": fit_windows,
        "held_out_windows": held_out_windows,
        "H1": h1,
        "H1_supported": bool(h1_supported),
        "H2": h2,
        "H3": h3,
        "verdicts": {
            "H1": "SUPPORTED" if h1_supported else "NOT_SUPPORTED",
            "H2": "SUPPORTED" if h2["h2_supported"] else "NOT_SUPPORTED",
            "H3": "SUPPORTED" if h3["h3_supported"] else "NOT_SUPPORTED",
        },
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "decision_rule_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    cells.to_csv(args.out_dir / "decision_cells.csv", index=False)
    pd.DataFrame(grid).to_csv(args.out_dir / "rule_selection_grid.csv", index=False)
    print(json.dumps(report["verdicts"], indent=2))
    print(json.dumps(h2["held_out_evaluation"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
