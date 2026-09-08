import polars as pl
from gse.joins import join_scores_to_perf


def _scores(rows):
    return pl.DataFrame(rows, schema=["loan_identifier", "acquisition_quarter", "vs4_current_method"],
                        orient="row")


def _perf(rows):
    return pl.DataFrame(rows, schema=["loan_identifier", "acquisition_quarter", "fico"], orient="row")


def test_full_match_rate():
    scores = _scores([("1", "2020Q2", 700), ("2", "2020Q2", 720)])
    perf = _perf([("1", "2020Q2", 690), ("2", "2020Q2", 715)])
    joined, stats = join_scores_to_perf(scores, perf)
    assert stats["match_rate"] == 1.0 and stats["matched"] == 2


def test_composite_key_disambiguates_same_loan_id_across_quarters():
    # same loan_identifier "1" in two quarters must NOT cross-match
    scores = _scores([("1", "2020Q2", 700), ("1", "2020Q3", 600)])
    perf = _perf([("1", "2020Q2", 690), ("1", "2020Q3", 590)])
    joined, stats = join_scores_to_perf(scores, perf)
    q3 = joined.filter(pl.col("acquisition_quarter") == "2020Q3").to_dicts()[0]
    assert q3["vs4_current_method"] == 600   # not 700


def test_partial_match_rate_and_dup_detection():
    scores = _scores([("1", "2020Q2", 700), ("1", "2020Q2", 705)])  # duplicate key in scores
    perf = _perf([("1", "2020Q2", 690), ("2", "2020Q2", 715)])      # loan 2 has no score
    joined, stats = join_scores_to_perf(scores, perf)
    assert stats["dup_scores"] == 1
    assert stats["match_rate"] < 1.0


def test_join_supports_a_non_vantage_match_column():
    scores = pl.DataFrame({
        "loan_identifier": [1],
        "acquisition_quarter": ["2020Q2"],
        "fico_10t_current_method": [730],
    })
    perf = _perf([(1, "2020Q2", 715)])
    joined, stats = join_scores_to_perf(
        scores, perf, match_column="fico_10t_current_method"
    )
    assert stats["match_rate"] == 1.0
    assert joined["fico_10t_current_method"][0] == 730
