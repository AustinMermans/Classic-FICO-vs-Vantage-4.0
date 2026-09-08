# Part 2 — Classic FICO vs. VantageScore 4.0 vs. FICO Score 10T

## Result

**FICO Score 10T ranks mortgage default risk best in this historical Fannie Mae sample.** On
24,702,598 loans with all three scores and a resolved 36-month outcome, 10T records a Gini of
**0.515**, ahead of VantageScore 4.0 at **0.492** and Classic FICO at **0.478**. Its advantage over
VantageScore is 229 Gini basis points; its advantage over Classic FICO is 377.

| Score | AUC | Gini | KS | Gini vs. Classic |
|---|---:|---:|---:|---:|
| Classic FICO | 0.7388 | 0.4775 | 0.3628 | — |
| VantageScore 4.0 | 0.7462 | 0.4923 | 0.3676 | +148 bp |
| **FICO Score 10T** | **0.7576** | **0.5153** | **0.3892** | **+377 bp** |

These are ranking metrics, not default probabilities. Higher is better. All three scores are
evaluated on exactly the same loans and outcomes.

![Default discrimination for all three scores](figures/part2_gini_comparison.png)

## What changed since Part 1

The original project could only compare VantageScore 4.0 with Classic FICO. On July 1, 2026,
Fannie Mae published historical FICO Score 10T data and a refreshed VantageScore 4.0 file. Each
score file contains 27,513,197 loans, covering acquisitions from 2013Q2 through 2025Q3. This makes
the modern-model head-to-head test possible for the first time.

The comparison retains the original mature outcome window, 2013Q2–2023Q1. The July 2026 score
files match 25,081,806 of the 25,087,678 loans in that panel (99.9766%) for each modern score;
25,075,933 loans have all three scores before outcome and borrower-count filters. The final sample
contains 288,057 defaults, a 1.17% default rate.

## The result is broad, not driven by one vintage

FICO 10T leads VantageScore 4.0 in **all 40 acquisition quarters**. The quarterly advantage ranges
from 90 to 394 Gini basis points and averages 230 basis points. It also leads Classic FICO in all
40 quarters. VantageScore, by contrast, leads Classic FICO in 35 of 40 quarters.

All three models lose discrimination for loans acquired just before and during the first part of
the COVID shock. FICO 10T's lead survives that shared deterioration; the result is not coming only
from quiet, low-default vintages.

![Default discrimination by acquisition quarter](figures/part2_gini_by_vintage.png)

## One borrower and two borrowers

10T also leads within both borrower-count groups:

| Borrowers | Loans | Defaults | Classic FICO Gini | VantageScore 4.0 Gini | FICO 10T Gini |
|---:|---:|---:|---:|---:|---:|
| 1 | 12,993,362 | 198,815 | 0.4439 | 0.4636 | **0.4908** |
| 2 | 11,709,236 | 89,242 | 0.5602 | 0.5604 | **0.5822** |

The original VantageScore edge over Classic FICO was almost entirely a single-borrower result.
FICO 10T improves on both models for solo borrowers and maintains a clear edge when there are two.

## When the modern models disagree

Ranking by each model and accepting the top 80% produces somewhat different marginal loans. The
loans selected only by FICO 10T default **1.57%** of the time, compared with **2.06%** for those
selected only by VantageScore 4.0—a 24.0% relative reduction. At the top-50% cutoff, the equivalent
rates are **0.62%** and **0.80%**, a 22.5% relative reduction.

The same exercise against Classic FICO is stronger: at the top-80% cutoff, 10T-only loans default
1.49% versus 2.32% for Classic-only loans. These are retrospective portfolio swaps, not causal
estimates of what a lender's approval policy would do. Integer score ties also make realized
selection counts slightly different around each nominal cutoff.

The models are related but far from interchangeable. Spearman rank correlation is 0.851 between
10T and VantageScore 4.0, 0.832 between 10T and Classic FICO, and 0.755 between VantageScore and
Classic. Their raw score levels should not be compared as if the same number represented the same
risk.

## Design

- **Population:** Fannie Mae Historical Loan Performance loans acquired from 2013Q2 through
  2023Q1, the original common window with sufficiently mature 36-month outcomes.
- **Outcome:** default within 36 months, defined as 180+ days delinquent or a credit-event
  zero-balance code (`02`, `03`, `09`, or `15`). Voluntary prepayment is a known non-default;
  active loans without a complete window are censored and excluded.
- **Score fields:** `fico` from the performance file, `vs4_current_method`, and
  `fico_10t_current_method`.
- **Borrower aggregation:** the two modern fields select the middle of three (or lower of two)
  bureau scores for each borrower, then the lowest borrower score for the loan.
- **Comparator discipline:** loans with more than two borrowers are excluded because the public
  Classic FICO fields contain only borrower and co-borrower scores, while the modern-model loan
  score can reflect up to four borrowers.
- **Metrics:** AUC, Gini, KS, acquisition-vintage Gini, borrower-count splits, rank correlation,
  and pairwise swing-loan default rates at matched nominal selection shares.
- **No immature-vintage headline:** the score files extend through 2025Q3, but those loans cannot
  yet supply a complete 36-month outcome. They are not mixed into the result.

## What this does not establish

The cleanest result is **10T versus VantageScore 4.0**, because Fannie constructed those two scores
from the same archived bureau data using the same borrower-aggregation method. Classic FICO is
less perfectly aligned: it is the score disclosed at origination, while the modern scores were
reconstructed from archived bureau data at the relevant monthly snapshot. A changed credit file
or pull date can therefore affect either modern-versus-Classic comparison.

This is also a selected mortgage population: loans Fannie Mae actually acquired. It contains no
denied applicants and cannot identify changes in credit access, pricing, lender behavior, or
adverse selection. Default is one 36-month performance definition, and COVID is the only severe
stress episode in the sample. Finally, the results measure rank ordering, not calibration or the
business value of adopting one model.

The defensible conclusion is therefore narrow but clear: **among these already-originated Fannie
Mae loans, FICO Score 10T provides the strongest retrospective ranking of 36-month default risk,
and its lead over VantageScore 4.0 is consistent across every acquisition quarter observed.**

## Reproduce Part 2

The full files are free but require Fannie Mae registration and acceptance of its data terms.
Download **FICO Score 10T Historical Scores for Historical Loan Performance Dataset** and the
updated **VantageScore 4.0 Historical Scores for Historical Loan Performance Dataset** from
[Fannie Mae's Historical Credit Score Files](https://historicalcreditscores.fanniemae.com/).

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

# Builds/resumes the one-row-per-loan outcome table from ~/Downloads/Performance_All.zip.
./.venv/bin/python run_full.py --labels-only

# Accepts ZIP or extracted TXT/CSV files; source downloads are never moved or deleted.
./.venv/bin/python 11_part2_load.py \
  --fico10t ~/Downloads/FICO10T_HistoricalScores_LoanPerformance_25.zip \
  --vs4 ~/Downloads/VantageScore4_HistoricalScores_LoanPerformance_25.zip

./.venv/bin/python 12_part2_join.py
./.venv/bin/python 13_part2_compare.py
```

The reproducible tables and full-resolution charts land in `data/outputs/`. Large raw and derived
data remain untracked by design.

## Sources

- [Fannie Mae — Historical Credit Score Files](https://historicalcreditscores.fanniemae.com/)
- [Fannie Mae — Single-Family Loan Performance Data](https://capitalmarkets.fanniemae.com/credit-risk-transfer/single-family-credit-risk-transfer/fannie-mae-single-family-loan-performance-data)
- [FHFA — Credit Scores](https://www.fhfa.gov/policy/credit-scores)
