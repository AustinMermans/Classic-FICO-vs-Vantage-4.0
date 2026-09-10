# Classic FICO vs. VantageScore 4.0 vs. FICO Score 10T

*A loan-level comparison on 24.7 million Fannie Mae mortgages*

> The [README](README.md) gives the quick answer. This report covers the design, exact results,
> technical checks, and limits. The [gallery](GALLERY.md) explains every figure.

## Abstract

Fannie Mae's 2026 historical score release makes a direct three-way test possible. This study
attaches Classic FICO, VantageScore 4.0, and FICO Score 10T to the same **24,697,071** mortgages,
then checks which score best ranks default during the following 36 months.

The result is consistent across several views:

- In each model's riskiest 10%—exactly 2,469,707 loans—10T finds **104,879** future defaults,
  versus **99,241** for VantageScore and **91,279** for Classic FICO.
- In equally large portfolios containing the safest 80% of loans, the 10T portfolio includes
  **128,122** future defaults, versus **134,695** under VantageScore and **140,395** under Classic.
- At that 80% mark, VantageScore and 10T swap 1,302,705 loans in each direction. The 10T-only
  group contains **6,573 fewer** future defaults.
- Standard ranking metrics agree: 10T has the highest Gini, AUC, and KS. It also leads in all 40
  acquisition-quarter comparisons and in both borrower-count groups.

The conclusion is narrow by design: **FICO Score 10T ranks 36-month default risk best among these
three scores for the Fannie-acquired mortgages studied.** This is not a test of approvals,
pricing, fairness, model cost, or the full consumer-credit market.

## 1. The question

Part 1 compared VantageScore 4.0 with the legacy Classic FICO score found in Fannie Mae's loan
data. VantageScore finished ahead overall, but the historical data needed to include FICO's newer
10T model did not yet exist.

Fannie Mae released historical FICO Score 10T data and refreshed VantageScore 4.0 data on July 1,
2026. The new files allow the more useful comparison: on the same mortgages, observed for the
same length of time, which score puts future defaults closest to the risky end of its ranking?

## 2. Data and design

### 2.1 Sample

The loan and outcome data come from Fannie Mae's Single-Family Historical Loan Performance
Dataset. The modern-score files join to that dataset on `loan_identifier + acquisition_quarter`.
The study keeps the mature 2013Q2–2023Q1 acquisition window so every included loan can have a
resolved 36-month outcome.

| Sample step | Loans |
|---|---:|
| Loan-performance panel, 2013Q2–2023Q1 | 25,087,678 |
| Valid VantageScore 4.0 current-method score | 25,081,806 |
| Valid FICO 10T current-method score | 25,071,037 |
| All three scores present, before outcome and borrower filters | 25,070,283 |
| Final resolved outcome, no more than two borrowers | **24,697,071** |

The final sample contains **287,830 defaults**.

### 2.2 Outcome

**Default within 36 months** means that a loan reaches 180 days delinquent or reports a
credit-event zero-balance code (`02`, `03`, `09`, or `15`) during the window. A voluntary
prepayment remains a known non-default. An active loan without enough observed history is
censored and excluded rather than labeled good.

### 2.3 Scores

- **Classic FICO:** the representative origination score in the loan-performance disclosure,
  using the lower available borrower/co-borrower score.
- **VantageScore 4.0:** `vs4_current_method`.
- **FICO Score 10T:** `fico_10t_current_method`.

For the modern scores, Fannie's current method takes the middle of three or lower of two bureau
scores for each borrower, then the lowest borrower score on the loan. Loans with more than two
borrowers are excluded because the public Classic FICO fields cover only a borrower and
co-borrower.

Fannie uses **9999** to mean that FICO 10T could not be calculated. The loader converts that value,
and any score outside the documented 300–850 range, to missing before the comparison. There are
14,029 such current-method records in the full 10T file; 5,527 would otherwise enter the headline
sample.

### 2.4 Plain-English tests

Each score ranks the same loans from riskiest to safest. The analysis then asks:

1. How many eventual defaults appear in the riskiest part of the list?
2. How many eventual defaults remain when an equally large safest portfolio is kept?
3. When 10T and VantageScore disagree, which model's equal-size group performs better?

Integer scores create ties. Exact-size comparisons break ties deterministically with the loan
identifier so every model contributes precisely the same number of loans. The standard metrics
later in the report handle ties directly and provide a separate check on the result.

## 3. Results readers can see directly

### 3.1 The riskiest 10% contains more of the future defaults under 10T

| Score | Loans in riskiest 10% | Future defaults found | Share of all defaults |
|---|---:|---:|---:|
| Classic FICO | 2,469,707 | 91,279 | 31.7% |
| VantageScore 4.0 | 2,469,707 | 99,241 | 34.5% |
| **FICO Score 10T** | **2,469,707** | **104,879** | **36.4%** |

![Share of defaults found while moving down each risk list](figures/part2_default_capture.png)

At the same 10% capacity, 10T finds 5,638 more defaults than VantageScore and 13,600 more than
Classic FICO. The lead continues beyond one cutoff: within the riskiest 20%, 10T finds 55.5% of
all defaults, versus 53.2% for VantageScore and 51.2% for Classic.

### 3.2 An equally large safe portfolio contains fewer future defaults under 10T

| Portfolio | Loans kept under each score | Classic defaults | VantageScore defaults | 10T defaults |
|---|---:|---:|---:|---:|
| Safest 50% | 12,348,536 | 48,410 | 47,765 | **44,498** |
| Safest 80% | 19,757,657 | 140,395 | 134,695 | **128,122** |

![Future defaults in equally large portfolios](figures/part2_same_size_portfolios.png)

At the 80% size, the 10T portfolio includes 6,573 fewer future defaults than the VantageScore
portfolio and 12,273 fewer than the Classic portfolio. Portfolio size is held fixed; only the
ranking changes.

### 3.3 The difference comes from the loans on which the models disagree

| Portfolio | Loans swapped each way | Defaults in VantageScore-only group | Defaults in 10T-only group | Fewer in 10T group |
|---|---:|---:|---:|---:|
| Safest 50% | 1,843,179 | 14,575 | **11,308** | **3,267** |
| Safest 80% | 1,302,705 | 26,631 | **20,058** | **6,573** |

![Future defaults in equal-size groups selected by only one modern model](figures/part2_exact_swaps.png)

This is an exact comparison. At the 80% point, the two portfolios share the same core and exchange
1,302,705 loans in each direction. The loans unique to 10T default less often, producing the
entire difference between the two same-size portfolios.

### 3.4 The separation is visible from the risky end to the safe end

Divide each ranking into ten equally large groups. In the riskiest group, 10T records **42.5
defaults per 1,000 loans**, compared with 40.2 under VantageScore and 37.0 under Classic. In the
safest group, 10T falls to **1.8 per 1,000**, compared with 1.9 and 2.1.

![Defaults per 1,000 loans in equal-size risk groups](figures/part2_defaults_by_risk_decile.png)

A useful ranking creates this spread: more of the bad outcomes at the risky end and fewer at the
safe end. This chart shows why the portfolio counts above move in 10T's favor.

## 4. Technical and robustness checks

### 4.1 Standard ranking metrics agree

| Score | Loans | Defaults | AUC | Gini | KS |
|---|---:|---:|---:|---:|---:|
| Classic FICO | 24,697,071 | 287,830 | 0.7387 | 0.4774 | 0.3628 |
| VantageScore 4.0 | 24,697,071 | 287,830 | 0.7461 | 0.4922 | 0.3675 |
| **FICO Score 10T** | **24,697,071** | **287,830** | **0.7582** | **0.5163** | **0.3897** |

![Overall Gini comparison](figures/part2_gini_comparison.png)

Gini, AUC, and KS all summarize how clearly a score separates defaulters from non-defaulters.
They are useful compact checks, but they are not needed to interpret the loan and default counts
in Section 3. AUC and Gini are the same ranking statistic on different scales, so they should not
be read as two independent tests.

### 4.2 The result holds across time

FICO 10T leads VantageScore in all **40 acquisition quarters**. Its quarterly Gini advantage
ranges from 101 to 415 basis points. It also leads Classic FICO in all 40 quarters, while
VantageScore leads Classic in 35 of 40.

![Ranking performance by acquisition quarter](figures/part2_gini_by_vintage.png)

All three lines fall for loans exposed to the early COVID shock. Defaults became harder to rank,
but the order of the models did not change. COVID is still one unusual episode, not proof about
every future downturn.

![10T's technical edge by acquisition quarter](figures/part2_gini_edge_by_vintage.png)

### 4.3 The result holds for one- and two-borrower loans

| Borrowers | Loans | Defaults | Classic FICO Gini | VantageScore Gini | 10T Gini |
|---:|---:|---:|---:|---:|---:|
| 1 | 12,988,302 | 198,595 | 0.4438 | 0.4635 | **0.4923** |
| 2 | 11,708,769 | 89,235 | 0.5602 | 0.5604 | **0.5823** |

![Ranking performance by borrower count](figures/part2_borrower_split.png)

The VantageScore–Classic tie on two-borrower loans from Part 1 remains. FICO 10T finishes ahead
in both groups, so its overall result is not carried by only one household structure.

### 4.4 The modern models agree often, but not always

VantageScore and 10T have a Spearman rank correlation of **0.852**. Their disagreement map shows
where one model places a loan higher or lower than the other and the observed default rate in each
cell.

![Default rate by modern-score rank groups](figures/part2_rank_disagreement.png)

Cells with fewer than 10,000 loans are hidden so tiny groups do not control the color scale. The
full table is written to `data/outputs/part2_rank_disagreement.csv`.

The earlier tie-inclusive selection exercise reaches the same conclusion across every nominal
portfolio share from 10% through 90%: the loans selected only by 10T default less often than the
loans selected only by VantageScore.

![Default rate of the modern-model swing loans across selection sizes](figures/part2_approval_estuary.png)

## 5. Interpretation

FICO 10T's advantage has a concrete shape. It moves more eventual defaults toward the risky end
and keeps fewer of them in same-size safe portfolios. That pattern appears in the full sample,
through time, and in both borrower-count groups.

The study cannot identify the proprietary design choice responsible for the difference. Both
modern scores use trended credit information, but the public files provide scores rather than the
models' internal weights. The evidence supports *which model ranked these loans better* and
*where the rankings differ*; it does not establish a causal explanation for why 10T wins.

Part 1's broader finding also remains: VantageScore 4.0 beats Classic FICO overall. The new data
change the winner of the modern comparison, not the evidence that competition with the legacy
score is technically credible.

## 6. Limits

- **These are loans, not applicants.** Every observation was already originated and acquired by
  Fannie Mae. The study cannot measure denials, access to credit, pricing, or lender behavior.
- **Ranking is not calibration.** Better ordering does not mean a raw score is a probability of
  default. The numerical score scales are not interchangeable.
- **The modern-versus-modern comparison is the cleanest.** FICO 10T and VantageScore were
  reconstructed from archived bureau data using aligned methods. Classic FICO is the disclosed
  origination score, so timing or credit-file contents may differ.
- **One outcome is tested.** The study uses a 36-month binary default definition and treats
  voluntary prepayment as a known non-default. Other horizons or definitions may change the size
  of the gaps.
- **One mortgage channel is tested.** Fannie Mae loans do not represent Freddie Mac, FHA/VA,
  portfolio mortgages, auto loans, credit cards, or the full consumer population.
- **No causal adoption effect is measured.** Lenders did not choose, price, or manage these loans
  with the reconstructed modern scores.
- **Cost and fairness are outside the test.** A model can rank defaults better without being the
  better operational, commercial, or policy choice.

## 7. Reproducing the analysis

The full score files are free but require Fannie Mae registration and acceptance of its terms.
Download the Historical Loan Performance files for FICO Score 10T and refreshed VantageScore 4.0
from Fannie Mae's [Historical Credit Score Files](https://historicalcreditscores.fanniemae.com/).

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

# Build or resume the 36-month loan outcome table from Performance_All.zip.
./.venv/bin/python run_full.py --labels-only

# Load the registered score files (ZIP or extracted TXT/CSV).
./.venv/bin/python 11_part2_load.py \
  --fico10t ~/Downloads/FICO10T_HistoricalScores_LoanPerformance_25.zip \
  --vs4 ~/Downloads/VantageScore4_HistoricalScores_LoanPerformance_25.zip

./.venv/bin/python 12_part2_join.py
./.venv/bin/python 13_part2_compare.py
./.venv/bin/python 14_part2_charts.py
```

`config.py` holds the analysis parameters. `gse/` contains the tested join, label, score-loading,
and metric code. Raw files, Parquet intermediates, and reproducible CSV outputs live in the
git-ignored `data/` directory; the chart script regenerates the public figures in `figures/`.

Key plain-language outputs are:

- `data/outputs/part2_default_capture.csv`
- `data/outputs/part2_defaults_by_risk_decile.csv`
- `data/outputs/part2_exact_size_portfolios.csv`
- `data/outputs/part2_exact_size_swaps.csv`

## References

- [Fannie Mae — Historical Credit Score Files](https://historicalcreditscores.fanniemae.com/)
- [Fannie Mae — July 1, 2026 data announcement](https://capitalmarkets.fanniemae.com/mortgage-backed-securities/fannie-mae-expands-transparency-additional-credit-data)
- [Fannie Mae — Single-Family Loan Performance Data](https://capitalmarkets.fanniemae.com/credit-risk-transfer/single-family-credit-risk-transfer/fannie-mae-single-family-loan-performance-data)
- [FHFA — Credit Scores](https://www.fhfa.gov/policy/credit-scores)

The [original two-score report](PART1_REPORT.md) and [original chart gallery](PART1_GALLERY.md) are
preserved for comparison.
