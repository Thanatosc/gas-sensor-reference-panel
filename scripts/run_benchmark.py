"""Run the pre-specified time-ordered recalibration benchmark."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gasdrift.metrics import calibration_slope, mae, nrmse, recovered_loss
from gasdrift.recalibration import fit_strategy, make_model
from gasdrift.split import make_split, validate_temporal_order


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def config_hash(config: dict) -> str:
    payload = json.dumps(config, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def reference_ids(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""
    if "row_in_batch" in frame:
        return ";".join(f"{row.batch_id}:{row.row_in_batch}" for row in frame.itertuples())
    return ";".join(str(index) for index in frame.index)


def preceding_source_error(
    frame: pd.DataFrame,
    source_batches: list,
    feature_columns: list[str],
    model_name: str,
    seed: int,
) -> tuple[float, int | None]:
    ordered_batches = sorted(source_batches)
    for validation_batch in reversed(ordered_batches[1:]):
        earlier_batches = [batch for batch in ordered_batches if batch < validation_batch]
        train = frame[frame["batch_id"].isin(earlier_batches)]
        validation = frame[frame["batch_id"] == validation_batch]
        shared_levels = sorted(set(train["target"]) & set(validation["target"]))
        train = train[train["target"].isin(shared_levels)]
        validation = validation[validation["target"].isin(shared_levels)]
        if train.empty or validation["target"].nunique() < 2:
            continue
        model = make_model(model_name, seed)
        model.fit(train[feature_columns].to_numpy(), train["target"].to_numpy())
        error = nrmse(
            validation["target"].to_numpy(),
            model.predict(validation[feature_columns].to_numpy()),
        )
        if math.isfinite(error):
            return error, validation_batch
    return float("nan"), None


def run(config: dict, frame: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    required = config["required_columns"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    issues = validate_temporal_order(frame, config["group_columns"])
    if issues:
        raise ValueError("temporal audit failed: " + "; ".join(issues[:5]))

    excluded = set(required + config.get("metadata_columns", []))
    feature_columns = [column for column in frame.columns if column not in excluded]
    if not feature_columns:
        raise ValueError("no sensor feature columns found")
    if any(not pd.api.types.is_numeric_dtype(frame[column]) for column in feature_columns):
        raise ValueError("all sensor feature columns must be numeric")

    rows: list[dict] = []
    skipped: list[dict] = []
    for gas_id in sorted(frame["gas_id"].unique().tolist()):
        gas_frame = frame[frame["gas_id"] == gas_id]
        for target_batch in config["target_batches"]:
            if gas_frame[gas_frame["batch_id"].isin(config["source_batches"])].empty:
                skipped.append({"gas_id": gas_id, "target_batch": target_batch, "reason": "no source rows"})
                continue
            if gas_frame[gas_frame["batch_id"] == target_batch].empty:
                skipped.append({"gas_id": gas_id, "target_batch": target_batch, "reason": "no target rows"})
                continue
            analysis_frame = gas_frame
            if config.get("restrict_to_common_concentration_support", False):
                source_target = gas_frame[
                    gas_frame["batch_id"].isin(config["source_batches"])
                ]["target"]
                target_target = gas_frame[gas_frame["batch_id"] == target_batch]["target"]
                if config.get("concentration_support_mode", "exact") == "range":
                    lower = max(float(source_target.min()), float(target_target.min()))
                    upper = min(float(source_target.max()), float(target_target.max()))
                    common_levels = [lower, upper]
                    analysis_frame = gas_frame[gas_frame["target"].between(lower, upper)]
                else:
                    common_levels = sorted(set(source_target) & set(target_target))
                    analysis_frame = gas_frame[gas_frame["target"].isin(common_levels)]
            else:
                common_levels = sorted(
                    gas_frame[gas_frame["batch_id"] == target_batch]["target"].unique().tolist()
                )
            target_level_count = analysis_frame[
                analysis_frame["batch_id"] == target_batch
            ]["target"].nunique()
            if target_level_count < config.get("minimum_target_concentrations", 2):
                skipped.append(
                    {
                        "gas_id": gas_id,
                        "target_batch": target_batch,
                        "reason": "insufficient common target concentration levels",
                        "common_concentrations": common_levels,
                    }
                )
                continue
            source_errors = {
                model_name: preceding_source_error(
                    analysis_frame,
                    config["source_batches"],
                    feature_columns,
                    model_name,
                    config["random_seed"],
                )
                for model_name in config["models"]
            }
            for budget in config["reference_budgets"]:
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
                pool_x = split.reference_pool[feature_columns].to_numpy()
                pool_y = split.reference_pool["target"].to_numpy()

                for model_name in config["models"]:
                    print(
                        f"gas={gas_id} target_batch={target_batch} budget={budget:.2f} model={model_name}",
                        flush=True,
                    )
                    oracle = make_model(model_name, config["random_seed"])
                    oracle.fit(np.concatenate([source_x, pool_x]), np.concatenate([source_y, pool_y]))
                    oracle_pred = oracle.predict(test_x)
                    oracle_error = nrmse(test_y, oracle_pred)

                    frozen = fit_strategy("frozen", make_model(model_name, config["random_seed"]), source_x, source_y, reference_x, reference_y)
                    frozen_pred = frozen.predict(test_x)
                    frozen_error = nrmse(test_y, frozen_pred)
                    source_error, source_validation_batch = source_errors[model_name]
                    drift_increase = (
                        (frozen_error - source_error) / source_error
                        if math.isfinite(source_error) and source_error > 0
                        else float("nan")
                    )
                    # Reference-panel diagnostic. Unlike `drift_increase`, which is
                    # computed from the frozen holdout and is therefore not available
                    # when the recalibration decision has to be made, this uses only
                    # the labelled reference panel and the source-validation error.
                    # See docs/uci360_primary_protocol.md.
                    if len(reference_y) >= 2 and float(np.ptp(reference_y)) > 0:
                        reference_frozen_nrmse = nrmse(
                            reference_y, frozen.predict(reference_x)
                        )
                    else:
                        reference_frozen_nrmse = float("nan")
                    d_ref = (
                        (reference_frozen_nrmse - source_error) / source_error
                        if math.isfinite(reference_frozen_nrmse)
                        and math.isfinite(source_error)
                        and source_error > 0
                        else float("nan")
                    )

                    for strategy in config["strategies"]:
                        fitted = fit_strategy(strategy, make_model(model_name, config["random_seed"]), source_x, source_y, reference_x, reference_y)
                        prediction = fitted.predict(test_x)
                        updated_error = nrmse(test_y, prediction)
                        rows.append(
                            {
                                "gas_id": gas_id,
                                "target_batch": target_batch,
                                "model": model_name,
                                "strategy": strategy,
                                "budget": budget,
                                "n_source": len(split.source),
                                "n_reference_pool": len(split.reference_pool),
                                "n_reference": len(split.references),
                                "n_test": len(split.test),
                                "common_concentration_count": target_level_count,
                                "reference_row_ids": reference_ids(split.references),
                                "mae": mae(test_y, prediction),
                                "nrmse": updated_error,
                                "calibration_slope": calibration_slope(test_y, prediction),
                                "frozen_nrmse": frozen_error,
                                "source_reference_nrmse": source_error,
                                "source_validation_batch": source_validation_batch,
                                "frozen_nrmse_relative_increase": drift_increase,
                                "reference_frozen_nrmse": reference_frozen_nrmse,
                                "d_ref": d_ref,
                                "oracle_nrmse": oracle_error,
                                "recovered_loss": recovered_loss(frozen_error, updated_error, oracle_error),
                            }
                        )
    return pd.DataFrame(rows), skipped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("results"))
    args = parser.parse_args()
    config = load_config(args.config)
    frame = pd.read_csv(args.input)
    results, skipped = run(config, frame)
    table_dir = args.out_dir / "tables"
    log_dir = args.out_dir / "logs"
    table_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(table_dir / "benchmark_results.csv", index=False)
    package_versions = {}
    for package in ("numpy", "pandas", "scikit-learn", "xgboost"):
        try:
            package_versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            package_versions[package] = None
    manifest = {
        "status": "UNVERIFIED",
        "command": " ".join(sys.argv),
        "python": sys.version,
        "platform": platform.platform(),
        "package_versions": package_versions,
        "config_hash": config_hash(config),
        "input": str(args.input),
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "rows": len(frame),
        "result_rows": len(results),
        "skipped_sequences": skipped,
    }
    (log_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
