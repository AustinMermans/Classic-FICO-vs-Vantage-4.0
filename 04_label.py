"""Collapse the monthly base panel to one row per loan with the default label + origination attrs.
Run: python 04_label.py

CDD-fix (round 1): loan_age is derived from monthly_reporting_period (populated on EVERY row,
including zero-balance/termination rows), NOT the raw loan_age column — which is null on exactly
those rows, so the old window filter silently dropped all prepay/credit-event records. Age is
months since the loan's first observed reporting period.

Classic FICO comparator = loan representative score = min(borrower, co-borrower), matching VS4
vs4_current_method (lowest-of-borrowers). num_borrowers carried through for the >2-borrower filter.
"""
import polars as pl
import config as C
from gse.labels import derive_default_labels

base = pl.scan_parquet(C.PARQUET / "base_perf.parquet").with_columns(
    pl.col("loan_identifier").cast(pl.Int64, strict=False),
).with_columns(
    (pl.col("loan_identifier").cast(pl.Utf8) + "|" + pl.col("acquisition_quarter")).alias("loan_key"),
    # MMYYYY -> absolute month index (works on zero-balance rows where loan_age is null)
    (pl.col("monthly_reporting_period").str.slice(2, 4).cast(pl.Int64) * 12
     + pl.col("monthly_reporting_period").str.slice(0, 2).cast(pl.Int64)).alias("rpt_idx"),
)

# --- default label: reconstruct TRUE loan age (origination-based) on every row, incl. zero-balance
#     rows where the raw loan_age is null. For observed rows raw_loan_age - rpt_idx is a per-loan
#     constant offset; apply it to rpt_idx so the ZB/termination rows get the correct age too.
#     Fallback (if a loan never has a populated loan_age): months since first observed period. ---
first = base.group_by("loan_key").agg(
    pl.col("rpt_idx").min().alias("first_idx"),
    (pl.col("loan_age").cast(pl.Int64, strict=False) - pl.col("rpt_idx")).min().alias("off_raw"),
)
panel = (
    base.join(first, on="loan_key")
    .with_columns(pl.coalesce(pl.col("off_raw"), -pl.col("first_idx")).alias("age_offset"))
    .select(
        "loan_key",
        (pl.col("rpt_idx") + pl.col("age_offset")).alias("loan_age"),
        pl.col("dlq_months").cast(pl.Int64, strict=False),
        "zero_balance_code",
    )
    .collect(engine="streaming")
)
labels = derive_default_labels(panel, window_months=C.PERF_WINDOW_MONTHS)

# --- origination attributes: one row per loan (first non-null), representative FICO = min ---
attrs = (
    base.group_by("loan_key", "loan_identifier", "acquisition_quarter")
    .agg(
        pl.col("fico").cast(pl.Float64, strict=False).drop_nulls().first().alias("fico_borrower"),
        pl.col("coborrower_fico").cast(pl.Float64, strict=False).drop_nulls().first().alias("fico_co"),
        pl.col("oltv").cast(pl.Float64, strict=False).drop_nulls().first().alias("oltv"),
        pl.col("ocltv").cast(pl.Float64, strict=False).drop_nulls().first().alias("ocltv"),
        pl.col("dti").cast(pl.Float64, strict=False).drop_nulls().first().alias("dti"),
        pl.col("first_time_buyer").drop_nulls().first().alias("first_time_buyer"),
        pl.col("loan_purpose").drop_nulls().first().alias("loan_purpose"),
        pl.col("property_state").drop_nulls().first().alias("property_state"),
        pl.col("occupancy").drop_nulls().first().alias("occupancy"),
        pl.col("num_borrowers").cast(pl.Int64, strict=False).drop_nulls().first().alias("num_borrowers"),
    )
    .with_columns(pl.min_horizontal("fico_borrower", "fico_co").alias("fico"))
    .collect(engine="streaming")
)

out = attrs.join(labels, on="loan_key", how="left")
dr = out["defaulted"].mean()
print(f"Loans: {out.height:,}  defaulted={out['defaulted'].sum():,}  prepaid={out['prepaid'].sum():,}  "
      f"censored(immature)={out['censored'].sum():,}  pooled_default={dr:.4f}  median_FICO={out['fico'].median()}")
assert 0.0 < dr < 0.25, f"GATE FAIL: implausible default rate {dr:.4f}"
out.write_parquet(C.PARQUET / "loans_labeled.parquet")
print("wrote loans_labeled.parquet")
