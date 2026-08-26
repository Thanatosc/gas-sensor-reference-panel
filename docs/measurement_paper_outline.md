# Paper Outline — Measurement

## Paper configuration

- **Working title:** *Budgeted Recalibration of Gas Sensor Arrays under Temporal Shift: When Is Lightweight Updating Insufficient?*
- **Target journal:** Measurement; official Guide for Authors verified on 2026-08-16.
- **Article type:** Original research paper / reproducible measurement-system evaluation study; maximum 30 pages including references.
- **Language:** English.
- **Target length:** approximately 6,200–6,800 words and 24–27 submission pages including references, leaving margin below the 30-page ceiling.
- **Structure pattern:** IMRaD with a focused related-work/problem-formulation section.
- **Statistical unit:** target temporal window; model classes and analytes are stratification dimensions, not independent replicates.
- **Venue profile:** `configs/measurement_venue_profile.yaml`.
- **Submission model:** double anonymized; separate title page and blind manuscript.

## Central research question

Under a leakage-controlled, time-ordered evaluation protocol, how does the absolute number of target-period reference observations affect lightweight output calibration versus full retraining, and in which analyte/model/temporal regimes does lightweight updating remain inadequate?

## Main thesis and claim boundary

Reference count alone does not determine recalibration success. Lightweight output calibration can improve held-out nRMSE in some temporal/model regimes but can worsen it in others; full retraining is more consistently beneficial in the evaluated confirmation panel at higher reference budgets. The study reports descriptive temporal-shift evidence and does not identify temporal change as physical sensor drift without a causal separation of environment, maintenance, and concentration effects.

## Detailed outline

### Abstract (220–240 words; not counted)

State the measurement-system evaluation problem, the time-ordered benchmark, the two evidence roles (exploratory UCI and Wörner confirmation), absolute budgets (0–50), three model classes, the primary five-reference result, the heterogeneous lightweight boundary, and the practical conclusion. Keep the abstract factual, stand-alone, below the official 250-word limit, free of citations, and free of unsupported acceptance probabilities. Provide six English keywords and a separate five-item Highlights file, each bullet no more than 85 characters including spaces.

### 1. Introduction (~900 words)

**Purpose.** Establish why reference-sample budgeting is a measurement-system question rather than only an algorithm-comparison question.

**1.1 Temporal change in gas-sensor measurements (~250 words).**

Frame changing sensor responses, environmental conditions, maintenance, and concentration support as a combined temporal-distribution problem. Use cautious language (“temporal shift” or “deployment-period change”) unless a source supports a narrower physical interpretation.

**1.2 Why recalibration cost and failure boundaries matter (~250 words).**

Explain the operational contrast between an output calibrator and fitting the predictive model again. Motivate an absolute reference-count axis and a held-out target test set. Verified sources for this distinction are recorded in `artifacts/ANNOTATED_BIBLIOGRAPHY.md` and `artifacts/SOURCE_TO_CLAIM_MATRIX.md`.

**1.3 Gap and research question (~200 words).**

Identify the missing joint evaluation: leakage-controlled temporal extrapolation, nested reference budgets, model/analyte heterogeneity, and explicit “insufficient lightweight update” outcomes.

**1.4 Contributions and scope limits (~200 words).**

List the protocol, budget-performance curves, heterogeneous decision boundary, denominator diagnostics, and reproducibility package. Define the primary advance as an evaluation procedure for performance analysis of a measurement system. Explicitly state that no new drift-compensation algorithm is proposed and causal physical-drift attribution is out of scope.

**Transition.** The introduction defines the decision problem; Section 2 positions it against prior drift and recalibration studies and formalizes the estimand.

### 2. Related work and problem formulation (~1,200 words)

**Purpose.** Define the benchmark’s conceptual distinctions and make the novelty claim search-bounded rather than absolute.

**2.1 Gas-sensor array drift and temporal-shift evaluation (~350 words).**

Synthesize verified studies that evaluate response changes over time, including the limits of attributing those changes to a single physical mechanism. Each statement must carry a verified DOI or official bibliographic record.

**2.2 Output calibration, target updating, and full retraining (~300 words).**

Separate prediction-space recalibration from model refitting and target-only fitting. Clarify that “lightweight” refers to the `calibrator_update` strategy in this paper, not to every low-compute method in the literature.

**2.3 Reference budgets, leakage, and deployment cost curves (~300 words).**

Review time-aware validation, calibration-panel selection, and sample-efficiency reporting. Contrast percentage budgets with the absolute-count primary axis used here.

**2.4 Estimand and decision gates (~250 words).**

Define held-out nRMSE, absolute change ΔnRMSE, and the protocol’s recovery ratio. State the descriptive gates: frozen nRMSE relative increase ≥0.20; recovery ≥0.50 as support; recovery <0.20 as inadequate. State that small denominators are reported as warnings and are never filtered after seeing results.

**Transition.** Section 2 identifies the methodological gap and defines the estimand; Section 3 gives the data contract and frozen analysis implementation.

### 3. Materials and methods (~1,550 words)

**Purpose.** Make every split, budget, model, metric, and provenance decision reproducible.

**3.1 Evidence roles and datasets (~250 words).**

Describe UCI 270/360 as exploratory Kill-Test evidence and keep them as one evidence family where applicable. Describe the untouched Wörner et al. (2025) Zenodo record (DOI `10.5281/zenodo.15681119`) as the confirmation panel. State that exploratory and confirmation results are not pooled as jointly pre-registered evidence.

**3.2 Wörner archive normalization and audit (~300 words).**

Report the checksum-verified archive, 700 raw measurement files, exclusion of 232 EtOH diluent/blank files from concentration regression, and inclusion of 468 Diacetyl/Phenylethanol records. Describe 62 gas sensors plus temperature/humidity and cycle-stage variables, 252 finite numeric features, exclusion of Day 14 for protocol deviation, and seven total temporal windows (three source windows and four target windows; the final target window has three available days). Link to `docs/worner_schema_audit.md`, `docs/worner_data_contract.md`, and `results/logs/worner_dataset_audit.json`.

**3.3 Time-ordered split and reference-panel construction (~300 words).**

Fit source models on batches 1–3 and evaluate target batches 4–7. Restrict each analyte/window to exact common concentration support, freeze the target holdout before selecting references, and use nested concentration-spread reference panels. Primary absolute budgets are 0, 2, 5, 10, 20, and 50 observations. Describe the alternative three-day-window and reference-seed sensitivity configurations without using them to redefine the primary result.

**3.4 Models and recalibration strategies (~250 words).**

Specify PLS, Random Forest, and XGBoost. Define `frozen`, `calibrator_update` (the lightweight strategy), `target_finetune`, and `full_retrain`; the oracle model uses all available target reference-pool labels only to define the denominator. Report seeds and package versions from the run manifests.

**3.5 Measurement model, endpoints, and denominator diagnostics (~300 words).**

Define the measurand as analyte concentration in ppm and distinguish the nominal reference concentration from the sensor-array response and the model prediction. Define nRMSE, MAE, calibration slope, frozen relative increase, ΔnRMSE, and `recovered_loss`. Leave recovery undefined when the denominator is non-positive or non-finite. Report denominator minimum/median/maximum and flag a descriptive `<0.05` nRMSE denominator warning without excluding or reweighting rows. State explicitly that the source archive does not provide a complete traceable uncertainty budget for the nominal concentrations; IQRs summarize temporal-window variation and are not measurement uncertainty or confidence intervals.

**3.6 Reproducibility and reporting unit (~200 words).**

State that each target temporal window is one observational unit for summaries, while all target rows remain prediction units. Report exact commands, configuration hashes, input checksums, sampled row identifiers, and the rerun tolerance result. Use medians and interquartile ranges for the four-window primary summary; do not present model rows as independent confidence-bearing replicates.

**Transition.** The methods define a fixed decision curve and guard against target leakage; Section 4 reports the complete confirmation result before interpretation.

### 4. Results (~1,400 words)

**Purpose.** Report all pre-specified budgets and regimes, leading with absolute error and using recovery as a bounded decision summary.

**4.1 Dataset and reproducibility audit (~220 words).**

Report 468 normalized rows, 252 features, seven total temporal windows (three source and four target; the final target window has three days), zero missing/non-finite features, 576 primary result rows, no skipped sequences, and the independent rerun result (`REPRODUCIBLE_WITH_FLOATING_POINT_VARIATION`; maximum absolute numeric difference approximately `3.7×10⁻13`; threshold decisions identical). Refer to Figure 1 and the audit table.

**4.2 Budget–performance curves (~350 words; Figure 2).**

Show median held-out nRMSE and IQR across budgets for each analyte/model. Report the direction of absolute ΔnRMSE for lightweight calibration and full retraining without collapsing across analytes or models. Keep target-finetune results in a supplementary table unless the journal requires all four strategies in the main text.

**4.3 Primary five-reference decision boundary (~350 words; Figure 3; Table 1).**

Report 10 drift-positive lightweight sequences, 7 drift-conditioned recoveries ≥0.50, and 2 drift-conditioned recoveries <0.20. Describe which analyte/model panels contain improvements and worsening in terms of absolute ΔnRMSE first. State that full retraining has 9 drift/recovery joint hits at the same budget. The counts are descriptive over temporal windows.

**4.4 Denominator stability and secondary endpoints (~220 words; Table 2).**

Report the 24 primary denominators (median and range by analyte/model), identify the smallest denominators and corresponding extreme ratios, and explain why the main interpretation does not rely on the most extreme `recovered_loss` values. Include MAE and calibration-slope summaries as secondary evidence.

**4.5 Sensitivity analyses (~260 words; Figure 4; Table 3).**

Report that the heterogeneous boundary remains present for three-day windows (12 high, 6 inadequate among drift-positive lightweight rows) and the alternative reference seed (9 high, 1 inadequate), while counts and regime medians move. State that common-support versus observed-range is structurally identical for this panel and that a missingness sensitivity is not applicable because the normalized panel has no missing/non-finite features.

**Transition.** The results establish what changed, where it changed, and how stable the boundary is; Section 5 explains the measurement and deployment implications without overextending causality.

### 5. Discussion (~1,200 words)

**Purpose.** Interpret the decision boundary for measurement practice and connect it to verified prior work.

**5.1 Principal interpretation (~250 words).**

The main result is not a universal ranking but a conditional boundary: reference count is necessary context, not a sufficient decision rule. Lightweight output calibration can be efficient but is not reliably protective under every temporal/model regime.

**5.2 Implications for measurement-system performance evaluation (~300 words).**

Recommend reporting absolute reference counts, held-out target error, model/analyte stratification, and denominator diagnostics when evaluating recalibration. Explain why a deployment team should not infer “five references are enough” from an aggregate median.

**5.3 Relation to prior literature (~250 words).**

Compare with verified temporal-drift and recalibration studies. Distinguish differences in split design, target support, reference-budget definition, and whether methods are algorithm proposals or evaluation protocols. This subsection cannot be finalized until the literature search and DOI checks are complete.

**5.4 Why full retraining is not a universal answer (~200 words).**

Discuss computational and labeling costs, the mixed Phenylethanol results, and the need to evaluate both improvement and failure. Avoid claiming full retraining “solves drift.”

**5.5 Practical decision rule and reporting checklist (~200 words).**

Offer a cautious operational rule: pilot a nested reference panel, inspect absolute ΔnRMSE and denominator stability, and escalate from lightweight updating to retraining only when the target-window validation evidence supports it. Make clear this is a reporting/selection heuristic, not a newly optimized algorithm.

### 6. Limitations (~550 words)

Cover: one confirmation evidence family; three-day final target window; two analytes and two concentration levels; no causal separation of physical drift from environment/maintenance/concentration change; no complete traceable uncertainty budget for the reference concentrations; model-hyperparameter scope; small number of temporal windows; sensitivity to reference-panel design; instability of ratio denominators; no monetary sampling-cost metadata; no prospective deployment or replacement-sensor experiment; and no inferential pooling across model classes.

### 7. Conclusions (~300 words)

Answer the RQ directly: absolute reference count should be evaluated with model/analyte/time-window context. Lightweight output calibration is conditionally useful but demonstrably insufficient in some regimes; full retraining is more reliable in the evaluated higher-budget cases but carries greater cost. Close with the reproducible protocol and the need for external prospective validation.

## Evidence map

| Section | Evidence assigned | Evidence type | Status |
|---|---|---|---|
| 1 | Wörner et al. 2025 dataset paper; verified gas-sensor recalibration literature to be searched | Problem framing | Dataset source verified; broader literature pending |
| 2.1–2.3 | Verified DOI records on gas-sensor temporal drift, calibration transfer, and time-aware validation | Literature synthesis | Verified; see `artifacts/LITERATURE_SEARCH_REPORT.md` and the source-to-claim matrix |
| 2.4 | `docs/revised_protocol_measurement.md`; `src/gasdrift/metrics.py` | Operational estimand and gates | Internal protocol verified |
| 3.1–3.2 | Zenodo `10.5281/zenodo.15681119`; `docs/worner_schema_audit.md`; `docs/worner_data_contract.md` | Dataset provenance and normalization | Verified |
| 3.3–3.6 | Frozen configs, source code, audit logs, run manifests, primary/reproducibility CSVs | Methods and reproducibility | Verified |
| 4 | `results/tables/confirmation_*.csv`; `artifacts/CONFIRMATION_REPORT.md`; `artifacts/CONFIRMATION_TABLES.md` | Primary and sensitivity results | Verified |
| 5 | Results plus verified prior studies | Interpretation and comparison | Results verified; comparison literature pending |
| 6–7 | Results and protocol boundary conditions | Limitations and conclusion | Ready after literature/official journal checks |

## Planned main-text tables and figures

1. **Figure 1:** temporal split and reference-budget workflow.
2. **Figure 2:** budget curves for held-out nRMSE, with IQR ribbons.
3. **Figure 3:** five-reference absolute ΔnRMSE and lightweight decision categories.
4. **Figure 4:** sensitivity of decision-gate proportions.
5. **Table 1:** primary five-reference regime summary (`results/tables/confirmation_primary_regime_summary.csv`).
6. **Table 2:** target-window decision matrix and denominator diagnostics (`results/tables/confirmation_primary_decision_matrix.csv`, `confirmation_denominator_diagnostics.csv`).
7. **Table 3:** budget curves and sensitivity counts (`confirmation_budget_summary.csv`, `confirmation_sensitivity_summary.csv`).

## Required pre-drafting gates

- [x] User approves this structure and delegates content decisions.
- [x] Official Measurement aims/scope, Guide for Authors, and data policy are checked.
- [x] Literature search produces verified DOI records and a source-to-claim matrix for Sections 1, 2, and 5 (`artifacts/LITERATURE_SEARCH_REPORT.md`, `artifacts/ANNOTATED_BIBLIOGRAPHY.md`, and `artifacts/SOURCE_TO_CLAIM_MATRIX.md`).
- [x] Figure rendering completes; figure trace hashes are refreshed.
- [x] Manuscript plan keeps UCI exploratory evidence separate from Wörner confirmation evidence.

## Binding submission-package rules

- Abstract: no more than 250 words; 1–7 English keywords.
- Highlights: required separate editable file, 3–5 bullets, each no more than 85 characters including spaces.
- Main source: editable Elsevier LaTeX; PDF is a checking artifact, not the source submission.
- Blind review: submit an anonymized manuscript and a separate title page; acknowledgments remain only in the title-page file.
- References: numbered square brackets in order of appearance; DOI included where available.
- Data: cite and link the source Zenodo dataset and deposit the analysis code/derived outputs in a persistent repository, or state why a component cannot be shared.
- Declarations: Data and code availability, CRediT, funding, competing interests, and generative-AI use.
- Figures: submit the vector PDF files separately; tables remain editable and use no vertical rules or shading.
- Cover letter: explicitly explain the advance in measurement-system evaluation and the disciplined use of metrological terminology.
