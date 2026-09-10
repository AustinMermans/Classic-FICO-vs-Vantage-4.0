"""Publication charts for the 2026 three-score follow-up.

Run after ``13_part2_compare.py``. Regenerates the public Part 2 figures in
``figures/`` and writes their supporting tables to ``data/outputs/``.
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


def _analysis_arrays() -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    columns = ["loan_identifier", *C.PART2_SCORES.values(), "defaulted"]
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
    scores = {label: data[column].to_numpy() for label, column in C.PART2_SCORES.items()}
    return scores, data["loan_identifier"].to_numpy(), data["defaulted"].to_numpy().astype(bool)


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


def exact_rank_evidence(
    scores: dict[str, np.ndarray], loan_ids: np.ndarray, default: np.ndarray
) -> None:
    """Build exact-size rankings so score ties cannot change the number of loans compared."""
    n = len(default)
    total_defaults = int(default.sum())
    capture_rows: list[dict] = []
    decile_rows: list[dict] = []
    portfolio_rows: list[dict] = []
    orders: dict[str, np.ndarray] = {}

    for label, score in scores.items():
        order = np.lexsort((loan_ids, score))  # low score (highest modeled risk) first
        orders[label] = order
        ranked_default = default[order]
        cumulative_defaults = np.cumsum(ranked_default, dtype=np.int64)

        for share in np.arange(0.10, 1.01, 0.10):
            count = min(round(n * share), n)
            defaults_found = int(cumulative_defaults[count - 1])
            capture_rows.append(
                {
                    "score": label,
                    "riskiest_share": float(share),
                    "loans": count,
                    "defaults_found": defaults_found,
                    "share_of_all_defaults": defaults_found / total_defaults,
                }
            )

        for decile in range(1, 11):
            start = round(n * (decile - 1) / 10)
            stop = round(n * decile / 10)
            segment = ranked_default[start:stop]
            decile_rows.append(
                {
                    "score": label,
                    "risk_decile": decile,
                    "loans": len(segment),
                    "defaults": int(segment.sum()),
                    "defaults_per_1000": float(segment.mean() * 1_000),
                }
            )

        for keep_share in (0.50, 0.80):
            count = round(n * keep_share)
            selected = ranked_default[n - count:]
            selected_defaults = int(selected.sum())
            portfolio_rows.append(
                {
                    "score": label,
                    "share_kept": keep_share,
                    "loans_kept": count,
                    "defaults_included": selected_defaults,
                    "defaults_per_100000_loans": selected_defaults / count * 100_000,
                }
            )

    capture = pl.DataFrame(capture_rows)
    deciles = pl.DataFrame(decile_rows)
    portfolios = pl.DataFrame(portfolio_rows)
    capture.write_csv(C.OUTPUTS / "part2_default_capture.csv")
    deciles.write_csv(C.OUTPUTS / "part2_defaults_by_risk_decile.csv")
    portfolios.write_csv(C.OUTPUTS / "part2_exact_size_portfolios.csv")

    _default_capture_chart(capture)
    _risk_decile_chart(deciles)
    _same_size_portfolio_chart(portfolios)
    _exact_swap_table(orders, default)


def _default_capture_chart(data: pl.DataFrame) -> None:
    ten_t_10 = data.filter(
        (pl.col("score") == "FICO Score 10T") & (pl.col("riskiest_share") == 0.10)
    )["share_of_all_defaults"].item()
    fig, ax = plt.subplots(figsize=(9.2, 5.7))
    for label in COLORS:
        sub = data.filter(pl.col("score") == label).sort("riskiest_share")
        ax.plot(
            sub["riskiest_share"].to_numpy() * 100,
            sub["share_of_all_defaults"].to_numpy() * 100,
            color=COLORS[label],
            marker="o",
            linewidth=2.4,
            markersize=4.5,
            label=label,
        )
    ax.plot([0, 100], [0, 100], color="#9CA3AF", linewidth=1.2, linestyle="--", label="Random order")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Share of loans, starting with those each model calls riskiest")
    ax.set_ylabel("Share of all future defaults found")
    ax.set_title(
        f"10T puts {ten_t_10:.0%} of all defaults in its riskiest 10% of loans",
        loc="left",
        weight="bold",
        pad=28,
    )
    ax.text(
        0,
        1.01,
        "A better ranking finds more of the eventual defaults sooner",
        transform=ax.transAxes,
        color="#4B5563",
        fontsize=10,
    )
    ax.xaxis.set_major_formatter(PercentFormatter())
    ax.yaxis.set_major_formatter(PercentFormatter())
    ax.legend(frameon=False, ncol=2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.18)
    _finish(fig, "part2_default_capture.png")


def _risk_decile_chart(data: pl.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    for label in COLORS:
        sub = data.filter(pl.col("score") == label).sort("risk_decile")
        ax.plot(
            sub["risk_decile"],
            sub["defaults_per_1000"],
            color=COLORS[label],
            marker="o",
            linewidth=2.4,
            markersize=5,
            label=label,
        )
    ax.set_xticks(range(1, 11), ["Riskiest\n10%"] + [str(i) for i in range(2, 10)] + ["Safest\n10%"])
    ax.set_xlabel("Ten equal-size groups under each score")
    ax.set_ylabel("Loans that defaulted per 1,000")
    ax.set_title("10T separates the risky end from the safe end most clearly", loc="left", weight="bold", pad=28)
    ax.text(
        0,
        1.01,
        "Each point represents about 2.47 million loans",
        transform=ax.transAxes,
        color="#4B5563",
        fontsize=10,
    )
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.18)
    _finish(fig, "part2_defaults_by_risk_decile.png")


def _same_size_portfolio_chart(data: pl.DataFrame) -> None:
    x = np.arange(2)
    width = 0.24
    fig, ax = plt.subplots(figsize=(9.2, 5.7))
    for index, label in enumerate(COLORS):
        sub = data.filter(pl.col("score") == label).sort("share_kept")
        values = sub["defaults_included"].to_numpy()
        bars = ax.bar(x + (index - 1) * width, values, width, color=COLORS[label], label=label)
        ax.bar_label(bars, labels=[f"{value:,}" for value in values], padding=3, fontsize=9)
    loan_counts = (
        data.filter(pl.col("score") == "Classic FICO")
        .sort("share_kept")["loans_kept"]
        .to_list()
    )
    ax.set_xticks(
        x,
        [
            f"Keep safest 50%\n{loan_counts[0]:,} loans each",
            f"Keep safest 80%\n{loan_counts[1]:,} loans each",
        ],
    )
    ax.set_ylabel("Loans that later defaulted")
    ax.set_title("At the same portfolio size, 10T includes fewer future defaults", loc="left", weight="bold", pad=28)
    ax.text(
        0,
        1.01,
        "Within each portfolio size, every bar contains exactly the same number of loans",
        transform=ax.transAxes,
        color="#4B5563",
        fontsize=10,
    )
    ax.legend(frameon=False, ncol=3)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", alpha=0.18)
    _finish(fig, "part2_same_size_portfolios.png")


def _exact_swap_table(orders: dict[str, np.ndarray], default: np.ndarray) -> None:
    n = len(default)
    rows = []
    for keep_share in (0.50, 0.80):
        count = round(n * keep_share)
        vantage_selected = np.zeros(n, dtype=bool)
        ten_t_selected = np.zeros(n, dtype=bool)
        vantage_selected[orders["VantageScore 4.0"][n - count:]] = True
        ten_t_selected[orders["FICO Score 10T"][n - count:]] = True
        vantage_only = vantage_selected & ~ten_t_selected
        ten_t_only = ten_t_selected & ~vantage_selected
        rows.append(
            {
                "share_kept": keep_share,
                "loans_swapped_each_way": int(vantage_only.sum()),
                "vantage_only_defaults": int(default[vantage_only].sum()),
                "fico_10t_only_defaults": int(default[ten_t_only].sum()),
                "fewer_defaults_in_10t_only_group": int(
                    default[vantage_only].sum() - default[ten_t_only].sum()
                ),
            }
        )
    data = pl.DataFrame(rows)
    data.write_csv(C.OUTPUTS / "part2_exact_size_swaps.csv")

    x = np.arange(2)
    width = 0.34
    fig, ax = plt.subplots(figsize=(9.2, 5.7))
    for offset, column, label, color in [
        (-width / 2, "vantage_only_defaults", "VantageScore-only loans", COLORS["VantageScore 4.0"]),
        (width / 2, "fico_10t_only_defaults", "FICO 10T-only loans", COLORS["FICO Score 10T"]),
    ]:
        values = data[column].to_numpy()
        bars = ax.bar(x + offset, values, width, color=color, label=label)
        ax.bar_label(bars, labels=[f"{value:,}" for value in values], padding=3, fontsize=10)
    swap_counts = data["loans_swapped_each_way"].to_list()
    ax.set_xticks(
        x,
        [
            f"Keep safest 50%\n{swap_counts[0]:,} loans swap each way",
            f"Keep safest 80%\n{swap_counts[1]:,} loans swap each way",
        ],
    )
    ax.set_ylabel("Loans that later defaulted")
    ax.set_title(
        "When the models swap the same number of loans, 10T's group defaults less",
        loc="left",
        weight="bold",
        pad=28,
    )
    ax.text(
        0,
        1.01,
        "Compare only the loans selected by one modern score but not the other",
        transform=ax.transAxes,
        color="#4B5563",
        fontsize=10,
    )
    ax.legend(frameon=False)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", alpha=0.18)
    _finish(fig, "part2_exact_swaps.png")


def main() -> None:
    headline_chart()
    vintage_chart()
    vintage_edge_chart()
    borrower_chart()
    matched_swing_chart()
    scores, loan_ids, default = _analysis_arrays()
    approval_estuary(scores["VantageScore 4.0"], scores["FICO Score 10T"], default)
    rank_disagreement_heatmap(scores["VantageScore 4.0"], scores["FICO Score 10T"], default)
    exact_rank_evidence(scores, loan_ids, default)
    print("Wrote eleven Part 2 charts to figures/ and supporting tables to data/outputs/")


if __name__ == "__main__":
    main()
