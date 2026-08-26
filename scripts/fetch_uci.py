"""Explicit UCI downloader; it never infers schema or temporal splits."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


DATASETS = {
    "gas_sensor_array_drift": 224,
    "gas_sensor_array_drift_concentration": 270,
    "gas_sensor_open_sampling": 251,
    "gas_sensor_dynamic_mixtures": 322,
    "air_quality": 360,
}

STATIC_ARCHIVES = {
    224: "https://archive.ics.uci.edu/static/public/224/gas+sensor+array+drift+dataset.zip",
    270: "https://archive.ics.uci.edu/static/public/270/gas+sensor+array+drift+dataset+at+different+concentrations.zip",
    251: "https://archive.ics.uci.edu/static/public/251/gas+sensor+arrays+in+open+sampling+settings.zip",
    322: "https://archive.ics.uci.edu/static/public/322/gas+sensor+array+under+dynamic+gas+mixtures.zip",
    360: "https://archive.ics.uci.edu/static/public/360/air+quality.zip",
}

# UCI 270's semicolon-prefixed label is currently shifted by ucimlrepo's CSV
# parser. Preserve the official archive and parse it explicitly instead.
STATIC_ONLY = {270}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()

    try:
        from ucimlrepo import fetch_ucirepo
    except ImportError as exc:
        raise SystemExit("Install requirements.txt before downloading UCI data") from exc

    dataset_id = DATASETS[args.dataset]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    metadata = {"name": args.dataset, "uci_id": dataset_id, "repository": "UCI Machine Learning Repository"}
    try:
        if dataset_id in STATIC_ONLY:
            raise RuntimeError("static archive required to preserve gas and concentration labels")
        dataset = fetch_ucirepo(id=dataset_id)
        features = dataset.data.features
        targets = dataset.data.targets
        features_path = args.out_dir / f"{args.dataset}_features.csv"
        features.to_csv(features_path, index=False)
        metadata.update({"transport": "ucimlrepo", "features_sha256": sha256(features_path)})
        if targets is not None:
            targets_path = args.out_dir / f"{args.dataset}_targets.csv"
            targets.to_csv(targets_path, index=False)
            metadata["targets_sha256"] = sha256(targets_path)
    except Exception as exc:
        url = STATIC_ARCHIVES[dataset_id]
        archive_path = args.out_dir / f"{args.dataset}.zip"
        urllib.request.urlretrieve(url, archive_path)
        metadata.update(
            {
                "transport": "uci_static_archive",
                "source_url": url,
                "archive": str(archive_path),
                "archive_sha256": sha256(archive_path),
                "ucimlrepo_fallback_reason": f"{type(exc).__name__}: {exc}",
            }
        )
    metadata.update(
        {
            "downloaded_by": "scripts/fetch_uci.py",
            "warning": "Normalize and document temporal/batch columns before benchmarking.",
        }
    )
    (args.out_dir / f"{args.dataset}_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
