"""Final paper figures from the gate findings: borrower-count split, COVID-timing of stress
defaults, matched-approval swing (both cutoffs), VS4 variant sensitivity.
Run: ./.venv/bin/python 10_report_charts.py
"""
import numpy as np
import polars as pl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import config as C
from gse.metrics import gini

O = C.OUTPUTS
df = pl.read_parquet(C.PARQUET / "analysis_table.parquet").filter(
    pl.col("fico").is_not_null() & pl.col(C.SCORE_VARIANT).is_not_null()
    & (~pl.col("censored")) & (pl.col("num_borrowers") <= 2))

# 1. Borrower-count split
fig, ax = plt.subplots(figsize=(7, 5))
x = np.arange(2); w = 0.36
fg, vg, edges = [], [], []
for nb in [1, 2]:
    s = df.filter(pl.col("num_borrowers") == nb); yy = s["defaulted"].to_numpy().astype(int)
    a = gini(s["fico"].to_numpy(), yy); b = gini(s[C.SCORE_VARIANT].to_numpy(), yy)
    fg.append(a); vg.append(b); edges.append((b - a) * 10000)
b1 = ax.bar(x - w/2, fg, w, label="Classic FICO", color="#1f77b4")
b2 = ax.bar(x + w/2, vg, w, label="VantageScore 4.0", color="#ff7f0e")
for bb in list(b1) + list(b2):
    ax.text(bb.get_x() + bb.get_width()/2, bb.get_height(), f"{bb.get_height():.3f}", ha="center", va="bottom", fontsize=9)
for i, e in enumerate(edges):
    ax.text(i, max(fg[i], vg[i]) + 0.03, f"edge {e:+.0f}bp", ha="center", fontsize=10, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(["1 borrower", "2 borrowers"]); ax.set_ylabel("Gini")
ax.set_ylim(0, 0.66); ax.set_title("VantageScore's edge is almost entirely single-borrower loans")
ax.legend(); fig.tight_layout(); fig.savefig(O / "borrower_split.png", dpi=150); plt.close()

# 2. COVID-timing of stress-vintage defaults
rows = []
for q, sub in df.group_by("acquisition_quarter"):
    yy = sub["defaulted"].to_numpy().astype(int)
    if yy.sum() < 50:
        continue
    rows.append((q[0], float(yy.mean())))
vt = pl.DataFrame(rows, schema=["vintage", "dr"], orient="row")
stressq = vt.filter(pl.col("dr") > 0.025)["vintage"].to_list()
defs = df.filter(pl.col("defaulted") & pl.col("acquisition_quarter").is_in(stressq)).with_columns(
    pl.col("acquisition_quarter").str.slice(0, 4).cast(pl.Int64).alias("ay"),
    ((pl.col("acquisition_quarter").str.slice(5, 1).cast(pl.Int64) - 1) * 3 + 1).alias("am"),
).with_columns((((pl.col("ay") * 12 + pl.col("am")) + pl.col("event_age").fill_null(0)) // 12).alias("yr"))
yc = defs.group_by("yr").len().sort("yr")
tot = yc["len"].sum()
plt.figure(figsize=(7.5, 5))
cols = ["#d62728" if y in (2020, 2021) else "#9aa0a6" for y in yc["yr"].to_list()]
bars = plt.bar([str(y) for y in yc["yr"].to_list()], [n / tot * 100 for n in yc["len"].to_list()], color=cols)
for bb, n in zip(bars, yc["len"].to_list()):
    if n / tot > 0.02:
        plt.text(bb.get_x() + bb.get_width()/2, bb.get_height(), f"{bb.get_height():.0f}%", ha="center", va="bottom", fontsize=9)
plt.ylabel("% of stress-vintage defaults"); plt.xlabel("Calendar year the default occurred")
plt.title("The 'stress' vintages defaulted into the COVID shock\n93% of their defaults landed in 2020–2021 (red)")
plt.tight_layout(); plt.savefig(O / "covid_timing.png", dpi=150); plt.close()

# 3. Matched-approval swing at 50% and 80%
sw = pl.read_csv(O / "swing_borrowers.csv")
order = ["approve_both", "vs_approve_fico_decline", "fico_approve_vs_decline", "decline_both"]
lab = ["Approve\nboth", "VS only", "FICO only", "Decline\nboth"]
fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
for ax, rate in zip(axes, ["50% approved", "80% approved"]):
    s = sw.filter(pl.col("approval_rate") == rate)
    d = dict(zip(s["segment"].to_list(), s["default_rate"].to_list()))
    vals = [d[k] * 100 for k in order]
    bars = ax.bar(lab, vals, color=["#2ca02c", "#ff7f0e", "#1f77b4", "#d62728"])
    for bb in bars:
        ax.text(bb.get_x() + bb.get_width()/2, bb.get_height(), f"{bb.get_height():.2f}%", ha="center", va="bottom", fontsize=8)
    ax.set_title(rate); ax.set_ylabel("Default rate (%)")
fig.suptitle("Swing borrowers at matched approval rates — VS-only vs FICO-only approvals")
fig.tight_layout(); fig.savefig(O / "swing_matched.png", dpi=150); plt.close()

# 4. Variant sensitivity (with the matched-comparator caveat)
y = df["defaulted"].to_numpy().astype(int); gf = gini(df["fico"].to_numpy(), y)
variants = [("current_method\n(lowest — MATCHED)", "vs4_current_method"),
            ("trimerge\n(avg)", "vs4_trimerge"), ("bimerge lowest\n(avg)", "vs4_bimerge_lowest"),
            ("bimerge median\n(avg)", "vs4_bimerge_median"), ("bimerge highest\n(avg)", "vs4_bimerge_highest")]
es = []
for _, v in variants:
    s = df[v].to_numpy(); m = ~np.isnan(s); es.append((gini(s[m], y[m]) - gf) * 10000)
plt.figure(figsize=(8.5, 5))
cols = ["#2ca02c"] + ["#bbbbbb"] * 4
bars = plt.bar([n for n, _ in variants], es, color=cols)
for bb in bars:
    plt.text(bb.get_x() + bb.get_width()/2, bb.get_height(), f"{bb.get_height():+.0f}", ha="center", va="bottom", fontsize=9)
plt.ylabel("Gini edge over representative FICO (bp)")
plt.title("Only the lowest-method VS is apples-to-apples with representative FICO\n(average-method variants inflate the edge via methodology mismatch)")
plt.tight_layout(); plt.savefig(O / "variant_sensitivity.png", dpi=150); plt.close()
print("wrote: borrower_split, covid_timing, swing_matched, variant_sensitivity")
