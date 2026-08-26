"""Create manuscript-ready tables from the frozen Wörner confirmation run.

The script is descriptive only.  It does not refit models, change thresholds,
remove rows, or pool models as independent replicates.  Temporal target
windows are the unit of aggregation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


PRIMARY_BUDGET = 5
PRIMARY_STRATEGIES = ["frozen", "calibrator_update", "full_retrain"]


def quantile(series: pd.Series, probability: float) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float(values.quantile(probability)) if len(values) else float("nan")


def summarize(part: pd.DataFrame) -> dict[str, object]:
    strategy = str(part["strategy"].iloc[0])
    delta = part["nrmse"] - part["frozen_nrmse"]
    denominator = part["frozen_nrmse"] - part["oracle_nrmse"]
    recovery = pd.to_numeric(part["recovered_loss"], errors="coerce")
    return {
        "gas_id": str(part["gas_id"].iloc[0]),
        "model": str(part["model"].iloc[0]),
        "budget": int(part["budget"].iloc[0]),
        "strategy": strategy,
        "n_temporal_windows": int(len(part)),
        "nrmse_median": float(part["nrmse"].median()),
        "nrmse_q1": quantile(part["nrmse"], 0.25),
        "nrmse_q3": quantile(part["nrmse"], 0.75),
        "mae_median": float(part["mae"].median()),
        "mae_q1": quantile(part["mae"], 0.25),
        "mae_q3": quantile(part["mae"], 0.75),
        "delta_nrmse_median": float(delta.median()),
        "delta_nrmse_q1": quantile(delta, 0.25),
        "delta_nrmse_q3": quantile(delta, 0.75),
        "calibration_slope_median": float(part["calibration_slope"].median()),
        "recovered_loss_median": float(recovery.median()),
        "recovered_loss_q1": quantile(recovery, 0.25),
        "recovered_loss_q3": quantile(recovery, 0.75),
        "recovered_loss_min": float(recovery.min()),
        "recovered_loss_max": float(recovery.max()),
        "oracle_denominator_median": float(denominator.median()),
        "oracle_denominator_min": float(denominator.min()),
        "oracle_denominator_max": float(denominator.max()),
        "n_recovered_loss_abs_gt_5": int((recovery.abs() > 5).sum()),
    }


def gate_summary(frame: pd.DataFrame, budget: int = PRIMARY_BUDGET) -> dict[str, object]:
    light = frame[(frame["budget"] == budget) & (frame["strategy"] == "calibrator_update")].copy()
    full = frame[(frame["budget"] == budget) & (frame["strategy"] == "full_retrain")].copy()
    drift = light["frozen_nrmse_relative_increase"] >= 0.20
    light_recovery = light["recovered_loss"] >= 0.50
    inadequate = light["recovered_loss"] < 0.20
    full_joint = (full["frozen_nrmse_relative_increase"] >= 0.20) & (full["recovered_loss"] >= 0.50)
    return {
        "budget": budget,
        "light_rows": int(len(light)),
        "drift_rows": int(drift.sum()),
        "light_drift_conditioned_recovery_ge_50": int((drift & light_recovery).sum()),
        "light_drift_conditioned_recovery_lt_20": int((drift & inadequate).sum()),
        "heterogeneous_boundary": bool((drift & light_recovery).any() and (drift & inadequate).any()),
        "full_retrain_joint_hits": int(full_joint.sum()),
    }


def fmt(value: object, digits: int = 3) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "NA"
    return f"{float(value):.{digits}f}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("results/confirmation_worner_v1/tables/benchmark_results.csv"))
    parser.add_argument("--window3-results", type=Path, default=Path("results/sensitivity_worner_window3/tables/benchmark_results.csv"))
    parser.add_argument("--seed-results", type=Path, default=Path("results/sensitivity_worner_seed20260816/tables/benchmark_results.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/tables"))
    parser.add_argument("--out-md", type=Path, default=Path("artifacts/CONFIRMATION_TABLES.md"))
    args = parser.parse_args()

    frame = pd.read_csv(args.results)
    frame["delta_nrmse"] = frame["nrmse"] - frame["frozen_nrmse"]
    frame["oracle_denominator"] = frame["frozen_nrmse"] - frame["oracle_nrmse"]

    budget_rows = []
    for keys, part in frame[frame["strategy"].isin(PRIMARY_STRATEGIES)].groupby(
        ["gas_id", "model", "budget", "strategy"], sort=True
    ):
        budget_rows.append(summarize(part))
    budget_summary = pd.DataFrame(budget_rows)
    budget_summary["strategy"] = pd.Categorical(budget_summary["strategy"], categories=PRIMARY_STRATEGIES, ordered=True)
    budget_summary = budget_summary.sort_values(["gas_id", "model", "budget", "strategy"])

    primary = frame[(frame["budget"] == PRIMARY_BUDGET) & frame["strategy"].isin(PRIMARY_STRATEGIES)]
    primary_rows = []
    for keys, part in primary.groupby(["gas_id", "model", "strategy"], sort=True):
        primary_rows.append(summarize(part))
    primary_summary = pd.DataFrame(primary_rows)
    primary_summary["strategy"] = pd.Categorical(primary_summary["strategy"], categories=PRIMARY_STRATEGIES, ordered=True)
    primary_summary = primary_summary.sort_values(["gas_id", "model", "strategy"])

    light_primary = frame[(frame["budget"] == PRIMARY_BUDGET) & (frame["strategy"] == "calibrator_update")].copy()
    light_primary["drift_hit"] = light_primary["frozen_nrmse_relative_increase"] >= 0.20
    light_primary["recovery_hit"] = light_primary["recovered_loss"] >= 0.50
    light_primary["inadequate"] = light_primary["recovered_loss"] < 0.20
    light_primary["small_oracle_denominator_lt_0_05"] = light_primary["oracle_denominator"] < 0.05
    decision_columns = [
        "gas_id", "target_batch", "model", "budget", "n_test",
        "frozen_nrmse", "nrmse", "delta_nrmse", "oracle_nrmse",
        "oracle_denominator", "recovered_loss", "frozen_nrmse_relative_increase",
        "drift_hit", "recovery_hit", "inadequate", "small_oracle_denominator_lt_0_05",
    ]
    decision_matrix = light_primary[decision_columns].sort_values(["gas_id", "model", "target_batch"])

    denominator = light_primary[
        ["gas_id", "target_batch", "model", "frozen_nrmse", "oracle_nrmse", "oracle_denominator", "recovered_loss"]
    ].copy()
    denominator["denominator_rank_small_to_large"] = denominator["oracle_denominator"].rank(method="first", ascending=True).astype(int)
    denominator["diagnostic_note"] = np.where(
        denominator["oracle_denominator"] < 0.05,
        "Small denominator; ratio is unstable for interpretation; no row excluded",
        "No small-denominator flag under descriptive 0.05 screen",
    )
    denominator = denominator.sort_values("oracle_denominator")

    sensitivity_rows = []
    for label, path in [
        ("six_day_primary", args.results),
        ("three_day_windows", args.window3_results),
        ("alternative_reference_seed", args.seed_results),
    ]:
        if path.exists():
            sensitivity_rows.append(gate_summary(pd.read_csv(path)))
            sensitivity_rows[-1]["analysis"] = label
    sensitivity_summary = pd.DataFrame(sensitivity_rows)[
        ["analysis", "budget", "light_rows", "drift_rows", "light_drift_conditioned_recovery_ge_50",
         "light_drift_conditioned_recovery_lt_20", "heterogeneous_boundary", "full_retrain_joint_hits"]
    ]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    budget_summary.to_csv(args.out_dir / "confirmation_budget_summary.csv", index=False)
    primary_summary.to_csv(args.out_dir / "confirmation_primary_regime_summary.csv", index=False)
    decision_matrix.to_csv(args.out_dir / "confirmation_primary_decision_matrix.csv", index=False)
    denominator.to_csv(args.out_dir / "confirmation_denominator_diagnostics.csv", index=False)
    sensitivity_summary.to_csv(args.out_dir / "confirmation_sensitivity_summary.csv", index=False)

    lines = [
        "# Confirmation tables for the Measurement manuscript",
        "",
        "These tables are generated from the frozen Wörner confirmation CSV. The temporal target window is the aggregation unit; model rows are shown separately and are not treated as independent replicates. `delta_nrmse` is updated nRMSE minus frozen nRMSE, so negative values indicate improvement.",
        "",
        "## Primary five-reference regime summary",
        "",
        "| Analyte | Model | Strategy | n windows | nRMSE median [Q1, Q3] | ΔnRMSE median [Q1, Q3] | Recovery median [Q1, Q3] | denominator median [min, max] | |recovery| > 5 (n) |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in primary_summary.itertuples(index=False):
        lines.append(
            f"| {row.gas_id} | {row.model} | {row.strategy} | {row.n_temporal_windows} | "
            f"{fmt(row.nrmse_median)} [{fmt(row.nrmse_q1)}, {fmt(row.nrmse_q3)}] | "
            f"{fmt(row.delta_nrmse_median)} [{fmt(row.delta_nrmse_q1)}, {fmt(row.delta_nrmse_q3)}] | "
            f"{fmt(row.recovered_loss_median)} [{fmt(row.recovered_loss_q1)}, {fmt(row.recovered_loss_q3)}] | "
            f"{fmt(row.oracle_denominator_median)} [{fmt(row.oracle_denominator_min)}, {fmt(row.oracle_denominator_max)}] | "
            f"{row.n_recovered_loss_abs_gt_5} |"
        )
    lines.extend([
        "",
        "## Decision matrix for the lightweight update",
        "",
        "The pre-specified descriptive gates are frozen nRMSE relative increase ≥ 0.20, recovery ≥ 0.50, and inadequate recovery < 0.20. The denominator screen (<0.05 nRMSE units) is a warning only; it does not remove observations or alter any gate.",
        "",
        "| Analyte | Target window | Model | Frozen nRMSE | Updated nRMSE | ΔnRMSE | Oracle denominator | Recovery | Drift ≥20% | Recovery ≥50% | Recovery <20% | Small denominator warning |",
        "|---|---:|---|---:|---:|---:|---:|---:|---|---|---|---|",
    ])
    for row in decision_matrix.itertuples(index=False):
        lines.append(
            f"| {row.gas_id} | {row.target_batch} | {row.model} | {fmt(row.frozen_nrmse)} | {fmt(row.nrmse)} | {fmt(row.delta_nrmse)} | {fmt(row.oracle_denominator)} | {fmt(row.recovered_loss)} | "
            f"{bool(row.drift_hit)} | {bool(row.recovery_hit)} | {bool(row.inadequate)} | {bool(row.small_oracle_denominator_lt_0_05)} |"
        )
    lines.extend([
        "",
        "## Sensitivity summary",
        "",
        "| Analysis | Light rows | Drift ≥20% | Drift-conditioned recovery ≥50% | Drift-conditioned recovery <20% | Heterogeneous boundary | Full-retrain joint hits |",
        "|---|---:|---:|---:|---:|---|---:|",
    ])
    for row in sensitivity_summary.itertuples(index=False):
        lines.append(
            f"| {row.analysis} | {row.light_rows} | {row.drift_rows} | {row.light_drift_conditioned_recovery_ge_50} | "
            f"{row.light_drift_conditioned_recovery_lt_20} | {bool(row.heterogeneous_boundary)} | {row.full_retrain_joint_hits} |"
        )
    lines.extend([
        "",
        "## Interpretation guard",
        "",
        "The recovered-loss ratio is retained because it was part of the frozen protocol, but it can become numerically unstable when the frozen-to-oracle nRMSE denominator is small. The manuscript should therefore lead with absolute nRMSE and ΔnRMSE, report the denominator diagnostics, and avoid interpreting extreme ratios as standalone evidence. Temporal changes are descriptive and are not identified as physical sensor drift.",
    ])
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    payload = {
        "source": str(args.results),
        "primary_budget": PRIMARY_BUDGET,
        "primary_summary_rows": int(len(primary_summary)),
        "decision_rows": int(len(decision_matrix)),
        "sensitivity": sensitivity_summary.to_dict(orient="records"),
        "files": [str(p) for p in sorted(args.out_dir.glob("confirmation_*.csv"))],
    }
    (args.out_dir / "confirmation_outputs_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
