# Data Contract

The benchmark consumes a normalized CSV. Raw UCI/Zenodo files remain untouched
under `data/raw/` or `data/external/`; normalization is a separately documented
step.

## Required columns

| Column | Type | Constraint |
|---|---|---|
| `timestamp` | ISO-8601 string or numeric order | non-null; sortable within a source sequence |
| `batch_id` | string/integer | non-null; source/target split unit |
| `location_id` | string/integer | non-null when available; use a stable sentinel only when the source has no location concept |
| `gas_id` | string/integer | non-null; stratification only |
| `target` | numeric | concentration/reference-analyzer value; non-null for scored rows |

All remaining columns are numeric sensor features. Feature columns must not
contain target, gas identity, batch, location, or future-derived variables.
`row_in_batch` is an allowed provenance column and is explicitly excluded from
model features.

## Temporal audit requirements

The audit must report row count, feature count, null counts, unique batches,
unique locations, timestamp range, per-sequence monotonicity, and overlap between
configured source and target batches. A benchmark cannot start unless the audit
status is `PASS`.

## Dataset provenance

Record the UCI dataset ID or DOI, download date, license, raw file checksum,
normalization script/command, and any column mapping. UCI IDs 224 and 270 must be
marked as the same evidence family if both appear in the workspace.

For UCI 270, exact sample timestamps are unavailable. The normalized
`timestamp` is therefore the batch ordinal, the documented temporal resolution
is batch-level, and `row_in_batch` is provenance rather than a sensor feature.
