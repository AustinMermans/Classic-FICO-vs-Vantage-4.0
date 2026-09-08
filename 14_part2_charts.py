"""Publication charts for the 2026 three-score follow-up.

Run after ``13_part2_compare.py``. Regenerates the public Part 2 figures in
``figures/`` and writes the full approval-curve data to ``data/outputs/``.
"""
from __future__ import annotations

import os

import numpy as np
import polars as pl

import config as C

os.environ.setdefault("MPLCONFIGDIR", str(C.DATA / ".matplotlib"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


COLORS = {
    "Classic FICO": "#1F77B4",
    "VantageScore 4.0": "#FF7F0E",
    "FICO Score 10T": "#2CA02C",
}
PUBLIC_FIGURES = C.ROOT / "figures"
PUBLIC_FIGURES.mkdir(exist_ok=True)


def _finish(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(PUBLIC_FIGURES / name, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def headline_chart() -> None:
    data = pl.read_csv(C.OUTPUTS / "part2_discrimination.csv")
    labels = data["score"].to_list()
    values = data["gini"].to_list()
    fig, ax = plt.subplots(figsize=(8.5, 5.1))
    bars = ax.bar(labels, values, color=[COLORS[label] for label in labels], width=0.72)
    ax.bar_label(bars, labels=[f"{value:.3f}" for value in values], padding=5, fontsize=12)
    ax.set_ylim(0, 0.57)
    ax.set_ylabel("Gini — higher means better risk ranking")
    ax.set_title(
        "FICO 10T separates future defaulters best", loc="left", weight="bold", pad=28
    )
    ax.text(
        0,
        1.01,
        "Same 24.7 million loans · 10T: +241 Gini bp vs VantageScore, +389 vs Classic",
        transform=ax.transAxes,
        color="#4B5563",
        fontsize=10,
    )
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", alpha=0.18)
    _finish(fig, "part2_gini_comparison.png")


def vintage_chart() -> None:
    data = pl.read_csv(C.OUTPUTS / "part2_discrimination_by_vintage.csv")
    fig, ax = plt.subplots(figsize=(12, 6.2))
    for label in COLORS:
        sub = data.filter(pl.col("score") == label).sort("vintage")
        ax.plot(
            sub["vintage"],
            sub["gini"],
            marker="o",
            markersize=3.2,
            linewidth=2,
            color=COLORS[label],
            label=label,
        )
    ax.set_ylabel("Gini")
    ax.set_xlabel("Quarter Fannie Mae acquired the loan")
    ax.set_title(
        "10T leads in every acquisition quarter", loc="left", weight="bold", pad=28
    )
    ax.text(
        0,
        1.01,
        "All scores weaken for loans exposed to the early COVID shock, but 10T stays ahead",
        transform=ax.transAxes,
        color="#4B5563",
        fontsize=10,
    )
    ax.tick_params(axis="x", rotation=90, labelsize=7)
    ax.legend(frameon=False, ncol=3, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.18)
    _finish(fig, "part2_gini_by_vintage.png")


def vintage_edge_chart() -> None:
    data = (
        pl.read_csv(C.OUTPUTS / "part2_discrimination_by_vintage.csv")
        .pivot(index="vintage", on="score", values="gini")
        .sort("vintage")
        .with_columns(
            ((pl.col("FICO Score 10T") - pl.col("VantageScore 4.0")) * 10_000)
            .alias("vs_vantage"),
            ((pl.col("FICO Score 10T") - pl.col("Classic FICO")) * 10_000)
            .alias("vs_classic"),
        )
    )
    fig, ax = plt.subplots(figsize=(12, 5.8))
    ax.axhline(0, color="#111827", linewidth=1)
    ax.plot(
        data["vintage"], data["vs_classic"], color=COLORS["Classic FICO"],
        marker="o", markersize=3, linewidth=1.8, label="10T advantage over Classic FICO",
    )
    ax.plot(
        data["vintage"], data["vs_vantage"], color=COLORS["VantageScore 4.0"],
        marker="o", markersize=3, linewidth=1.8, label="10T advantage over VantageScore 4.0",
    )
    ax.fill_between(
        np.arange(data.height), 0, data["vs_vantage"].to_numpy(),
        color=COLORS["VantageScore 4.0"], alpha=0.10,
    )
    ax.set_ylabel("10T Gini advantage (basis points)")
    ax.set_xlabel("Acquisition quarter")
    ax.set_title("The size of 10T's lead changes; its direction does not", loc="left", weight="bold")
    ax.tick_params(axis="x", rotation=90, labelsize=7)
    ax.legend(frameon=False, ncol=2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.18)
    _finish(fig, "part2_gini_edge_by_vintage.png")


def borrower_chart() -> None:
    data = pl.read_csv(C.OUTPUTS / "part2_discrimination_by_borrower_count.csv")
    x = np.arange(2)
    width = 0.24
    fig, ax = plt.subplots(figsize=(8.7, 5.4))
    for index, label in enumerate(COLORS):
        sub = data.filter(pl.col("score") == label).sort("num_borrowers")
        bars = ax.bar(
            x + (index - 1) * width,
            sub["gini"],
            width,
            label=label,
            color=COLORS[label],
        )
        ax.bar_label(bars, labels=[f"{v:.3f}" for v in sub["gini"]], padding=3, fontsize=9)
    ax.set_xticks(x, ["One borrower\n13.0M loans", "Two borrowers\n11.7M loans"])
    ax.set_ylim(0, 0.65)
    ax.set_ylabel("Gini")
    ax.set_title(
        "10T's lead holds with one borrower or two", loc="left", weight="bold", pad=28
    )
    ax.text(
        0,
        1.01,
        "The VantageScore–Classic tie on two-borrower loans does not extend to 10T",
        transform=ax.transAxes,
        color="#4B5563",
        fontsize=10,
    )
    ax.legend(frameon=False, ncol=3, loc="upper left")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", alpha=0.18)
    _finish(fig, "part2_borrower_split.png")


def matched_swing_chart() -> None:
    data = pl.read_csv(C.OUTPUTS / "part2_pairwise_swings.csv").filter(
        (pl.col("left_score") == "VantageScore 4.0")
        & (pl.col("right_score") == "FICO Score 10T")
        & pl.col("segment").is_in(["left_only", "right_only"])
    )
    x = np.arange(2)
    width = 0.34
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    for offset, segment, label, color in [
        (-width / 2, "left_only", "VantageScore-only", COLORS["VantageScore 4.0"]),
        (width / 2, "right_only", "FICO 10T-only", COLORS["FICO Score 10T"]),
    ]:
        sub = data.filter(pl.col("segment") == segment).sort("approval_rate")
        values = sub["default_rate"].to_numpy() * 100
        bars = ax.bar(x + offset, values, width, color=color, label=label)
        ax.bar_label(bars, labels=[f"{value:.2f}%" for value in values], padding=3, fontsize=10)
    ax.set_xticks(x, ["Keep top 50%", "Keep top 80%"])
    ax.set_ylabel("Default rate of loans only that model keeps")
    ax.set_title(
        "When the models swap loans, 10T picks the safer group",
        loc="left",
        weight="bold",
        pad=28,
    )
    ax.text(
        0,
        1.01,
        "Retrospective matched-selection exercise; lower is better",
        transform=ax.transAxes,
        color="#4B5563",
        fontsize=10,
    )
    ax.yaxis.set_major_formatter(PercentFormatter())
    ax.legend(frameon=False)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", alpha=0.18)
    _finish(fig, "part2_swing_matched.png")


def _analysis_arrays() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    columns = ["vs4_current_method", "fico_10t_current_method", "defaulted"]
    data = (
        pl.scan_parquet(C.PARQUET / "part2_analysis_table.parquet")
        .filter(
            pl.all_horizontal([pl.col(column).is_not_null() for column in C.PART2_SCORES.values()])
            & (~pl.col("censored"))
            & (pl.col("num_borrowers") <= C.MAX_BORROWERS_FOR_COMPARISON)
        )
        .select(columns)
        .collect(engine="streaming")
    )
    return (
        data["vs4_current_method"].to_numpy(),
        data["fico_10t_current_method"].to_numpy(),
        data["defaulted"].to_numpy().astype(bool),
    )


def approval_estuary(vantage: np.ndarray, ten_t: np.ndarray, default: np.ndarray) -> None:
    rows = []
    for rate in np.arange(0.10, 0.91, 0.05):
        vantage_cutoff = float(np.quantile(vantage, 1 - rate))
        ten_t_cutoff = float(np.quantile(ten_t, 1 - rate))
        vantage_ok = vantage >= vantage_cutoff
        ten_t_ok = ten_t >= ten_t_cutoff
        vantage_only = vantage_ok & ~ten_t_ok
        ten_t_only = ten_t_ok & ~vantage_ok
        rows.append(
            {
                "approval_rate": float(rate),
                "vantage_cutoff": vantage_cutoff,
                "fico_10t_cutoff": ten_t_cutoff,
                "vantage_only_n": int(vantage_only.sum()),
                "fico_10t_only_n": int(ten_t_only.sum()),
                "vantage_only_default_rate": float(default[vantage_only].mean()),
                "fico_10t_only_default_rate": float(default[ten_t_only].mean()),
            }
        )
    data = pl.DataFrame(rows)
    data.write_csv(C.OUTPUTS / "part2_approval_estuary.csv")

    x = data["approval_rate"].to_numpy() * 100
    vantage_rate = data["vantage_only_default_rate"].to_numpy() * 100
    ten_t_rate = data["fico_10t_only_default_rate"].to_numpy() * 100
    fig, ax = plt.subplots(figsize=(9.7, 5.8))
    ax.plot(x, vantage_rate, color=COLORS["VantageScore 4.0"], linewidth=2.5,
            marker="o", markersize=4, label="VantageScore-only loans")
    ax.plot(x, ten_t_rate, color=COLORS["FICO Score 10T"], linewidth=2.5,
            marker="o", markersize=4, label="FICO 10T-only loans")
    ax.fill_between(x, ten_t_rate, vantage_rate, color="#F59E0B", alpha=0.16)
    ax.set_xlabel("Share of loans kept by each model")
    ax.set_ylabel("Default rate of the swing loans")
    ax.set_title(
        "10T picks safer swing loans across the selection curve",
        loc="left",
        weight="bold",
        pad=28,
    )
    ax.text(
        0,
        1.01,
        "At each cutoff, compare loans kept by only one of the two modern scores",
        transform=ax.transAxes,
        color="#4B5563",
        fontsize=10,
    )
    ax.xaxis.set_major_formatter(PercentFormatter())
    ax.yaxis.set_major_formatter(PercentFormatter())
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.18)
    _finish(fig, "part2_approval_estuary.png")


def rank_disagreement_heatmap(
    vantage: np.ndarray, ten_t: np.ndarray, default: np.ndarray
) -> None:
    probabilities = np.arange(0.1, 1.0, 0.1)
    vantage_edges = np.quantile(vantage, probabilities)
    ten_t_edges = np.quantile(ten_t, probabilities)
    vantage_decile = np.searchsorted(vantage_edges, vantage, side="right")
    ten_t_decile = np.searchsorted(ten_t_edges, ten_t, side="right")
    cell = ten_t_decile * 10 + vantage_decile
    counts = np.bincount(cell, minlength=100).reshape(10, 10)
    defaults = np.bincount(cell, weights=default.astype(float), minlength=100).reshape(10, 10)
    raw_rates = np.divide(
        defaults, counts, out=np.full((10, 10), np.nan), where=counts > 0
    )
    rates = raw_rates * 100
    minimum_cell_n = 10_000
    rates[counts < minimum_cell_n] = np.nan
    pl.DataFrame(
        {
            "fico_10t_rank_group": np.repeat(np.arange(1, 11), 10),
            "vantage_rank_group": np.tile(np.arange(1, 11), 10),
            "n": counts.ravel(),
            "default_rate": raw_rates.ravel(),
        }
    ).write_csv(C.OUTPUTS / "part2_rank_disagreement.csv")

    fig, ax = plt.subplots(figsize=(8.7, 7.4))
    image = ax.imshow(rates, origin="lower", cmap="YlOrRd", aspect="equal")
    ax.set_xticks(range(10), [str(i) for i in range(1, 11)])
    ax.set_yticks(range(10), [str(i) for i in range(1, 11)])
    ax.set_xlabel("VantageScore rank group (1 = riskiest, 10 = safest)")
    ax.set_ylabel("FICO 10T rank group (1 = riskiest, 10 = safest)")
    ax.set_title(
        "Default risk follows both scores—and exposes their disagreements",
        loc="left",
        weight="bold",
        pad=28,
    )
    ax.text(
        0,
        1.01,
        "Observed default rate by score decile · cells with fewer than 10,000 loans hidden",
        transform=ax.transAxes,
        color="#4B5563",
        fontsize=10,
    )
    bar = fig.colorbar(image, ax=ax, fraction=0.047, pad=0.04)
    bar.set_label("Default rate (%)")
    _finish(fig, "part2_rank_disagreement.png")


def main() -> None:
    headline_chart()
    vintage_chart()
    vintage_edge_chart()
    borrower_chart()
    matched_swing_chart()
    vantage, ten_t, default = _analysis_arrays()
    approval_estuary(vantage, ten_t, default)
    rank_disagreement_heatmap(vantage, ten_t, default)
    print("Wrote seven Part 2 charts to figures/ and approval-curve data to data/outputs/")


if __name__ == "__main__":
    main()
