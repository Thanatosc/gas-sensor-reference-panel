# Budgeted Recalibration of Gas Sensor Arrays under Temporal Shift: When Is Lightweight Updating Insufficient?

## Abstract

Reference measurements are costly, yet the number of target-period references
required to maintain a gas-sensor measurement system is rarely evaluated as an
absolute, time-ordered decision variable. We develop a leakage-controlled
evaluation procedure that compares a frozen model, a lightweight output
calibrator, target-only fitting, and full retraining over nested reference
budgets. The confirmation panel is a checksum-verified one-year electronic-nose
archive containing 468 concentration-bearing records, 252 derived sensor
features, two analytes, and four target temporal windows. Partial least squares,
random forest, and gradient-boosted regression are evaluated at 0, 2, 5, 10, 20,
and 50 labelled target-window references. At the primary five-reference budget,
lightweight updating is heterogeneous: 10 of 24 model/analyte/window sequences
meet the frozen-error increase gate, seven of those reach at least 50% recovery
toward an oracle, and two remain below 20% recovery. Full retraining produces
nine drift/recovery joint hits at the same budget. The direction and magnitude of
the absolute nRMSE change vary across analytes, model classes, and windows;
therefore, reference count alone is not a sufficient recalibration rule. The
qualitative boundary persists in three-day-window and reference-seed
sensitivity analyses, although regime medians move. We report temporal-shift
evidence rather than causal physical drift, and we treat recovery ratios as
secondary because small denominators can create extreme values. The resulting
procedure is a measurement-system performance evaluation framework, not a new
drift-compensation algorithm.

**Keywords:** gas sensor array; temporal shift; recalibration; calibration transfer;
reference budget; time-ordered validation

## 1. Introduction

### 1.1 Temporal change in gas-sensor measurements

Gas-sensor arrays are attractive because a group of partially selective sensing
elements can encode complex mixtures without requiring a separate highly
selective transducer for every analyte. In deployment, however, the mapping from
the array response to a concentration or class is not fixed. Sensor aging,
temperature and humidity, operating history, maintenance, sample matrix, and
changes in concentration support can all alter the observed response. Reviews of
electronic noses describe this loss of temporal validity as a central barrier to
practical use and distinguish drift correction, standardization, and calibration
update as different responses to it [1]. Reviews of metal-oxide sensor
stability likewise emphasize that environmental and material factors affect
long-term signal behavior [2]. In field air-quality work, laboratory and
collocation calibration can produce different deployment errors, and drift has
to be examined over the intended operating period [3].

These observations motivate a causal-neutral term in this paper. We use
*temporal shift* for a change in the joint distribution of sensor features and
nominal concentration labels between source and later deployment windows. The
term does not assert that the change is caused by a single physical sensor-drift
mechanism. A recent audit of a widely used metal-oxide gas dataset found that
recording batches were temporally clustered and that residual short-term drift
could reveal the batch; random benchmark splits could therefore overstate
classification performance [4]. Batch experiments also show how environmental
covariates can become entangled with sensor drift [5]. A temporal change in a
public archive is thus useful evidence for a deployment-period evaluation, but it
is not, by itself, a causal estimate of physical drift.

### 1.2 Why recalibration cost and failure boundaries matter

The operational response to temporal shift is not unique. A measurement team can
leave the source model frozen, fit a low-dimensional output calibration using a
small panel of labelled target references, fit a target-only model, or retrain on
the source data together with the labelled target references. The first update
can be cheap and fast, but it changes only the prediction-space mapping. Full
retraining can use the target features more extensively, but requires a model fit
and can be unstable when the labelled panel is small or poorly spread. Calibration
transfer literature makes a related distinction between robust calibration,
bias/skew adjustment using a modest reference set, and transformation of the
measurement response [6]. Multivariate calibration-transfer treatments place
these choices in a broader model-transfer framework [7].

The practical question is therefore not simply which algorithm has the highest
accuracy on one benchmark. It is how many labelled target references are needed
before an updating strategy improves a held-out deployment period, and whether a
small update can make the prediction error worse. Reference-sample availability
is explicitly identified as a practical constraint in reviews of electronic-nose
calibration update [1]. Yet many compensation studies report a single panel
design, a percentage of target data, or a classification accuracy without a
nested absolute budget curve [8–11]. Those summaries cannot answer
whether “five references” is an operationally portable rule.

### 1.3 Leakage, time order, and the evaluation gap

Random cross-validation is not a neutral default when the deployment question is
prediction in a later temporal window. Time-series validation studies show that
the validity of ordinary cross-validation depends on the temporal dependence and
the forecasting target [12]. Comparative work on time-series performance
estimation finds that the evaluation method itself changes the reported result
[13]. More general blocked-validation guidance warns that ignoring temporal
structure can underestimate predictive error, especially when extrapolation is
the intended task [14]. Target leakage is the related failure in which information
about the prediction target enters model selection even though it will not be
available at deployment; learn–predict separation is a basic safeguard [15].

The gas-sensor literature contains strong algorithmic contributions, including
component correction, classifier ensembles, domain adaptation, and online
self-training [8–11, 16–24]. The unresolved evaluation question is narrower:
under a frozen temporal holdout, how does an *absolute* labelled-reference budget
change the performance of a lightweight output update relative to full
retraining, and where does the lightweight update remain inadequate? The question
is measurement-oriented because it concerns the performance analysis of a
measurement system, its operating-period validation, and the evidence required
before choosing a recalibration action.

### 1.4 Contributions and scope limits

This paper makes four bounded contributions. First, it specifies a leakage-
controlled temporal protocol in which the target test set is frozen before the
reference panel is selected and the same panel is supplied to every updating
strategy. Second, it reports budget–performance curves on an absolute reference
axis (0, 2, 5, 10, 20, and 50 observations) rather than reducing the decision to a
single percentage. Third, it reports heterogeneous outcomes by analyte, model
class, and target window, including cases in which lightweight updating worsens
absolute nRMSE. Fourth, it makes ratio-denominator diagnostics and reference-panel
sensitivity part of the result rather than hiding them in a post-hoc filter.

The study does not propose a new PLS, random-forest, XGBoost, or drift-compensation
algorithm. It does not estimate the monetary cost of sampling, construct a
traceable uncertainty budget for the nominal concentrations, or identify physical
sensor drift separately from environment, maintenance, and concentration-distribution
change. The principal claim is consequently procedural and search-bounded: a
stratified, leakage-controlled budget evaluation is needed to decide when a
lightweight update is insufficient under the tested measurement context.

## 2. Related work and problem formulation

### 2.1 Gas-sensor temporal change and compensation

The classical gas-array drift literature is dominated by feature- or model-space
compensation. Orthogonal signal correction and common principal-component methods
remove structured variation before recognition [16, 18]. Classifier ensembles
adapt the decision function across batches or time periods [8, 9, 19]. Coupled
task learning treats calibration transfer and drift compensation as related
transfer tasks [17]. More recent work explores calibrant-free compensation,
semi-supervised domain adaptation, online self-training, and knowledge
distillation [20–24]. These studies show that temporal change can be
substantial and that low-label or label-free operation is scientifically valuable.

Their estimands are not identical. Several use gas classification accuracy or
F1-score, whereas the present paper predicts concentration and reports nRMSE,
MAE, and calibration slope. Some use a public three-year classification dataset
or a single target-domain task, while the present protocol evaluates four
deployment windows with a fixed held-out test set. The differences matter: a
method that preserves class separation need not preserve a quantitative
concentration mapping, and an update that improves an aggregate metric can still
fail in one analyte/model/window regime.

The recent literature also contains cautionary evidence. Dennler et al. showed
that temporal batch structure and residual drift in a popular dataset can act as
shortcuts for classification [4]. Sun and Zheng report a small-data compensation
procedure on a 36-month, two-gas dataset [25], while Oh et al. model environmental
covariates in batch experiments [5]. These studies support the importance of
time order and covariate context, but neither supplies the absolute reference
budget comparison used here. The Wörner archive used for our confirmation panel
was introduced specifically to provide a documented one-year, 62-sensor dataset
for drift detection and compensation [26].

### 2.2 Output calibration, target updating, and full retraining

We use *calibrator update* in a deliberately narrow sense. A source model is fit
once; its target-window predictions for the labelled references are then mapped
to nominal target values with a one-dimensional affine calibration. The underlying
feature-to-prediction model is not refit. This is the lightweight strategy in the
paper. It should not be conflated with every low-compute drift method in the
literature, nor with instrument-level metrological calibration.

The comparison strategies are therefore operational rather than algorithmic:

- **frozen:** source model only;
- **calibrator_update:** source model plus a target-reference affine output map;
- **target_finetune:** model fit on the target references only (reported as a
  secondary strategy); and
- **full_retrain:** model fit on source data concatenated with target references.

Calibration-transfer reviews describe related bias/skew adjustments and response
standardization using modest reference subsets [6, 7]. The present protocol
extends that perspective in one direction: it treats the number of labelled
target observations as a controlled cost axis and asks when the update changes a
held-out later-period error. It does not claim that an affine output map is the
best transfer method, only that it is a transparent lightweight baseline for a
measurement-system decision.

### 2.3 Reference budgets and temporal leakage

Absolute budgets are preferable to percentages when a deployment team must decide
how many physical reference measurements to collect. A percentage can represent
different laboratory workloads as the target window changes; it can also obscure
that the smallest windows cannot support the same concentration spread. We use
nested concentration-spread panels at 0, 2, 5, 10, 20, and 50 observations,
capped by the available reference pool. The target holdout is fixed before panel
selection. Every strategy therefore sees the same labelled references and the
same held-out rows.

This design follows the general warning from blocked-validation work that the
split should match the deployment extrapolation task [12–14]. It also applies
the learn–predict separation implied by leakage definitions [15]. No target-test
prediction is used to choose a reference panel, model, budget, or threshold.
Models and analytes are stratification dimensions. The temporal window is the
summary unit; model rows are not independent replicates.

### 2.4 Estimand and decision gates

The measurand is analyte concentration, expressed in ppm. The archive supplies
nominal concentration labels as reference values, but it does not document them
as traceable certified values. A feature vector \(x\) is a sensor-array response;
a model prediction \(\hat{y}\) is an estimate of the nominal target. For a target
test set with observed range \(R_y = \max(y)-\min(y)\), we define

\[
\mathrm{nRMSE} = \frac{\sqrt{n^{-1}\sum_i(y_i-\hat{y}_i)^2}}{R_y},
\qquad
\Delta\mathrm{nRMSE} = \mathrm{nRMSE}_{\mathrm{updated}}-
\mathrm{nRMSE}_{\mathrm{frozen}}.
\]

To identify a target window in which the frozen model has degraded relative to
the immediately preceding source validation, we first train on source windows 1–2,
validate on source window 3, and compute

\[
d_{frozen} =
\frac{\mathrm{nRMSE}_{frozen,target}-\mathrm{nRMSE}_{source,validation}}
{\mathrm{nRMSE}_{source,validation}}.
\]

The frozen-error increase gate is \(d_{frozen} \ge 0.20\); it is independent of
which updating strategy is later evaluated.
For rows with a positive finite oracle denominator, recovery toward the oracle
is

\[
\mathrm{recovered\_loss} =
\frac{\mathrm{nRMSE}_{frozen}-\mathrm{nRMSE}_{updated}}
{\mathrm{nRMSE}_{frozen}-\mathrm{nRMSE}_{oracle}}.
\]

Recovery ≥0.50 is a descriptive support gate and recovery <0.20 is a descriptive
inadequacy gate. The denominator screen of 0.05 nRMSE units is a display warning
only. Rows are not deleted, reweighted, or reclassified because of the warning.
In line with VIM and GUM [27, 28], we call the outputs predictive error and
recovery, not measurement uncertainty or traceable accuracy. IQRs across temporal
windows are descriptive dispersion summaries, not uncertainty intervals.

## 3. Materials and methods

### 3.1 Evidence roles and datasets

The project began with a pre-specified exploratory Kill Test on two UCI gas-array
corpora. That test did not satisfy the joint cross-corpus lightweight-transfer
criterion and is retained only as motivation for the revised question. The two
UCI corpora are not pooled with the confirmation evidence as if they had been
pre-registered together.

The confirmation panel is the one-year electronic-nose archive released by Wörner,
Eimler, and Pein-Hackelbusch [26] (publication DOI
10.1038/s41597-025-05993-8; Zenodo DOI 10.5281/zenodo.15681119). The downloaded
archive was checked against the published MD5
9937678cac4118c53287276009172a74. It contains 700 raw measurement CSV files, an
incomplete pre-extracted feature table, a notebook, and day directories. The
source study used a commercial array with 62 metal-oxide sensors and recorded
diacetyl, 2-phenylethanol, and ethanol over approximately one year [26].

### 3.2 Normalization and schema audit

Each raw CSV contains 62 resistance channels, temperature, humidity, cycle-stage
information, and time/date fields. The normalizer reproduces four feature families:
the mean of the last ten stage-2 values for the 62 resistance plus environmental
channels (64 features), the stage-2 versus stage-1 relative difference (64), a
first-30-stage-2 slope for the resistance channels (62), and a stage-3/stage-1
recovery ratio for the resistance channels (62). The resulting feature vector has
252 finite numeric values. Target, filename, day/window labels, and future
observations are excluded from the feature matrix.

The 232 ethanol files are 5% v/v diluent/blank measurements and do not provide a
varying concentration target. They are excluded from concentration regression,
leaving 468 records: 117 diacetyl measurements at each of 0.1 and 1 ppm and 117
2-phenylethanol measurements at each of 200 and 1000 ppm. No missing or non-finite
feature values remain. The exclusion and checksum decisions are retained in the
normalization audit and provenance logs.

### 3.3 Temporal split and reference panels

The 39 available day folders are sorted by day number and grouped into consecutive
six-day windows. The primary analysis uses source windows 1–3 and target windows
4–7; the last target window has only three available days and is reported
explicitly. For each analyte/window sequence, the target rows are stratified by
the two concentration levels. Approximately one third of each eligible stratum
is frozen as the test set before reference selection; the final short window
therefore has six test rows rather than twelve.

Reference candidates are ordered to alternate the available concentration levels,
which creates a nested concentration-spread panel. The primary absolute budgets
are 0, 2, 5, 10, 20, and 50 observations. At budget zero, all strategies reduce
to the source model. References and tests are disjoint by construction. The
three-day-window analysis and the alternative-reference-seed analysis are frozen
secondary configurations; they do not redefine the primary result.

### 3.4 Models and updating strategies

The base regressors are partial least squares (PLS, two components after feature
standardization), a 200-tree random forest, and an XGBoost regressor with 300
trees, maximum depth five, learning rate 0.05, and 0.8 row/feature subsampling.
Random seeds and package versions are recorded in each run manifest. No
hyperparameter search uses target-test predictions.

For `calibrator_update`, the source model is fit on source windows. Predictions
for the labelled references are regressed on the nominal reference values with a
linear output map; a one-parameter intercept correction is used when the panel
does not contain enough variation. `target_finetune` fits the base model only on
the reference panel and is retained as a secondary comparison. `full_retrain`
fits the same model family on source observations concatenated with the references.
An oracle fit uses all available target reference-pool labels only to define the
denominator; oracle predictions are never used for strategy selection.

### 3.5 Endpoints and denominator diagnostics

For each held-out window we compute nRMSE, MAE, calibration slope, and the
recovered-loss ratio. Recovery is undefined when the frozen-to-oracle denominator
is non-positive or non-finite. The primary analysis reports absolute nRMSE and
ΔnRMSE before any ratio. The denominator minimum, median, and maximum are retained
for every analyte/model group. A denominator below 0.05 nRMSE units is flagged as
a descriptive warning; it is not an exclusion rule.

The archive supplies nominal concentration labels and sensor responses but not a
complete traceable uncertainty budget. Accordingly, the paper does not convert
IQRs, MAE, or nRMSE into measurement uncertainty, confidence intervals, or
metrological accuracy. This boundary follows the uncertainty-aware sensor and
measurement literature [29–33] and the VIM/GUM terminology [27, 28].

### 3.6 Reproducibility and reporting unit

The frozen primary configuration produces 576 rows: two analytes, four target
windows, three models, four strategies, and six budgets. The summary unit is the
target temporal window; all target rows remain prediction units. A same-configuration
rerun produced the same gate decisions, with a maximum absolute metric difference
of 3.6948×10−13 attributable to floating-point and multithreaded tree-fitting
order. Input checksums, configuration files, sampled row identifiers, and figure
trace hashes are retained in the project repository.

## 4. Results

### 4.1 Audit and reproducibility

The normalized confirmation panel contains 468 concentration-bearing records and
252 finite numeric features. The audit identifies seven temporal windows (three
source and four target), no missing or non-finite feature vectors, and no skipped
confirmation sequences. The final target window contains three days and is kept in
the primary analysis with its smaller held-out test set. Figure 1 shows the
source-to-target split, holdout freeze, reference-panel construction, and strategy
comparison.

The independent rerun reproduced all threshold flags. The maximum absolute
numeric difference was approximately 3.7×10−13; the small difference is consistent
with floating-point order in multithreaded tree fitting and does not alter any
decision gate. This supports computational reproducibility of the frozen analysis,
not external validity or causal identification.

### 4.2 Budget–performance curves

Figure 2 reports median held-out nRMSE and interquartile ranges across the four
target windows for every analyte/model group. The frozen curves are horizontal by
construction. Updating curves are not monotone in the number of references for
all groups: some improve rapidly between two and ten references, whereas others
remain close to or above the frozen error until higher budgets. We therefore retain
the complete budget table rather than reporting only the primary five-reference
point.

At five references (Table 1), lightweight updating lowers median nRMSE for Diacetyl/PLS
from 0.307 to 0.248, Diacetyl/random forest from 0.132 to 0.070, and
Diacetyl/XGBoost from 0.255 to 0.135. It also lowers Phenylethanol/PLS from 0.742
to 0.634. In contrast, Phenylethanol/random forest increases from 0.490 to 0.683,
and Phenylethanol/XGBoost increases from 0.503 to 0.576. The corresponding median
ΔnRMSE values are −0.063, −0.045, −0.006, −0.160, +0.193, and +0.072,
respectively. These are descriptive medians across four windows, not independent
replicate estimates.

Full retraining is more favorable in several groups at the same budget: its
median nRMSE is 0.232, 0.060, and 0.090 for the three Diacetyl models and 0.608
for Phenylethanol/PLS. It remains close to frozen for Phenylethanol/random forest
(0.495) and Phenylethanol/XGBoost (0.539). The full curves do not establish a
universal ranking because model classes, analytes, and windows are not pooled as
independent samples.

### 4.3 Primary five-reference decision boundary

Figure 3 displays the target-window-specific direction of lightweight updating
at the five-reference budget, with recovery regimes and small-denominator
warnings encoded separately.

The 24 lightweight analyte/model/window combinations yield 10 drift-positive
sequences under the ≥20% frozen-error increase gate. Seven of these reach recovery
≥0.50 toward the oracle, while two remain below 0.20. The remaining drift-positive
sequence lies between the descriptive gates. The result is a heterogeneous
boundary rather than a single threshold: the same five-reference budget can be
useful, inconclusive, or harmful depending on the analyte, model, and target
window.

The decision matrix shows the direction in absolute terms. Diacetyl/PLS improves
by 0.160 and 0.210 nRMSE units in target windows 4 and 5 but worsens by 0.096 in
window 6. Diacetyl/XGBoost improves by 0.332 in window 4 yet worsens by 0.474 in
window 5. Phenylethanol/PLS improves by 0.320 in window 4 and 0.159 in window 7
but worsens by 0.236 in window 6. Phenylethanol/random forest worsens by 0.366
and 0.492 in windows 6 and 7, and Phenylethanol/XGBoost worsens by 0.136 and
0.570 in those windows. These absolute changes are the primary evidence; the
recovery ratio is a bounded secondary summary.

Full retraining yields nine drift/recovery joint hits at five references. It
improves all three Diacetyl groups in several windows and produces median recovery
above 0.50 for Diacetyl/PLS, Diacetyl/random forest, Diacetyl/XGBoost, and
Phenylethanol/PLS. It does not uniformly recover the Phenylethanol random-forest
or XGBoost sequences. Thus, the higher-capacity update is more consistently
beneficial in the evaluated positive-shift regimes, but it is not a universal
solution.

### 4.4 Denominators and secondary endpoints

The 24 primary lightweight denominators (Table 2) range from 0.00181 to 0.544 nRMSE units;
the smallest value occurs for Phenylethanol/XGBoost in target window 7. Five rows
are below the descriptive 0.05 warning. The corresponding recovered-loss values
include −315.025, −29.032, and −1.700, but their absolute ΔnRMSE values are +0.570,
+0.492, and +0.096. These examples show why an extreme ratio is not interpreted
as a standalone effect.

MAE and calibration slope generally follow the direction of nRMSE within the
Diacetyl groups, while Phenylethanol retains larger absolute concentration errors.
Because the two analytes have different concentration units and ranges, their
MAE values are not pooled. Calibration slopes are reported as secondary model
diagnostics and are not treated as evidence of traceability or trueness.

### 4.5 Sensitivity analyses

Figure 4 summarizes the joint temporal-increase and recovery counts across the
primary and two sensitivity configurations.

The three-day-window sensitivity (Table 3) contains 42 lightweight rows, 21 drift-positive
rows, 12 drift-conditioned recoveries ≥0.50, and six below 0.20; the heterogeneous
boundary remains present. The alternative reference seed contains 24 lightweight
rows, 11 drift-positive rows, nine recoveries ≥0.50, and one below 0.20. Full-
retraining joint hits vary from 19 in the three-day analysis to six under the
alternative seed, compared with nine in the primary configuration.

The sensitivity results support the qualitative existence of both useful and
inadequate lightweight regimes, but they do not stabilize every model-specific
median. Common-support and observed-range analyses are structurally identical
because each eligible sequence contains the same two concentration levels.
Missingness sensitivity is not applicable: the normalized panel has no missing or
non-finite features.

## 5. Discussion

### 5.1 Principal interpretation

The principal result is conditional, not a universal budget recommendation. Five
labelled references are sufficient to produce meaningful held-out improvement in
some target-window/model regimes, yet the same budget increases error in others.
The sign changes are visible in absolute ΔnRMSE before any ratio is considered.
Reference count is therefore necessary context but not a sufficient recalibration
rule.

This conclusion is consistent with two strands of prior evidence. Calibration-
update reviews emphasize that a reduced reference subset can be useful but must
represent the new variation [1, 6]. Temporal-validation work shows that a
deployment-period estimate depends on respecting the structure of the data
[12–15]. Our contribution is to join these ideas in a reproducible decision
curve: the same labelled reference panel is supplied to competing updating
strategies, and every later-period window remains visible.

### 5.2 Implications for measurement-system performance evaluation

For a measurement team, the protocol suggests five reporting requirements. First,
report the absolute number of labelled references, not only a percentage. Second,
freeze a later-period test set before choosing references or update settings.
Third, stratify results by analyte, model class, and deployment window. Fourth,
lead with absolute predictive error and ΔnRMSE, then show any normalized recovery
measure with its denominator. Fifth, disclose the reference-panel design and a
panel-seed sensitivity analysis.

These requirements are measurement-science requirements even when the underlying
regressors are standard. The object being evaluated is the measurement system in
operation: sensor responses, nominal reference values, model update, and held-out
performance. The procedure provides evidence for a deployment decision without
claiming a new learning algorithm or a traceable uncertainty evaluation.

### 5.3 Relation to prior literature

Prior gas-array studies often optimize a correction or adaptation algorithm and
report classification performance [8–11, 16–24]. Our study instead keeps
the model families deliberately conventional and varies the updating decision.
This makes the comparison complementary rather than competitive. The Wörner
dataset paper provides the long-term archive [26]; Dennler et al. show why
temporal batch structure must be respected [4]; and deployment-calibration
reviews show that field conditions matter [3, 34, 35]. None of these sources alone
defines the present absolute-budget, four-strategy, denominator-diagnostic
protocol. The gap statement is search-bounded and does not claim priority.

### 5.4 Why full retraining is not a universal answer

Full retraining is a useful escalation option because it can incorporate target
features and labels more flexibly than an output calibrator. In this panel it
produces nine joint drift/recovery hits at five references and strong median
improvements for the Diacetyl groups. It is not uniformly protective: the
Phenylethanol random-forest and XGBoost groups remain close to frozen or worsen in
some windows. Full retraining also consumes the same labelled references and adds
model-fitting complexity. The archive contains no laboratory-time or monetary
metadata, so the paper does not translate reference counts into currency or claim
an economic optimum.

### 5.5 A cautious operational rule

The evidence supports a staged rule for this measurement context. Collect a small
nested reference panel that spans the available target concentrations, evaluate a
lightweight update on a frozen later-period holdout, and inspect absolute ΔnRMSE,
MAE, slope, and denominator stability. Escalate to full retraining only when the
held-out evidence supports it for the relevant analyte/model/window regime. If
the panel produces a large ratio but a small denominator, treat the ratio as
diagnostic rather than decisive. This is a reporting and selection heuristic, not
a newly optimized recalibration algorithm.

## 6. Limitations

The confirmation evidence belongs to one open-data family and two analytes. The
four target windows are few, and the final window has only three days. Model
classes and windows are therefore not pooled into inferential replicates, and no
population-level confidence statement is made. The source archive contains two
concentration levels per analyte, so the concentration-spread panel is necessarily
small. The alternative reference seed changes several regime medians, showing
that panel design remains consequential.

The temporal change cannot be causally separated into physical sensor drift,
environment, maintenance, concentration-distribution shift, and other operating
effects. The nominal concentrations are supplied labels rather than documented
traceable certified reference values, and the archive does not provide a complete
uncertainty budget. Consequently, predictive error is not called measurement
accuracy, and IQRs are not called uncertainty intervals. The study also omits
monetary sampling costs, replacement-sensor experiments, prospective deployment,
and external validation on a second long-term concentration-regression corpus.

The base-model hyperparameters are fixed and limited to PLS, random forest, and
XGBoost. Other transfer methods, probabilistic models, and sensor-level drift
models may behave differently. Finally, the exploratory UCI Kill Test motivated
the revised question but is not pooled with the confirmation results. This role
separation protects the interpretation from treating a post-failure pivot as if
it had been pre-registered from the beginning.

## 7. Conclusions

We evaluated how absolute labelled-reference budgets affect recalibration of a
gas-sensor array under a leakage-controlled temporal shift. In a checksum-verified
one-year archive, lightweight output calibration improved held-out concentration
error in some analyte/model/window regimes and worsened it in others. At five
references, seven drift-positive sequences reached at least 50% descriptive
recovery toward an oracle, while two remained below 20%; full retraining produced
nine joint hits but was not uniformly beneficial. The qualitative boundary
survived temporal-window and reference-seed sensitivities, although detailed
medians changed.

The practical conclusion is not that five references are enough, nor that full
retraining solves temporal change. A measurement-system evaluation should report
the absolute reference budget, freeze a later-period holdout, stratify by the
relevant analyte/model/window, and show absolute error before ratio-based recovery.
The protocol and derived artifacts provide a reproducible starting point for
prospective studies with traceable reference values, explicit uncertainty budgets,
and independent long-term sensor arrays.

## Declarations

### Data availability

The raw confirmation archive is available from Zenodo under DOI
10.5281/zenodo.15681119 and is cited as Wörner et al. [26]. An anonymized
reproducibility package containing the analysis scripts, configuration files,
normalized-schema audit, result tables, and figure-generation scripts is supplied
as supplementary material. At submission, the DOI-bearing archival record for
these materials will be reported to the editor through non-review metadata.
Because its creator metadata identifies the author, that identifier is withheld
from this reviewer-visible version and will be restored in the article after
double-anonymized review.

### Code availability

The code, configuration files, normalization audit, complete benchmark tables,
run manifests, and figure-generation scripts are supplied as anonymized
supplementary material. A DOI-bearing Zenodo record will be created immediately
before submission and disclosed to the editor in the title page, cover letter,
and submission system, which are not sent to reviewers. The persistent
identifier is intentionally omitted here to avoid indirect author identification
and will be inserted after the double-anonymized review stage.

### Ethics statement

This study reanalyses a public archive of non-human sensor measurements and does
not involve human participants, animals, or identifiable personal data. No
institutional ethics approval was required for the analyses reported here.

### Funding

Funding information is provided in the separate title-page file to preserve
double-anonymized review.

### Declaration of competing interests

The competing-interest declaration is provided as a separate submission file.

### Author contributions (CRediT)

The CRediT author statement is provided in the separate title-page file to
preserve double-anonymized review.

### Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

During the preparation of this work, the authors used OpenAI Codex to support
bibliographic organization, code and documentation review, drafting and editing,
and LaTeX formatting. After using this tool, the authors reviewed and edited the
content as needed and take full responsibility for the content of the published
article.

## References 

[1] A. Rudnitskaya, Calibration update and drift correction for electronic
noses and tongues, Front. Chem. 6 (2018) 433.
https://doi.org/10.3389/fchem.2018.00433.

[2] H. Chai, Z. Zheng, K. Liu, J. Xu, K. Wu, Y. Luo, H. Liao, M. Debliquy,
C. Zhang, Stability of metal oxide semiconductor gas sensors: A review, IEEE
Sens. J. 22 (2022) 5470–5481. https://doi.org/10.1109/JSEN.2022.3148264.

[3] R. Piedrahita, Y. Xiang, N. Masson, J. Ortega, A. Collier, Y. Jiang, K. Li,
R.P. Dick, Q. Lv, M. Hannigan, L. Shang, The next generation of low-cost
personal air quality sensors for quantitative exposure monitoring, Atmos. Meas.
Tech. 7 (2014) 3325–3336. https://doi.org/10.5194/amt-7-3325-2014.

[4] N. Dennler, S. Rastogi, J. Fonollosa, A. van Schaik, M. Schmuker, Drift in
a popular metal oxide sensor dataset reveals limitations for gas classification
benchmarks, Sens. Actuators B Chem. 361 (2022) 131668.
https://doi.org/10.1016/j.snb.2022.131668.

[5] Y. Oh, J. Lee, S. Kim, Sensor drift compensation for gas mixture
classification in batch experiments, Qual. Reliab. Eng. Int. 39 (2023)
2422–2437. https://doi.org/10.1002/qre.3354.

[6] T. Fearn, Standardisation and calibration transfer for near infrared
instruments: A review, J. Near Infrared Spectrosc. 9 (2001) 229–244.
https://doi.org/10.1255/jnirs.309.

[7] S.D. Brown, Transfer of multivariate calibration models, in:
Comprehensive Chemometrics, Elsevier, 2009, pp. 345–378.
https://doi.org/10.1016/B978-044452701-1.00077-6.

[8] A. Vergara, S. Vembu, T. Ayhan, M.A. Ryan, M.L. Homer, R. Huerta,
Chemical gas sensor drift compensation using classifier ensembles, Sens.
Actuators B Chem. 166–167 (2012) 320–329.
https://doi.org/10.1016/j.snb.2012.01.074.

[9] H. Liu, Z. Tang, Metal oxide gas sensor drift compensation using a dynamic
classifier ensemble based on fitting, Sensors 13 (2013) 9160–9173.
https://doi.org/10.3390/s130709160.

[10] S. Lu, J. Guo, S. Liu, B. Yang, M. Liu, L. Yin, W. Zheng, An improved
algorithm of drift compensation for olfactory sensors, Appl. Sci. 12 (2022)
9529. https://doi.org/10.3390/app12199529.

[11] Y. Yao, B. Chen, C. Liu, C. Qu, Investigation on the combined model of
sensor drift compensation and open-set gas recognition based on electronic nose
datasets, Chemom. Intell. Lab. Syst. 242 (2023) 105003.
https://doi.org/10.1016/j.chemolab.2023.105003.

[12] C. Bergmeir, R.J. Hyndman, B. Koo, A note on the validity of
cross-validation for evaluating autoregressive time series prediction, Comput.
Stat. Data Anal. 120 (2018) 70–83.
https://doi.org/10.1016/j.csda.2017.11.003.

[13] V. Cerqueira, L. Torgo, I. Mozetič, Evaluating time series forecasting
models: An empirical study on performance estimation methods, Mach. Learn. 109
(2020) 1997–2028. https://doi.org/10.1007/s10994-020-05910-7.

[14] D.R. Roberts, V. Bahn, S. Ciuti, et al., Cross-validation strategies for
data with temporal, spatial, hierarchical, or phylogenetic structure, Ecography
40 (2017) 913–929. https://doi.org/10.1111/ecog.02881.

[15] S. Kaufman, S. Rosset, C. Perlich, O. Stitelman, Leakage in data mining,
ACM Trans. Knowl. Discov. Data 6 (2012) 1–21.
https://doi.org/10.1145/2382577.2382579.

[16] M. Padilla, A. Perera, I. Montoliu, A. Chaudry, K. Persaud, S. Marco,
Drift compensation of gas sensor array data by orthogonal signal correction,
Chemom. Intell. Lab. Syst. 100 (2010) 28–35.
https://doi.org/10.1016/j.chemolab.2009.10.002.

[17] K. Yan, D. Zhang, Calibration transfer and drift compensation of e-noses
via coupled task learning, Sens. Actuators B Chem. 225 (2016) 288–297.
https://doi.org/10.1016/j.snb.2015.11.058.

[18] A. Ziyatdinov, S. Marco, A. Chaudry, K. Persaud, P. Caminal, A. Perera,
Drift compensation of gas sensor array data by common principal component
analysis, Sens. Actuators B Chem. 146 (2010) 460–465.
https://doi.org/10.1016/j.snb.2009.11.034.

[19] H. Liu, R. Chu, Z. Tang, Metal oxide gas sensor drift compensation using a
two-dimensional classifier ensemble, Sensors 15 (2015) 10180–10193.
https://doi.org/10.3390/s150510180.

[20] P. Maho, C. Herrier, T. Livache, P. Comon, S. Barthelmé, A calibrant-free
drift compensation method for gas sensor arrays, Chemom. Intell. Lab. Syst. 225
(2022) 104549. https://doi.org/10.1016/j.chemolab.2022.104549.

[21] Z. Jiang, P. Xu, Y. Du, F. Yuan, K. Song, Balanced distribution adaptation
for metal oxide semiconductor gas sensor array drift compensation, Sensors 21
(2021) 3403. https://doi.org/10.3390/s21103403.

[22] X. Dong, S. Han, A. Wang, K. Shang, Online inertial machine learning for
sensor array long-term drift compensation, Chemosensors 9 (2021) 353.
https://doi.org/10.3390/chemosensors9120353.

[23] J. Lin, X. Zhan, Sensor-drift compensation in electronic-nose-based gas
recognition using knowledge distillation, Informatics 13 (2026) 15.
https://doi.org/10.3390/informatics13010015.

[24] B. Zong, S. Wu, Y. Yang, Q. Li, T. Tao, S. Mao, Smart gas sensors: Recent
developments and future prospective, Nano-Micro Lett. 17 (2025).
https://doi.org/10.1007/s40820-024-01543-w.

[25] Y. Sun, Y. Zheng, A method of gas sensor drift compensation based on
intrinsic characteristics of response curve, Sci. Rep. 13 (2023).
https://doi.org/10.1038/s41598-023-39246-8.

[26] J. Wörner, J. Eimler, M. Pein-Hackelbusch, Long-term drift behavior in
metal oxide gas sensor arrays: A one-year dataset from an electronic nose, Sci.
Data 12 (2025). https://doi.org/10.1038/s41597-025-05993-8.

[27] JCGM 100:2008, Evaluation of measurement data—Guide to the expression of
uncertainty in measurement (GUM), BIPM, 2008.
https://www.bipm.org/en/committees/jc/jcgm/publications/ (accessed 16 August
2026).

[28] JCGM 200:2012, International vocabulary of metrology—Basic and general
concepts and associated terms (VIM), third ed., BIPM, 2012.
https://www.bipm.org/en/committees/jc/jcgm/publications/ (accessed 16 August
2026).


[29] T. Dorst, M. Gruber, B. Seeger, A.P. Vedurmudi, T. Schneider,
S. Eichstädt, A. Schütze, Uncertainty-aware data pipeline of calibrated MEMS
sensors used for machine learning, Measurement: Sensors 22 (2022) 100376.
https://doi.org/10.1016/j.measen.2022.100376.

[30] T. Dorst, T. Schneider, S. Eichstädt, A. Schütze, Influence of measurement
uncertainty on machine learning results demonstrated for a smart gas sensor,
J. Sens. Sens. Syst. 12 (2023) 45–60.
https://doi.org/10.5194/jsss-12-45-2023.

[31] P. Harris, P.F. Østergaard, S. Tabandeh, et al., Measurement uncertainty
evaluation for sensor network metrology, Metrology 5 (2025) 3.
https://doi.org/10.3390/metrology5010003.

[32] A. Thompson, Analytical results for combined data and model uncertainty
for machine learning regression, Measurement: Sensors 38 (2025) 101788.
https://doi.org/10.1016/j.measen.2024.101788.

[33] S. Salicone, New frontiers in measurement uncertainty, Metrology 2 (2022)
495–498. https://doi.org/10.3390/metrology2040029.

[34] A. Schütze, T. Baur, M. Leidinger, W. Reimringer, R. Jung, T. Conrad,
T. Sauerwald, Highly sensitive and selective VOC sensor systems based on
semiconductor gas sensors: How to?, Environments 4 (2017) 20.
https://doi.org/10.3390/environments4010020.

[35] L. Spinelle, M. Gerboles, G. Kok, S. Persijn, T. Sauerwald, Review of
portable and low-cost sensors for the ambient air monitoring of benzene and other
volatile organic compounds, Sensors 17 (2017) 1520.
https://doi.org/10.3390/s17071520.
