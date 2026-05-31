"""Disk-safe full-panel run. For each acquisition quarter: extract its CSV from Performance_All.zip
-> compact parquet (needed cols) -> collapse to one-row-per-loan labels (the SAME unit-tested
derive_default_labels path as the 2020Q2 smoke) -> delete the CSV. Then combine the tiny per-loan
label tables and write the full VS4 scores. Peak disk ~ one quarter's CSV (<=25GB).

Usage:
  ./.venv/bin/python run_full.py             # all quarters 2013Q2-2023Q1
  ./.venv/bin/python run_full.py 2020Q2      # specific quarter(s)  (validation)
Resumable: quarters whose labels/<q>.parquet already exists are skipped.
"""
import sys
import shutil
import zipfile
import traceback
from pathlib import Path

import duckdb
import polars as pl

import config as C
from gse.labels import derive_default_labels

ZIP = Path.home() / "Downloads" / "Performance_All.zip"
RAWDIR = C.RAW / "base_loanperf"; RAWDIR.mkdir(parents=True, exist_ok=True)
LABELDIR = C.PARQUET / "labels"; LABELDIR.mkdir(parents=True, exist_ok=True)
ALLQ = [f"{y}Q{q}" for y in range(2013, 2024) for q in (1, 2, 3, 4)]
WINDOW = [q for q in ALLQ if "2013Q2" <= q <= "2023Q1"]


def extract(q: str) -> Path:
    csv = RAWDIR / f"{q}.csv"
    if csv.exists():
        return csv
    with zipfile.ZipFile(ZIP) as z, z.open(f"{q}.csv") as src, open(csv, "wb") as dst:
        shutil.copyfileobj(src, dst, length=16 * 1024 * 1024)
    return csv


def base_parquet(q: str, csv: Path) -> Path:
    con = duckdb.connect()
    names = con.sql(f"SELECT * FROM read_csv('{csv}', delim='|', header=false, all_varchar=true) LIMIT 0").columns
    parts = []
    for name, idx in C.BASE_PERF_COLUMN_MAP.items():
        parts.append(f"CAST({names[idx]} AS BIGINT) AS loan_identifier" if name == "loan_identifier"
                     else f"{names[idx]} AS {name}")
    parts.append(f"'{q}' AS acquisition_quarter")
    out = C.PARQUET / f"_base_{q}.parquet"
    con.sql(f"COPY (SELECT {', '.join(parts)} FROM read_csv('{csv}', delim='|', header=false, "
            f"all_varchar=true)) TO '{out}' (FORMAT PARQUET)")
    return out


def label_quarter(base_pq: Path) -> tuple[int, int]:
    base = pl.scan_parquet(base_pq).with_columns(
        pl.col("loan_identifier").cast(pl.Int64, strict=False),
    ).with_columns(
        (pl.col("loan_identifier").cast(pl.Utf8) + "|" + pl.col("acquisition_quarter")).alias("loan_key"),
        (pl.col("monthly_reporting_period").str.slice(2, 4).cast(pl.Int64) * 12
         + pl.col("monthly_reporting_period").str.slice(0, 2).cast(pl.Int64)).alias("rpt_idx"),
    )
    first = base.group_by("loan_key").agg(
        pl.col("rpt_idx").min().alias("first_idx"),
        (pl.col("loan_age").cast(pl.Int64, strict=False) - pl.col("rpt_idx")).min().alias("off_raw"),
    )
    panel = (
        base.join(first, on="loan_key")
        .with_columns(pl.coalesce(pl.col("off_raw"), -pl.col("first_idx")).alias("age_offset"))
        .select("loan_key", (pl.col("rpt_idx") + pl.col("age_offset")).alias("loan_age"),
                pl.col("dlq_months").cast(pl.Int64, strict=False), "zero_balance_code")
        .collect(engine="streaming")
    )
    labels = derive_default_labels(panel, window_months=C.PERF_WINDOW_MONTHS)
    attrs = (
        base.group_by("loan_key", "loan_identifier", "acquisition_quarter").agg(
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
        ).with_columns(pl.min_horizontal("fico_borrower", "fico_co").alias("fico"))
        .collect(engine="streaming")
    )
    out = attrs.join(labels, on="loan_key", how="left")
    return out, int(out["defaulted"].sum())


def write_vs4_full() -> None:
    files = list((C.RAW / "vs4_loanperf").glob("*.txt")) + list((C.RAW / "vs4_loanperf").glob("*.csv"))
    df = pl.scan_csv(files, separator="|", infer_schema_length=10000).with_columns(
        pl.col("loan_identifier").cast(pl.Int64, strict=False)).collect()
    df.write_parquet(C.PARQUET / "vs4_scores.parquet")
    print(f"VS4 scores (full): {df.height:,} rows", flush=True)


def main():
    quarters = sys.argv[1:] or WINDOW
    failed = []
    for i, q in enumerate(quarters, 1):
        lp = LABELDIR / f"{q}.parquet"
        if lp.exists():
            print(f"[{i}/{len(quarters)}] {q} already done, skip", flush=True)
            continue
        try:
            print(f"[{i}/{len(quarters)}] {q}: extracting...", flush=True)
            csv = extract(q)
            bpq = base_parquet(q, csv)
            csv.unlink(missing_ok=True)                 # free the big CSV immediately
            out, d = label_quarter(bpq)
            bpq.unlink(missing_ok=True)
            out.write_parquet(lp)
            print(f"[{i}/{len(quarters)}] {q}: loans={out.height:,} defaults={d:,}", flush=True)
        except Exception:
            print(f"[{i}/{len(quarters)}] {q}: ERROR\n{traceback.format_exc()}", flush=True)
            failed.append(q)

    # Completeness gate: never emit a panel that LOOKS complete (exit 0) but silently dropped a quarter.
    have = {p.stem for p in LABELDIR.glob("*.parquet")}
    missing = sorted(set(quarters) - have)
    if failed or missing:
        print(f"INCOMPLETE PANEL — failed={failed} missing={missing}. NOT writing loans_labeled "
              f"(it would look complete). The run is resumable — fix the cause and re-run.", flush=True)
        sys.exit(1)

    done = sorted(p for p in LABELDIR.glob("*.parquet") if p.stem in set(quarters))
    loans = pl.concat([pl.read_parquet(p) for p in done])
    loans.write_parquet(C.PARQUET / "loans_labeled.parquet")
    print(f"COMBINED loans_labeled: {loans.height:,} loans across {len(done)} quarters", flush=True)
    write_vs4_full()


if __name__ == "__main__":
    main()
