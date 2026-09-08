"""Load and validate Fannie Mae historical credit-score files."""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import zipfile

import polars as pl


def materialize_score_inputs(
    inputs: Iterable[str | Path], destination: Path, *, member_hint: str | None = None
) -> list[Path]:
    """Return readable text/CSV score files, extracting ZIP inputs without deleting their sources."""
    destination.mkdir(parents=True, exist_ok=True)
    materialized: list[Path] = []
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        if path.suffix.lower() != ".zip":
            materialized.append(path)
            continue

        with zipfile.ZipFile(path) as archive:
            members = [
                name for name in archive.namelist()
                if not name.endswith("/") and Path(name).suffix.lower() in {".txt", ".csv"}
            ]
            if member_hint:
                members = [name for name in members if member_hint.lower() in name.lower()]
            if len(members) != 1:
                raise ValueError(
                    f"Expected one score text file in {path.name}; found {len(members)}: {members}"
                )
            member = members[0]
            target = destination / Path(member).name
            if not target.exists() or target.stat().st_size != archive.getinfo(member).file_size:
                with archive.open(member) as source, target.open("wb") as output:
                    while chunk := source.read(16 * 1024 * 1024):
                        output.write(chunk)
            materialized.append(target)
    return materialized


def load_score_files(files: Iterable[str | Path], required_columns: list[str]) -> pl.DataFrame:
    """Read pipe-delimited historical-score files and enforce schema, type, and key uniqueness."""
    paths = [Path(path) for path in files]
    if not paths:
        raise ValueError("No historical score files supplied")

    frame = pl.scan_csv(paths, separator="|", infer_schema_length=10_000)
    names = frame.collect_schema().names()
    missing = sorted(set(required_columns) - set(names))
    if missing:
        raise ValueError(f"Historical score file missing columns: {missing}")

    score_columns = [name for name in required_columns if name not in {
        "loan_identifier", "acquisition_quarter"
    }]
    result = (
        frame.select(required_columns)
        .with_columns(
            pl.col("loan_identifier").cast(pl.Int64, strict=False),
            pl.col("acquisition_quarter").cast(pl.Utf8),
            *[pl.col(name).cast(pl.Float64, strict=False) for name in score_columns],
        )
        .collect(engine="streaming")
    )
    null_keys = result.filter(
        pl.col("loan_identifier").is_null() | pl.col("acquisition_quarter").is_null()
    ).height
    if null_keys:
        raise ValueError(f"Historical score file contains {null_keys:,} null/invalid join keys")
    duplicate_groups = (
        result.group_by("loan_identifier", "acquisition_quarter")
        .len()
        .filter(pl.col("len") > 1)
        .height
    )
    if duplicate_groups:
        raise ValueError(f"Historical score file contains {duplicate_groups:,} duplicate key groups")
    return result
