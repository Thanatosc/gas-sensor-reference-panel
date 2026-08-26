"""Normalize UCI 360 into fixed-width deployment windows over the full span.

The original `normalize_uci360.py` truncates at `batch_id <= 3`, keeping 270 of
389 available days. This variant keeps the full span and takes the window width
as a parameter, so that the number of temporal sequences is set by the protocol
rather than by an incidental truncation.

Frozen by docs/uci360_primary_protocol.md (window_days=30, windows 1-13).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

SENSOR_COLUMNS = [
    "PT08.S1(CO)",
    "PT08.S2(NMHC)",
    "PT08.S3(NOx)",
    "PT08.S4(NO2)",
    "PT08.S5(O3)",
]
TARGETS = {
    "CO": ("CO(GT)", "mg/m3"),
    "NOx": ("NOx(GT)", "ppb"),
    "NO2": ("NO2(GT)", "ug/m3"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--window-days", type=int, default=30)
    parser.add_argument(
        "--max-window",
        type=int,
        default=0,
        help="0 keeps every window; a positive value truncates for comparison runs",
    )
    args = parser.parse_args()

    raw = pd.read_csv(args.input)
    timestamp = pd.to_datetime(
        raw["Date"].astype(str) + " " + raw["Time"].astype(str),
        format="mixed",
        dayfirst=False,
        errors="raise",
    )
    raw = raw.assign(timestamp=timestamp).sort_values("timestamp").reset_index(drop=True)
    raw = raw.replace(-200, pd.NA)
    start = raw["timestamp"].min()
    window_seconds = args.window_days * 24 * 3600
    raw["batch_id"] = (
        (raw["timestamp"] - start).dt.total_seconds() // window_seconds
    ).astype(int) + 1
    if args.max_window > 0:
        raw = raw[raw["batch_id"] <= args.max_window].copy()

    panels = []
    counts = {}
    for gas_id, (target_column, unit) in TARGETS.items():
        panel = raw[["timestamp", "batch_id", target_column] + SENSOR_COLUMNS].dropna().copy()
        panel.insert(2, "location_id", "urban_roadside_station")
        panel.insert(3, "gas_id", gas_id)
        panel = panel.rename(columns={target_column: "target"})
        panel["row_in_batch"] = panel.groupby("batch_id").cumcount() + 1
        panel = panel.rename(
            columns={
                column: f"sensor_feature_{index:03d}"
                for index, column in enumerate(SENSOR_COLUMNS, 1)
            }
        )
        panels.append(panel)
        counts[gas_id] = {
            "unit": unit,
            "rows": len(panel),
            "rows_by_window": {
                str(window): int(size)
                for window, size in panel.groupby("batch_id").size().items()
            },
            "distinct_reference_values_by_window": {
                str(window): int(part["target"].nunique())
                for window, part in panel.groupby("batch_id")
            },
        }

    output = pd.concat(panels, ignore_index=True)
    output["timestamp"] = output["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)

    windows = (
        raw.groupby("batch_id")["timestamp"]
        .agg(["min", "max"])
        .astype(str)
        .to_dict(orient="index")
    )
    provenance = {
        "dataset": "Air Quality",
        "uci_id": 360,
        "doi": "10.24432/C59K5F",
        "evidence_family": "UCI 360",
        "protocol": "docs/uci360_primary_protocol.md",
        "protocol_status": "frozen_before_rewindowed_benchmark",
        "input": str(args.input),
        "input_sha256": sha256(args.input),
        "window_definition": (
            f"consecutive {args.window_days}-day windows from the first timestamp; "
            "full span retained"
        ),
        "window_days": args.window_days,
        "window_count": int(raw["batch_id"].nunique()),
        "span": {"min": str(raw["timestamp"].min()), "max": str(raw["timestamp"].max())},
        "span_days": int((raw["timestamp"].max() - raw["timestamp"].min()).days),
        "date_parse": "ucimlrepo CSV parsed as month/day/year; variable-width fields allowed",
        "windows": {str(key): value for key, value in windows.items()},
        "targets": counts,
        "features": SENSOR_COLUMNS,
        "excluded_features": ["T", "RH", "AH"],
        "excluded_features_reason": (
            "contemporaneous environmental covariates are withheld so that temporal "
            "shift is not absorbed by them; unchanged from the original run"
        ),
        "missing_value_policy": "replace -200 with missing and use complete cases per target",
        "excluded_target": "NMHC(GT), because 8443/9357 rows use the -200 missing sentinel",
        "supersedes": (
            "data/processed/uci360_normalized.csv, which truncated at batch_id<=3 "
            "and discarded 119 of 389 available days"
        ),
    }
    args.provenance.parent.mkdir(parents=True, exist_ok=True)
    args.provenance.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print(json.dumps(provenance, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
