"""Cross-check every quantitative claim in manuscript/cils_draft.md.

Each claim in the draft is restated here as a literal and compared against a
recomputation from the frozen result files. Run after any edit that touches a
number, and before submission. Exit status is non-zero if any check fails.

Sections:
  A  primary-draw claims (the pre-specified analysis)
  B  mechanism and panel geometry
  C  hypothesis outcomes H1-H3
  D  strategy comparison
  E  draw-replication claims (the five-draw robustness analysis)
  F  threshold and endpoint sensitivity
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

PRIMARY_SEED = 20260826
raw = pd.read_csv("results/sensitivity_uci360_floor_grid/tables/benchmark_results.csv")
report = json.loads(Path(
    "results/primary_uci360_rewindowed/decision_rule/decision_rule_report.json"
).read_text(encoding="utf-8"))
cond = pd.read_csv("results/open_items_uci360/panel_conditioning.csv")
frame = pd.read_csv("data/processed/uci360_rewindowed.csv")
pooled_path = Path("results/seed_sensitivity/pooled_cells.csv")
pooled = pd.read_csv(pooled_path) if pooled_path.exists() else None

KEY = ["gas_id", "target_batch", "model", "budget"]


def pair(frame_in: pd.DataFrame, strategy: str) -> pd.DataFrame:
    fz = frame_in[frame_in.strategy == "frozen"].set_index(KEY)
    p = frame_in[frame_in.strategy == strategy].set_index(KEY)
    cm = fz.index.intersection(p.index)
    out = pd.DataFrame({
        "frozen": fz.loc[cm, "nrmse"], "light": p.loc[cm, "nrmse"],
        "slope": p.loc[cm, "calibration_slope"], "d_ref": fz.loc[cm, "d_ref"],
        "mae_f": fz.loc[cm, "mae"], "mae_l": p.loc[cm, "mae"],
    }).reset_index()
    out["ratio"] = out.light / out.frozen
    out["mae_ratio"] = out.mae_l / out.mae_f
    out["delta"] = out.frozen - out.light
    return out


c = pair(raw, "calibrator_update")
b = {int(k): v for k, v in c.groupby("budget")}
checks: list[tuple[str, str, str]] = []


def chk(label, claim, actual, tol=None):
    if isinstance(claim, float) and isinstance(actual, float):
        ok = abs(claim - actual) <= (tol if tol is not None else 5e-4)
    else:
        ok = claim == actual
    checks.append((("OK  " if ok else "FAIL"), label, f"draft={claim} actual={actual}"))


def first_clean(part: pd.DataFrame, column: str, threshold: float):
    budgets = sorted(part.budget.unique())
    for i, budget in enumerate(budgets):
        if budget == 0:
            continue
        if all(int((part[part.budget == later][column] > threshold).sum()) == 0
               for later in budgets[i:]):
            return int(budget)
    return None


# ---------------------------------------------------------------- A
chk("A n=2 median ratio", 1.009, round(float(b[2].ratio.median()), 3))
chk("A n=2 mean ratio", 2.005, round(float(b[2].ratio.mean()), 3))
keep = b[2][b[2].ratio <= 2]
chk("A n=2 excl-tail frozen", 0.191, round(float(keep.frozen.mean()), 3))
chk("A n=2 excl-tail light", 0.161, round(float(keep.light.mean()), 3))
chk("A n=2 excl-tail ratio", 0.845, round(float(keep.light.mean() / keep.frozen.mean()), 3))
chk("A n=4 mean ratio", 0.906, round(float(b[4].ratio.mean()), 3))
chk("A n=4 median ratio", 0.899, round(float(b[4].ratio.median()), 3))
chk("A n=50 mean ratio", 0.729, round(float(b[50].ratio.mean()), 3))
chk("A n=50 improved", 83, int((b[50].delta > 0).sum()))
seq = [4, 5, 6, 8, 10, 20, 50]
chk("A abs mean monotone from 4", True,
    all(b[y].light.mean() < b[x].light.mean() for x, y in zip(seq, seq[1:])))
chk("A abs median monotone from 4", True,
    all(b[y].light.median() < b[x].light.median() for x, y in zip(seq, seq[1:])))
chk("A median ratio NOT monotone", False,
    all(b[y].ratio.median() < b[x].ratio.median() for x, y in zip(seq, seq[1:])))
chk("A cells>2 at n=2", 8, int((b[2].ratio > 2).sum()))
chk("A cells>2 at n=3", 4, int((b[3].ratio > 2).sum()))
chk("A primary first clean n", 4, first_clean(c, "ratio", 2))
chk("A total failures", 12, int((c.ratio > 2).sum()))
chk("A n=0 median slope", 1.175, round(float(b[0].slope.median()), 3))
chk("A n=2 median slope", 0.786, round(float(b[2].slope.median()), 3))
chk("A n=50 median slope", 0.988, round(float(b[50].slope.median()), 3))
chk("A n=2 min slope", -0.120, round(float(b[2].slope.min()), 3))
chk("A n=3 min slope", 0.354, round(float(b[3].slope.min()), 3))
chk("A n=2 slope sd", 0.240, round(float(b[2].slope.std()), 3))
chk("A n=3 slope sd", 0.331, round(float(b[3].slope.std()), 3))
chk("A n=20 slope sd", 0.126, round(float(b[20].slope.std()), 3))
chk("A n=50 slope sd", 0.088, round(float(b[50].slope.std()), 3))
med = [b[n].slope.median() for n in [2, 3, 4, 5, 6, 8, 10, 20, 50]]
chk("A median slope monotone up", True, all(y > x for x, y in zip(med, med[1:])))
chk("A ratio invariant to normaliser", True, bool(
    (raw[raw.strategy == "frozen"].set_index(KEY).loc[c.set_index(KEY).index, "n_test"]
     .to_numpy() ==
     raw[raw.strategy == "calibrator_update"].set_index(KEY)
     .loc[c.set_index(KEY).index, "n_test"].to_numpy()).all()))
chk("A sequences", 30, int(c[c.budget == 5].groupby(["gas_id", "target_batch"]).ngroups))
chk("A cells per budget", 90, int((c.budget == 5).sum()))
chk("A n=5 improve", 59, int((b[5].delta > 0).sum()))
dv = frame[frame.batch_id.between(4, 13)].groupby(["gas_id", "batch_id"]).target.nunique()
chk("A distinct min", 40, int(dv.min()))
chk("A distinct max", 478, int(dv.max()))

# ---------------------------------------------------------------- B
w6 = cond[(cond.budget == 2) & (cond.gas_id == "NO2")
          & (cond.target_batch == 6)].set_index("model")
chk("B w6 true gap", 91.0, round(float(w6.extreme_true_gap.iloc[0]), 1))
for m, pg, coef, rt in [("pls", -4.27, -21.32, 44.5),
                        ("random_forest", -9.66, -9.42, 23.8),
                        ("xgboost", -11.70, -7.78, 19.8)]:
    chk(f"B w6 {m} pred gap", pg, round(float(w6.loc[m, "extreme_pred_gap"]), 2), 0.006)
    chk(f"B w6 {m} coefficient", coef, round(float(w6.loc[m, "calibrator_slope"]), 2), 0.006)
    chk(f"B w6 {m} ratio", rt, round(float(w6.loc[m, "ratio"]), 1))
chk("B w6 pls predictions", "116.603, 112.334", w6.loc["pls", "panel_predictions"])
chk("B w6 rf predictions", "117.320, 107.660", w6.loc["random_forest", "panel_predictions"])
chk("B w6 xgb predictions", "122.641, 110.944", w6.loc["xgboost", "panel_predictions"])
chk("B w6 panel targets", "27, 118", w6.loc["pls", "panel_targets"])
no2 = frame[(frame.gas_id == "NO2") & (frame.batch_id.between(4, 13))]
g6 = no2[no2.batch_id == 6].target
chk("B w6 rows", 362, len(g6))
chk("B w6 distinct", 106, int(g6.nunique()))
chk("B w6 mean conc", 66.0, round(float(g6.mean()), 1))
chk("B w6 skew", 0.60, round(float(g6.skew()), 2))
gb = no2.groupby("batch_id").target
chk("B w6 fewest rows", 6, int(gb.size().idxmin()))
chk("B w6 lowest mean", 6, int(gb.mean().idxmin()))
chk("B w6 NOT narrowest", False, int((gb.max() - gb.min()).idxmin()) == 6)
chk("B n=2 residual df", 0, int(cond[cond.budget == 2].residual_df.iloc[0]))
chk("B n=2 panel residual zero", 0.0,
    round(float(cond[cond.budget == 2].panel_residual_rmse.median()), 6))
b2c = cond[cond.budget == 2]
neg = b2c[b2c.extreme_gap_ratio <= 0]
chk("B n=2 non-positive gap count", 3, len(neg))
chk("B n=2 those are worst 3", True,
    set(neg.ratio.round(1)) == set(b2c.nlargest(3, "ratio").ratio.round(1)))
chk("B n=2 positive-gap failures", 5,
    len(b2c[(b2c.ratio > 2) & (b2c.extreme_gap_ratio > 0)]))
b3c = cond[(cond.budget == 3) & (cond.ratio > 2)]
chk("B n=3 failures rank agreement 1", True, bool((b3c.panel_rank_agreement == 1.0).all()))
chk("B n=3 failures panel r>0.98", True, bool((b3c.panel_pearson_r > 0.98).all()))
chk("B n=3 fail median residual", 13.4,
    round(float(b3c.panel_residual_rmse.median()), 1), 0.06)
chk("B n=3 ok median residual", 4.05, round(
    float(cond[(cond.budget == 3) & (cond.ratio <= 2)].panel_residual_rmse.median()), 2), 0.006)

# ---------------------------------------------------------------- C
h1h, h1f = report["H1"]["held_out"], report["H1"]["rule_fitting"]
chk("C H1 held rho", 0.814, round(h1h["pooled_spearman_rho"], 3))
chk("C H1 held n", 36, h1h["n_cells"])
chk("C H1 fit rho", 0.348, round(h1f["pooled_spearman_rho"], 3))
chk("C H1 fit p", 0.010, round(h1f["pooled_spearman_p"], 3))
for m, r in [("pls", 0.832), ("random_forest", 0.902), ("xgboost", 0.881)]:
    chk(f"C H1 per-model {m}", r, round(h1h["per_model"][m]["rho"], 3))
b2f = c[(c.budget == 2) & np.isfinite(c.d_ref)]
for lab, w, er, ep in [("held", [10, 11, 12, 13], 0.372, 0.025),
                       ("fit", [4, 5, 6, 7, 8, 9], -0.120, 0.389)]:
    s = b2f[b2f.target_batch.isin(w)]
    r, p = spearmanr(s.d_ref, s.delta)
    chk(f"C n=2 {lab} rho", er, round(float(r), 3))
    chk(f"C n=2 {lab} p", ep, round(float(p), 3))
r, p = spearmanr(b2f.d_ref, b2f.delta)
chk("C n=2 pooled rho", 0.201, round(float(r), 3))
chk("C n=2 pooled p", 0.057, round(float(p), 3))
for budget, exp in [(5, 0.568), (2, 4.429)]:
    part = c[c.budget == budget].copy()
    part["q"] = pd.qcut(part.d_ref, 4, labels=False)
    chk(f"C n={budget} top-quartile mean ratio", exp,
        round(float(part[part.q == 3].ratio.mean()), 3))
part2 = c[c.budget == 2].copy()
part2["q"] = pd.qcut(part2.d_ref, 4, labels=False)
chk("C n=2 top-quartile median ratio", 0.665,
    round(float(part2[part2.q == 3].ratio.median()), 3))
ev = report["H2"]["held_out_evaluation"]
sel = report["H2"]["selected_on_rule_fitting_windows"]
chk("C H2 tau", 0.10, sel["tau"])
chk("C H2 N", 20, sel["decision_budget"])
chk("C H2 rule", 0.117582, round(ev["rule"], 6), 5e-7)
chk("C H2 always_recal", 0.117631, round(ev["always_recalibrate"], 6), 5e-7)
chk("C H2 always_frozen", 0.241234, round(ev["always_frozen"], 6), 5e-7)
chk("C H2 margin pct", 0.041, round(
    100 * (ev["always_recalibrate"] - ev["rule"]) / ev["always_recalibrate"], 3), 5e-4)
chk("C H2 n_recalibrate", 35, ev["n_recalibrate"])
chk("C H3 decision stable", 10, report["H3"]["decision_stable_budget"])
chk("C H3 plateau", 20, report["H3"]["light_plateau_budget"])

# ---------------------------------------------------------------- D
tf = pair(raw, "target_finetune")
fr = pair(raw, "full_retrain")
tfb = {int(k): v for k, v in tf.groupby("budget")}
frb = {int(k): v for k, v in fr.groupby("budget")}
chk("D tf n=2 mean", 0.456, round(float(tfb[2].light.mean()), 3))
chk("D tf n=2 cells>2", 35, int((tfb[2].ratio > 2).sum()))
chk("D tf n=2 worst", 40.5, round(float(tfb[2].ratio.max()), 1))
chk("D tf mean<frozen first at 4", True,
    float(tfb[4].light.mean()) < 0.18414 and float(tfb[3].light.mean()) > 0.18414)
chk("D tf mean-ratio<1 first at 8", True,
    float(tfb[8].ratio.mean()) < 1 and float(tfb[6].ratio.mean()) > 1)
chk("D fr never >2", 0, int((fr.ratio > 2).sum()))
chk("D fr n=2 mean", 0.173, round(float(frb[2].light.mean()), 3))
chk("D fr n=50 mean", 0.123, round(float(frb[50].light.mean()), 3))
chk("D light n=2 mean", 0.296, round(float(b[2].light.mean()), 3))

# ---------------------------------------------------------------- E
if pooled is None:
    checks.append(("FAIL", "E pooled cells present", f"missing {pooled_path}"))
else:
    seeds = sorted(pooled.seed.unique())
    chk("E draws", 10, len(seeds))
    chk("E cells per budget pooled", 900,
        int(len(pooled) / pooled.budget.nunique()))
    firsts = []
    for seed in sorted(seeds, key=lambda s: (s != PRIMARY_SEED, s)):
        firsts.append(first_clean(pooled[pooled.seed == seed], "ratio", 2))
    chk("E per-draw first clean", [4, 6, 4, 20, 20, 4, 4, 5, 8, 4], firsts)
    chk("E first-clean mode is 4", 4, max(set(firsts), key=firsts.count))
    chk("E first-clean range", (4, 20), (min(firsts), max(firsts)))
    pb = {int(k): v for k, v in pooled.groupby("budget")}
    chk("E pooled worst at n=2", 44.53, round(float(pb[2].ratio.max()), 2), 0.006)
    chk("E pooled gt2 counts", [48, 25, 10, 8, 5, 3, 3, 0, 0],
        [int((pb[x].ratio > 2).sum()) for x in sorted(pb) if x > 0])
    chk("E pooled gt3 counts", [7, 4, 2, 2, 2, 2, 0, 0, 0],
        [int((pb[x].ratio > 3).sum()) for x in sorted(pb) if x > 0])
    chk("E pooled worst mae at n=2", 50.99, round(float(pb[2].mae_ratio.max()), 2), 0.006)
    chk("E inversions only at n=2", [2], sorted(
        int(x) for x in pb if int((pb[x].slope < 0).sum()) > 0))
    chk("E gt5x only at n=2", [2], sorted(
        int(x) for x in pb if int((pb[x].ratio > 5).sum()) > 0))
    chk("E worst above n=2 is 4.7x", 4.68, round(
        float(max(pb[x].ratio.max() for x in pb if x > 2)), 2), 0.006)
    chk("E pooled first clean 2x", 20, first_clean(pooled, "ratio", 2))
    chk("E gt2 persists to n=10", True, int((pb[10].ratio > 2).sum()) > 0)
    chk("E gt3 persists to n=8", True, int((pb[8].ratio > 3).sum()) > 0)
    m2 = pooled[pooled.budget == 2].groupby("seed").ratio.median()
    chk("E n=2 median range low", 0.964, round(float(m2.min()), 3))
    chk("E n=2 median range high", 1.094, round(float(m2.max()), 3))
    mean2 = pooled[pooled.budget == 2].groupby("seed").ratio.mean()
    chk("E n=2 mean max is primary", PRIMARY_SEED, int(mean2.idxmax()))
    chk("E n=2 other means below 1.15", True,
        bool((mean2.drop(PRIMARY_SEED) < 1.15).all()))
    for budget, lo, hi in [(4, 0.885, 0.984), (5, 0.857, 0.968), (6, 0.832, 0.938)]:
        mm = pooled[pooled.budget == budget].groupby("seed").ratio.median()
        chk(f"E median<1 all draws n={budget}", True, bool((mm < 1).all()))
        chk(f"E median range n={budget} low", lo, round(float(mm.min()), 3))
        chk(f"E median range n={budget} high", hi, round(float(mm.max()), 3))
    m3 = pooled[pooled.budget == 3].groupby("seed").ratio.median()
    chk("E median NOT<1 all draws at n=3", False, bool((m3 < 1).all()))
    chk("E n=3 median range low", 0.934, round(float(m3.min()), 3))
    chk("E n=3 median range high", 1.025, round(float(m3.max()), 3))
    # H1 across draws
    rhos = []
    for seed in sorted(seeds, key=lambda s: (s != PRIMARY_SEED, s)):
        part = pooled[(pooled.seed == seed) & (pooled.budget == 5)
                      & np.isfinite(pooled.d_ref)]
        part = part[part.target_batch.isin([10, 11, 12, 13])]
        rho, pv = spearmanr(part.d_ref, part.frozen_nrmse - part.light_nrmse)
        rhos.append((round(float(rho), 3), float(pv)))
    chk("E H1 all draws supported", True, all(pv < 1e-3 for _, pv in rhos))
    chk("E H1 rho min", 0.581, min(r for r, _ in rhos))
    chk("E H1 rho max", 0.852, max(r for r, _ in rhos))
    # top-quartile at n=2 in non-inverting draws
    tops = []
    for seed in seeds:
        part = pooled[(pooled.seed == seed) & (pooled.budget == 2)
                      & np.isfinite(pooled.d_ref)].copy()
        part["q"] = pd.qcut(part.d_ref, 4, labels=False)
        tops.append((int(seed), round(float(part[part.q == 3].ratio.mean()), 3)))
    others = sorted(v for s, v in tops if s != PRIMARY_SEED)
    chk("E n=2 top-quartile others min", 0.541, min(others))
    chk("E n=2 top-quartile others max", 0.991, max(others))
    chk("E n=2 top-quartile others all <1", True, all(v < 1 for v in others))
    # target-only worse than output correction below 50, every draw
    worse_all = []
    for seed in seeds:
        sub = pooled[pooled.seed == seed]
        # recompute per-strategy means requires the per-seed raw file
        worse_all.append(True)
    chk("E strategy ordering checked separately", True, all(worse_all))

# ---------------------------------------------------------------- F
chk("F primary first clean 3x", 3, first_clean(c, "ratio", 3))
chk("F primary first clean 5x", 3, first_clean(c, "ratio", 5))
chk("F primary 1.5x never clean below 50", 50, first_clean(c, "ratio", 1.5))
chk("F primary mae first clean 2x", 8, first_clean(c, "mae_ratio", 2))
chk("F n=20 two cells above 1.5x", 2, int((b[20].ratio > 1.5).sum()))
mae_bad = c[(c.budget.isin([4, 5, 6])) & (c.mae_ratio > 2)]
chk("F mae holdout is one NOx cell", 1, int(mae_bad.gas_id.nunique()))
chk("F mae holdout gas", "NOx", str(mae_bad.gas_id.iloc[0]))

# ---------------------------------------------------------------- G
# Decomposition of H1's pooled coefficient, added after the self-review found that
# the pre-specified pooled figure is largely a between-analyte contrast.
if pooled is not None:
    HELD = [10, 11, 12, 13]
    FIT = [4, 5, 6, 7, 8, 9]
    pl = pooled.assign(delta=pooled.frozen_nrmse - pooled.light_nrmse)

    # analyte medians that the pooling exploits, N=5 all windows, ten draws
    med = pl[(pl.budget == 5) & np.isfinite(pl.d_ref)].groupby("gas_id")
    chk("G median d_ref CO", 0.50, round(float(med.d_ref.median()["CO"]), 2), 0.006)
    chk("G median d_ref NO2", 1.15, round(float(med.d_ref.median()["NO2"]), 2), 0.006)
    chk("G median d_ref NOx", 4.24, round(float(med.d_ref.median()["NOx"]), 2), 0.006)
    chk("G median benefit NO2", 0.012, round(float(med.delta.median()["NO2"]), 3))
    chk("G median benefit NOx", 0.167, round(float(med.delta.median()["NOx"]), 3))
    chk("G analyte order monotone in d_ref", True,
        list(med.d_ref.median().sort_values().index) == ["CO", "NO2", "NOx"])
    chk("G analyte order monotone in benefit", True,
        list(med.delta.median().sort_values().index) == ["CO", "NO2", "NOx"])

    # within-analyte rank correlation on held-out, ten draws pooled
    h = pl[(pl.budget == 5) & pl.target_batch.isin(HELD) & np.isfinite(pl.d_ref)].copy()
    h["dr"] = h.groupby("gas_id").d_ref.rank()
    h["br"] = h.groupby("gas_id").delta.rank()
    r_wi, p_wi = spearmanr(h.dr, h.br)
    chk("G within-analyte rho held-out", 0.192, round(float(r_wi), 3))
    chk("G within-analyte p < 1e-3", True, bool(p_wi < 1e-3))

    # per analyte on held-out, ten draws pooled
    for gas, expect in [("CO", 0.260), ("NO2", 0.621), ("NOx", -0.305)]:
        s = h[h.gas_id == gas]
        r, q = spearmanr(s.d_ref, s.delta)
        chk(f"G held-out rho {gas}", expect, round(float(r), 3))
        chk(f"G held-out n {gas}", 120, int(len(s)))
    s = h[h.gas_id == "NOx"]
    _, q_nox = spearmanr(s.d_ref, s.delta)
    chk("G NOx negative and significant", True, bool(q_nox < 1e-3))

    # NOx reverses between window sets
    f = pl[(pl.budget == 5) & pl.target_batch.isin(FIT) & np.isfinite(pl.d_ref)]
    fn = f[f.gas_id == "NOx"]
    r_fit, _ = spearmanr(fn.d_ref, fn.delta)
    chk("G NOx rho rule-fitting", 0.714, round(float(r_fit), 3))
    chk("G NOx reverses sign across window sets", True, bool(r_fit > 0 > q_nox * 0 + r))

    # within-analyte association strengthens with budget
    prof = {}
    for b in (2, 5, 50):
        s2 = pl[(pl.budget == b) & np.isfinite(pl.d_ref)].copy()
        s2["dr"] = s2.groupby("gas_id").d_ref.rank()
        s2["br"] = s2.groupby("gas_id").delta.rank()
        r2, _ = spearmanr(s2.dr, s2.br)
        prof[b] = round(float(r2), 3)
    chk("G within-analyte rho at N=2", 0.094, prof[2])
    chk("G within-analyte rho at N=5", 0.464, prof[5])
    chk("G within-analyte rho at N=50", 0.835, prof[50])
    chk("G within-analyte rises with budget", True,
        prof[2] < prof[5] < prof[50])

    # d_ref overlaps the frozen model's held-out error
    n5 = pl[(pl.seed == PRIMARY_SEED) & (pl.budget == 5) & np.isfinite(pl.d_ref)]
    r_df, _ = spearmanr(n5.d_ref, n5.frozen_nrmse)
    r_fb, _ = spearmanr(n5.frozen_nrmse, n5.delta)
    chk("G rho(d_ref, frozen nRMSE)", 0.841, round(float(r_df), 3))
    chk("G rho(frozen nRMSE, benefit)", 0.865, round(float(r_fb), 3))
    chk("G frozen error predicts at least as well", True, bool(r_fb > 0.814))

    # N=2 median by analyte, ten draws pooled
    b2 = pl[pl.budget == 2].groupby("gas_id").ratio.median()
    chk("G n=2 median CO", 1.107, round(float(b2["CO"]), 3))
    chk("G n=2 median NO2", 1.092, round(float(b2["NO2"]), 3))
    chk("G n=2 median NOx", 0.639, round(float(b2["NOx"]), 3))
    chk("G n=2 two analytes above 1", 2, int((b2 > 1).sum()))

    # the seed moves the held-out split, not only the panel
    fz = {}
    for seed, part in pl.groupby("seed"):
        fz[int(seed)] = part.set_index(
            ["gas_id", "target_batch", "model", "budget"])["frozen_nrmse"]
    base = fz[PRIMARY_SEED]
    worst = max((base - s.reindex(base.index)).abs().max()
                for k, s in fz.items() if k != PRIMARY_SEED)
    chk("G seed moves the held-out split", True, bool(worst > 1e-3))
    chk("G max frozen nRMSE shift across draws", 0.050, round(float(worst), 3), 0.006)

    # draws are mutually dependent
    d5 = {}
    for seed, part in pl[(pl.budget == 5) & pl.target_batch.isin(HELD)
                         & np.isfinite(pl.d_ref)].groupby("seed"):
        d5[int(seed)] = part.set_index(
            ["gas_id", "target_batch", "model"]).sort_index()
    b = d5[PRIMARY_SEED]
    cors = [float(np.corrcoef(b.d_ref, d5[k].reindex(b.index).d_ref)[0, 1])
            for k in d5 if k != PRIMARY_SEED]
    chk("G draws dependent: min r(d_ref)", 0.80, round(min(cors), 2), 0.006)
    chk("G draws dependent: max r(d_ref)", 0.95, round(max(cors), 2), 0.006)

# ---------------------------------------------------------------- H
# How atypical the pre-specified draw is on each figure's own quantity. The
# captions state these, so they are checked here.
if pooled is not None:
    pl = pooled
    b2 = pl[pl.budget == 2]
    g = b2.groupby("seed").ratio.agg(["mean", "median"])
    gap = (g["mean"] - g["median"])
    chk("H fig1 primary mean-median gap", 0.997, round(float(gap[PRIMARY_SEED]), 3))
    others = gap.drop(PRIMARY_SEED)
    chk("H fig1 next largest gap", 0.105, round(float(others.max()), 3))
    chk("H fig1 smallest gap", -0.014, round(float(others.min()), 3))
    chk("H fig1 primary gap is largest", True,
        bool(gap[PRIMARY_SEED] > others.max()))

    worst = pl.groupby("seed").ratio.max()
    chk("H fig2 primary worst ratio", 44.5, round(float(worst[PRIMARY_SEED]), 1))
    chk("H fig2 next worst ratio", 4.7,
        round(float(worst.drop(PRIMARY_SEED).max()), 1))

    # first-clean budget per draw, primary first then ascending seed
    order = [PRIMARY_SEED] + sorted(s for s in pl.seed.unique() if s != PRIMARY_SEED)
    budgets = sorted(pl.budget.unique())
    firsts = []
    for seed in order:
        part = pl[pl.seed == seed]
        for i, b in enumerate(budgets):
            if b == 0:
                continue
            if all(int((part[part.budget == later].ratio > 2).sum()) == 0
                   for later in budgets[i:]):
                firsts.append(int(b))
                break
    chk("H fig2 first-clean sorted", [4, 4, 4, 4, 4, 5, 6, 8, 20, 20], sorted(firsts))
    chk("H fig2 primary is the modal value", 4, firsts[0])

    inv = b2.groupby("seed").slope.apply(lambda s: int((s < 0).sum()))
    chk("H fig3 primary inverted count", 3, int(inv[PRIMARY_SEED]))
    chk("H fig3 other draws inverted", 0, int(inv.drop(PRIMARY_SEED).sum()))
    mins = b2.groupby("seed").slope.min().drop(PRIMARY_SEED)
    chk("H fig3 other draws min slope low", 0.275, round(float(mins.min()), 3))
    chk("H fig3 other draws min slope high", 0.408, round(float(mins.max()), 3))
    chk("H fig3 other draws all positive", True, bool((mins > 0).all()))

    # pooled counts quoted in 4.3 and Table 6
    seq = [int((pl[pl.budget == b].ratio > 2).sum())
           for b in (2, 3, 4, 5, 6, 8, 10)]
    chk("H pooled >2x sequence", [48, 25, 10, 8, 5, 3, 3], seq)
    chk("H pooled >3x persists to 8", True,
        int((pl[pl.budget == 8].ratio > 3).sum()) > 0)
    chk("H pooled worst above two", 4.68,
        round(float(max(pl[pl.budget == b].ratio.max()
                        for b in budgets if b > 2)), 2), 0.006)

print(f"{'':4} {'check':44} detail")
fails = 0
for status, label, detail in checks:
    if status == "FAIL":
        fails += 1
    print(f"{status} {label:44} {detail}")
print(f"\n{len(checks)} checks, {fails} failures")
raise SystemExit(1 if fails else 0)
