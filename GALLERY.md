# Part 2 chart gallery

Every chart below comes from the same 24.7 million-loan comparison. The short version is in the
[README](README.md); exact methods and numbers are in the [extended report](REPORT.md). The
[original Classic-FICO-versus-VantageScore gallery](PART1_GALLERY.md) is preserved separately.

## Who wins overall?

![Overall Gini comparison](figures/part2_gini_comparison.png)

**What it shows:** how well each score sorts future defaulters toward the risky end of the list.
Gini is 0 for a random ranking and 1 for a perfect one. FICO 10T is highest at 0.516; VantageScore
4.0 is next at 0.492; Classic FICO is 0.477.

**What to notice:** the newer models both beat Classic FICO, but 10T's gain over VantageScore is
larger than VantageScore's gain over Classic. This is a ranking result, not a claim that 10T's raw
score numbers are calibrated probabilities.

## Does the winner change from year to year?

![Gini by acquisition quarter](figures/part2_gini_by_vintage.png)

**What it shows:** the same ranking test repeated separately for each quarter in which Fannie Mae
acquired the loans.

**What to notice:** the lines move together because the economic environment changes how easy
defaults are to rank. They fall sharply for loans exposed to the early COVID shock. The green 10T
line nevertheless stays above both alternatives in all 40 quarters.

## How large is 10T's lead each quarter?

![10T edge by acquisition quarter](figures/part2_gini_edge_by_vintage.png)

**What it shows:** the previous chart with the common movement stripped away. Each point is 10T's
Gini minus the competing score's Gini for that quarter. A point above zero is a 10T win.

**What to notice:** every point is above zero. The 10T–VantageScore gap ranges from about 101 to
415 Gini basis points. This is the strongest evidence that the pooled result is not being driven by
one giant vintage.

## Does adding a second borrower change the answer?

![Gini by borrower count](figures/part2_borrower_split.png)

**What it shows:** the three-way comparison separately for loans with one borrower and two.

**What to notice:** all three models rank two-borrower loans more cleanly. VantageScore and Classic
FICO are almost tied in that group—the central finding from Part 1—but 10T is still ahead. Its lead
is therefore broader than VantageScore's original advantage over Classic.

## What happens to the loans where the modern scores disagree?

![Swing borrowers at two portfolio sizes](figures/part2_swing_matched.png)

**What it shows:** rank the same originated loans by each modern score and keep a nominal top 50%
or 80%. Then look only at the loans kept by one model but not the other. Lower default is better.

**What to notice:** the orange VantageScore-only group defaults more often at both points. At the
80% point it is 2.06%, versus 1.56% for the green 10T-only group. This is a retrospective loan
selection exercise, not a study of applicants or actual mortgage approvals.

## Is that swing-loan result just one convenient cutoff?

![Swing loans across the selection curve](figures/part2_approval_estuary.png)

**What it shows:** the previous test repeated from keeping the best-scoring 10% through 90% of the
observed loans. The shaded space is the difference in default rates between the two swap groups.

**What to notice:** the 10T-only loans have the lower default rate at every tested portfolio size.
The absolute gap gets wider as more marginal loans enter the selected group. Integer score ties
make realized portfolio shares slightly different at each nominal cutoff.

## Where do the two modern scores disagree?

![Default rate across modern-score rank groups](figures/part2_rank_disagreement.png)

**What it shows:** every loan is placed into a risk-ranked tenth under each modern model. The color
is the observed 36-month default rate for that pair of rank groups.

**What to notice:** risk is darkest in the lower-left, where both models call a loan risky, and
lightest toward the upper-right, where both call it safe. Moving vertically while holding
VantageScore's rank fixed still changes risk, and moving horizontally while holding 10T fixed does
too: the models overlap, but neither is a copy of the other. Cells with fewer than 10,000 loans are
hidden so tiny extreme-disagreement groups do not control the color scale.

## Want the original pictures?

Part 1 contains additional Classic-FICO-versus-VantageScore views, including score-band
transitions, calibration bands, loan-level COVID heatmaps, and segment cuts. They remain in the
[Part 1 gallery](PART1_GALLERY.md); this page keeps the current three-score story front and center.
