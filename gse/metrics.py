"""Discrimination + comparison metrics for credit scores vs a binary default label."""
import numpy as np
import polars as pl
from sklearn.metrics import roc_auc_score


def _clean(score, default):
    score = np.asarray(score, dtype=float)
    default = np.asarray(default, dtype=int)
    mask = ~np.isnan(score)
    return score[mask], default[mask]


def auc_default(score, default) -> float:
    """AUC of using a credit score to predict DEFAULT. Higher score = lower risk, so default is
    predicted with -score. 1.0 = perfect (low scorers default); 0.5 = no discrimination."""
    score, default = _clean(score, default)
    return float(roc_auc_score(default, -score))


def gini(score, default) -> float:
    """Gini = 2*AUC - 1."""
    return 2.0 * auc_default(score, default) - 1.0


def ks(score, default) -> float:
    """Kolmogorov-Smirnov: max gap between cumulative default vs non-default distributions over score."""
    score, default = _clean(score, default)
    order = np.argsort(score, kind="mergesort")
    d = default[order]
    n_bad = int(d.sum())
    n_good = len(d) - n_bad
    cum_bad = np.cumsum(d) / max(n_bad, 1)
    cum_good = np.cumsum(1 - d) / max(n_good, 1)
    return float(np.max(np.abs(cum_bad - cum_good)))


def score_band(values: pl.Series, edges: list[int]) -> pl.Series:
    """Bucket scores into half-open [lo,hi) bands labelled '[lo,hi)'. Out-of-range -> null.

    Uses numpy.digitize on the interior edges for a version-robust, vectorized bucketing.
    """
    labels = [f"[{edges[i]},{edges[i+1]})" for i in range(len(edges) - 1)]
    v = values.cast(pl.Float64).to_numpy()
    interior = edges[1:-1]
    idx = np.digitize(v, interior, right=False)   # 0..len(labels)-1 across the full range
    lo, hi = edges[0], edges[-1]
    out = [
        labels[i] if (not np.isnan(x)) and (lo <= x < hi) and (0 <= i < len(labels)) else None
        for x, i in zip(v, idx)
    ]
    return pl.Series(out, dtype=pl.Utf8)


def transition_matrix(df: pl.DataFrame, fico_band_col: str, vs_band_col: str) -> pl.DataFrame:
    """Counts per (fico_band, vs_band) cell."""
    return (
        df.group_by([fico_band_col, vs_band_col])
        .len()
        .rename({"len": "n"})
        .sort([fico_band_col, vs_band_col])
    )


def calibration_table(df: pl.DataFrame, band_col: str, default_col: str) -> pl.DataFrame:
    """Observed default rate and count per band."""
    return (
        df.group_by(band_col)
        .agg(pl.col(default_col).mean().alias("default_rate"), pl.len().alias("n"))
        .sort(band_col)
    )


def swing_borrowers(
    df: pl.DataFrame, fico_col: str, vs_col: str, default_col: str, *, fico_cut: float, vs_cut: float
) -> pl.DataFrame:
    """Segment loans by approve/decline under each score at the given cutoffs; report n + default rate.

    Approve = score >= cutoff. Segments: approve_both, decline_both, fico_approve_vs_decline,
    vs_approve_fico_decline. The last two are the swing borrowers the FICO-moat question turns on.
    """
    seg = (
        df.with_columns(
            (pl.col(fico_col) >= fico_cut).alias("_fico_ok"),
            (pl.col(vs_col) >= vs_cut).alias("_vs_ok"),
        )
        .with_columns(
            pl.when(pl.col("_fico_ok") & pl.col("_vs_ok")).then(pl.lit("approve_both"))
            .when(~pl.col("_fico_ok") & ~pl.col("_vs_ok")).then(pl.lit("decline_both"))
            .when(pl.col("_fico_ok") & ~pl.col("_vs_ok")).then(pl.lit("fico_approve_vs_decline"))
            .otherwise(pl.lit("vs_approve_fico_decline"))
            .alias("segment")
        )
    )
    return (
        seg.group_by("segment")
        .agg(pl.len().alias("n"), pl.col(default_col).mean().alias("default_rate"))
        .sort("segment")
    )
