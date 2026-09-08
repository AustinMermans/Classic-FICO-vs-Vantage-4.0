"""Part 2 three-way comparison: Classic FICO vs VantageScore 4.0 vs FICO Score 10T."""
from __future__ import annotations

from itertools import combinations
import os

import config as C

os.environ.setdefault("MPLCONFIGDIR", str(C.DATA / ".matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import polars as pl

from gse.metrics import auc_default, gini, ks, swing_borrowers


COLORS = {
    "Classic FICO": "#6B7280",
    "VantageScore 4.0": "#0F766E",
    "FICO Score 10T": "#C2410C",
}


def _headline_sample(raw: pl.DataFrame) -> pl.DataFrame:
    score_columns = list(C.PART2_SCORES.values())
    return raw.filter(
        pl.all_horizontal([pl.col(column).is_not_null() for column in score_columns])
        & (~pl.col("censored"))
        & (pl.col("num_borrowers") <= C.MAX_BORROWERS_FOR_COMPARISON)
    )


def discrimination(df: pl.DataFrame) -> pl.DataFrame:
    y = df["defaulted"].to_numpy()
    rows = []
    for label, column in C.PART2_SCORES.items():
        score = df[column].to_numpy()
        rows.append({"score": label, "n": df.height, "defaults": int(y.sum()),
                     "auc": auc_default(score, y), "gini": gini(score, y), "ks": ks(score, y)})
    return pl.DataFrame(rows)


def by_vintage(df: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for key, sub in df.group_by("acquisition_quarter"):
        y = sub["defaulted"].to_numpy()
        if sub.height < 500 or y.sum() < 20 or y.sum() == sub.height:
            continue
        for label, column in C.PART2_SCORES.items():
            rows.append({"vintage": key[0], "score": label, "n": sub.height,
                         "defaults": int(y.sum()), "default_rate": float(y.mean()),
                         "gini": gini(sub[column].to_numpy(), y)})
    return pl.DataFrame(rows).sort("vintage", "score")


def by_borrower_count(df: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for borrowers in (1, 2):
        sub = df.filter(pl.col("num_borrowers") == borrowers)
        y = sub["defaulted"].to_numpy()
        for label, column in C.PART2_SCORES.items():
            rows.append({"num_borrowers": borrowers, "score": label, "n": sub.height,
                         "defaults": int(y.sum()), "gini": gini(sub[column].to_numpy(), y)})
    return pl.DataFrame(rows)


def pairwise_swings(df: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for (left_label, left), (right_label, right) in combinations(C.PART2_SCORES.items(), 2):
        for rate in C.SWING_APPROVAL_RATES:
            left_cut = float(df[left].quantile(1 - rate))
            right_cut = float(df[right].quantile(1 - rate))
            result = swing_borrowers(
                df, left, right, "defaulted", fico_cut=left_cut, vs_cut=right_cut
            )
            mapping = {
                "approve_both": "approve_both",
                "decline_both": "decline_both",
                "fico_approve_vs_decline": "left_only",
                "vs_approve_fico_decline": "right_only",
            }
            for row in result.iter_rows(named=True):
                rows.append({"left_score": left_label, "right_score": right_label,
                             "approval_rate": rate, "left_cutoff": left_cut,
                             "right_cutoff": right_cut, "segment": mapping[row["segment"]],
                             "n": row["n"], "default_rate": row["default_rate"]})
    return pl.DataFrame(rows)


def correlations(df: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for (left_label, left), (right_label, right) in combinations(C.PART2_SCORES.items(), 2):
        rows.append({"left_score": left_label, "right_score": right_label,
                     "spearman": df.select(pl.corr(left, right, method="spearman")).item(),
                     "median_left_minus_right": float((df[left] - df[right]).median())})
    return pl.DataFrame(rows)


def make_charts(disc: pl.DataFrame, vintages: pl.DataFrame) -> None:
    labels = disc["score"].to_list()
    values = disc["gini"].to_list()
    fig, ax = plt.subplots(figsize=(8, 4.8))
    bars = ax.bar(labels, values, color=[COLORS[label] for label in labels])
    ax.bar_label(bars, labels=[f"{value:.3f}" for value in values], padding=3)
    ax.set_ylabel("Gini (higher is better)")
    ax.set_title("Default discrimination on the same Fannie Mae loans")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(C.OUTPUTS / "part2_gini_comparison.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    for label in C.PART2_SCORES:
        sub = vintages.filter(pl.col("score") == label).sort("vintage")
        ax.plot(sub["vintage"], sub["gini"], marker="o", markersize=3,
                linewidth=1.7, color=COLORS[label], label=label)
    ax.axhline(0, color="#9CA3AF", linewidth=0.8)
    ax.set_ylabel("Gini")
    ax.set_xlabel("Acquisition quarter")
    ax.set_title("Default discrimination by acquisition vintage")
    ax.tick_params(axis="x", rotation=90, labelsize=7)
    ax.legend(frameon=False, ncol=3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(C.OUTPUTS / "part2_gini_by_vintage.png", dpi=180)
    plt.close(fig)


def main() -> None:
    raw = pl.read_parquet(C.PARQUET / "part2_analysis_table.parquet")
    df = _headline_sample(raw)
    if df.is_empty() or df["defaulted"].sum() == 0:
        raise SystemExit("GATE FAIL: Part 2 headline sample has no usable outcomes")

    print("=== PART 2 POPULATION ===")
    print(f"joined loans: {raw.height:,}")
    print(f"triple-score, resolved, <=2 borrowers: {df.height:,}")
    print(f"defaults: {df['defaulted'].sum():,} ({df['defaulted'].mean():.2%})")

    disc = discrimination(df)
    vintages = by_vintage(df)
    borrowers = by_borrower_count(df)
    swings = pairwise_swings(df)
    corr = correlations(df)
    disc.write_csv(C.OUTPUTS / "part2_discrimination.csv")
    vintages.write_csv(C.OUTPUTS / "part2_discrimination_by_vintage.csv")
    borrowers.write_csv(C.OUTPUTS / "part2_discrimination_by_borrower_count.csv")
    swings.write_csv(C.OUTPUTS / "part2_pairwise_swings.csv")
    corr.write_csv(C.OUTPUTS / "part2_score_correlations.csv")
    make_charts(disc, vintages)

    print("\n=== DISCRIMINATION ===")
    print(disc)
    for left, right in combinations(disc.iter_rows(named=True), 2):
        print(f"{right['score']} minus {left['score']}: "
              f"{(right['gini'] - left['gini']) * 10_000:+.0f} Gini bp")
    print(f"\nWrote Part 2 tables and charts to {C.OUTPUTS}")


if __name__ == "__main__":
    main()
