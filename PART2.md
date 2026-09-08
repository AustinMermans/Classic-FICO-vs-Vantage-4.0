# Part 2 — Classic FICO vs. VantageScore 4.0 vs. FICO Score 10T

## Why this follow-up exists

The original project could only compare VantageScore 4.0 with Classic FICO. On July 1, 2026,
Fannie Mae published historical FICO Score 10T data and a refreshed VantageScore 4.0 file covering
the same 27.5 million loans in its Historical Loan Performance Dataset. That release makes the
modern head-to-head test possible for the first time.

This follow-up preserves Part 1 and asks a cleaner question: **on the same Fannie-acquired loans,
with the same outcome window and the same borrower-aggregation method, which of Classic FICO,
VantageScore 4.0, and FICO Score 10T best ranks mortgage default risk?**

> **Run status:** the code and schema checks are complete. Headline results will be inserted here
> after the two registered full score files finish downloading and the full loan panel runs.

## Design locked before looking at the result

- **Population:** Fannie Mae Historical Loan Performance loans acquired from 2013Q2 through
  2023Q1, the original common window with sufficiently mature 36-month outcomes.
- **Outcome:** default within 36 months, defined as 180+ days delinquent or a credit-event
  zero-balance code (`02`, `03`, `09`, or `15`). Voluntary prepayment is a known non-default;
  active loans without a complete window are censored and excluded.
- **Score fields:** `fico` from the performance file, `vs4_current_method`, and
  `fico_10t_current_method`. The two new-model fields both select the middle of three (or lower of
  two) bureau scores for each borrower, then the lowest borrower score for the loan.
- **Comparator discipline:** loans with more than two borrowers are excluded because the public
  Classic FICO fields contain only borrower and co-borrower scores, while the new-model loan score
  can reflect up to four borrowers.
- **Metrics:** AUC, Gini, KS, acquisition-vintage Gini, borrower-count splits, rank correlation, and
  pairwise swing-borrower default rates at matched approval volumes.
- **No immature-vintage headline:** the July 2026 score files extend through 2025Q3, but those
  loans cannot yet supply a 36-month default outcome. They are not mixed into the headline result.

## Important identification limit

The Classic FICO value comes from the loan's actual origination disclosure. The historical FICO
10T and VantageScore 4.0 values were reconstructed from archived bureau data at a specified point
in the relevant month, which may not be the exact day the lender pulled the original credit report.
That makes the 10T-vs.-Vantage comparison more temporally aligned than either new model's
comparison with Classic FICO. The report will treat this as a design limitation, not bury it.

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
  --fico10t ~/Downloads/FICO10T_HistoricalScores_LP.zip \
  --vs4 ~/Downloads/VantageScore4_HistoricalScores_LP.zip

./.venv/bin/python 12_part2_join.py
./.venv/bin/python 13_part2_compare.py
```

The outputs land in `data/outputs/`:

- `part2_discrimination.csv`
- `part2_discrimination_by_vintage.csv`
- `part2_discrimination_by_borrower_count.csv`
- `part2_pairwise_swings.csv`
- `part2_score_correlations.csv`
- `part2_gini_comparison.png`
- `part2_gini_by_vintage.png`

## Sources

- [Fannie Mae — Historical Credit Score Files](https://historicalcreditscores.fanniemae.com/)
- [Fannie Mae — Single-Family Loan Performance Data](https://capitalmarkets.fanniemae.com/credit-risk-transfer/single-family-credit-risk-transfer/fannie-mae-single-family-loan-performance-data)
- [FHFA — Credit Scores](https://www.fhfa.gov/policy/credit-scores)
