"""Join VS4 scores onto the labeled one-row-per-loan table; enforce the match-rate gate.
Run: python 03_join.py
"""
import sys
import polars as pl
import config as C
from gse.joins import join_scores_to_perf

scores = pl.read_parquet(C.PARQUET / "vs4_scores.parquet").with_columns(
    [pl.col(c).cast(pl.Float64, strict=False) for c in C.VS4_SCORE_COLUMNS if c.startswith("vs4_")]
)
loans = pl.read_parquet(C.PARQUET / "loans_labeled.parquet")
joined, stats = join_scores_to_perf(scores, loans)
print("JOIN STATS:", stats)
if stats["dup_perf"] > 0:
    sys.exit(f"GATE FAIL: base side not unique per key (dup_perf={stats['dup_perf']})")
if stats["dup_scores"] > 0:
    sys.exit(f"GATE FAIL: VS4 scores not unique per key (dup_scores={stats['dup_scores']}) — "
             f"join_scores_to_perf() would silently keep='first'; investigate before trusting the match.")
if stats["match_rate"] < C.MIN_MATCH_RATE:
    sys.exit(f"GATE FAIL: match_rate {stats['match_rate']:.3f} < {C.MIN_MATCH_RATE} — LOOP BACK, "
             f"re-examine the join key / cohort coverage before proceeding")
joined.write_parquet(C.PARQUET / "analysis_table.parquet")
print(f"analysis_table: {joined.height:,} loans with both scores + label")
