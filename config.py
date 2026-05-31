"""Central config for the VantageScore-vs-FICO bake-off. Edit here, never hardcode in scripts."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RAW = DATA / "raw"            # registered base + VS4 files land here
PARQUET = DATA / "parquet"    # typed columnar artifacts
OUTPUTS = DATA / "outputs"    # tables + figures
for _p in (RAW, PARQUET, OUTPUTS):
    _p.mkdir(parents=True, exist_ok=True)

# --- smoke mode: restrict to one acquisition cohort to validate the pipeline cheaply ---
SMOKE = os.environ.get("GSE_MODE", "").lower() == "smoke"
SMOKE_COHORT = "2020Q2"      # one acquisition_quarter for smoke runs

# --- VS4 historical-score file (CONFIRMED schema, pipe-delimited WITH header) ---
VS4_SCORE_COLUMNS = [
    "acquisition_quarter", "loan_identifier",
    "vs4_current_method", "vs4_trimerge",
    "vs4_bimerge_lowest", "vs4_bimerge_median", "vs4_bimerge_highest",
]
JOIN_KEYS = ["loan_identifier", "acquisition_quarter"]   # composite key
SCORE_VARIANT = "vs4_current_method"   # apples-to-apples with Classic FICO; sensitivity-check others

# --- default label (CRT-style credit event) ---
DLQ_THRESHOLD_MONTHS = 6                       # 180+ days delinquent
DEFAULT_ZB_CODES = frozenset({"02", "03", "09", "15"})  # 3rd-party sale, short sale, REO/DIL, note sale
PREPAY_ZB_CODES = frozenset({"01"})            # voluntary prepay = competing risk (NOT default)
PERF_WINDOW_MONTHS = 36                         # outcome window from origination

# --- credit-score band edges (shared by FICO and VS4; both ~300-850) ---
SCORE_BAND_EDGES = [300, 620, 660, 700, 740, 780, 851]

# --- comparison fairness (CDD round 1 fixes) ---
# Immature loans (observed < window, no event, not prepaid) are EXCLUDED from discrimination;
# prepaid loans are kept as known non-defaults. Swing analysis uses MATCHED approval rates, not
# arbitrary medians. The FICO comparator only has borrower+co-borrower, so loans with >2 borrowers
# are excluded from the headline (VS4 lowest-of-borrowers would unfairly advantage FICO there).
SWING_APPROVAL_RATES = [0.50, 0.80]   # approve the top X% under each score; matched across scores
MAX_BORROWERS_FOR_COMPARISON = 2

# --- match-rate gate (Task 7 fails below this) ---
MIN_MATCH_RATE = 0.95

# --- base SF Loan Performance positional layout (CONFIRMED empirically 2026-05-31 against the
#     real 2020Q2 file: 113 pipe-delimited fields, no header). 0-based column index. ---
BASE_PERF_COLUMN_MAP: dict[str, int] = {
    "loan_identifier": 1,          # zero-padded string -> normalize to int for join (see note below)
    "monthly_reporting_period": 2, # MMYYYY
    "orig_upb": 9,
    "loan_age": 15,
    "oltv": 19,
    "ocltv": 20,
    "num_borrowers": 21,
    "dti": 22,
    "fico": 23,                    # Borrower Credit Score at Origination (Classic FICO)
    "coborrower_fico": 24,         # Co-Borrower Credit Score at Origination
    "first_time_buyer": 25,
    "loan_purpose": 26,
    "occupancy": 29,
    "property_state": 30,
    "dlq_months": 39,              # Current Loan Delinquency Status ('00'=current, '06'=180d)
    "zero_balance_code": 43,       # None=active, '01'=prepay, '02/03/09/15'=credit event
}

# JOIN-KEY NORMALIZATION (CONFIRMED 2026-05-31): base loan_identifier is a zero-padded 12-char
# string ('000099520484'); the VS4 file stores it as a plain integer (99520484). Cast BOTH to
# Int64 before joining. With that, 2020Q2 IDs overlap 100% (range 99,520,484-100,756,258).
