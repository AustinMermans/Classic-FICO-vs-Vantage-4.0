from pathlib import Path
import zipfile

import polars as pl
import pytest

from gse.scores import load_score_files, materialize_score_inputs


COLUMNS = [
    "acquisition_quarter", "loan_identifier", "fico_10t_current_method",
    "fico_10t_trimerge", "fico_10t_bimerge_lowest", "fico_10t_bimerge_median",
    "fico_10t_bimerge_highest",
]
HEADER = "|".join(COLUMNS)


def test_load_score_files_normalizes_keys_and_scores(tmp_path: Path):
    source = tmp_path / "scores.txt"
    source.write_text(HEADER + "\n2020Q2|000000000123|700|701|699|701|703\n")
    result = load_score_files([source], COLUMNS)
    assert result.schema["loan_identifier"] == pl.Int64
    assert result.schema["fico_10t_current_method"] == pl.Float64
    assert result.row(0, named=True)["loan_identifier"] == 123


def test_load_score_files_rejects_duplicate_composite_keys(tmp_path: Path):
    source = tmp_path / "scores.txt"
    row = "2020Q2|123|700|701|699|701|703\n"
    source.write_text(HEADER + "\n" + row + row)
    with pytest.raises(ValueError, match="duplicate key groups"):
        load_score_files([source], COLUMNS)


def test_materialize_zip_extracts_single_score_member(tmp_path: Path):
    archive = tmp_path / "scores.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("nested/scores.txt", HEADER + "\n")
    files = materialize_score_inputs([archive], tmp_path / "raw")
    assert len(files) == 1
    assert files[0].read_text() == HEADER + "\n"
