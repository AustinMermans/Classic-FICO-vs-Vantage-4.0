"""Join Classic FICO, refreshed VantageScore 4.0, and FICO 10T on the same Fannie loans."""
from __future__ import annotations

import sys

import polars as pl

import config as C
from gse.joins import join_scores_to_perf


def _join_and_gate(
    loans: pl.DataFrame, scores: pl.DataFrame, *, name: str, match_column: str
) -> pl.DataFrame:
    joined, stats = join_scores_to_perf(scores, loans, match_column=match_column)
    print(f"{name} JOIN STATS: {stats}")
    if stats["dup_perf"] or stats["dup_scores"]:
        sys.exit(f"GATE FAIL: {name} join keys are not unique: {stats}")
    if stats["match_rate"] < C.MIN_MATCH_RATE:
        sys.exit(
            f"GATE FAIL: {name} match rate {stats['match_rate']:.3%} < {C.MIN_MATCH_RATE:.0%}"
        )
    return joined


def main() -> None:
    loans = pl.read_parquet(C.PARQUET / "loans_labeled.parquet").filter(
        pl.col("acquisition_quarter").is_between(
            pl.lit(C.PART2_HEADLINE_START), pl.lit(C.PART2_HEADLINE_END), closed="both"
        )
    )
    vs4 = pl.read_parquet(C.PART2_SCORE_PARQUETS["vs4"])
    fico10t = pl.read_parquet(C.PART2_SCORE_PARQUETS["fico10t"])

    joined = _join_and_gate(
        loans, vs4, name="VantageScore 4.0", match_column="vs4_current_method"
    )
    joined = _join_and_gate(
        joined, fico10t, name="FICO Score 10T", match_column="fico_10t_current_method"
    )
    out = C.PARQUET / "part2_analysis_table.parquet"
    triple = joined.select(
        pl.all_horizontal([pl.col(column).is_not_null() for column in C.PART2_SCORES.values()])
        .sum()
    ).item()
    triple_rate = triple / max(joined.height, 1)
    if triple_rate < C.MIN_MATCH_RATE:
        sys.exit(
            f"GATE FAIL: all-three-score coverage {triple_rate:.3%} < {C.MIN_MATCH_RATE:.0%}"
        )
    joined.write_parquet(out)
    print(f"Part 2 table: {joined.height:,} loans; {triple:,} have all three scores -> {out}")


if __name__ == "__main__":
    main()
