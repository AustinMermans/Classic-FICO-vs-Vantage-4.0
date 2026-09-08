# Which credit score predicts mortgage defaults best?

*Classic FICO vs. VantageScore 4.0 vs. FICO Score 10T, tested on the same 24.7 million mortgages.*

[Extended report](REPORT.md) · [Chart gallery](GALLERY.md) · [Original two-score study](PART1.md)

The first version of this project had an annoying hole in the middle of it. I could test the new
VantageScore 4.0 against old Classic FICO, but the historical data for FICO's newer model—FICO
Score 10T—didn't exist yet. So the real modern-versus-modern contest had to wait.

That data arrived on July 1, 2026. I rebuilt the study with all three scores attached to the same
Fannie Mae loans, then watched what happened to each mortgage over the next three years.

**In this test, FICO 10T wins.**

A useful credit score should push the loans that later default toward the risky end of the list.
Gini measures how well it does that: zero is no better than random ordering, and higher is better.
FICO 10T scores **0.516**, ahead of VantageScore at **0.492** and Classic FICO at **0.477**.

![FICO 10T separates future defaulters best](figures/part2_gini_comparison.png)

That is not an enormous gulf, but it is not a one-off wobble. Split the loans into the 40 quarters
when Fannie acquired them and 10T finishes first in every single one. All three scores struggle
more with loans exposed to the early COVID shock, but 10T keeps its lead through that period too.

![FICO 10T leads in every acquisition quarter](figures/part2_gini_by_vintage.png)

The borrower split tells the same story. In the original study, VantageScore's advantage over
Classic FICO came almost entirely from loans with one borrower; on two-borrower loans they tied.
FICO 10T improves on both of them in both groups.

![FICO 10T leads with one borrower or two](figures/part2_borrower_split.png)

The most practical test is what happens when the models disagree. Imagine keeping the best-scoring
80% of these already-originated loans under each modern score. The two models swap about 1.3
million loans in each direction. The loans kept only by 10T default **1.56%** of the time; the loans
kept only by VantageScore default **2.06%** of the time. At the 50% mark it is **0.61% versus
0.80%**. Across selection rates from 10% to 90%, the 10T-only group defaults less every time.

![Default rate of the loans kept by only one modern score](figures/part2_approval_estuary.png)

So is FICO 10T *the* best credit score? On the question this dataset can answer, yes: it is the best
of these three at ranking 36-month default risk for mortgages Fannie Mae actually acquired.
VantageScore still beats Classic FICO overall, so the first study's case for competition survives;
the new result simply says the newer FICO model is stronger here.

There is a harder limit around “here.” These are mortgages that were originated and sold to
Fannie—not applications, denied borrowers, or the full credit market. This study cannot tell us
who gains access to a mortgage, how a lender would price it, what either model costs, or what would
happen if lenders changed behavior after adoption. It measures risk ranking, not fairness,
calibration, or business value. And the only serious stress episode in the window is COVID.

The answer, then, is clear without being universal: **FICO 10T wins this historical mortgage
bake-off.** The [extended report](REPORT.md) has the exact sample construction, metrics, robustness
checks, and limitations. The [gallery](GALLERY.md) walks through every new figure. The
[original Part 1 study](PART1.md) is preserved exactly as the question looked before 10T data
arrived.
