"""Join VS4 historical scores onto base per-loan records on the composite key, with QA stats."""
import polars as pl
from config import JOIN_KEYS, SCORE_VARIANT


def join_scores_to_perf(
    scores: pl.DataFrame,
    perf_loans: pl.DataFrame,
    *,
    keys: list[str] | None = None,
    match_column: str = SCORE_VARIANT,
) -> tuple[pl.DataFrame, dict]:
    """Left-join scores onto one-row-per-loan base records on the composite key.

    Returns (joined, stats). stats: perf_rows, matched, match_rate, dup_scores, dup_perf.
    dup_* count key groups appearing more than once on each side (a silent-misjoin tripwire).
    perf_loans MUST already be collapsed to one row per (loan_identifier, acquisition_quarter).
    """
    keys = keys or JOIN_KEYS
    dup_scores = scores.group_by(keys).len().filter(pl.col("len") > 1).height
    dup_perf = perf_loans.group_by(keys).len().filter(pl.col("len") > 1).height

    joined = perf_loans.join(scores.unique(subset=keys, keep="first"), on=keys, how="left")
    if match_column not in scores.columns:
        raise ValueError(f"match_column {match_column!r} is absent from score file")
    matched = joined.filter(pl.col(match_column).is_not_null()).height
    stats = {
        "perf_rows": perf_loans.height,
        "matched": matched,
        "match_rate": matched / max(perf_loans.height, 1),
        "dup_scores": dup_scores,
        "dup_perf": dup_perf,
    }
    return joined, stats
