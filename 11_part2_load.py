"""Prepare the July 2026 FICO 10T and refreshed VantageScore 4.0 score files.

Examples:
  ./.venv/bin/python 11_part2_load.py \
      --fico10t ~/Downloads/FICO10T_HistoricalScores_LP.zip \
      --vs4 ~/Downloads/VantageScore4_HistoricalScores_LP.zip

ZIP inputs are extracted under data/raw/ and retained for resumable runs. Source downloads are
never moved or deleted. Pipe-delimited TXT/CSV inputs can also be supplied directly.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import config as C
from gse.scores import load_score_files, materialize_score_inputs


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fico10t", action="append", required=True, type=Path,
                        help="FICO 10T historical loan-performance ZIP/TXT (repeatable)")
    parser.add_argument("--vs4", action="append", required=True, type=Path,
                        help="July 2026 VantageScore 4.0 loan-performance ZIP/TXT (repeatable)")
    return parser


def _load(name: str, inputs: list[Path], columns: list[str]) -> None:
    raw_dir = C.PART2_SCORE_DIRS[name]
    files = materialize_score_inputs(inputs, raw_dir)
    frame = load_score_files(files, columns)
    out = C.PART2_SCORE_PARQUETS[name]
    frame.write_parquet(out)
    quarters = frame["acquisition_quarter"]
    print(
        f"{name}: {frame.height:,} rows, {quarters.min()}-{quarters.max()}, "
        f"{len(files)} source file(s) -> {out.relative_to(C.ROOT)}"
    )


def main() -> None:
    args = _parser().parse_args()
    _load("fico10t", args.fico10t, C.FICO10T_SCORE_COLUMNS)
    _load("vs4", args.vs4, C.VS4_SCORE_COLUMNS)


if __name__ == "__main__":
    main()
