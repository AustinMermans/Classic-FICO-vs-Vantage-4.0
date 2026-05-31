"""Render the Layer-1 smoke charts from existing outputs. Run: python 06_charts.py"""
import numpy as np
import polars as pl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import config as C

O = C.OUTPUTS
disc = pl.read_csv(O / "discrimination.csv")
swing = pl.read_csv(O / "swing_borrowers.csv")
tm = pl.read_csv(O / "transition_matrix.csv")
at = pl.read_parquet(C.PARQUET / "analysis_table.parquet").filter(
    pl.col("fico").is_not_null() & pl.col(C.SCORE_VARIANT).is_not_null()
    & (~pl.col("censored")) & (pl.col("num_borrowers") <= C.MAX_BORROWERS_FOR_COMPARISON)
)
bands = [f"[{C.SCORE_BAND_EDGES[i]},{C.SCORE_BAND_EDGES[i+1]})" for i in range(len(C.SCORE_BAND_EDGES) - 1)]

# 1. Discrimination bars
metrics = ["auc", "gini", "ks"]
fv = [disc.filter(pl.col("score") == "Classic FICO")[m][0] for m in metrics]
vv = [disc.filter(pl.col("score").str.contains("VantageScore"))[m][0] for m in metrics]
x = np.arange(len(metrics)); w = 0.36
plt.figure(figsize=(7, 5))
b1 = plt.bar(x - w/2, fv, w, label="Classic FICO", color="#1f77b4")
b2 = plt.bar(x + w/2, vv, w, label="VantageScore 4.0", color="#ff7f0e")
for b in list(b1) + list(b2):
    plt.text(b.get_x() + b.get_width()/2, b.get_height(), f"{b.get_height():.3f}", ha="center", va="bottom", fontsize=9)
plt.xticks(x, [m.upper() for m in metrics]); plt.ylabel("value")
plt.title(f"Discrimination: who ranks default better ({'2020Q2 smoke' if C.SMOKE else 'full panel 2013-2023'})")
plt.legend(); plt.tight_layout(); plt.savefig(O / "discrimination_bars.png", dpi=150); plt.close()

# 2. Swing borrowers (at the 50%-approved matched operating point)
swing = swing.filter(pl.col("approval_rate") == "50% approved") if "approval_rate" in swing.columns else swing
order = ["approve_both", "vs_approve_fico_decline", "fico_approve_vs_decline", "decline_both"]
labels = ["Approve\nboth", "VS only\n(FICO declines)", "FICO only\n(VS declines)", "Decline\nboth"]
sd = dict(zip(swing["segment"].to_list(), swing["default_rate"].to_list()))
sn = dict(zip(swing["segment"].to_list(), swing["n"].to_list()))
vals = [sd[s] * 100 for s in order]; ns = [sn[s] for s in order]
plt.figure(figsize=(7.5, 5))
bars = plt.bar(labels, vals, color=["#2ca02c", "#ff7f0e", "#1f77b4", "#d62728"])
for b, n in zip(bars, ns):
    plt.text(b.get_x() + b.get_width()/2, b.get_height(), f"{b.get_height():.2f}%\nn={n:,}", ha="center", va="bottom", fontsize=8)
plt.ylabel("Default rate (%)")
plt.title("Swing borrowers: default rate by approve/decline segment\n(cutoffs = median FICO & median VS4)")
plt.tight_layout(); plt.savefig(O / "swing_borrowers.png", dpi=150); plt.close()

# 3. Transition heatmap (row-normalized: where each FICO band lands in VS)
idx = {b: i for i, b in enumerate(bands)}
M = np.zeros((len(bands), len(bands)))
for r in tm.iter_rows(named=True):
    fi, vi = idx.get(r["fico_band"]), idx.get(r["vs_band"])
    if fi is not None and vi is not None:
        M[fi, vi] = r["n"]
Mshare = M / M.sum(axis=1, keepdims=True).clip(min=1)
plt.figure(figsize=(7.5, 6))
im = plt.imshow(Mshare, cmap="Blues", aspect="auto", vmin=0, vmax=1)
plt.colorbar(im, label="row share")
plt.xticks(range(len(bands)), bands, rotation=45, ha="right"); plt.yticks(range(len(bands)), bands)
plt.xlabel("VantageScore 4.0 band"); plt.ylabel("Classic FICO band")
plt.title("Where each FICO band lands in VantageScore (row-normalized %)")
for i in range(len(bands)):
    for j in range(len(bands)):
        if M[i, j] > 0:
            plt.text(j, i, f"{Mshare[i, j]*100:.0f}", ha="center", va="center", fontsize=7,
                     color="white" if Mshare[i, j] > 0.5 else "black")
plt.tight_layout(); plt.savefig(O / "transition_heatmap.png", dpi=150); plt.close()

# 4. Score agreement hexbin
fico = at["fico"].to_numpy(); vs = at[C.SCORE_VARIANT].to_numpy()
plt.figure(figsize=(6.8, 6))
hb = plt.hexbin(fico, vs, gridsize=45, cmap="viridis", bins="log", mincnt=1)
plt.plot([580, 850], [580, 850], "r--", lw=1, label="y = x")
plt.colorbar(hb, label="log10(loan count)")
plt.xlabel("Classic FICO (loan representative)"); plt.ylabel("VantageScore 4.0 (current method)")
_sp = at.select(pl.corr("fico", C.SCORE_VARIANT, method="spearman")).item()
plt.title(f"FICO vs VantageScore — {len(fico):,} loans (Spearman {_sp:.2f})")
plt.legend(); plt.tight_layout(); plt.savefig(O / "score_scatter_hexbin.png", dpi=150); plt.close()

# 5. Per-vintage Gini — the headline nuance (edge compresses when defaults rise)
vpath = O / "discrimination_by_vintage.csv"
if vpath.exists():
    bv = pl.read_csv(vpath).sort("vintage")
    x = np.arange(bv.height)
    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax2 = ax1.twinx()
    ax2.bar(x, [d * 100 for d in bv["default_rate"].to_list()], alpha=0.15, color="gray")
    ax1.set_zorder(ax2.get_zorder() + 1); ax1.patch.set_visible(False)
    ax1.plot(x, bv["fico_gini"].to_list(), marker="o", color="#1f77b4", label="Classic FICO Gini")
    ax1.plot(x, bv["vs_gini"].to_list(), marker="s", color="#ff7f0e", label="VantageScore 4.0 Gini")
    ax1.set_ylabel("Gini (lines)"); ax2.set_ylabel("Default rate % (gray bars)")
    ax1.set_xticks(x); ax1.set_xticklabels(bv["vintage"].to_list(), rotation=90, fontsize=7)
    ax1.set_xlabel("Acquisition vintage"); ax1.legend(loc="upper right")
    ax1.set_title(f"Discrimination by vintage — VantageScore's edge compresses as defaults rise "
                  f"({'smoke' if C.SMOKE else 'full panel 2013-2023'})")
    fig.tight_layout(); fig.savefig(O / "gini_by_vintage.png", dpi=150); plt.close()

print("wrote: discrimination_bars, swing_borrowers, transition_heatmap, score_scatter_hexbin, gini_by_vintage")
