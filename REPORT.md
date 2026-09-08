# Classic FICO vs. VantageScore 4.0 vs. FICO Score 10T

*A loan-level default-prediction bake-off on 24.7 million Fannie Mae mortgages*

> Start with the [plain-English summary](README.md). This report gives the full design, exact
> results, and limitations. The [figure gallery](GALLERY.md) has a guided tour of every chart.

## Abstract

- Fannie Mae's July 2026 historical score release makes a modern-model comparison possible: FICO
  Score 10T and VantageScore 4.0, constructed from archived bureau data for the same loans.
- The headline sample contains **24,697,071** Fannie-acquired mortgages from 2013Q2–2023Q1 with
  all three scores, no more than two borrowers, and a resolved 36-month outcome.
- **FICO 10T ranks default risk best:** Gini **0.5163**, versus **0.4922** for VantageScore 4.0 and
  **0.4774** for Classic FICO. The 10T edge is +241 Gini bp over VantageScore and +389 bp over
  Classic.
- The result is broad. 10T leads both alternatives in all **40 acquisition quarters** and in both
  the one- and two-borrower samples.
- In retrospective matched-selection exercises, the loans kept only by 10T default less than the
  loans kept only by VantageScore at every tested portfolio share from 10% through 90%.
- This is evidence about default ranking among loans Fannie acquired—not mortgage access, pricing,
  denied applicants, fairness, model cost, or performance across the full consumer-credit market.

## 1. Why run the test again?

Part 1 had an unavoidable missing contestant. The public data included VantageScore 4.0 and the
legacy Classic FICO score disclosed with each loan, but not FICO's newer 10T model. VantageScore
edged Classic FICO overall, with important differences across vintages and borrower counts. That
answered whether VantageScore could compete with the old score; it did not answer which modern
model was stronger.

On July 1, 2026, Fannie Mae published historical FICO 10T scores and refreshed VantageScore 4.0
scores. The files use the same loan keys and offer the same loan-level aggregation methods. The
question can now be asked cleanly: on the same mortgages, followed for the same length of time,
which score puts future defaulters closest to the risky end of the ranking?

## 2. Data and sample

The loan and outcome data come from Fannie Mae's Single-Family Historical Loan Performance
Dataset. The two modern-score files each contain **27,513,197** loans acquired from 2013Q2 through
2025Q3. They join to the performance data on `loan_identifier + acquisition_quarter`.

The headline retains Part 1's mature window, 2013Q2–2023Q1. Later acquisitions cannot yet supply a
complete 36-month outcome and are not mixed into the main result.

| Sample step | Loans |
|---|---:|
| Loan-performance panel, 2013Q2–2023Q1 | 25,087,678 |
| Valid VantageScore 4.0 current-method score | 25,081,806 |
| Valid FICO 10T current-method score | 25,071,037 |
| All three scores present, before outcome/borrower filters | 25,070,283 |
| Final resolved outcome, no more than two borrowers | **24,697,071** |

## 3. Methods

### 3.1 Outcome

**Default within 36 months** means the loan ever reaches 180 days delinquent or reports a
credit-event zero-balance code (`02`, `03`, `09`, or `15`) during the window. Voluntary prepayment
is retained as a known non-default. An active loan without enough observed history is censored and
excluded rather than labeled good.

### 3.2 Scores

- **Classic FICO:** the representative origination score in the loan-performance disclosure,
  constructed as the lower available borrower/co-borrower score.
- **VantageScore 4.0:** `vs4_current_method`.
- **FICO Score 10T:** `fico_10t_current_method`.

For the two modern scores, Fannie's current method chooses the middle of three or lower of two
bureau scores for each borrower, then the lowest borrower score on the loan. Loans with more than
two borrowers are excluded because the public Classic FICO fields cover only borrower and
co-borrower; leaving them in would create an aggregation mismatch.

Fannie documents **9999** as “FICO 10T could not be calculated.” The loader converts that sentinel,
and any value outside the documented 300–850 range, to missing before joins or metrics. There are
14,029 such current-method records in the full 10T file; 5,527 would otherwise enter the headline
sample. Treating 9999 as a very high score would reverse its meaning and bias the comparison.

### 3.3 Metrics

The primary metric is **Gini**, which summarizes how well a score ranks defaulters below
non-defaulters: 0 is random ranking and 1 is perfect ranking. AUC reports the same ranking statistic
on a different scale (`Gini = 2 × AUC − 1`), so it is not an independent confirmation. KS is the
largest separation between the score distributions of defaulters and non-defaulters.

The analysis reports pooled AUC/Gini/KS, Gini by acquisition quarter, loan- and default-weighted
within-quarter results, borrower-count splits, rank correlations, and retrospective swing-loan
comparisons at matched nominal portfolio shares. Integer score ties make the realized shares
slightly different around a cutoff.

## 4. Results

### 4.1 Overall: 10T wins

| Score | Loans | Defaults | AUC | Gini | KS | Gini vs. Classic |
|---|---:|---:|---:|---:|---:|---:|
| Classic FICO | 24,697,071 | 287,830 | 0.7387 | 0.4774 | 0.3628 | — |
| VantageScore 4.0 | 24,697,071 | 287,830 | 0.7461 | 0.4922 | 0.3675 | +148 bp |
| **FICO Score 10T** | **24,697,071** | **287,830** | **0.7582** | **0.5163** | **0.3897** | **+389 bp** |

![Overall Gini comparison](figures/part2_gini_comparison.png)

The pooled gap between 10T and VantageScore is **241 Gini bp**. That is a modest improvement in
absolute terms, but it is larger than VantageScore's 148 bp advantage over Classic FICO and is
remarkably consistent in the splits below.

### 4.2 Every acquisition quarter points the same way

FICO 10T leads VantageScore in all 40 quarters. Its quarterly edge ranges from **101 to 415 bp**
and averages **244 bp** without weighting, **231 bp** weighted by loans, and **265 bp** weighted by
defaults. It also leads Classic FICO in all 40 quarters. VantageScore leads Classic in 35 of 40.

![Gini by acquisition quarter](figures/part2_gini_by_vintage.png)

The fall in all three lines for 2017Q4–2020Q1 acquisitions is the same COVID-era pattern identified
in Part 1: defaults became harder to rank because a common shock reached farther into the score
distribution. Unlike VantageScore's Part 1 edge over Classic, 10T's advantage does not disappear
in those cohorts. Still, COVID is one unusual episode, not proof about every future recession.

The companion chart removes the levels and plots only 10T's lead. Every point above zero means 10T
ranked that quarter better.

![10T Gini edge by quarter](figures/part2_gini_edge_by_vintage.png)

### 4.3 One borrower and two borrowers

| Borrowers | Loans | Defaults | Classic FICO | VantageScore 4.0 | FICO 10T |
|---:|---:|---:|---:|---:|---:|
| 1 | 12,988,302 | 198,595 | 0.4438 | 0.4635 | **0.4923** |
| 2 | 11,708,769 | 89,235 | 0.5602 | 0.5604 | **0.5823** |

![Gini by borrower count](figures/part2_borrower_split.png)

VantageScore and Classic remain essentially tied on two-borrower loans, reproducing Part 1. FICO
10T leads VantageScore by **288 bp** on one-borrower loans and **219 bp** on two-borrower loans. The
new model's gain is therefore not confined to the place where VantageScore already looked strong.

### 4.4 The loans where 10T and VantageScore disagree

The models have a Spearman rank correlation of **0.852**: they usually agree, but not enough to be
interchangeable. A matched-selection exercise makes the disagreements concrete. Rank these same
loans under each model, keep a nominal top share, and compare only the loans kept by one score but
not the other.

| Nominal share kept | VantageScore-only default rate | 10T-only default rate | Relative reduction |
|---:|---:|---:|---:|
| 50% | 0.80% | **0.61%** | 23.7% |
| 80% | 2.06% | **1.56%** | 24.5% |

![Modern-model swing loans](figures/part2_swing_matched.png)

At the 80% point, each score keeps about 1.3 million loans the other leaves out. The 50% point
swaps about 1.8–1.9 million in each direction. Extending the calculation from 10% through 90%, the
10T-only group has the lower observed default rate at every tested cutoff.

![Swing loans across the selection curve](figures/part2_approval_estuary.png)

This is a retrospective portfolio comparison, not an approval experiment. Everyone in the sample
already received a mortgage that Fannie acquired. The exercise says which ranking chose safer
loans at equal-ish volume; it says nothing directly about access to credit.

### 4.5 What the disagreement map adds

The rank heatmap puts each loan into a VantageScore decile and a FICO 10T decile. Risk generally
falls from the lower-left (both models say risky) toward the upper-right (both say safe). The
off-diagonal cells are the disagreements. Their changing color shows that each model contains
information the other does not fully reproduce, even though 10T is the stronger ranking overall.

![Default rate by modern-score rank groups](figures/part2_rank_disagreement.png)

Cells with fewer than 10,000 loans are hidden so a tiny extreme-disagreement group cannot dominate
the color scale. The full cell counts and rates are written to
`data/outputs/part2_rank_disagreement.csv` when the chart script runs.

## 5. Interpretation

The cleanest statement is also the narrowest: **FICO Score 10T is the strongest of these three
scores at ranking 36-month default risk among the Fannie-acquired mortgages studied.** The pooled
metrics, every acquisition quarter, both borrower-count groups, and the swing-loan tests all point
the same way.

That does not erase Part 1. VantageScore 4.0 still ranks better than Classic FICO overall, which
supports the idea that a non-FICO model can be a credible competitor to the legacy standard. Part
2 changes the winner, not the broader argument that model competition is technically possible.

## 6. Limitations / ways this could mislead

- **Selected loans, not applicants.** The dataset begins after origination and Fannie acquisition.
  It cannot measure denials, approval expansion, pricing, lender behavior, or adverse selection.
- **Ranking, not calibration.** A higher Gini does not mean the score number itself is a better
  probability of default. The raw numerical scales are not interchangeable.
- **Modern-versus-Classic timing.** The two modern scores were reconstructed from archived bureau
  data using an aligned process. Classic FICO is the disclosed origination score. Differences in
  report timing or credit-file contents make either modern-versus-Classic comparison less clean
  than 10T versus VantageScore.
- **One outcome.** Results use a 36-month binary default label with prepayment treated as a known
  non-default, not a competing-risks model. Other horizons or definitions can change magnitudes.
- **One mortgage channel.** These are Fannie Mae loans, not Freddie Mac, FHA/VA, portfolio loans,
  auto loans, credit cards, or the full consumer population.
- **One severe shock.** COVID is the only major stress episode in the observed window, and
  delinquency marks may reflect forbearance mechanics as well as credit deterioration.
- **No causal adoption effect.** The scores are evaluated after the fact. Lenders did not choose,
  price, or manage these loans using the reconstructed 10T and VantageScore values.

## 7. Reproducing the analysis

The full score files are free but require Fannie Mae registration and acceptance of its terms.
Download the FICO Score 10T and refreshed VantageScore 4.0 files for the Historical Loan
Performance Dataset from Fannie's [Historical Credit Score Files](https://historicalcreditscores.fanniemae.com/).

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

# Build/resume the 36-month loan outcome table from Performance_All.zip.
./.venv/bin/python run_full.py --labels-only

# Load the two registered score files (ZIP or extracted TXT/CSV).
./.venv/bin/python 11_part2_load.py \
  --fico10t ~/Downloads/FICO10T_HistoricalScores_LoanPerformance_25.zip \
  --vs4 ~/Downloads/VantageScore4_HistoricalScores_LoanPerformance_25.zip

./.venv/bin/python 12_part2_join.py
./.venv/bin/python 13_part2_compare.py
./.venv/bin/python 14_part2_charts.py
```

`config.py` holds the analysis parameters. `gse/` contains the tested join, label, score-loading,
and metric code. Raw files, Parquet intermediates, and reproducible CSV outputs live under the
git-ignored `data/` directory; publication figures are regenerated into `figures/`.

## References

- [Fannie Mae — Historical Credit Score Files](https://historicalcreditscores.fanniemae.com/)
- [Fannie Mae — July 1, 2026 data announcement](https://capitalmarkets.fanniemae.com/mortgage-backed-securities/fannie-mae-expands-transparency-additional-credit-data)
- [Fannie Mae — Single-Family Loan Performance Data](https://capitalmarkets.fanniemae.com/credit-risk-transfer/single-family-credit-risk-transfer/fannie-mae-single-family-loan-performance-data)
- [FHFA — Credit Scores](https://www.fhfa.gov/policy/credit-scores)

The [original two-score report](PART1_REPORT.md) and [original chart gallery](PART1_GALLERY.md) are
preserved for comparison.
