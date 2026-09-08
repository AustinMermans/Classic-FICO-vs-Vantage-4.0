import polars as pl

import config as C


def test_part2_headline_window_uses_literal_quarter_bounds():
    frame = pl.DataFrame({"acquisition_quarter": ["2013Q1", "2013Q2", "2023Q1", "2023Q2"]})
    result = frame.filter(
        pl.col("acquisition_quarter").is_between(
            pl.lit(C.PART2_HEADLINE_START), pl.lit(C.PART2_HEADLINE_END), closed="both"
        )
    )
    assert result["acquisition_quarter"].to_list() == ["2013Q2", "2023Q1"]
