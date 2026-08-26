"""Normalize separately downloaded feature/target CSVs into the data contract.

This helper intentionally requires explicit column mappings. It will not guess
which column represents time, batch, gas identity, or the reference target.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timestamp-column", required=True)
    parser.add_argument("--batch-column", required=True)
    parser.add_argument("--location-column", required=True)
    parser.add_argument("--gas-column", required=True)
    parser.add_argument("--target-column", required=True)
    parser.add_argument("--provenance", type=Path)
    args = parser.parse_args()

    features = pd.read_csv(args.features)
    targets = pd.read_csv(args.targets)
    if len(features) != len(targets):
        raise SystemExit(f"row count mismatch: features={len(features)} targets={len(targets)}")

    required_mappings = {
        "timestamp": args.timestamp_column,
        "batch_id": args.batch_column,
        "location_id": args.location_column,
        "gas_id": args.gas_column,
        "target": args.target_column,
    }
    missing = [
        f"{canonical}={source}"
        for canonical, source in required_mappings.items()
        if source not in features.columns and source not in targets.columns
    ]
    if missing:
        raise SystemExit("missing mapped columns: " + ", ".join(missing))

    output = pd.DataFrame(index=features.index)
    for canonical, source in required_mappings.items():
        source_frame = features if source in features.columns else targets
        output[canonical] = source_frame[source].to_numpy()
    feature_columns = [column for column in features.columns if column not in required_mappings.values()]
    for column in feature_columns:
        output[column] = pd.to_numeric(features[column], errors="raise")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    if args.provenance:
        args.provenance.parent.mkdir(parents=True, exist_ok=True)
        args.provenance.write_text(
            json.dumps(
                {
                    "features": str(args.features),
                    "targets": str(args.targets),
                    "output": str(args.output),
                    "mappings": required_mappings,
                    "feature_columns": feature_columns,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    print(f"wrote {len(output)} rows and {len(feature_columns)} sensor features to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
