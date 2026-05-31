import numpy as np
import polars as pl
from gse.metrics import (auc_default, gini, ks, score_band, transition_matrix,
                         calibration_table, swing_borrowers)


def test_perfect_inverse_score_gives_auc_one():
    # low scores -> default, high -> no default; perfect ordering
    score = np.array([600, 650, 700, 750, 800], float)
    default = np.array([1, 1, 0, 0, 0], int)
    assert auc_default(score, default) == 1.0
    assert gini(score, default) == 1.0


def test_ks_perfect_separation_is_one():
    score = np.array([600, 620, 700, 760, 800], float)
    default = np.array([1, 1, 0, 0, 0], int)
    assert abs(ks(score, default) - 1.0) < 1e-9


def test_symmetric_default_auc_half():
    # defaulters straddle the non-defaulters symmetrically -> no discrimination (AUC 0.5)
    score = np.array([600, 650, 700, 750], float)
    default = np.array([1, 0, 0, 1], int)
    assert abs(auc_default(score, default) - 0.5) < 1e-9


def test_nan_scores_are_dropped():
    score = np.array([600, np.nan, 700, 800], float)
    default = np.array([1, 1, 0, 0], int)
    # dropping the nan leaves a perfectly separating set
    assert auc_default(score, default) == 1.0


def test_score_band_labels():
    s = pl.Series([610, 650, 705, 800])
    bands = score_band(s, [300, 620, 660, 700, 740, 780, 851])
    assert bands.to_list() == ["[300,620)", "[620,660)", "[700,740)", "[780,851)"]


def test_transition_matrix_counts():
    df = pl.DataFrame({"fico_band": ["A", "A", "B"], "vs_band": ["A", "B", "B"]})
    tm = transition_matrix(df, "fico_band", "vs_band")
    cell = tm.filter((pl.col("fico_band") == "A") & (pl.col("vs_band") == "B"))["n"][0]
    assert cell == 1


def test_calibration_default_rate_per_band():
    df = pl.DataFrame({"band": ["A", "A", "B", "B"], "defaulted": [True, False, True, True]})
    cal = calibration_table(df, "band", "defaulted").sort("band")
    assert cal.filter(pl.col("band") == "A")["default_rate"][0] == 0.5
    assert cal.filter(pl.col("band") == "B")["default_rate"][0] == 1.0


def test_swing_borrowers_segments():
    # fico_cut=700, vs_cut=700. One loan approved by VS only, defaults.
    df = pl.DataFrame({
        "fico": [680, 720, 690, 710],
        "vs":   [710, 720, 680, 705],
        "defaulted": [True, False, False, False],
    })
    seg = swing_borrowers(df, "fico", "vs", "defaulted", fico_cut=700, vs_cut=700)
    vs_only = seg.filter(pl.col("segment") == "vs_approve_fico_decline")
    assert vs_only["n"][0] == 1 and vs_only["default_rate"][0] == 1.0
