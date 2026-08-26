"""Audit the normalized CSV before any model is allowed to run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

REQUIRED = ["timestamp", "batch_id", "location_id", "gas_id", "target"]
METADATA = ["row_in_batch"]


def audit(path: Path, group_columns: list[str] | None = None) -> dict:
    frame = pd.read_csv(path)
    group_columns = group_columns or ["gas_id", "batch_id", "location_id"]
    issues: list[str] = []
    missing = [column for column in REQUIRED if column not in frame.columns]
    issues.extend(f"missing required column: {column}" for column in missing)
    if frame.empty:
        issues.append("input has zero rows")

    numeric_timestamp = pd.to_numeric(frame["timestamp"], errors="coerce") if "timestamp" in frame else pd.Series(dtype=float)
    timestamp = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True) if "timestamp" in frame else pd.Series(dtype="datetime64[ns, UTC]")
    timestamp_order = numeric_timestamp if numeric_timestamp.notna().all() else timestamp
    if timestamp_order.isna().any():
        issues.append("timestamp contains values that are neither datetime nor numeric")
    for column in REQUIRED:
        if column in frame and frame[column].isna().any():
            issues.append(f"required column contains nulls: {column}")

    feature_columns = [column for column in frame.columns if column not in REQUIRED + METADATA]
    non_numeric_features = [column for column in feature_columns if not pd.api.types.is_numeric_dtype(frame[column])]
    issues.extend(f"feature is non-numeric: {column}" for column in non_numeric_features)

    sequence_issues = []
    if "timestamp" in frame and all(column in frame for column in group_columns):
        checked = frame[group_columns].copy()
        checked["_timestamp_order"] = timestamp_order.to_numpy()
        for group, part in checked.groupby(group_columns, dropna=False, sort=False):
            values = part["_timestamp_order"].tolist()
            if any(left > right for left, right in zip(values, values[1:])):
                sequence_issues.append(f"non-monotonic sequence: {group!r}")
    issues.extend(sequence_issues)

    report = {
        "status": "PASS" if not issues else "FAIL",
        "input": str(path),
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "feature_columns": feature_columns,
        "feature_count": len(feature_columns),
        "batch_count": int(frame["batch_id"].nunique(dropna=False)) if "batch_id" in frame else 0,
        "location_count": int(frame["location_id"].nunique(dropna=False)) if "location_id" in frame else 0,
        "gas_count": int(frame["gas_id"].nunique(dropna=False)) if "gas_id" in frame else 0,
        "timestamp_min": str(timestamp_order.min()) if timestamp_order.notna().any() else None,
        "timestamp_max": str(timestamp_order.max()) if timestamp_order.notna().any() else None,
        "temporal_group_columns": group_columns,
        "issues": issues,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    group_columns = None
    if args.config:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        group_columns = config.get("group_columns")
        METADATA.extend(column for column in config.get("metadata_columns", []) if column not in METADATA)
    report = audit(args.input, group_columns)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
