"""Layer-1 bake-off: discrimination, agreement, calibration, swing borrowers. Emits tables + figures.
Run: python 05_compare.py

CDD-fix (round 1): metrics are computed on RESOLVED, comparable loans only —
  - exclude immature/censored loans (outcome unknown within the window),
  - keep prepaid loans as known non-defaults,
  - exclude >2-borrower loans (FICO comparator is incomplete there).
Swing analysis uses MATCHED approval rates. All results are CONDITIONAL on Fannie acquisition
(FICO floored at ~620) — not unconditional score performance.
"""
import polars as pl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import config as C
from gse.metrics import (auc_default, gini, ks, score_band, transition_matrix,
                         calibration_table, swing_borrowers)

raw = pl.read_parquet(C.PARQUET / "analysis_table.parquet")
n0 = raw.height
df = raw.filter(pl.col("fico").is_not_null() & pl.col(C.SCORE_VARIANT).is_not_null())
n1 = df.height
df = df.filter(~pl.col("censored"))                                   # drop immature (unknown outcome)
n2 = df.height
df = df.filter(pl.col("num_borrowers") <= C.MAX_BORROWERS_FOR_COMPARISON)  # FICO comparator complete
n3 = df.height
print("=== POPULATION FUNNEL ===")
print(f"  matched loans            {n0:,}")
print(f"  with both scores         {n1:,}")
print(f"  resolved (excl immature) {n2:,}   (dropped {n1-n2:,} immature)")
print(f"  <=2 borrowers (headline) {n3:,}   (dropped {n2-n3:,} multi-borrower)")
print(f"  pooled default rate      {df['defaulted'].mean()*100:.2f}%   prepaid kept as non-default")

fico = df["fico"].to_numpy(); vs = df[C.SCORE_VARIANT].to_numpy(); y = df["defaulted"].to_numpy()

# 1. Discrimination (CONDITIONAL on Fannie acquisition; resolved loans only)
disc = pl.DataFrame({
    "score": ["Classic FICO", "VantageScore 4.0 (current)"],
    "auc": [auc_default(fico, y), auc_default(vs, y)],
    "gini": [gini(fico, y), gini(vs, y)],
    "ks": [ks(fico, y), ks(vs, y)],
})
disc.write_csv(C.OUTPUTS / "discrimination.csv")
edge = (disc["gini"][1] - disc["gini"][0]) * 10000
print("\n=== DISCRIMINATION (resolved loans; conditional on Fannie acquisition, FICO>=620) ===")
print(disc)
print(f"VantageScore Gini edge: {edge:+.0f} bp")

# 1b. By vintage (note: immature already excluded; recent vintages still have fewer resolved loans)
seg_rows = []
for q, sub in df.group_by("acquisition_quarter"):
    if sub.height < 500:
        continue
    seg_rows.append({"vintage": q[0], "n_resolved": sub.height, "default_rate": sub["defaulted"].mean(),
                     "fico_gini": gini(sub["fico"].to_numpy(), sub["defaulted"].to_numpy()),
                     "vs_gini": gini(sub[C.SCORE_VARIANT].to_numpy(), sub["defaulted"].to_numpy())})
if seg_rows:
    pl.DataFrame(seg_rows).sort("vintage").write_csv(C.OUTPUTS / "discrimination_by_vintage.csv")

# 2. Agreement
df2 = df.with_columns(
    score_band(df["fico"], C.SCORE_BAND_EDGES).alias("fico_band"),
    score_band(df[C.SCORE_VARIANT], C.SCORE_BAND_EDGES).alias("vs_band"),
)
spearman = df.select(pl.corr("fico", C.SCORE_VARIANT, method="spearman")).item()
print(f"\nSpearman(FICO, VS4) = {spearman:.4f}")
transition_matrix(df2, "fico_band", "vs_band").write_csv(C.OUTPUTS / "transition_matrix.csv")

# 3. Swing borrowers at MATCHED approval rates (approve top X% under each score)
print("\n=== SWING BORROWERS (matched approval rates) ===")
swing_all = []
for r in C.SWING_APPROVAL_RATES:
    fico_cut = float(df["fico"].quantile(1 - r)); vs_cut = float(df[C.SCORE_VARIANT].quantile(1 - r))
    s = swing_borrowers(df, "fico", C.SCORE_VARIANT, "defaulted", fico_cut=fico_cut, vs_cut=vs_cut)
    s = s.with_columns(pl.lit(f"{int(r*100)}% approved").alias("approval_rate"))
    swing_all.append(s)
    print(f"-- approve top {int(r*100)}% (FICO>={fico_cut:.0f}, VS4>={vs_cut:.0f}) --")
    print(s.select("segment", "n", "default_rate"))
pl.concat(swing_all).write_csv(C.OUTPUTS / "swing_borrowers.csv")

# 4. Calibration
calf = calibration_table(df2, "fico_band", "defaulted").sort("fico_band")
calv = calibration_table(df2, "vs_band", "defaulted").sort("vs_band")
calf.write_csv(C.OUTPUTS / "calibration_fico.csv"); calv.write_csv(C.OUTPUTS / "calibration_vs.csv")
band_order = [f"[{C.SCORE_BAND_EDGES[i]},{C.SCORE_BAND_EDGES[i+1]})" for i in range(len(C.SCORE_BAND_EDGES) - 1)]
calf_d = dict(zip(calf["fico_band"].to_list(), calf["default_rate"].to_list()))
calv_d = dict(zip(calv["vs_band"].to_list(), calv["default_rate"].to_list()))
yf = [calf_d.get(b, float("nan")) for b in band_order]
yv = [calv_d.get(b, float("nan")) for b in band_order]
plt.figure()
plt.plot(band_order, yf, marker="o", label="Classic FICO")
plt.plot(band_order, yv, marker="s", label="VantageScore 4.0")
plt.ylabel("Observed default rate"); plt.xlabel("Score band (low → high)"); plt.xticks(rotation=45)
plt.title(f"Default rate by score band ({'smoke 2020Q2' if C.SMOKE else 'full panel'}, resolved loans)")
plt.legend(); plt.tight_layout(); plt.savefig(C.OUTPUTS / "calibration_by_band.png", dpi=150)
print("\nWrote tables + calibration_by_band.png to", C.OUTPUTS)
