# Panel-draw sensitivity: what survives and what does not

> **Updated 2026-08-26 to ten draws.** The tables below were written at five
> draws; every conclusion held when extended to ten. Per-draw boundaries are now
> 4, 6, 4, 20, 20, 4, 4, 5, 8, 4 — range 4–20, **mode 4**, so the pre-specified
> draw was typical rather than unlucky. Inversion still appears in exactly one
> draw, now 1 of 10. Pooled counts per budget doubled to 900 cells; >2× counts
> are 48, 25, 10, 8, 5, 3, 3, 0, 0 and >3× are 7, 4, 2, 2, 2, 2, 0, 0, 0.
> H1 held-out rho across ten draws: 0.581–0.852, all p < 0.001. Top d_ref
> quartile at N=2 in the nine non-inverting draws: 0.541–0.991, all below 1.
> Canonical current numbers: `results/seed_sensitivity/pooled_summary.md` and
> Tables 5–6 of `manuscript/uci360_tables.md`.

- Date: 2026-08-26
- Scripts: `scripts/run_seed_sensitivity.py`, `scripts/summarize_seed_sensitivity.py`
- Runs: `results/seed_sensitivity/seed_{11,22,33,44}/`, pooled in
  `results/seed_sensitivity/pooled_cells.csv`
- Primary draw: seed 20260826 (the frozen protocol's seed)
- Status: **post-hoc robustness analysis.** Changes no hypothesis, threshold, or
  verdict of `docs/uci360_primary_protocol.md`. It tests whether a *descriptive*
  finding survives a nuisance parameter, and it does not.

Five independent reference-panel draws, 90 decision cells per budget each, 450
pooled per budget. The seed governs both the panel draw and the model random
states, so each draw is a different plausible deployment.

## Why this had to be run

The floor of N = 4 reported in `UCI360_PRIMARY_FINDINGS.md` rested on **one**
panel draw. A two-sample panel is exactly determined, so whether its pathological
case materialises depends on which two rows are drawn. One draw can therefore
neither establish nor refute a floor. This is the first objection a referee would
raise and it is answerable with compute.

## Result 1 — the N = 4 floor does not replicate

Cells above 2× frozen error, per draw:

| seed | N=2 | N=3 | N=4 | N=5 | N=6 | N=8 | N=10 | N=20 | N=50 | floor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **20260826** (primary) | **8** | **4** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **4** |
| 11 | 2 | 2 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 6 |
| 22 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| 33 | 6 | 3 | 3 | 2 | 1 | 1 | 1 | 0 | 0 | **20** |
| 44 | 7 | 5 | 4 | 4 | 3 | 2 | 2 | 0 | 0 | **20** |

Per-draw floors are **4, 6, 4, 20, 20**. The claim "no sequence exceeds twice its
frozen error from four references onward" is a property of the primary draw, not
of the method. **Retracted.**

Pooled over all 450 cells per budget, the 2× criterion is not met by every draw
until **N = 20**.

## Result 2 — the sharp N=2 → N=3 break does not replicate either

Worst nRMSE ratio per draw:

| seed | N=2 | N=3 | drop |
|---|---:|---:|---:|
| **20260826** | **44.53** | 2.16 | **20.6×** |
| 11 | 2.49 | 2.38 | 1.04× |
| 22 | 2.25 | 2.27 | 0.99× |
| 33 | 3.34 | 3.42 | 0.98× |
| 44 | 4.62 | 4.68 | 0.99× |

In four of five draws N = 3 is no better than N = 2 in the worst case. The
"structural break between two and three references" was an artefact of the primary
draw. **Retracted as a general claim**; it remains true that the *mechanism*
available at N = 2 is unavailable at N = 3 (see Result 4).

## Result 3 — catastrophic failure is confined to N = 2, and is rare

Pooled over 450 cells per budget:

| N | worst nRMSE ratio | worst MAE ratio | inverted | >5× | >3× | >2× |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1.000 | 1.000 | 0 | 0 | 0 | 0 |
| **2** | **44.53** | **50.99** | **3** | **3** | 6 | 24 |
| 3 | 4.68 | 4.41 | 0 | 0 | 3 | 15 |
| 4 | 4.54 | 4.27 | 0 | 0 | 2 | 8 |
| 5 | 4.60 | 4.27 | 0 | 0 | 2 | 7 |
| 6 | 3.53 | 3.52 | 0 | 0 | 2 | 4 |
| 8 | 3.13 | 2.99 | 0 | 0 | 2 | 3 |
| 10 | 2.63 | 2.36 | 0 | 0 | 0 | 3 |
| 20 | 1.64 | 1.68 | 0 | 0 | 0 | 0 |
| 50 | 1.19 | 1.19 | 0 | 0 | 0 | 0 |

Slope inversion occurs at **N = 2 and at no other budget, in any draw**. The same
is true of inflation beyond 5×. Both occur in **one of five draws**, which is what
makes this a tail risk rather than an expected cost: the primary draw happened to
hit it, four draws did not.

## Result 4 — the mechanism claim stands, and is the durable contribution

At N = 2 the correction is exactly determined, so
$b = (y_2 - y_1)/(\hat y_2 - \hat y_1)$, the fit interpolates both references, the
panel residual is identically zero, and residual d.f. = 0. Nothing computed from
the panel can reveal that $b$ is wrong. From N = 3 a residual degree of freedom
exists.

This is a property of the estimator, not of a draw, and it correctly predicts
where the unbounded failures are possible: only at N = 2, in every draw. Result 3
is the empirical confirmation. What the mechanism does **not** predict — and
Result 2 shows does not happen — is that N = 3 is therefore safe.

## Result 5 — two descriptive claims survive all five draws

**Median-neutral at N = 2.** Median ratio by draw: 1.009, 1.022, 1.028, 0.979,
1.055 (range 0.979–1.055). The typical sequence is unaffected at two references in
every draw. **Stands.**

**Median improvement from N = 4.** Median ratio below 1 in all five draws at
N = 4 (range 0.899–0.957), N = 5 (0.857–0.937) and N = 6 (0.832–0.884). At N = 3
it is not: range 0.934–1.025. **Stands, with N = 4 as the crossing point.**

The mean/median divergence at N = 2 is itself draw-dependent. Primary draw: mean
2.005 against median 1.009. Other draws: means 1.009–1.119. The divergence exists
only when the tail is realised, which is the correct behaviour for a
tail-driven mean and is worth stating as such rather than as a fixed effect size.

## Consequences for the manuscript

1. **The title and headline change.** There is no floor at four. The defensible
   claims are (a) the exactly-determined panel is uniquely capable of unbounded
   failure and uniquely unable to detect it, and (b) no small panel is reliably
   safe — moderate failures persist to N = 10 and the 2× criterion is met by every
   draw only at N = 20.
2. **The recommendation changes** from "refuse below four" to "never use an
   exactly-determined panel; expect residual risk up to roughly twenty; inspect
   the panel geometry, because the count alone does not protect you."
3. **The negative result is now part of the contribution.** A single-draw
   evaluation of this exact question would have reported a clean floor at four.
   That is a methodological warning for the sample-size literature, and it is
   worth reporting explicitly.
4. **Five draws is few.** The per-draw floors range over 4–20 on five draws, so
   even the pooled statement is imprecise. More draws would sharpen it; the
   qualitative conclusions (inversion only at N=2, no safe small panel) are
   unlikely to move.
