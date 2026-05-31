import polars as pl
from gse.labels import derive_default_labels


def _panel(rows):
    # rows: (loan_key, loan_age, dlq_months, zero_balance_code)
    return pl.DataFrame(rows, schema=["loan_key", "loan_age", "dlq_months", "zero_balance_code"],
                        orient="row")


def test_default_by_delinquency():
    # loan reaches 6 months DLQ within window -> defaulted
    df = _panel([("A", 1, 0, None), ("A", 12, 6, None)])
    out = derive_default_labels(df, window_months=36).sort("loan_key")
    row = out.filter(pl.col("loan_key") == "A").to_dicts()[0]
    assert row["defaulted"] is True and row["event_age"] == 12 and row["censored"] is False


def test_default_by_zero_balance_code():
    # ZB 09 (REO/deed-in-lieu) is a credit event even if DLQ never crosses threshold
    df = _panel([("B", 1, 0, None), ("B", 20, 3, "09")])
    row = derive_default_labels(df, window_months=36).to_dicts()[0]
    assert row["defaulted"] is True and row["event_age"] == 20


def test_prepay_is_not_default():
    # ZB 01 (voluntary prepay) is a competing risk, not a default
    df = _panel([("C", 1, 0, None), ("C", 18, 0, "01")])
    row = derive_default_labels(df, window_months=36).to_dicts()[0]
    assert row["defaulted"] is False and row["prepaid"] is True and row["censored"] is False


def test_clean_performer_full_window_is_not_censored():
    df = _panel([("D", 1, 0, None), ("D", 36, 0, None)])
    row = derive_default_labels(df, window_months=36).to_dicts()[0]
    assert row["defaulted"] is False and row["censored"] is False


def test_short_seasoning_is_censored():
    # only 10 months observed, window 36, no event -> censored (insufficient seasoning)
    df = _panel([("E", 1, 0, None), ("E", 10, 1, None)])
    row = derive_default_labels(df, window_months=36).to_dicts()[0]
    assert row["defaulted"] is False and row["censored"] is True


def test_event_after_window_is_ignored():
    # DLQ 6 only at age 40, window 36 -> not counted as default within window
    df = _panel([("F", 1, 0, None), ("F", 40, 6, None)])
    row = derive_default_labels(df, window_months=36).to_dicts()[0]
    assert row["defaulted"] is False
