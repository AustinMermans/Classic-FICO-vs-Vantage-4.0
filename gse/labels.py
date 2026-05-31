"""Collapse a monthly loan-performance panel to one default label per loan."""
import polars as pl
from config import DLQ_THRESHOLD_MONTHS, DEFAULT_ZB_CODES, PREPAY_ZB_CODES


def derive_default_labels(
    perf: pl.DataFrame,
    *,
    dlq_threshold_months: int = DLQ_THRESHOLD_MONTHS,
    default_zb_codes=DEFAULT_ZB_CODES,
    prepay_zb_codes=PREPAY_ZB_CODES,
    window_months: int | None = None,
) -> pl.DataFrame:
    """One row per loan_key with: defaulted, event_age, prepaid, censored, max_age, max_dlq.

    Required input columns: loan_key, loan_age (int months), dlq_months (int, 0=current, may be
    null), zero_balance_code (str, null while active). A loan defaults if, within the window, it
    ever reaches dlq_months >= threshold OR carries a zero_balance_code in default_zb_codes.
    Voluntary prepay (code in prepay_zb_codes) is a competing risk, not a default. A non-defaulted,
    non-prepaid loan with fewer than window_months observed is censored (insufficient seasoning).
    """
    df = perf
    if window_months is not None:
        df = df.filter(pl.col("loan_age") <= window_months)

    default_list = list(default_zb_codes)
    prepay_list = list(prepay_zb_codes)

    agg = df.group_by("loan_key").agg(
        pl.col("dlq_months").max().alias("max_dlq"),
        pl.col("loan_age").max().alias("max_age"),
        pl.col("loan_age").filter(pl.col("dlq_months") >= dlq_threshold_months).min().alias("dlq_event_age"),
        pl.col("loan_age").filter(pl.col("zero_balance_code").is_in(default_list)).min().alias("zb_event_age"),
        pl.col("zero_balance_code").is_in(default_list).any().alias("zb_default"),
        pl.col("zero_balance_code").is_in(prepay_list).any().alias("prepaid"),
    )

    agg = agg.with_columns(
        ((pl.col("max_dlq") >= dlq_threshold_months) | pl.col("zb_default").fill_null(False)).alias("defaulted"),
        pl.min_horizontal("dlq_event_age", "zb_event_age").alias("event_age"),
        pl.col("prepaid").fill_null(False).alias("prepaid"),
    )

    if window_months is not None:
        censored_expr = (~pl.col("defaulted")) & (~pl.col("prepaid")) & (pl.col("max_age") < window_months)
    else:
        censored_expr = (~pl.col("defaulted")) & (~pl.col("prepaid"))

    return agg.with_columns(censored_expr.alias("censored")).select(
        "loan_key", "defaulted", "event_age", "prepaid", "censored", "max_age", "max_dlq"
    )
