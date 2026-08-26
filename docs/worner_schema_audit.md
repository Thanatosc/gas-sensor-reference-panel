## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: validate
- Origin Date: 2026-08-15
- Verification Status: VERIFIED
- Version Label: worner_schema_audit_v1

# Wörner confirmation-corpus schema audit

## Provenance

- Dataset: *Long-Term Drift Behavior of Electronic Nose*
- Zenodo DOI: `10.5281/zenodo.15681119`
- Publication DOI: `10.1038/s41597-025-05993-8`
- Zenodo license: CC BY 4.0
- Archive: `data/raw/worner_zenodo_15681119_Dataset.bits.zip`
- Published archive size: 141,110,296 bytes
- Published MD5: `9937678cac4118c53287276009172a74`
- Local MD5: `9937678cac4118c53287276009172a74` (match)

## Archive structure

The archive contains 741 entries: 700 raw measurement CSVs, one
`extracted_features.csv`, one notebook, and 39 day directories. `Day 14` is
absent as described by the publication because that day was discarded for
protocol deviations. Two days contain 17 files rather than 18; the four
concentration-bearing classes themselves remain complete at 117 files per
class. The pre-extracted table has 624 rows and 36 dates, so it is not treated
as the complete confirmation panel.

Each raw CSV has 67 columns:

- time and date;
- `R1[Ohm]`–`R62[Ohm]` gas-sensor resistance channels;
- `T01[degC]` and `H01[%rh]` environmental channels;
- `Cycle_Stage` with baseline (1), sample exposure (2), and recovery (3).

The raw files contain approximately 20 minutes of one-second observations and
are individually labeled by filename. The first timestamp in each file is used
as the measurement timestamp; the file name supplies the analyte and target
concentration.

## Label and target decision

The publication defines 117 measurements at each of two diacetyl levels
(0.1 and 1 ppm), 117 at each of two 2-phenylethanol levels (200 and 1000 ppm),
and 232 ethanol measurements. Ethanol is a 5% v/v aqueous solution used as a
diluent and blank, not an analyte with a varying concentration label. It is
therefore excluded from the primary concentration-regression table rather than
assigned an artificial target of zero.

The normalized confirmation table will contain 468 rows, two analyte sequences,
two concentration levels per sequence, and a numeric `target` in ppm. Ethanol
files and their exclusion reason are retained in the provenance JSON.

## Feature contract

The normalizer reproduces the archive notebook's four feature families for each
measurement file:

1. mean of the last 10 stage-2 values for 62 resistance, temperature, and
   humidity channels (64 features);
2. relative stage-2 versus stage-1 difference using the last 10 values (64);
3. linear slope over the first 30 stage-2 values for the 62 resistance
   channels (62);
4. stage-3/stage-1 recovery ratio using the last 10 values for the 62
   resistance channels (62).

This yields 252 numeric sensor features. No class, target, day, file name, or
future-window variable is included as a model feature.

## Temporal unit and windows

The inferential unit is a temporal deployment window, not an individual
one-second sensor row or a nominally independent model run. The normalizer
orders the 39 available day folders by day number and creates consecutive
six-day windows. `batch_id` is the resulting window identifier; `day_id` and
`row_in_batch` are provenance metadata. The final window can be shorter and is
reported explicitly in the audit. Reference panels are sampled from a target
window after a fixed evaluation holdout is frozen.

## Gate decision

The corpus passes the schema/provenance gate for the revised Measurement RQ:
it has time order, concentration-bearing labels, raw sensor responses, and
within-cycle stage information. It does not by itself identify physical sensor
drift separately from residual environmental or maintenance effects; all
results remain temporal-shift evidence rather than a causal drift estimate.
