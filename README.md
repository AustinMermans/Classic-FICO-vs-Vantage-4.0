# Does a newer credit score predict mortgage defaults better than FICO?

For two decades, getting a Fannie Mae or Freddie Mac mortgage meant being graded by one company: FICO. No rival was allowed, and in the last few years FICO raised the price of its mortgage score sharply, because lenders had nowhere else to go. Regulators have now approved a competitor, VantageScore 4.0, and in July 2024 the data to test it went public for the first time. So I ran the test.

I took 25 million mortgages Fannie Mae bought between 2013 and 2023. Each one carries both a Classic FICO score and a VantageScore 4.0, and I know which ones defaulted. The question is simple: which score better predicts who will?

To compare them, rank borrowers by each score and see where the defaulters land. A score that works puts them near the bottom. I measured that overall, then split the loans by the year they were made and by number of borrowers.

Across the whole set, VantageScore comes out a little ahead of Classic FICO. But that lead depends on the year the loan was made. In years with few defaults, VantageScore sorted risk better; in the high-default years the two were even. Those high-default years were 2018 and 2019, and 93% of the defaults on those loans landed in 2020 and 2021. When the pandemic hit, defaults jumped across every score level at once, so where a borrower ranked mattered less. Read it as a COVID-period result; the data don't show how the scores hold up in other downturns.

![How well each score sorts risk, by loan year](figures/gini_by_vintage.png)
![When the high-default loans defaulted](figures/covid_timing.png)

Split the loans by how many people are on them, and almost all of VantageScore's edge comes from single-borrower loans. On two-borrower loans the scores tie, and both do better than they do on solo borrowers.

![Single-borrower vs two-borrower loans](figures/borrower_split.png)

The two scores often disagree about the same person, and when they do, the default outcome tracks VantageScore a bit more than FICO. The sharpest example: borrowers FICO rates top-tier but VantageScore flags as risky default about five times as often as borrowers both scores rate highly.

![Where the defaults are when the scores disagree](figures/disagreement_resolution.png)

One more. Say a lender approved the same share of applicants under each score. They'd let in slightly different people, and the ones only VantageScore approves default less than the ones only FICO approves: 1.7% versus 2.0%.

![Borrowers each score uniquely approves](figures/swing_matched.png)

What this doesn't settle: the FICO here is Classic FICO, the old model. FICO's current one, 10T, is the real head-to-head, and that data isn't out until summer 2026. These are also only the loans Fannie actually bought, so it says nothing about applicants turned down before a loan existed, or about pricing, or about how lenders would really use the scores. And the one rough patch in the data is COVID.

On the loans I can see, VantageScore 4.0 is about as good as Classic FICO, and a bit better in the cases above. It dents the idea that FICO can't be replaced. It doesn't crown the new score either. Its edge is small, and whether it shows up depends on which borrowers and which years you look at.

Numbers, methods, and code are in [REPORT.md](REPORT.md). More charts are in [GALLERY.md](GALLERY.md).
