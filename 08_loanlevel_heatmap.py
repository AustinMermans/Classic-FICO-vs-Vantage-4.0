"""Loan-level heatmaps in (FICO x VantageScore) score space, colored by observed default rate.
Leverages the 24.7M individual loans. Also splits benign vs stress vintages to see if the default
cluster moves. Run: ./.venv/bin/python 08_loanlevel_heatmap.py
"""
import numpy as np
import polars as pl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import config as C

df = pl.read_parquet(C.PARQUET / "analysis_table.parquet").filter(
    pl.col("fico").is_not_null() & pl.col(C.SCORE_VARIANT).is_not_null()
    & (~pl.col("censored")) & (pl.col("num_borrowers") <= 2))
vr = df.group_by("acquisition_quarter").agg(pl.col("defaulted").mean().alias("vdr"))
df = df.join(vr, on="acquisition_quarter")
fico = df["fico"].to_numpy(); vs = df[C.SCORE_VARIANT].to_numpy()
y = df["defaulted"].to_numpy().astype(float); vdr = df["vdr"].to_numpy()

# 1. all loans: default rate across score space
plt.figure(figsize=(7.8, 6.8))
hb = plt.hexbin(fico, vs, C=y, reduce_C_function=np.mean, gridsize=55, mincnt=300, cmap="inferno_r")
plt.colorbar(hb, label="default rate (mean per cell)")
plt.plot([600, 850], [600, 850], "c--", lw=1, alpha=0.7, label="FICO = VS")
plt.xlabel("Classic FICO"); plt.ylabel("VantageScore 4.0")
plt.title(f"Where defaults live in score space — {len(fico):,} loans\ncolor = default rate (cells with <300 loans hidden)")
plt.legend(loc="lower right"); plt.tight_layout()
plt.savefig(C.OUTPUTS / "loanlevel_default_heatmap.png", dpi=150); plt.close()

# 2. benign vs stress vintages (does the cluster move?)
benign = vdr < 0.01; stress = vdr > 0.025
fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharex=True, sharey=True)
hb = None
for ax, mask, name in [(axes[0], benign, "Benign vintages (vintage default <1%)"),
                       (axes[1], stress, "Stress vintages (vintage default >2.5%)")]:
    hb = ax.hexbin(fico[mask], vs[mask], C=y[mask], reduce_C_function=np.mean,
                   gridsize=50, mincnt=200, cmap="inferno_r", vmin=0, vmax=0.12)
    ax.plot([600, 850], [600, 850], "c--", lw=1, alpha=0.6)
    ax.set_title(f"{name}\nn={int(mask.sum()):,}"); ax.set_xlabel("Classic FICO")
axes[0].set_ylabel("VantageScore 4.0")
fig.colorbar(hb, ax=axes, label="default rate", shrink=0.85)
fig.suptitle("Does the default cluster move under stress? (loan-level, score space)")
fig.savefig(C.OUTPUTS / "loanlevel_heatmap_regime.png", dpi=150, bbox_inches="tight"); plt.close()
print(f"wrote loanlevel heatmaps; benign n={int(benign.sum()):,}  stress n={int(stress.sum()):,}")
