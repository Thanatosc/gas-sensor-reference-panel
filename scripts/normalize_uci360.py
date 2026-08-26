"""Normalize UCI 360 into three continuous 90-day deployment windows."""

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
    raw["batch_id"] = ((raw["timestamp"] - start).dt.total_seconds() // (90 * 24 * 3600)).astype(int) + 1
    raw = raw[raw["batch_id"] <= 3].copy()

    panels = []
    counts = {}
    for gas_id, (target_column, unit) in TARGETS.items():
        panel = raw[["timestamp", "batch_id", target_column] + SENSOR_COLUMNS].dropna().copy()
        panel.insert(2, "location_id", "urban_roadside_station")
        panel.insert(3, "gas_id", gas_id)
        panel = panel.rename(columns={target_column: "target"})
        panel["row_in_batch"] = panel.groupby("batch_id").cumcount() + 1
        panel = panel.rename(
            columns={column: f"sensor_feature_{index:03d}" for index, column in enumerate(SENSOR_COLUMNS, 1)}
        )
        panels.append(panel)
        counts[gas_id] = {
            "unit": unit,
            "rows": len(panel),
            "rows_by_window": panel.groupby("batch_id").size().to_dict(),
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
        "input": str(args.input),
        "input_sha256": sha256(args.input),
        "window_definition": "three consecutive 90-day windows from the first timestamp",
        "date_parse": "ucimlrepo CSV parsed as month/day/year; variable-width fields allowed",
        "windows": windows,
        "targets": counts,
        "features": SENSOR_COLUMNS,
        "missing_value_policy": "replace -200 with missing and use complete cases per target",
        "excluded_target": "NMHC(GT), because 8443/9357 rows use the -200 missing sentinel",
    }
    args.provenance.parent.mkdir(parents=True, exist_ok=True)
    args.provenance.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print(json.dumps(provenance, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
