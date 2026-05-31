"""CDD empirical gate + stratified numbers for the polished report.
Tests the two converged dissent-risks (comparator choice; stress=artifact?) and computes the
within-vintage / borrower-count / residual-Gini figures the fan-out flagged. Read-only on the data.
Run: ./.venv/bin/python 09_gate.py
"""
import numpy as np
import polars as pl
import config as C
from gse.metrics import gini, score_band

df = pl.read_parquet(C.PARQUET / "analysis_table.parquet").filter(
    pl.col("fico").is_not_null() & pl.col(C.SCORE_VARIANT).is_not_null()
    & (~pl.col("censored")) & (pl.col("num_borrowers") <= 2))
y = df["defaulted"].to_numpy().astype(int)
fico = df["fico"].to_numpy()
gf = gini(fico, y)

print(f"headline n={df.height:,}  FICO Gini={gf:.4f}\n")

print("=== A. VS4 VARIANT SENSITIVITY (Gini vs representative FICO) — comparator-choice gate ===")
print("   (current_method = lowest-of-borrowers, MATCHES representative FICO; others are average-then-average)")
for v in ["vs4_current_method", "vs4_trimerge", "vs4_bimerge_lowest", "vs4_bimerge_median", "vs4_bimerge_highest"]:
    s = df[v].to_numpy(); m = ~np.isnan(s)
    gv = gini(s[m], y[m])
    print(f"   {v:24} Gini {gv:.4f}  edge {(gv-gf)*10000:+.0f}bp")

print("\n=== B. BORROWER-COUNT SPLIT (current_method) ===")
for nb in [1, 2]:
    sub = df.filter(pl.col("num_borrowers") == nb)
    yy = sub["defaulted"].to_numpy().astype(int)
    gff = gini(sub["fico"].to_numpy(), yy); gvv = gini(sub[C.SCORE_VARIANT].to_numpy(), yy)
    print(f"   {nb}-borrower (n={sub.height:,}): FICO {gff:.4f}  VS {gvv:.4f}  edge {(gvv-gff)*10000:+.0f}bp")

print("\n=== C. AGGREGATION: pooled vs within-vintage (loan- and default-weighted) ===")
rows = []
for q, sub in df.group_by("acquisition_quarter"):
    yy = sub["defaulted"].to_numpy().astype(int)
    if yy.sum() < 50:
        continue
    gff = gini(sub["fico"].to_numpy(), yy); gvv = gini(sub[C.SCORE_VARIANT].to_numpy(), yy)
    rows.append((q[0], sub.height, int(yy.sum()), float(yy.mean()), (gvv - gff) * 10000))
vt = pl.DataFrame(rows, schema=["vintage", "n", "ndef", "dr", "edge"], orient="row")
pooled = (gini(df[C.SCORE_VARIANT].to_numpy(), y) - gf) * 10000
lw = (vt["edge"] * vt["n"]).sum() / vt["n"].sum()
dw = (vt["edge"] * vt["ndef"]).sum() / vt["ndef"].sum()
print(f"   pooled {pooled:+.0f}bp | within-vintage loan-wtd {lw:+.0f}bp | default-wtd {dw:+.0f}bp")
for name, sel in [("benign (<1% dr)", vt.filter(pl.col("dr") < 0.01)),
                  ("stress (>2.5% dr)", vt.filter(pl.col("dr") > 0.025))]:
    e = (sel["edge"] * sel["ndef"]).sum() / sel["ndef"].sum()
    print(f"   {name}: default-wtd edge {e:+.0f}bp  ({sel.height} vintages)")

print("\n=== D. RESIDUAL GINI (within-band, loan-weighted) ===")
df2 = df.with_columns(score_band(df["fico"], C.SCORE_BAND_EDGES).alias("fb"),
                      score_band(df[C.SCORE_VARIANT], C.SCORE_BAND_EDGES).alias("vb"))
def within_gini(frame, strat, score):
    num = den = 0.0
    for _, sub in frame.group_by(strat):
        yy = sub["defaulted"].to_numpy().astype(int)
        if yy.sum() < 50 or yy.sum() == len(yy):
            continue
        num += gini(sub[score].to_numpy(), yy) * sub.height; den += sub.height
    return num / den
print(f"   VS within fixed FICO bands: {within_gini(df2, 'fb', C.SCORE_VARIANT):.3f}")
print(f"   FICO within fixed VS bands: {within_gini(df2, 'vb', 'fico'):.3f}")

print("\n=== E. STRESS = COVID-TIMING? calendar year of the D180/credit event ===")
defs = df.filter(pl.col("defaulted")).with_columns(
    pl.col("acquisition_quarter").str.slice(0, 4).cast(pl.Int64).alias("ay"),
    ((pl.col("acquisition_quarter").str.slice(5, 1).cast(pl.Int64) - 1) * 3 + 1).alias("am"),
).with_columns(((pl.col("ay") * 12 + pl.col("am")) + pl.col("event_age").fill_null(0)).alias("midx")
).with_columns((pl.col("midx") // 12).alias("def_year"))
stressq = vt.filter(pl.col("dr") > 0.025)["vintage"].to_list()
sd = defs.filter(pl.col("acquisition_quarter").is_in(stressq))
tot = sd.height
print(f"   stress-vintage defaults (n={tot:,}) by calendar year of default:")
yr = sd.group_by("def_year").len().sort("def_year")
for r in yr.iter_rows(named=True):
    print(f"     {r['def_year']}: {r['len']:>9,}  ({r['len']/tot*100:4.1f}%)")
