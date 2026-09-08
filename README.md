# Does a newer credit score predict mortgage defaults better than FICO?

> **2026 update:** Fannie Mae released historical FICO Score 10T data on July 1, 2026.
> The completed three-way follow-up—Classic FICO vs. VantageScore 4.0 vs. FICO 10T—is in
> **[Part 2](PART2.md)**. FICO 10T leads both alternatives on the same 24.7 million loans. The
> original study below is preserved as Part 1.

For two decades, getting a Fannie Mae or Freddie Mac mortgage meant being graded by one company: FICO. No rival was allowed, and in the last few years FICO raised the price of its mortgage score sharply, because lenders had nowhere else to go. Regulators have now approved a competitor, VantageScore 4.0, and in July 2024 the data to test it went public for the first time. So I ran the test.

I took 24.7 million mortgages Fannie Mae bought between 2013 and 2023. Each one carries both a Classic FICO score and a VantageScore 4.0, and each has a resolved default outcome. The question is simple: which score better predicts who defaults?

To compare them, rank borrowers by each score and see where the defaulters land. A score that works puts them near the bottom. I measured that overall, then split the loans by the year they were made and by number of borrowers.

Across the whole set, VantageScore comes out a little ahead of Classic FICO. But that lead depends on the year the loan was made. In years with few defaults, VantageScore sorted risk better; in the high-default years the two were even. Those high-default loans were mostly made between 2018 and early 2020, and 93% of their defaults landed in 2020 and 2021. When the pandemic hit, defaults jumped across every score level at once, so where a borrower ranked mattered less. Read it as a COVID-period result; the data don't show how the scores hold up in other downturns.

![How well each score sorts risk, by loan year](figures/gini_by_vintage.png)

Split the loans by how many people are on them, and almost all of VantageScore's edge comes from single-borrower loans. On two-borrower loans the scores tie, and both do better than they do on solo borrowers.

![Single-borrower vs two-borrower loans](figures/borrower_split.png)

The two scores often disagree about the same person, and when they do, the default outcome tracks VantageScore a bit more than FICO. The sharpest example: borrowers FICO rates top-tier but VantageScore flags as risky default about five times as often as borrowers both scores rate highly.

![Where the defaults are when the scores disagree](figures/disagreement_resolution.png)

Say a lender ranked these same loans by each score and kept the best-scoring share. The two scores pick slightly different loans, and at every cutoff the ones only VantageScore keeps default less than the ones only FICO keeps. At a four-in-five rate it's 1.7% versus 2.0%; tighten the cutoff and the gap widens.

![Default rate of the loans only one score keeps, at every cutoff](figures/approval_estuary.png)

What this Part 1 comparison didn't settle: the FICO here is Classic FICO, the old model. FICO 10T is the real head-to-head, and its historical data was released in July 2026. **[Part 2 runs that comparison](PART2.md)** and finds 10T ahead of both VantageScore 4.0 and Classic FICO. These are still only the loans Fannie actually bought, so they say nothing about borrowers turned down before a loan existed, or about pricing, or about how lenders would really use the scores. And the only stretch of real stress in the data is COVID, so that part of the result rests on a single episode.

On the loans I can see, VantageScore 4.0 is about as good as Classic FICO, and a bit better in the cases above. That weakens the claim that FICO can't be replaced, but it doesn't make VantageScore the clear winner: the edge is small, and whether it shows up at all depends on which borrowers and which years you look at.

Numbers, methods, and code are in [REPORT.md](REPORT.md). More charts are in [GALLERY.md](GALLERY.md).
