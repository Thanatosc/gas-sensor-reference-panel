"""Summarize the two-corpus Kill Test without treating models as replicates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def bootstrap_median(values: pd.Series, seed: int, replicates: int) -> tuple[float, float, float]:
    clean = values.dropna().to_numpy(dtype=float)
    if not len(clean):
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    estimates = np.median(rng.choice(clean, size=(replicates, len(clean)), replace=True), axis=1)
    return float(np.median(clean)), float(np.quantile(estimates, 0.025)), float(np.quantile(estimates, 0.975))


def fmt(value: float) -> str:
    return "NA" if not np.isfinite(value) else f"{value:.3f}"


def corpus_summary(name: str, frame: pd.DataFrame, config: dict) -> tuple[dict, list[str]]:
    budget = 0.05
    lightweight = config["lightweight_strategies"]
    light = frame[(frame["budget"] == budget) & frame["strategy"].isin(lightweight)].copy()
    full = frame[(frame["budget"] == budget) & (frame["strategy"] == "full_retrain")].copy()
    threshold_drift = config["kill_test"]["frozen_nrmse_relative_increase"]
    threshold_recovery = config["kill_test"]["minimum_recovered_loss_at_5_percent"]
    light["joint_hit"] = (
        (light["frozen_nrmse_relative_increase"] >= threshold_drift)
        & (light["recovered_loss"] >= threshold_recovery)
    )
    full["joint_hit"] = (
        (full["frozen_nrmse_relative_increase"] >= threshold_drift)
        & (full["recovered_loss"] >= threshold_recovery)
    )
    summaries = []
    markdown_rows = []
    for model in config["models"]:
        model_light = light[light["model"] == model]
        model_full = full[full["model"] == model]
        median, low, high = bootstrap_median(
            model_light["recovered_loss"],
            config["random_seed"],
            config["bootstrap_replicates"],
        )
        summary = {
            "model": model,
            "sequence_count": int(len(model_light)),
            "drift_ge_20_count": int((model_light["frozen_nrmse_relative_increase"] >= threshold_drift).sum()),
            "light_recovery_ge_50_count": int((model_light["recovered_loss"] >= threshold_recovery).sum()),
            "light_joint_hit_count": int(model_light["joint_hit"].sum()),
            "light_median_recovered_loss": median,
            "light_median_bootstrap_ci": [low, high],
            "full_retrain_joint_hit_count": int(model_full["joint_hit"].sum()),
            "full_retrain_median_recovered_loss": float(model_full["recovered_loss"].median()),
        }
        summaries.append(summary)
        markdown_rows.append(
            f"| {name} | {model} | {summary['sequence_count']} | "
            f"{summary['drift_ge_20_count']} | {summary['light_recovery_ge_50_count']} | "
            f"{summary['light_joint_hit_count']} | {fmt(median)} [{fmt(low)}, {fmt(high)}] | "
            f"{summary['full_retrain_joint_hit_count']} |"
        )
    direction = bool(
        (
            (light["frozen_nrmse_relative_increase"] >= threshold_drift)
            & (light["recovered_loss"] > 0)
        ).any()
    )
    result = {
        "corpus": name,
        "models": summaries,
        "corpus_hit": bool(light["joint_hit"].any()),
        "positive_direction_under_drift": direction,
        "undefined_recovery_rows": int(light["recovered_loss"].isna().sum()),
    }
    return result, markdown_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uci270-results", type=Path, required=True)
    parser.add_argument("--uci270-config", type=Path, required=True)
    parser.add_argument("--uci360-results", type=Path, required=True)
    parser.add_argument("--uci360-config", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--verification-status", choices=["ANALYZED", "VERIFIED"], default="ANALYZED")
    parser.add_argument("--reproducibility-verdict", default="CANNOT_VERIFY")
    args = parser.parse_args()

    inputs = [
        ("UCI 270", pd.read_csv(args.uci270_results), json.loads(args.uci270_config.read_text(encoding="utf-8"))),
        ("UCI 360", pd.read_csv(args.uci360_results), json.loads(args.uci360_config.read_text(encoding="utf-8"))),
    ]
    corpora = []
    table_rows = []
    for name, frame, config in inputs:
        summary, rows = corpus_summary(name, frame, config)
        corpora.append(summary)
        table_rows.extend(rows)

    hit_count = sum(corpus["corpus_hit"] for corpus in corpora)
    other_direction_consistent = all(
        corpus["positive_direction_under_drift"] for corpus in corpora if not corpus["corpus_hit"]
    )
    if hit_count >= 2:
        verdict = "PASS"
        rationale = "At least two evidence families meet both the drift and 5% lightweight-recovery thresholds."
    elif hit_count == 1 and other_direction_consistent:
        verdict = "CONDITIONAL"
        rationale = "One corpus meets the joint threshold and the other is directionally consistent but does not cross it."
    else:
        verdict = "FAIL"
        rationale = "The two evidence families do not provide the pre-specified same-direction joint effect."

    output = {
        "verification_status": args.verification_status,
        "reproducibility_verdict": args.reproducibility_verdict,
        "kill_test_verdict": verdict,
        "rationale": rationale,
        "corpora": corpora,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(output, indent=2), encoding="utf-8")

    report = f"""## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: validate
- Origin Date: 2026-08-14
- Verification Status: {args.verification_status}
- Version Label: validation_v1

## Validation Report

- **Source**: UCI 270 Kill Test v2 + UCI 360 Kill Test v1
- **Overall Confidence**: RED_FLAG for causal drift attribution; CAUTION for the numerical benchmark
- **Pre-specified Kill Test verdict**: **{verdict}**
- **Rationale**: {rationale}

### Statistical Findings

Models are treatments, not independent replicates. Counts below are gas/batch
sequences within each model. Bootstrap intervals are medians over sequences;
with only 6 UCI 270 and 3 UCI 360 sequences per model, they are descriptive and
expected to be wide.

| Corpus | Model | Sequences | Drift >=20% | Light recovery >=50% | Joint hits | Light median recovery [95% bootstrap CI] | Full-retrain joint hits |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(table_rows)}

The lightweight strategy is `calibrator_update`. `full_retrain` is shown for
diagnosis but cannot satisfy the lightweight PASS condition. Recovery above 1
is possible when recalibration outperforms the full-reference oracle model;
negative values mean recalibration worsened nRMSE relative to the frozen model.

### Warnings

| Type | Detail | Affected |
|---|---|---|
| Data support | UCI 270 has no exact timestamps and 4/10 gas/batch combinations have only one common concentration; gas 6 is absent from target batches 4-5. | UCI 270 generalizability |
| Dataset shift | UCI 360 windows span seasonal and environmental change, so error change is not identifiable as sensor drift alone. | Causal drift claim |
| Oracle denominator | Recovery is undefined when the full-reference oracle does not improve on frozen. | One UCI 270 model/sequence |
| Multiple paths | v0-v2 method changes occurred after preliminary outputs and before preregistration. | Confirmatory interpretation |
| Small sequence count | Bootstrap operates on 3 or 6 sequences per model. | CI precision |

### Fallacy Scan

- **Coverage**: 11/11 fallacy types checked

| Fallacy | Severity | Detail |
|---|---|---|
| Simpson's paradox | CAUTION | Aggregate recovery reverses across analytes/models; only stratified results are defensible. |
| Ecological fallacy | NOTE | Inference is limited to dataset-level deployment sequences, not individual sensors or all electronic noses. |
| Berkson's paradox | CAUTION | UCI 360 uses complete cases; analyzer/sensor availability may select non-random hours. |
| Collider bias | CAUTION | Common-support and complete-case filtering may condition on variables affected by environment and instrument state. |
| Base-rate neglect | NOTE | Not a diagnostic classification analysis; base-rate metrics are not used. |
| Regression to the mean | NOTE | Periods were selected temporally, not for extreme error, but oracle-normalized recovery can amplify small denominators. |
| Survivorship bias | CAUTION | Missing analyzer hours are excluded; missingness patterns require a sensitivity analysis. |
| Look-elsewhere effect | CAUTION | Three models, multiple strategies, budgets, and targets were inspected; no inferential multiplicity claim is made yet. |
| Garden of forking paths | RED_FLAG | Method revisions followed v0/v1 diagnostics. Treat v2/v1 as exploratory until frozen and reproduced on untouched data. |
| Correlation != causation | RED_FLAG | Secondary observational sequences cannot isolate physical sensor drift from season, environment, maintenance, or concentration shift. |
| Reverse causality | NOTE | No directional causal relation between concentration and error recovery is claimed. |

### Reproducibility

- **Method**: exact command re-run in the same environment
- **Verdict**: {args.reproducibility_verdict}

Execution reproducibility does not upgrade the causal interpretation. The Kill
Test verdict applies to the pre-specified two-corpus rule, not to whether a
revised full-retraining or replacement-boundary paper could still be viable.
"""
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(report, encoding="utf-8")
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
