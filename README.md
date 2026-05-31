# Classic FICO vs. VantageScore 4.0 — a loan-level default-prediction bake-off

*Which mortgage credit score actually predicts default better, on the same loans — and are they substitutable?*

> **Status:** full-panel run in progress. Results/conclusions below are placeholders for the questions the analysis will answer. No numbers are reported until the full 2013–2023 panel completes.

## Abstract
- Head-to-head test of **Classic FICO** vs **VantageScore 4.0** as default predictors on the *same* Fannie Mae mortgages, using the first public loan-level VantageScore data (released 2024).
- Goal: turn the long-running "FICO vs VantageScore" debate from an argument into a measurement — discrimination, agreement, and marginal-borrower behavior.
- Motivated by the GSEs' move to accept VantageScore 4.0 / FICO 10T, which puts FICO's decades-long sole-score position (and pricing power) in play.

## Introduction
- FHFA validated FICO 10T and VantageScore 4.0 for the GSEs (2022) and the enterprises began accepting them (2026); a substitute score is only adoptable if it underwrites at least as well.
- The 2024 public release of loan-level VantageScore 4.0 scores (joinable to the existing loan-performance data) makes an independent, outcome-based comparison possible for the first time.
- Question this repo answers: **is VantageScore 4.0 a genuine substitute for Classic FICO in mortgage credit risk, and for which borrowers do they disagree?**

## Data
- Fannie Mae **Single-Family Loan Performance** dataset (origination attributes + monthly performance) joined to the **VantageScore 4.0 Historical Scores** file.
- Acquisition quarters **2013Q2–2023Q1** (the VantageScore-overlap window); ~25M loans in the score file; loan-level join on `loan_identifier + acquisition_quarter`.
- Each loan carries **both** scores (Classic FICO + VantageScore 4.0) and a realized default outcome. Public, anonymized, free (registration required).

## Methods
- **Default** = ever-180-days-delinquent or credit-event termination within a 36-month window from origination; voluntary prepayment treated as a competing risk (known non-default), not censoring.
- **Comparator scores:** VantageScore `vs4_current_method` vs the Classic FICO **loan representative score** = min(borrower, co-borrower), matching the lowest-of-borrowers methodology.
- **Discrimination:** AUC / Gini / KS, overall and **per vintage** (stress-vintage robustness). Immature (unresolved) loans excluded; results are **conditional on GSE acquisition** (FICO floored ~620), not unconditional.
- **Agreement & marginal analysis:** rank correlation, score-band transition matrix, and a **matched-approval-rate** swing-borrower test (who each score uniquely approves, and how those loans perform).

## Results — *(to be filled by the full-panel run)*
- [ ] Which score ranks default better overall (AUC / Gini / KS)?
- [ ] Does any edge **survive the 2022 stress vintages** (per-vintage Gini)?
- [ ] How substitutable are the two scores (rank correlation; band-transition reshuffling)?
- [ ] At matched approval rates, whose **marginal (swing) approvals default less** — i.e., who would expand access more safely?
- [ ] How much risk does VantageScore see **below FICO's ~620 floor** that FICO cannot express?

## Conclusion — *(placeholder)*
- [ ] Verdict on substitutability — and for which borrower segments it does/doesn't hold.
- [ ] Implications for credit-score competition and FICO's mortgage pricing-power moat.
- [ ] Forward look: this compares **Classic FICO, not FICO 10T** — the like-for-like 10T comparison unlocks with the summer-2026 data release.

---

## Reproducing

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m pytest -q          # unit-tested label/metrics/join engine
```

1. **Get the data** (free, registration): the VantageScore 4.0 Historical Scores for the Historical Loan Performance Dataset (`historicalcreditscores.fanniemae.com`) and the Single-Family Loan Performance quarterly files (`datadynamics.fanniemae.com`).
2. **Smoke (one quarter):** place a quarter's files, then `GSE_MODE=smoke ./.venv/bin/python 02_load.py && 04_label.py && 03_join.py && 05_compare.py`.
3. **Full panel:** `./.venv/bin/python run_full.py` (disk-safe, quarter-by-quarter) `&& 03_join.py && 05_compare.py && 06_charts.py`.

- `config.py` holds all parameters (default definition, window, score variant, column map). `gse/` is the unit-tested core; `0X_*.py` are the pipeline stages. Data lives under `data/` (git-ignored).

## References
- FHFA, *Validation of FICO 10T and VantageScore 4.0* (2022); *Historical VantageScore 4.0 release* (Jul 2024); *FICO 10T historical data + extended VantageScore* announcement (Apr 2026).
- Fannie Mae, *Single-Family Loan Performance Dataset* and *Historical Credit Score Files* (Credit Score Models and Reports Initiative).
