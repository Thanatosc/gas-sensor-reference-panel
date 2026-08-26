"""Build the two Zenodo release archives and their metadata.

Follows the project's established convention of splitting the deposit:

- **code record** (`software`), a new version under concept DOI 10.5281/zenodo.21973116.
  Contains code, protocol, configs, derived summaries, figures, tables, the
  manuscript and the LaTeX build. Supersedes v1.0.0, which archived the
  withdrawn Wörner-primary analysis.
- **data record** (`dataset`), a new concept. Contains only the row-level
  benchmark tables: the ten panel draws that the non-replication result rests on,
  plus the normalised corpus they were computed from.

Both archives are written with deterministic member order and fixed timestamps so
that rebuilding produces an identical zip, and each gets a manifest listing
per-file SHA-256.

Usage:
    python scripts/build_zenodo_packages.py
    python scripts/build_zenodo_packages.py --outdir release
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE_VERSION = "2.0.0"
DATA_VERSION = "1.0.0"
CODE_CONCEPT_DOI = "10.5281/zenodo.21973116"
CODE_V1_DOI = "10.5281/zenodo.21973117"
UCI_DOI = "10.24432/C59K5F"
WORNER_DOI = "10.5281/zenodo.15681119"
ORCID = "0009-0003-3716-0008"
AFFILIATION = "School of Computing and Artificial Intelligence, Southwest Jiaotong University"

# Fixed timestamp so rebuilds are byte-identical (1980-01-01, the zip epoch).
ZIP_DATE = (1980, 1, 1, 0, 0, 0)

CODE_INCLUDE: list[tuple[str, str]] = [
    ("README.md", "README.md"),
    ("requirements.txt", "requirements.txt"),
    ("LICENSE-CODE-MIT.txt", "LICENSE-CODE-MIT.txt"),
    ("LICENSE-DERIVED-CC-BY-4.0.txt", "LICENSE-DERIVED-CC-BY-4.0.txt"),
]
CODE_TREES: list[tuple[str, str]] = [
    ("src", "src"),
    ("scripts", "scripts"),
    ("configs", "configs"),
    ("docs", "docs"),
    ("manuscript", "manuscript"),
    ("latex", "latex"),
]
# Derived results the manuscript cites, excluding row-level benchmark tables.
CODE_RESULT_GLOBS = [
    "results/figures_uci360_cils/*",
    "results/open_items_uci360/*",
    "results/seed_sensitivity/pooled_cells.csv",
    "results/seed_sensitivity/pooled_summary.md",
    "results/seed_sensitivity/pooled_summary.json",
    "results/seed_sensitivity/tail_profiles.csv",
    "results/seed_sensitivity/floor_summary.json",
    "results/primary_uci360_rewindowed/decision_rule/*",
    "results/primary_uci360_rewindowed/logs/*",
    "results/sensitivity_uci360_floor_grid/logs/*",
    "results/tables/*",
    "results/validation/*",
]
CODE_ARTIFACT_GLOBS = ["artifacts/UCI360_*.md", "artifacts/METHOD_CHANGELOG.md",
                       "artifacts/PROJECT_STATUS.md"]

DATA_GLOBS = [
    "results/seed_sensitivity/seed_*/tables/benchmark_results.csv",
    "results/seed_sensitivity/seed_*/config.json",
    "results/seed_sensitivity/seed_*/logs/run_manifest.json",
    "results/sensitivity_uci360_floor_grid/tables/benchmark_results.csv",
    "results/primary_uci360_rewindowed/tables/benchmark_results.csv",
    "results/repro_primary_uci360_rewindowed/tables/benchmark_results.csv",
    "data/processed/uci360_rewindowed.csv",
    "data/processed/uci360_rewindowed_provenance.json",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(globs: list[str]) -> list[Path]:
    out: set[Path] = set()
    for pattern in globs:
        for p in ROOT.glob(pattern):
            if p.is_file():
                out.add(p)
    return sorted(out)


def collect_tree(rel: str) -> list[Path]:
    base = ROOT / rel
    if not base.exists():
        return []
    skip = {"__pycache__", "_preview"}
    keep_suffix = {".py", ".json", ".md", ".yaml", ".yml", ".txt", ".tex",
                   ".pdf", ".csv", ".cls", ".bib"}
    out = []
    for p in sorted(base.rglob("*")):
        if not p.is_file() or any(s in p.parts for s in skip):
            continue
        # Underscore-prefixed files are throwaway working scripts. Excluding them
        # also keeps the archive reproducible: otherwise a scratch file created
        # between two builds changes the zip.
        if p.name.startswith("_"):
            continue
        if p.suffix.lower() in keep_suffix or p.name.startswith("."):
            if p.name.startswith(".") and p.name != ".gitkeep":
                continue
            out.append(p)
    return out


def write_zip(members: list[tuple[Path, str]], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src, arc in sorted(members, key=lambda m: m[1]):
            info = zipfile.ZipInfo(arc, date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, src.read_bytes())


def manifest_lines(members: list[tuple[Path, str]]) -> list[str]:
    rows = ["sha256  size  path"]
    for src, arc in sorted(members, key=lambda m: m[1]):
        rows.append(f"{sha256(src)}  {src.stat().st_size}  {arc}")
    return rows


CODE_DESCRIPTION = f"""<p>Analysis code and derived results for the manuscript
<em>The Exactly-Determined Reference Panel: Why Two-Sample Slope-and-Bias
Recalibration Cannot Be Checked, and Why Larger Panels Are Not Reliably Safe
Either</em>, submitted to Chemometrics and Intelligent Laboratory Systems.</p>

<p><strong>This version supersedes v1.0.0 ({CODE_V1_DOI}), which archived a
withdrawn analysis.</strong> In v1.0.0 the W&ouml;rner two-level electronic-nose
archive was treated as the primary corpus and the UCI air-quality array as
exploratory. That evidence hierarchy was inverted: the two-level corpus cannot
support a claim about reference-set size, because with two nominal concentration
levels there is no range over which a calibration slope can be estimated. The
present version makes the De Vito UCI air-quality array ({UCI_DOI}) primary and
retains W&ouml;rner only as a contrast corpus.</p>

<p>The study evaluates slope-and-bias recalibration of a five-channel metal-oxide
gas-sensor array against co-located reference-analyser values over 389 days, under
a protocol in which the held-out set of each 30-day target window is frozen before
any reference sample is selected. Three analytes, three model classes and ten
target windows give 90 decision cells at each of ten reference budgets from 0 to
50, and the whole evaluation is repeated under ten independent reference-panel
draws.</p>

<p>Two findings are reported at different strengths. The structural one is
draw-invariant: a two-parameter correction fitted on exactly two reference samples
has no residual degrees of freedom, so it interpolates both references and cannot
be contradicted by the data that produced it; across ten draws and 900 decision
cells per budget, calibration-slope inversion and error inflation beyond fivefold
occur at two references and at no other budget, the worst case inflating
normalised RMSE 44.5-fold. The second is a negative result about single-draw
evaluation of standardization-set size: an apparently clean threshold at four
references does not replicate, taking the values 4, 4, 4, 4, 4, 5, 6, 8, 20 and 20
across the ten draws, and moving further with the failure criterion and the error
metric. That threshold is retracted in favour of a bound; the retraction record is
included as artifacts/UCI360_DRAW_SENSITIVITY.md.</p>

<p>Contents: the frozen protocol, run configurations, split/recalibration/metric
implementation, benchmark and analysis runners, the ten-draw replication driver,
derived summaries and decision cells, five vector figures, six main and five
supplementary tables, the manuscript, and an elsarticle LaTeX build. Two audit
scripts are included and exit non-zero on failure: one restates 141 quantitative
claims from the manuscript and recomputes each from the frozen result files, the
other audits the compiled PDF text layer for damage that still compiles.</p>

<p>Row-level benchmark tables for the ten panel draws are archived separately as a
dataset record, following the convention that large numerical arrays are deposited
apart from code. Raw source data are not redistributed: the UCI air-quality array
is public at {UCI_DOI} and the W&ouml;rner contrast archive at {WORNER_DOI};
provenance JSON with checksums is included.</p>

<p>Source code is licensed under MIT; derived tables, figures, protocol documents
and reports under CC BY 4.0.</p>"""

DATA_DESCRIPTION = f"""<p>Row-level benchmark results underlying the manuscript
<em>The Exactly-Determined Reference Panel: Why Two-Sample Slope-and-Bias
Recalibration Cannot Be Checked, and Why Larger Panels Are Not Reliably Safe
Either</em>, submitted to Chemometrics and Intelligent Laboratory Systems.</p>

<p>This record holds the per-cell benchmark tables that the manuscript's central
negative result rests on. Slope-and-bias recalibration of a five-channel
metal-oxide gas-sensor array is evaluated against co-located reference-analyser
values on the De Vito UCI air-quality corpus ({UCI_DOI}), re-windowed into
thirteen 30-day windows over 389 days. Each table has one row per (analyte, target
window, model class, reference budget, update strategy) combination, with held-out
normalised RMSE, MAE, fitted calibration slope, the pre-decision reference-panel
diagnostic, and panel composition.</p>

<p>Ten independent reference-panel draws are included, each redrawing every panel
and reseeding the model random states, giving 3600 rows per draw and 900 decision
cells per reference budget in total. The draws exist because a single one is not
sufficient to establish a minimum reference count: across these ten, the budget
from which no cell exceeds twice frozen error takes the values 4, 4, 4, 4, 4, 5, 6,
8, 20 and 20. Slope inversion and error inflation beyond fivefold occur only at the
exactly-determined two-sample panel, and only in one of the ten draws, which is
what makes the failure a tail risk rather than an expected cost.</p>

<p>Also included: the pre-specified primary run and its independent reproduction
(maximum absolute numerical difference 2.487e-13), and the normalised corpus the
benchmarks were computed from, with its provenance and checksums. Raw source data
are not redistributed; the UCI archive is public at {UCI_DOI}.</p>

<p>Analysis code that produces and consumes these tables is deposited separately
under concept DOI {CODE_CONCEPT_DOI}. Licensed under CC BY 4.0.</p>"""

KEYWORDS = [
    "calibration transfer",
    "model updating",
    "slope and bias correction",
    "standardization set size",
    "gas sensor array",
    "instrumental drift",
    "tail risk",
    "reproducibility",
]


def code_metadata() -> dict:
    return {
        "metadata": {
            "title": ("Reference-set size for slope-and-bias recalibration of a "
                      "drifting gas-sensor array: analysis code and derived results"),
            "upload_type": "software",
            "description": CODE_DESCRIPTION,
            "creators": [{"name": "Cai, Siyu", "affiliation": AFFILIATION,
                          "orcid": ORCID}],
            "keywords": KEYWORDS,
            "access_right": "open",
            "license": "other-open",
            "language": "eng",
            "version": CODE_VERSION,
            "related_identifiers": [
                {"identifier": CODE_V1_DOI, "relation": "isNewVersionOf",
                 "resource_type": "software"},
                {"identifier": UCI_DOI, "relation": "isSupplementTo",
                 "resource_type": "dataset"},
                {"identifier": WORNER_DOI, "relation": "references",
                 "resource_type": "dataset"},
                {"identifier": "10.1016/j.snb.2007.09.060", "relation": "references",
                 "resource_type": "publication-article"},
                {"identifier": "10.1016/j.snb.2009.08.041", "relation": "references",
                 "resource_type": "publication-article"},
            ],
            "notes": ("Supersedes v1.0.0, which archived a withdrawn analysis in "
                      "which the Woerner two-level corpus was treated as primary."),
        }
    }


def data_metadata() -> dict:
    return {
        "metadata": {
            "title": ("Row-level benchmark results for slope-and-bias recalibration "
                      "of a drifting gas-sensor array under ten reference-panel draws"),
            "upload_type": "dataset",
            "description": DATA_DESCRIPTION,
            "creators": [{"name": "Cai, Siyu", "affiliation": AFFILIATION,
                          "orcid": ORCID}],
            "keywords": KEYWORDS,
            "access_right": "open",
            "license": "cc-by-4.0",
            "language": "eng",
            "version": DATA_VERSION,
            "related_identifiers": [
                {"identifier": CODE_CONCEPT_DOI, "relation": "isSupplementTo",
                 "resource_type": "software"},
                {"identifier": UCI_DOI, "relation": "isDerivedFrom",
                 "resource_type": "dataset"},
            ],
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=ROOT / "release")
    args = parser.parse_args()
    out = args.outdir
    out.mkdir(parents=True, exist_ok=True)

    # ---------------- code record ----------------
    members: list[tuple[Path, str]] = []
    for rel, arc in CODE_INCLUDE:
        p = ROOT / rel
        if p.exists():
            members.append((p, arc))
    for rel, arc_root in CODE_TREES:
        for p in collect_tree(rel):
            members.append((p, f"{arc_root}/{p.relative_to(ROOT / rel).as_posix()}"))
    for p in collect(CODE_RESULT_GLOBS + CODE_ARTIFACT_GLOBS):
        members.append((p, p.relative_to(ROOT).as_posix()))
    # drop drafting PNGs: the PDFs are the deliverable
    members = [(s, a) for s, a in members if not a.endswith(".png")]

    code_zip = out / f"gas_sensor_recalibration_v{CODE_VERSION}.zip"
    write_zip(members, code_zip)
    (out / f"code_v{CODE_VERSION}_manifest.txt").write_text(
        "\n".join(manifest_lines(members)) + "\n", encoding="utf-8")
    (out / "zenodo_code_metadata.json").write_text(
        json.dumps(code_metadata(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"code record : {code_zip.name}  {code_zip.stat().st_size / 1e6:.2f} MB, "
          f"{len(members)} files")
    print(f"              sha256 {sha256(code_zip)}")

    # ---------------- data record ----------------
    dmembers: list[tuple[Path, str]] = []
    for p in collect(DATA_GLOBS):
        dmembers.append((p, p.relative_to(ROOT).as_posix()))
    readme = out / "_DATA_README.md"
    readme.write_text(data_readme(dmembers), encoding="utf-8")
    dmembers.append((readme, "README.md"))

    data_zip = out / f"gas_sensor_recalibration_data_v{DATA_VERSION}.zip"
    write_zip(dmembers, data_zip)
    (out / f"data_v{DATA_VERSION}_manifest.txt").write_text(
        "\n".join(manifest_lines(dmembers)) + "\n", encoding="utf-8")
    (out / "zenodo_data_metadata.json").write_text(
        json.dumps(data_metadata(), indent=2, ensure_ascii=False), encoding="utf-8")
    readme.unlink()
    print(f"data record : {data_zip.name}  {data_zip.stat().st_size / 1e6:.2f} MB, "
          f"{len(dmembers)} files")
    print(f"              sha256 {sha256(data_zip)}")
    print(f"\nwrote to {out}")
    return 0


def data_readme(members: list[tuple[Path, str]]) -> str:
    seeds = sorted({a.split("/")[2].replace("seed_", "")
                    for _, a in members if "/seed_" in a})
    return f"""# Row-level benchmark results

Underlying data for the manuscript *The Exactly-Determined Reference Panel*
(Chemometrics and Intelligent Laboratory Systems). Analysis code is deposited
separately under concept DOI {CODE_CONCEPT_DOI}.

## Contents

```text
results/sensitivity_uci360_floor_grid/tables/benchmark_results.csv
    Pre-specified panel draw (seed 20260826), dense budget grid.
results/seed_sensitivity/seed_<N>/tables/benchmark_results.csv
    Nine replication draws, seeds {', '.join(seeds)}.
results/seed_sensitivity/seed_<N>/config.json
    The exact configuration used for each draw.
results/primary_uci360_rewindowed/tables/benchmark_results.csv
results/repro_primary_uci360_rewindowed/tables/benchmark_results.csv
    Pre-specified primary run on the 6-point budget grid, and its independent
    reproduction. Maximum absolute numerical difference: 2.487e-13.
data/processed/uci360_rewindowed.csv
    Normalised corpus the benchmarks were computed from.
data/processed/uci360_rewindowed_provenance.json
    Source checksums and the normalisation record.
```

## Row schema

One row per (gas_id, target_batch, model, strategy, budget). Key columns:

| column | meaning |
|---|---|
| `gas_id` | analyte: CO, NO2, NOx |
| `target_batch` | 30-day target window, 4–13 |
| `model` | pls, random_forest, xgboost |
| `strategy` | frozen, calibrator_update, target_finetune, full_retrain |
| `budget` | labelled target-period references, 0/2/3/4/5/6/8/10/20/50 |
| `nrmse`, `mae` | held-out error |
| `calibration_slope` | slope of reference values on predictions, held-out; 1 is ideal |
| `frozen_nrmse` | the frozen model's held-out nRMSE for the same cell |
| `d_ref` | pre-decision reference-panel diagnostic |
| `reference_row_ids` | which rows formed the panel |
| `n_reference`, `n_test` | panel and held-out sizes |

`calibrator_update` is the slope-and-bias correction under study. Note that
`calibration_slope` is evaluated on the held-out set and is not the correction's
own fitted coefficient; the two differ by an order of magnitude in the failure
cases.

## Why ten draws

A single draw is not sufficient to establish a minimum reference count. Across
these ten, the budget from which no cell exceeds twice its frozen error takes the
values 4, 4, 4, 4, 4, 5, 6, 8, 20 and 20. Slope inversion and error inflation
beyond fivefold occur only at the exactly-determined two-sample panel, and only in
one of the ten draws.

## Raw data

Not redistributed. The source corpus is the De Vito air-quality array, public at
{UCI_DOI}. The contrast corpus referenced in the manuscript is at {WORNER_DOI}.

Licensed CC BY 4.0.
"""


if __name__ == "__main__":
    raise SystemExit(main())
