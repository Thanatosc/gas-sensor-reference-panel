"""Normalize the Wörner et al. one-year electronic-nose archive.

The archive contains one raw time-series CSV per sample measurement.  This
normalizer reproduces the feature recipe supplied with the archive, but reads
the raw files with a whitespace/quote-safe parser and derives the numeric
concentration label from the filename.  Ethanol files are deliberately
excluded: the publication defines them as a 5% v/v diluent/blank rather than a
concentration-bearing analyte.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import linregress


EXPECTED_MD5 = "9937678cac4118c53287276009172a74"
DOI = "10.5281/zenodo.15681119"
PUBLICATION_DOI = "10.1038/s41597-025-05993-8"
WINDOW_WIDTH_DAYS = 6


def digest(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def day_number(name: str) -> int:
    match = re.match(r"Day (\d+)/", name)
    if not match:
        raise ValueError(f"cannot parse day directory from {name!r}")
    return int(match.group(1))


def parse_label(name: str) -> tuple[str, float, str] | None:
    stem = Path(name).stem
    if stem.startswith("EtOH_"):
        return None
    match = re.match(r"(Diacetyl|Phenylethanol)_([0-9.]+)ppm_[0-9]+$", stem)
    if not match:
        raise ValueError(f"unsupported concentration label in {name!r}")
    analyte = match.group(1)
    return analyte, float(match.group(2)), "ppm"


def extract_features(frame: pd.DataFrame) -> dict[str, float]:
    resistance = [f"R{i}[Ohm]" for i in range(1, 63)]
    environment = ["T01[degC]", "H01[%rh]"]
    all_sensors = resistance + environment
    features: dict[str, float] = {}
    phase1 = frame[frame["Cycle_Stage"] == 1]
    phase2 = frame[frame["Cycle_Stage"] == 2]
    phase3 = frame[frame["Cycle_Stage"] == 3]

    for column in all_sensors:
        features[f"mean_{column}"] = float(phase2[column].tail(10).mean())
        baseline = float(phase1[column].tail(10).mean())
        sample = float(phase2[column].tail(10).mean())
        clean = column.replace("[Ohm]", "")
        features[f"rel_diff_{clean}"] = (sample - baseline) / baseline

    x = np.arange(30, dtype=float)
    for column in resistance:
        first30 = phase2[column].head(30).to_numpy(dtype=float)
        features[f"sample_startslope_{column.replace('[Ohm]', '')}"] = float(
            linregress(x, first30).slope
        )

    for column in resistance:
        initial = float(phase1[column].tail(10).mean())
        recovery = float(phase3[column].tail(10).mean())
        features[f"rec_lvl_{column.replace('[Ohm]', '')}"] = recovery / initial
    return features


def read_first_timestamp(archive: zipfile.ZipFile, name: str) -> tuple[datetime, str]:
    with archive.open(name) as raw:
        frame = pd.read_csv(raw, sep=r"\s+", engine="python", nrows=1)
    date_text = str(frame.iloc[0]["Date[yyyy-mm-dd]"])
    time_text = str(frame.iloc[0]["Time[hh:mm:ss]"])
    start = datetime.strptime(f"{date_text} {time_text}", "%y-%m-%d %H:%M:%S")
    return start, date_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--window-width", type=int, default=WINDOW_WIDTH_DAYS)
    args = parser.parse_args()
    if args.window_width < 1:
        raise SystemExit("--window-width must be positive")

    if digest(args.archive, "md5") != EXPECTED_MD5:
        raise SystemExit("archive MD5 does not match the published Zenodo checksum")

    records: list[dict[str, object]] = []
    excluded: Counter[str] = Counter()
    failures: list[dict[str, str]] = []
    with zipfile.ZipFile(args.archive) as archive:
        members = sorted(
            (info.filename for info in archive.infolist() if re.match(r"Day \d+/.+\.csv$", info.filename)),
            key=lambda name: (day_number(name), name),
        )
        day_ids = sorted({day_number(name) for name in members})
        day_ordinal = {day: i for i, day in enumerate(day_ids, start=1)}
        for name in members:
            label = parse_label(name)
            if label is None:
                excluded["EtOH 5% v/v diluent/blank has no analyte concentration target"] += 1
                continue
            analyte, target, unit = label
            day_id = day_number(name)
            try:
                with archive.open(name) as raw:
                    frame = pd.read_csv(raw, sep=r"\s+", engine="python")
                start, date_text = read_first_timestamp(archive, name)
                values = extract_features(frame)
                if not all(np.isfinite(value) for value in values.values()):
                    raise ValueError("feature vector contains non-finite values")
                records.append(
                    {
                        "timestamp": start.isoformat(),
                        "batch_id": (day_ordinal[day_id] - 1) // args.window_width + 1,
                        "location_id": "laboratory_e_nose",
                        "gas_id": analyte,
                        "target": target,
                        "target_unit": unit,
                        "day_id": day_id,
                        "day_ordinal": day_ordinal[day_id],
                        "date_source": date_text,
                        "record_id": Path(name).stem,
                        "source_file": name,
                        **values,
                    }
                )
            except Exception as exc:  # retain a machine-readable audit trail
                failures.append({"source_file": name, "error": repr(exc)})

    if failures:
        raise SystemExit(json.dumps({"normalization_failures": failures[:10], "count": len(failures)}, indent=2))

    output = pd.DataFrame(records).sort_values(["timestamp", "gas_id", "target", "record_id"]).reset_index(drop=True)
    output["row_in_batch"] = output.groupby(["gas_id", "batch_id", "location_id"], sort=False).cumcount() + 1
    required = ["timestamp", "batch_id", "location_id", "gas_id", "target"]
    metadata = ["target_unit", "day_id", "day_ordinal", "date_source", "record_id", "source_file", "row_in_batch"]
    feature_columns = [column for column in output.columns if column not in required + metadata]
    output = output[required + metadata + feature_columns]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)

    windows: dict[str, dict[str, object]] = {}
    for batch_id, part in output.groupby("batch_id", sort=True):
        windows[str(batch_id)] = {
            "day_ids": sorted(part["day_id"].unique().tolist()),
            "rows": int(len(part)),
            "timestamp_min": str(part["timestamp"].min()),
            "timestamp_max": str(part["timestamp"].max()),
        }
    provenance = {
        "dataset": "Long-Term Drift Behavior of Electronic Nose",
        "zenodo_doi": DOI,
        "publication_doi": PUBLICATION_DOI,
        "license": "CC BY 4.0",
        "archive": str(args.archive),
        "archive_md5": digest(args.archive, "md5"),
        "archive_sha256": digest(args.archive, "sha256"),
        "normalization": "raw measurement CSVs; one row per measurement file",
        "feature_recipe": ["mean last 10 stage-2 values", "relative stage-2 vs stage-1 difference", "stage-2 first-30-point slope", "stage-3/stage-1 recovery ratio"],
        "feature_count": len(feature_columns),
        "raw_measurement_files": len(members),
        "included_rows": len(output),
        "excluded_files": dict(excluded),
        "failed_files": failures,
        "day_ids_present": day_ids,
        "missing_day_ids_in_1_to_40": sorted(set(range(1, 41)) - set(day_ids)),
        "window_definition": f"consecutive available day folders, {args.window_width} days per window; final window may be shorter",
        "windows": windows,
        "label_mapping": {"Diacetyl_0.1ppm": {"gas_id": "Diacetyl", "target": 0.1, "unit": "ppm"}, "Diacetyl_1ppm": {"gas_id": "Diacetyl", "target": 1.0, "unit": "ppm"}, "Phenylethanol_200ppm": {"gas_id": "Phenylethanol", "target": 200.0, "unit": "ppm"}, "Phenylethanol_1000ppm": {"gas_id": "Phenylethanol", "target": 1000.0, "unit": "ppm"}},
        "target_scope": "concentration regression for Diacetyl and Phenylethanol; EtOH is excluded as a 5% v/v diluent/blank",
        "output": str(args.output),
    }
    args.provenance.parent.mkdir(parents=True, exist_ok=True)
    args.provenance.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print(json.dumps(provenance, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
