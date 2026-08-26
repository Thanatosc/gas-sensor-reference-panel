"""Parse UCI 270's batch-wise LIBSVM-like archive into the data contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

import pandas as pd

BATCH_PATTERN = re.compile(r"(?:^|/)batch(\d+)\.dat$", re.IGNORECASE)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_line(line: str, batch_id: int, row_in_batch: int) -> dict:
    tokens = line.strip().split()
    if not tokens or ";" not in tokens[0]:
        raise ValueError(f"batch {batch_id} row {row_in_batch}: missing gas;concentration label")
    gas_label, concentration = tokens[0].split(";", maxsplit=1)
    row = {
        # Exact acquisition dates are not present. The batch ordinal is the
        # only defensible temporal resolution in this public archive.
        "timestamp": batch_id,
        "batch_id": batch_id,
        "location_id": "controlled_lab",
        "gas_id": int(gas_label),
        "target": float(concentration),
        "row_in_batch": row_in_batch,
    }
    seen: set[int] = set()
    for token in tokens[1:]:
        feature_id_text, value_text = token.split(":", maxsplit=1)
        feature_id = int(feature_id_text)
        if feature_id in seen:
            raise ValueError(f"batch {batch_id} row {row_in_batch}: duplicate feature {feature_id}")
        seen.add(feature_id)
        row[f"sensor_feature_{feature_id:03d}"] = float(value_text)
    if seen != set(range(1, 129)):
        raise ValueError(f"batch {batch_id} row {row_in_batch}: expected features 1..128")
    return row


def parse_archive(path: Path) -> pd.DataFrame:
    rows: list[dict] = []
    with zipfile.ZipFile(path) as archive:
        entries = []
        for name in archive.namelist():
            match = BATCH_PATTERN.search(name)
            if match:
                entries.append((int(match.group(1)), name))
        if [batch for batch, _ in sorted(entries)] != list(range(1, 11)):
            raise ValueError("archive must contain exactly batch1.dat through batch10.dat")
        for batch_id, name in sorted(entries):
            with archive.open(name) as raw:
                for row_in_batch, payload in enumerate(raw, start=1):
                    line = payload.decode("utf-8").strip()
                    if line:
                        rows.append(parse_line(line, batch_id, row_in_batch))
    frame = pd.DataFrame(rows)
    expected_columns = 5 + 1 + 128
    if len(frame) != 13910:
        raise ValueError(f"expected 13910 rows, found {len(frame)}")
    if len(frame.columns) != expected_columns:
        raise ValueError(f"expected {expected_columns} columns, found {len(frame.columns)}")
    return frame


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    args = parser.parse_args()

    frame = parse_archive(args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)
    provenance = {
        "dataset": "Gas Sensor Array Drift at Different Concentrations",
        "uci_id": 270,
        "doi": "10.24432/C5MK6M",
        "evidence_family": "UCI 224/270",
        "archive": str(args.archive),
        "archive_sha256": sha256(args.archive),
        "rows": len(frame),
        "batches": sorted(frame["batch_id"].unique().tolist()),
        "gas_labels": sorted(frame["gas_id"].unique().tolist()),
        "target_unit": "ppmv",
        "timestamp_resolution": "batch ordinal only",
        "location_id": "controlled_lab",
        "warning": "No exact sample timestamps are available; do not claim within-batch temporal resolution.",
    }
    args.provenance.parent.mkdir(parents=True, exist_ok=True)
    args.provenance.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print(json.dumps(provenance, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
