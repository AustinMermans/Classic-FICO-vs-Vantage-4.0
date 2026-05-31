"""Load raw VS4 + base files into typed parquet, with runtime schema/gating checks.
Run: python 02_load.py   (honors GSE_MODE=smoke)

VS4 file: pipe-delimited WITH header. Base file: pipe-delimited, NO header, 113 positional fields.
loan_identifier is normalized to Int64 on BOTH sides (base is zero-padded string, VS4 is integer).
"""
import sys
import duckdb
import polars as pl
import config as C


def load_vs4_scores() -> None:
    files = list((C.RAW / "vs4_loanperf").glob("*.txt")) + list((C.RAW / "vs4_loanperf").glob("*.csv"))
    if not files:
        sys.exit("GATE FAIL: no VS4 score files in data/raw/vs4_loanperf/")
    lf = pl.scan_csv(files, separator="|", infer_schema_length=10000)
    missing = set(C.VS4_SCORE_COLUMNS) - set(lf.collect_schema().names())
    if missing:
        sys.exit(f"GATE FAIL: VS4 file missing columns {missing}")
    lf = lf.with_columns(pl.col("loan_identifier").cast(pl.Int64, strict=False))
    if C.SMOKE:
        lf = lf.filter(pl.col("acquisition_quarter") == C.SMOKE_COHORT)
    df = lf.collect()
    df.write_parquet(C.PARQUET / "vs4_scores.parquet")
    print(f"VS4 scores: {df.height:,} rows -> vs4_scores.parquet")


def load_base_perf() -> None:
    if not C.BASE_PERF_COLUMN_MAP:
        sys.exit("GATE FAIL: config.BASE_PERF_COLUMN_MAP is empty")
    files = list((C.RAW / "base_loanperf").glob("*.csv")) + list((C.RAW / "base_loanperf").glob("*.txt"))
    if not files:
        sys.exit("GATE FAIL: no base perf files in data/raw/base_loanperf/")
    con = duckdb.connect()
    glob = str(C.RAW / "base_loanperf" / "*")
    names = con.sql(
        f"SELECT * FROM read_csv('{glob}', delim='|', header=false, all_varchar=true) LIMIT 0"
    ).columns
    cols = C.BASE_PERF_COLUMN_MAP
    parts = []
    for name, idx in cols.items():
        if name == "loan_identifier":
            parts.append(f"CAST({names[idx]} AS BIGINT) AS loan_identifier")
        else:
            parts.append(f"{names[idx]} AS {name}")
    parts.append("regexp_extract(filename, '([0-9]{4}Q[0-9])', 1) AS acquisition_quarter")
    select = ", ".join(parts)
    if C.SMOKE:
        where = f"WHERE regexp_extract(filename, '([0-9]{{4}}Q[0-9])', 1) = '{C.SMOKE_COHORT}'"
    else:
        # full run: only the VS4-overlap quarters. Relies on per-quarter filenames carrying YYYYQX;
        # if base is one combined file with no quarter in the name this yields 0 rows (gate fails
        # loudly -> switch to per-quarter downloads rather than silently mis-deriving the quarter).
        where = "WHERE regexp_extract(filename, '([0-9]{4}Q[0-9])', 1) BETWEEN '2013Q2' AND '2023Q1'"
    out = str(C.PARQUET / "base_perf.parquet")
    con.sql(
        f"COPY (SELECT {select} FROM read_csv('{glob}', delim='|', header=false, "
        f"all_varchar=true, filename=true) {where}) TO '{out}' (FORMAT PARQUET)"
    )
    n = con.sql(f"SELECT count(*) FROM read_parquet('{out}')").fetchone()[0]
    print(f"Base perf: {n:,} monthly rows -> base_perf.parquet")


if __name__ == "__main__":
    load_vs4_scores()
    load_base_perf()
