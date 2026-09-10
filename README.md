# Which credit score predicts mortgage defaults best?

*Classic FICO, VantageScore 4.0, and FICO Score 10T—tested on the same 24.7 million mortgages.*

[Extended report](REPORT.md) · [Chart gallery](GALLERY.md) · [Original two-score study](PART1.md)

## The short answer

**FICO Score 10T wins this test.** It does the best job of moving the loans that later defaulted
toward the risky end of the list. VantageScore 4.0 finishes second, and Classic FICO finishes
third.

The test is deliberately simple. Give each score the same Fannie Mae loans, sort them from
riskiest to safest, and follow every loan for three years. A better score should find more future
defaults near the risky end—and leave fewer of them in an equally large safe portfolio.

## How much better is the ranking?

Start with the riskiest 10% under each model: exactly **2,469,707 loans per list**.

- FICO 10T finds **104,879** future defaults, or **36%** of all defaults in the sample.
- VantageScore finds **99,241**, or **34%**.
- Classic FICO finds **91,279**, or **32%**.

![Share of future defaults found as each model moves down its risk list](figures/part2_default_capture.png)

That is the central result in plain English. When all three models are allowed to flag the same
number of loans, 10T puts more of the eventual trouble in the group it calls risky. Because these
scores are whole numbers, ties at an exact boundary are broken consistently with the loan ID; the
technical checks in the report handle tied scores directly.

## What if the goal is to keep the safer loans?

Turn the ranking around and keep the safest 80% under each score. Every portfolio now contains
exactly **19,757,657 loans**.

- The 10T portfolio contains **128,122** loans that later default.
- The VantageScore portfolio contains **134,695**.
- The Classic FICO portfolio contains **140,395**.

So 10T includes **6,573 fewer future defaults than VantageScore** and **12,273 fewer than Classic
FICO**, without changing the portfolio size.

![Future defaults in equally large portfolios](figures/part2_same_size_portfolios.png)

## Is that just a cutoff trick?

No. At the 80% portfolio size, 10T and VantageScore agree on most loans but swap **1,302,705** in
each direction. Among the VantageScore-only loans, **26,631** later default. Among the equally
large 10T-only group, **20,058** default. The entire 6,573-loan difference comes from the loans on
which the two models disagree.

![Defaults among equal-size groups where the modern models disagree](figures/part2_exact_swaps.png)

The same swap pattern appears at the 50% portfolio size and across every tested selection point
from 10% to 90%. In separate ranking checks, 10T also leads in every acquisition quarter and for
both one- and two-borrower loans.

## What this says—and what it does not

The result is strong but specific: **among these three scores, FICO 10T produced the best
36-month default ranking for mortgages Fannie Mae acquired from 2013Q2 through 2023Q1.**
VantageScore still improves on Classic FICO overall, so the original study's case for a credible
alternative to the legacy score remains intact.

The data show *how* 10T wins: it concentrates more defaults at the risky end and leaves fewer in
same-size safe portfolios. They cannot reveal *which proprietary ingredient* causes the lead.
Both modern scores use trended credit data, but their internal model weights are not public.

This is also not a study of mortgage applications. Every loan here was already originated and
acquired by Fannie Mae. The results do not measure approvals, pricing, fairness, model cost, or
performance in other credit markets.

For the full sample design, technical metrics, robustness checks, and limitations, see the
[extended report](REPORT.md). For a quick tour of every chart, open the [gallery](GALLERY.md).
