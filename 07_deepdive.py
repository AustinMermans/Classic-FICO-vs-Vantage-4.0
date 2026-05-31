"""Deep-dive charts (full panel):
  1. Disagreement-resolution heatmap  — default rate by FICO-band x VS-band (who's right when they disagree)
  2. Approval frontier                — default rate at every approval volume, FICO- vs VS-ranked
  3. Segment edge                     — VantageScore Gini edge by LTV / DTI / FTHB / purpose
                                         (FICO-band strata intentionally excluded — see note in code)
  4. Macro overlay                    — vintage edge vs realized default, colored by origination mortgage rate
Run: ./.venv/bin/python 07_deepdive.py
"""
import numpy as np
import polars as pl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import config as C
from gse.metrics import gini, score_band

O = C.OUTPUTS
BANDS = [f"[{C.SCORE_BAND_EDGES[i]},{C.SCORE_BAND_EDGES[i+1]})" for i in range(len(C.SCORE_BAND_EDGES) - 1)]

df = pl.read_parquet(C.PARQUET / "analysis_table.parquet").filter(
    pl.col("fico").is_not_null() & pl.col(C.SCORE_VARIANT).is_not_null()
    & (~pl.col("censored")) & (pl.col("num_borrowers") <= C.MAX_BORROWERS_FOR_COMPARISON)
)
df = df.with_columns(
    score_band(df["fico"], C.SCORE_BAND_EDGES).alias("fb"),
    score_band(df[C.SCORE_VARIANT], C.SCORE_BAND_EDGES).alias("vb"),
)
fico = df["fico"].to_numpy(); vs = df[C.SCORE_VARIANT].to_numpy(); y = df["defaulted"].to_numpy().astype(int)


def safe_gini(s, yy):
    if yy.sum() == 0 or yy.sum() == len(yy):
        return np.nan
    return gini(s, yy)


# ---- 1. Disagreement-resolution heatmap ----
cell = df.group_by(["fb", "vb"]).agg(pl.col("defaulted").mean().alias("dr"), pl.len().alias("n"))
idx = {b: i for i, b in enumerate(BANDS)}
M = np.full((len(BANDS), len(BANDS)), np.nan); N = np.zeros_like(M)
for r in cell.iter_rows(named=True):
    if r["fb"] in idx and r["vb"] in idx:
        M[idx[r["fb"]], idx[r["vb"]]] = r["dr"] * 100; N[idx[r["fb"]], idx[r["vb"]]] = r["n"]
plt.figure(figsize=(8.5, 7))
im = plt.imshow(M, cmap="Reds", aspect="auto")
plt.colorbar(im, label="default rate %")
plt.xticks(range(len(BANDS)), BANDS, rotation=45, ha="right"); plt.yticks(range(len(BANDS)), BANDS)
plt.xlabel("VantageScore 4.0 band"); plt.ylabel("Classic FICO band")
plt.title("When the scores DISAGREE, who's right?\ndefault rate by FICO x VS band — off-diagonal = disagreement")
hi = np.nanmax(M)
for i in range(len(BANDS)):
    for j in range(len(BANDS)):
        if not np.isnan(M[i, j]) and N[i, j] >= 200:
            plt.text(j, i, f"{M[i, j]:.1f}", ha="center", va="center", fontsize=7,
                     color="white" if M[i, j] > hi * 0.5 else "black")
plt.tight_layout(); plt.savefig(O / "disagreement_resolution.png", dpi=150); plt.close()

# ---- 2. Approval frontier ----
def frontier(score, yy, grid):
    order = np.argsort(-score, kind="mergesort")
    cum = np.cumsum(yy[order].astype(float))
    n = len(yy)
    return [cum[max(1, int(p * n)) - 1] / max(1, int(p * n)) for p in grid]

grid = np.linspace(0.05, 1.0, 40)
plt.figure(figsize=(8, 5.5))
plt.plot(grid * 100, np.array(frontier(fico, y, grid)) * 100, marker="o", ms=3, label="Rank by Classic FICO")
plt.plot(grid * 100, np.array(frontier(vs, y, grid)) * 100, marker="s", ms=3, label="Rank by VantageScore 4.0")
plt.xlabel("Approval rate (% approved, best scores first)")
plt.ylabel("Default rate of the approved book (%)")
plt.title("Approval frontier — default rate at every approval volume\nlower = better (the score that lets in fewer future defaults)")
plt.legend(); plt.grid(alpha=0.3); plt.tight_layout(); plt.savefig(O / "approval_frontier.png", dpi=150); plt.close()

# ---- 3. Segment edge ----
df = df.with_columns(
    pl.when(pl.col("oltv") <= 60).then(pl.lit("LTV ≤60"))
      .when(pl.col("oltv") <= 80).then(pl.lit("LTV 60-80"))
      .when(pl.col("oltv") <= 90).then(pl.lit("LTV 80-90"))
      .when(pl.col("oltv") <= 95).then(pl.lit("LTV 90-95"))
      .otherwise(pl.lit("LTV 95+")).alias("ltv_b"),
    pl.when(pl.col("dti") <= 20).then(pl.lit("DTI ≤20"))
      .when(pl.col("dti") <= 36).then(pl.lit("DTI 20-36"))
      .when(pl.col("dti") <= 43).then(pl.lit("DTI 36-43"))
      .otherwise(pl.lit("DTI 43+")).alias("dti_b"),
)
purpose = {"P": "Purchase", "C": "Cash-out refi", "R": "Rate/term refi", "U": "Unknown"}
fthb = {"Y": "First-time buyer", "N": "Repeat buyer", "U": "FTHB unknown"}
rows = []
# NOTE: FICO-band segments are intentionally excluded — within a fixed FICO band, FICO is ~constant
# so its Gini is ~0 and any "edge" is mechanical. The within-band residual signal of VS is shown by
# the disagreement-resolution heatmap instead.
for dim, col, mapper in [("LTV", "ltv_b", None), ("DTI", "dti_b", None),
                         ("Buyer", "first_time_buyer", fthb), ("Purpose", "loan_purpose", purpose)]:
    for val, sub in df.group_by(col):
        v = val[0]
        if v is None or sub.height < 20000:
            continue
        yy = sub["defaulted"].to_numpy().astype(int)
        gf = safe_gini(sub["fico"].to_numpy(), yy); gv = safe_gini(sub[C.SCORE_VARIANT].to_numpy(), yy)
        if np.isnan(gf) or np.isnan(gv):
            continue
        label = (mapper.get(v, v) if mapper else v)
        rows.append({"seg": label, "dim": dim, "n": sub.height, "edge": (gv - gf) * 10000})
seg = pl.DataFrame(rows).sort("edge")
colors = {"LTV": "#1f77b4", "DTI": "#ff7f0e", "Buyer": "#2ca02c", "Purpose": "#d62728"}
plt.figure(figsize=(9, max(5, 0.42 * seg.height)))
ypos = np.arange(seg.height)
plt.barh(ypos, seg["edge"].to_list(), color=[colors[d] for d in seg["dim"].to_list()])
plt.yticks(ypos, [f"{s}  (n={n:,})" for s, n in zip(seg["seg"].to_list(), seg["n"].to_list())], fontsize=8)
plt.axvline(0, color="black", lw=0.8)
plt.xlabel("VantageScore Gini edge over Classic FICO (bp)  —  right = VS better")
plt.title("Where VantageScore's edge comes from (by segment)")
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors.values()]
plt.legend(handles, colors.keys(), fontsize=8, loc="lower right")
plt.tight_layout(); plt.savefig(O / "segment_edge.png", dpi=150); plt.close()

# ---- 4. Macro overlay ----
try:
    mort = pl.read_csv("data/macro/MORTGAGE30US.csv").with_columns(
        pl.col("observation_date").str.slice(0, 4).cast(pl.Int64).alias("yr"),
        pl.col("observation_date").str.slice(5, 2).cast(pl.Int64).alias("mo"),
    ).with_columns(((pl.col("mo") - 1) // 3 + 1).alias("q"))
    mortq = (mort.group_by("yr", "q").agg(pl.col("MORTGAGE30US").mean().alias("rate"))
             .with_columns((pl.col("yr").cast(pl.Utf8) + "Q" + pl.col("q").cast(pl.Utf8)).alias("vintage")))
    bv = pl.read_csv(O / "discrimination_by_vintage.csv").with_columns(
        ((pl.col("vs_gini") - pl.col("fico_gini")) * 10000).alias("edge_bp"))
    m = bv.join(mortq.select("vintage", "rate"), on="vintage", how="left")
    plt.figure(figsize=(9.5, 6))
    sc = plt.scatter(m["default_rate"].to_numpy() * 100, m["edge_bp"].to_numpy(),
                     c=m["rate"].to_numpy(), cmap="viridis", s=70, edgecolor="k", linewidth=0.3)
    plt.colorbar(sc, label="30-yr mortgage rate at acquisition (%)")
    for r in m.iter_rows(named=True):
        plt.annotate(r["vintage"], (r["default_rate"] * 100, r["edge_bp"]), fontsize=6, alpha=0.6,
                     xytext=(2, 2), textcoords="offset points")
    plt.axhline(0, color="gray", lw=0.8, ls="--")
    plt.xlabel("Realized vintage default rate (%)")
    plt.ylabel("VantageScore Gini edge over FICO (bp)")
    plt.title("VantageScore's edge fades as realized defaults rise\n(each point = a vintage; color = 30-yr mortgage rate at acquisition)")
    plt.tight_layout(); plt.savefig(O / "macro_edge_vs_default.png", dpi=150); plt.close()
    print("macro chart written")
except Exception as e:
    print("macro chart skipped:", e)

print("deep-dive charts:", seg.height, "segments;",
      "wrote disagreement_resolution, approval_frontier, segment_edge, macro_edge_vs_default")
