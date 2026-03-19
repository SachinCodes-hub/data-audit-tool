import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Dataset Quality Analyzer",
    page_icon="🔬",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 16px 20px;
    border-left: 4px solid #ccc;
    margin-bottom: 10px;
}
.metric-card.critical { border-left-color: #e74c3c; }
.metric-card.warning  { border-left-color: #f39c12; }
.metric-card.good     { border-left-color: #2ecc71; }
.score-circle {
    font-size: 64px;
    font-weight: 800;
    text-align: center;
    padding: 20px;
}
.score-label {
    font-size: 18px;
    text-align: center;
    font-weight: 500;
    margin-top: -10px;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FAULT DETECTION FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_file(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)


def detect_completeness(df):
    """D1: Missing values in all forms"""
    results = {}
    total_cells = df.shape[0] * df.shape[1]

    # True NaN/None/NaT
    null_count = df.isnull().sum().sum()

    # Empty strings (for object columns)
    empty_str = 0
    placeholder_count = 0
    whitespace_count = 0
    placeholders = {"n/a", "na", "none", "null", "nil", "-", "--", "?",
                    "unknown", "undefined", "missing", "not available",
                    "not applicable", "tbd", "tbc", "#n/a"}

    for col in df.select_dtypes(include="object").columns:
        col_vals = df[col].dropna().astype(str)
        empty_str        += (col_vals == "").sum()
        whitespace_count += col_vals.str.strip().eq("").sum() - (col_vals == "").sum()
        placeholder_count += col_vals.str.strip().str.lower().isin(placeholders).sum()

    total_missing = null_count + empty_str + whitespace_count + placeholder_count
    missing_rate  = total_missing / total_cells if total_cells > 0 else 0

    per_col = {}
    for col in df.columns:
        col_null   = df[col].isnull().sum()
        col_empty  = 0
        col_holder = 0
        if df[col].dtype == object:
            vals = df[col].dropna().astype(str)
            col_empty  = (vals.str.strip() == "").sum()
            col_holder = vals.str.strip().str.lower().isin(placeholders).sum()
        total_col = col_null + col_empty + col_holder
        if total_col > 0:
            per_col[col] = {
                "null": int(col_null),
                "empty_str": int(col_empty),
                "placeholder": int(col_holder),
                "total_missing": int(total_col),
                "missing_%": round(total_col / len(df) * 100, 2)
            }

    results = {
        "null_count":          int(null_count),
        "empty_str_count":     int(empty_str),
        "whitespace_count":    int(whitespace_count),
        "placeholder_count":   int(placeholder_count),
        "total_missing":       int(total_missing),
        "total_cells":         int(total_cells),
        "missing_rate":        round(missing_rate * 100, 4),
        "per_column":          per_col,
        "columns_with_missing": len(per_col),
        "fully_empty_cols":    int((df.isnull().sum() == len(df)).sum()),
    }
    # Score: 0 = all missing, 100 = none missing
    results["score"] = max(0, round(100 - (missing_rate * 100 * 1.5), 2))
    return results


def detect_uniqueness(df):
    """D2: Duplicate rows and duplicate columns"""
    n = len(df)

    exact_dupes       = int(df.duplicated().sum())
    exact_dupe_rate   = exact_dupes / n if n > 0 else 0

    # Duplicate columns (same values, different name)
    dup_cols = []
    cols = list(df.columns)
    for i in range(len(cols)):
        for j in range(i+1, len(cols)):
            try:
                if df[cols[i]].equals(df[cols[j]]):
                    dup_cols.append((cols[i], cols[j]))
            except Exception:
                pass

    # Constant columns (zero variance — no information)
    constant_cols = [col for col in df.columns if df[col].nunique(dropna=True) <= 1]

    # Near-duplicate detection (sample for performance)
    near_dupe_rate = 0.0
    sample_size    = min(n, 5000)
    if n > 1 and df.select_dtypes(include="number").shape[1] > 0:
        num_df = df.select_dtypes(include="number").dropna()
        if len(num_df) > 1:
            sample = num_df.sample(min(sample_size, len(num_df)), random_state=42)
            try:
                from sklearn.neighbors import NearestNeighbors
                nbrs = NearestNeighbors(n_neighbors=2, algorithm="auto").fit(sample)
                dists, _ = nbrs.kneighbors(sample)
                close = (dists[:, 1] < 1e-6).sum()
                near_dupe_rate = round(close / len(sample) * 100, 2)
            except ImportError:
                pass

    total_dupe_rate = exact_dupe_rate + (near_dupe_rate / 100 * 0.3)

    results = {
        "exact_duplicates":    exact_dupes,
        "exact_dupe_rate_%":   round(exact_dupe_rate * 100, 3),
        "duplicate_columns":   dup_cols,
        "constant_columns":    constant_cols,
        "near_dupe_rate_%":    near_dupe_rate,
        "total_unique_rows":   n - exact_dupes,
    }
    results["score"] = max(0, round(100 - (total_dupe_rate * 100 * 2), 2))
    return results


def detect_consistency(df):
    """D3: Type inconsistencies, format issues, case inconsistency"""
    issues = []
    mixed_type_cols  = []
    date_format_cols = []
    case_issue_cols  = []
    encoding_issues  = []

    import re

    for col in df.columns:
        col_data = df[col].dropna()
        if len(col_data) == 0:
            continue

        # Mixed numeric/string in object columns
        if df[col].dtype == object:
            looks_numeric = pd.to_numeric(col_data, errors="coerce").notnull().sum()
            looks_string  = (col_data.astype(str).str.match(r"^[A-Za-z]")).sum()
            if 0 < looks_numeric < len(col_data) and looks_string > 0:
                mixed_type_cols.append({
                    "column": col,
                    "numeric_count": int(looks_numeric),
                    "string_count":  int(looks_string),
                    "total":         int(len(col_data))
                })

        # Date format inconsistency
        if df[col].dtype == object:
            sample_vals = col_data.astype(str).head(200)
            date_patterns = [
                r"\d{4}-\d{2}-\d{2}",           # YYYY-MM-DD
                r"\d{2}/\d{2}/\d{4}",            # DD/MM/YYYY
                r"\d{2}-\d{2}-\d{4}",            # DD-MM-YYYY
                r"\d{1,2} [A-Za-z]{3} \d{4}",    # 1 Jan 2023
                r"[A-Za-z]{3,9} \d{1,2},? \d{4}" # Jan 1, 2023
            ]
            formats_found = set()
            for pat in date_patterns:
                if sample_vals.str.contains(pat, regex=True).any():
                    formats_found.add(pat)
            if len(formats_found) > 1:
                date_format_cols.append({"column": col, "formats_found": len(formats_found)})

        # Case inconsistency in categorical columns
        if df[col].dtype == object and df[col].nunique() <= 100:
            lower_vals = col_data.astype(str).str.strip().str.lower()
            orig_vals  = col_data.astype(str).str.strip()
            unique_orig  = orig_vals.nunique()
            unique_lower = lower_vals.nunique()
            if unique_lower < unique_orig:
                case_issue_cols.append({
                    "column": col,
                    "unique_original": int(unique_orig),
                    "unique_after_lower": int(unique_lower),
                    "extra_due_to_case": int(unique_orig - unique_lower)
                })

        # Encoding / special character issues
        if df[col].dtype == object:
            weird = col_data.astype(str).str.contains(
                r"[^\x00-\x7F]|â€|Ã©|Ã¨|Ã |ÃŽ|Â©|Â®", regex=True, na=False
            ).sum()
            if weird > 0:
                encoding_issues.append({"column": col, "affected_rows": int(weird)})

    total_issue_cols = (len(mixed_type_cols) + len(date_format_cols) +
                        len(case_issue_cols) + len(encoding_issues))
    total_cols       = df.shape[1]
    issue_rate       = total_issue_cols / total_cols if total_cols > 0 else 0

    results = {
        "mixed_type_columns":   mixed_type_cols,
        "date_format_columns":  date_format_cols,
        "case_issue_columns":   case_issue_cols,
        "encoding_issues":      encoding_issues,
        "total_issue_columns":  total_issue_cols,
        "issue_rate_%":         round(issue_rate * 100, 2),
    }
    results["score"] = max(0, round(100 - (issue_rate * 100 * 1.8), 2))
    return results


def detect_validity(df):
    """D4: Outliers, impossible values, range violations"""
    outlier_cols = []
    impossible   = []
    future_dates = []

    import datetime

    for col in df.select_dtypes(include="number").columns:
        col_data = df[col].dropna()
        if len(col_data) < 4:
            continue

        # IQR outlier detection
        Q1, Q3 = col_data.quantile(0.25), col_data.quantile(0.75)
        IQR    = Q3 - Q1
        if IQR > 0:
            lower = Q1 - 3.0 * IQR
            upper = Q3 + 3.0 * IQR
            outlier_mask = (col_data < lower) | (col_data > upper)
            n_out = outlier_mask.sum()
            if n_out > 0:
                outlier_cols.append({
                    "column":       col,
                    "outlier_count": int(n_out),
                    "outlier_%":    round(n_out / len(col_data) * 100, 2),
                    "lower_bound":  round(lower, 4),
                    "upper_bound":  round(upper, 4),
                    "min_value":    round(float(col_data.min()), 4),
                    "max_value":    round(float(col_data.max()), 4),
                })

        # Impossible values (domain-specific heuristics)
        col_lower = col.lower()
        if any(k in col_lower for k in ["age", "years"]):
            neg = (col_data < 0).sum()
            over = (col_data > 150).sum()
            if neg + over > 0:
                impossible.append({"column": col, "reason": "Age < 0 or > 150", "count": int(neg + over)})

        if any(k in col_lower for k in ["price", "cost", "salary", "revenue", "amount", "fee"]):
            neg = (col_data < 0).sum()
            if neg > 0:
                impossible.append({"column": col, "reason": "Negative monetary value", "count": int(neg)})

        if any(k in col_lower for k in ["percent", "pct", "rate", "ratio"]):
            out_of_range = ((col_data < 0) | (col_data > 100)).sum()
            if out_of_range > 0:
                impossible.append({"column": col, "reason": "Percent out of 0-100 range", "count": int(out_of_range)})

    # Future dates
    now = pd.Timestamp.now()
    for col in df.columns:
        if df[col].dtype == object or str(df[col].dtype).startswith("datetime"):
            try:
                parsed = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True)
                future = (parsed > now).sum()
                if future > 0:
                    future_dates.append({"column": col, "future_dates": int(future)})
            except Exception:
                pass

    total_outlier_cells = sum(o["outlier_count"] for o in outlier_cols)
    total_cells_num     = sum(df[c].dropna().shape[0] for c in df.select_dtypes("number").columns)
    outlier_rate        = total_outlier_cells / total_cells_num if total_cells_num > 0 else 0

    total_impossible    = sum(i["count"] for i in impossible)
    impossible_rate     = total_impossible / len(df) if len(df) > 0 else 0

    validity_penalty = outlier_rate * 60 + impossible_rate * 100

    results = {
        "outlier_columns":      outlier_cols,
        "impossible_values":    impossible,
        "future_date_columns":  future_dates,
        "total_outlier_cells":  total_outlier_cells,
        "outlier_rate_%":       round(outlier_rate * 100, 2),
        "impossible_rate_%":    round(impossible_rate * 100, 2),
    }
    results["score"] = max(0, round(100 - validity_penalty, 2))
    return results


def detect_accuracy(df):
    """D5: Class imbalance, distribution skewness"""
    skew_cols    = []
    imbalance    = []
    skew_penalty = 0

    for col in df.select_dtypes(include="number").columns:
        col_data = df[col].dropna()
        if len(col_data) < 4:
            continue
        sk = float(col_data.skew())
        if abs(sk) > 2.0:
            skew_cols.append({"column": col, "skewness": round(sk, 4),
                               "severity": "extreme" if abs(sk) > 5 else "high"})
            skew_penalty += min(abs(sk) / 20, 0.05)

    for col in df.select_dtypes(include="object").columns:
        vc = df[col].value_counts(normalize=True)
        if len(vc) >= 2:
            top_ratio = float(vc.iloc[0])
            if top_ratio > 0.85:
                imbalance.append({
                    "column":         col,
                    "dominant_class": str(vc.index[0]),
                    "dominant_%":     round(top_ratio * 100, 2),
                    "n_classes":      len(vc)
                })

    imbalance_penalty = len(imbalance) / df.select_dtypes("object").shape[1] * 20 \
                        if df.select_dtypes("object").shape[1] > 0 else 0

    results = {
        "skewed_columns":     skew_cols,
        "imbalanced_columns": imbalance,
        "skew_penalty":       round(skew_penalty * 100, 2),
        "imbalance_penalty":  round(imbalance_penalty, 2),
    }
    results["score"] = max(0, round(100 - skew_penalty * 100 - imbalance_penalty, 2))
    return results


def detect_structure(df):
    """D6: Column naming, schema issues, row/col ratio"""
    issues   = []
    bad_cols = []

    import re

    # Column naming issues
    for col in df.columns:
        col_str = str(col)
        if col_str.strip() == "":
            bad_cols.append({"column": col_str, "issue": "Empty column name"})
        elif re.match(r"^[Uu]nnamed", col_str):
            bad_cols.append({"column": col_str, "issue": "Unnamed column (likely index leak)"})
        elif re.search(r"\s{2,}", col_str):
            bad_cols.append({"column": col_str, "issue": "Multiple spaces in name"})
        elif re.search(r"[^a-zA-Z0-9_ ]", col_str):
            bad_cols.append({"column": col_str, "issue": "Special characters in name"})

    # Fully empty rows
    empty_rows = int(df.isnull().all(axis=1).sum())
    if empty_rows > 0:
        issues.append(f"{empty_rows} completely empty rows")

    # Row-to-column ratio (heuristic: <5 is very poor for ML)
    row_col_ratio = df.shape[0] / df.shape[1] if df.shape[1] > 0 else 0
    if row_col_ratio < 5:
        issues.append(f"Low row-to-column ratio ({row_col_ratio:.1f}) — may cause high-dimensionality issues")
    if row_col_ratio < 2:
        issues.append("Critically low rows vs columns — underdetermined dataset")

    # Single-value rows (all identical across columns)
    single_val_rows = int((df.nunique(axis=1) == 1).sum())
    if single_val_rows > 0:
        issues.append(f"{single_val_rows} rows where all values are identical")

    # Inferred-type mismatch (column looks numeric but stored as object)
    wrong_type_cols = []
    for col in df.select_dtypes("object").columns:
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notnull().mean() > 0.95:
            wrong_type_cols.append({"column": col, "issue": "Stored as text but appears numeric"})

    penalty = (len(bad_cols) + len(wrong_type_cols)) / df.shape[1] * 30 + \
              (1 if row_col_ratio < 5 else 0) * 10

    results = {
        "bad_column_names":   bad_cols,
        "wrong_type_cols":    wrong_type_cols,
        "empty_rows":         empty_rows,
        "general_issues":     issues,
        "row_col_ratio":      round(row_col_ratio, 2),
    }
    results["score"] = max(0, round(100 - penalty, 2))
    return results


def detect_correlation(df):
    """D7: High multicollinearity, potential data leakage, redundant features"""
    high_corr_pairs = []
    redundant_cols  = []

    num_df = df.select_dtypes(include="number").dropna(axis=1, how="all")
    if num_df.shape[1] >= 2:
        corr_matrix = num_df.corr().abs()
        cols = corr_matrix.columns
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                val = corr_matrix.iloc[i, j]
                if val > 0.95:
                    high_corr_pairs.append({
                        "col_a":       cols[i],
                        "col_b":       cols[j],
                        "correlation": round(float(val), 4),
                        "type":        "perfect" if val > 0.999 else "very high"
                    })
                    if val > 0.999:
                        redundant_cols.append(cols[j])

    penalty = len(high_corr_pairs) * 3

    results = {
        "high_correlation_pairs": high_corr_pairs,
        "redundant_columns":      list(set(redundant_cols)),
        "n_high_corr_pairs":      len(high_corr_pairs),
    }
    results["score"] = max(0, round(100 - penalty, 2))
    return results


# ══════════════════════════════════════════════════════════════════════════════
# UNIVERSAL DQS FORMULA
# ══════════════════════════════════════════════════════════════════════════════
# 
# DQS = Σ (Wᵢ × Dᵢ) × Size_Factor × Diversity_Bonus
#
# Dimensions and their weights (sum to 1.0):
#   D1 Completeness  → W=0.28  (most fundamental fault)
#   D2 Uniqueness    → W=0.18  (duplicates corrupt training & analysis)
#   D3 Consistency   → W=0.16  (mixed types/formats break pipelines)
#   D4 Validity      → W=0.16  (outliers & impossible values = noise)
#   D5 Accuracy      → W=0.10  (skew & imbalance affect ML models)
#   D6 Structure     → W=0.07  (schema issues compound other problems)
#   D7 Correlation   → W=0.05  (redundancy reduces information density)
#
# Size_Factor    = min(1.0, log10(n_rows + 1) / 4)   → penalizes tiny datasets
# Diversity_Bonus= min(1.05, 1 + (n_dtypes - 1) * 0.01) → slight reward for rich schema
#
# Final: DQS = raw_score × Size_Factor × Diversity_Bonus  clamped [0, 100]

WEIGHTS = {
    "completeness":  0.28,
    "uniqueness":    0.18,
    "consistency":   0.16,
    "validity":      0.16,
    "accuracy":      0.10,
    "structure":     0.07,
    "correlation":   0.05,
}

def compute_dqs(scores_dict, df):
    raw_score = sum(WEIGHTS[dim] * scores_dict[dim] for dim in WEIGHTS)

    n_rows      = len(df)
    size_factor = min(1.0, np.log10(n_rows + 1) / 4.0) if n_rows > 0 else 0.1
    size_factor = max(0.5, size_factor)   # floor at 0.5 so tiny datasets still score

    n_dtypes       = df.dtypes.nunique()
    diversity_bonus = min(1.05, 1 + (n_dtypes - 1) * 0.01)

    dqs = raw_score * size_factor * diversity_bonus
    return round(min(100, max(0, dqs)), 2), round(raw_score, 2), round(size_factor, 4), round(diversity_bonus, 4)


def dqs_grade(score):
    if score >= 90: return "Excellent", "#2ecc71"
    if score >= 75: return "Good",      "#27ae60"
    if score >= 60: return "Fair",      "#f39c12"
    if score >= 40: return "Poor",      "#e67e22"
    return "Critical", "#e74c3c"


# ══════════════════════════════════════════════════════════════════════════════
# STREAMLIT UI
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.title("🔬 DQ Analyzer")
    st.caption("Dataset Quality — Part 2")
    st.divider()
    file = st.file_uploader("Upload your dataset", type=["csv", "xlsx"])
    st.divider()
    st.markdown("**Weight Configuration**")
    st.caption("Adjust dimension weights to suit your use case:")
    w_complete  = st.slider("Completeness",  0.05, 0.50, 0.28, 0.01)
    w_unique    = st.slider("Uniqueness",    0.05, 0.40, 0.18, 0.01)
    w_consist   = st.slider("Consistency",  0.05, 0.40, 0.16, 0.01)
    w_valid     = st.slider("Validity",     0.05, 0.40, 0.16, 0.01)
    w_accuracy  = st.slider("Accuracy",     0.02, 0.30, 0.10, 0.01)
    w_structure = st.slider("Structure",    0.02, 0.20, 0.07, 0.01)
    w_corr      = st.slider("Correlation",  0.01, 0.20, 0.05, 0.01)

    total_w = w_complete + w_unique + w_consist + w_valid + w_accuracy + w_structure + w_corr
    st.caption(f"Total weight: **{total_w:.2f}** (ideally 1.00)")

    WEIGHTS["completeness"]  = w_complete / total_w
    WEIGHTS["uniqueness"]    = w_unique   / total_w
    WEIGHTS["consistency"]   = w_consist  / total_w
    WEIGHTS["validity"]      = w_valid    / total_w
    WEIGHTS["accuracy"]      = w_accuracy / total_w
    WEIGHTS["structure"]     = w_structure / total_w
    WEIGHTS["correlation"]   = w_corr     / total_w

# ── Main ──────────────────────────────────────────────────────────────────────
st.title("🔬 Dataset Quality Analyzer")
st.caption("Part 2 — Complete fault detection + Universal Quality Score (DQS)")

if file is None:
    st.info("Upload a CSV or Excel file from the sidebar to begin analysis.")

    st.divider()
    st.subheader("The Universal DQS Formula")

    st.latex(r"""
    DQS = \left(\sum_{i=1}^{7} W_i \cdot D_i\right) \times F_{size} \times B_{diversity}
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**Dimension scores (D₁–D₇)** each range 0–100:

| # | Dimension | Weight | Why |
|---|-----------|--------|-----|
| D1 | Completeness | 0.28 | Missing data is the #1 failure mode |
| D2 | Uniqueness | 0.18 | Duplicates silently bias every metric |
| D3 | Consistency | 0.16 | Mixed types break pipelines |
| D4 | Validity | 0.16 | Outliers & impossible values = noise |
| D5 | Accuracy | 0.10 | Skew/imbalance hurts ML models |
| D6 | Structure | 0.07 | Schema issues compound everything |
| D7 | Correlation | 0.05 | Redundancy reduces info density |
""")
    with col2:
        st.markdown("""
**Adjustment factors:**

`Size_Factor = min(1.0, log₁₀(n_rows + 1) / 4)`
- A 10-row dataset cannot be called high quality regardless of raw scores
- log₁₀ scale: 10k rows = 1.0, 1k rows = 0.75, 100 rows = 0.5

`Diversity_Bonus = min(1.05, 1 + (n_dtypes - 1) × 0.01)`
- Datasets with multiple data types are richer and slightly rewarded
- Capped at 1.05 — bonus is small, not dominant

**Grades:**
- 90–100 → Excellent
- 75–89  → Good
- 60–74  → Fair
- 40–59  → Poor
- 0–39   → Critical
""")
    st.stop()

# ── Load & validate ───────────────────────────────────────────────────────────
try:
    df = load_file(file)
    st.success(f"Loaded **{file.name}** — {df.shape[0]:,} rows × {df.shape[1]} columns")
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

# ── Run all detectors with progress ──────────────────────────────────────────
with st.spinner("Running full quality scan..."):
    bar = st.progress(0, "Scanning completeness...")
    r_complete = detect_completeness(df);  bar.progress(14, "Scanning uniqueness...")
    r_unique   = detect_uniqueness(df);    bar.progress(28, "Scanning consistency...")
    r_consist  = detect_consistency(df);   bar.progress(42, "Scanning validity...")
    r_valid    = detect_validity(df);      bar.progress(57, "Scanning accuracy...")
    r_accuracy = detect_accuracy(df);      bar.progress(71, "Scanning structure...")
    r_struct   = detect_structure(df);     bar.progress(85, "Scanning correlations...")
    r_corr     = detect_correlation(df);   bar.progress(100, "Done!")

scores_dict = {
    "completeness": r_complete["score"],
    "uniqueness":   r_unique["score"],
    "consistency":  r_consist["score"],
    "validity":     r_valid["score"],
    "accuracy":     r_accuracy["score"],
    "structure":    r_struct["score"],
    "correlation":  r_corr["score"],
}
dqs, raw_score, size_factor, diversity_bonus = compute_dqs(scores_dict, df)
grade, grade_color = dqs_grade(dqs)

bar.empty()
st.divider()

# ═══════════════════════════════════════════════════════════════════
# SCORE DASHBOARD
# ═══════════════════════════════════════════════════════════════════
st.subheader("Quality Score Dashboard")

score_col, breakdown_col, radar_col = st.columns([1, 1.5, 1.5])

with score_col:
    st.markdown(f"""
<div style="text-align:center; padding:20px; background:#f8f9fa; border-radius:16px; border: 3px solid {grade_color}">
<div style="font-size:72px; font-weight:800; color:{grade_color}; line-height:1">{dqs}</div>
<div style="font-size:22px; font-weight:600; color:{grade_color}; margin-top:4px">{grade}</div>
<div style="font-size:12px; color:#888; margin-top:8px">Dataset Quality Score</div>
</div>
""", unsafe_allow_html=True)
    st.caption(f"Raw: {raw_score} × Size({size_factor}) × Diversity({diversity_bonus})")

with breakdown_col:
    st.markdown("**Dimension breakdown**")
    dim_labels = ["Completeness","Uniqueness","Consistency",
                  "Validity","Accuracy","Structure","Correlation"]
    dim_scores = [r_complete["score"], r_unique["score"], r_consist["score"],
                  r_valid["score"], r_accuracy["score"], r_struct["score"], r_corr["score"]]
    dim_weights = [WEIGHTS["completeness"], WEIGHTS["uniqueness"], WEIGHTS["consistency"],
                   WEIGHTS["validity"], WEIGHTS["accuracy"], WEIGHTS["structure"], WEIGHTS["correlation"]]

    for label, score, weight in zip(dim_labels, dim_scores, dim_weights):
        color = "#2ecc71" if score >= 80 else "#f39c12" if score >= 60 else "#e74c3c"
        bar_width = int(score)
        st.markdown(f"""
<div style="margin-bottom:8px">
  <div style="display:flex; justify-content:space-between; font-size:13px; margin-bottom:2px">
    <span>{label} <span style="color:#888; font-size:11px">(w={weight:.2f})</span></span>
    <span style="font-weight:600; color:{color}">{score}</span>
  </div>
  <div style="background:#e0e0e0; border-radius:4px; height:8px">
    <div style="background:{color}; width:{bar_width}%; height:8px; border-radius:4px"></div>
  </div>
</div>
""", unsafe_allow_html=True)

with radar_col:
    st.markdown("**Radar view**")
    categories  = ["Complete.", "Unique.", "Consist.", "Valid.", "Accuracy", "Structure", "Correl."]
    values      = dim_scores + [dim_scores[0]]
    angles      = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles     += angles[:1]
    fig, ax = plt.subplots(figsize=(3.5, 3.5), subplot_kw=dict(polar=True))
    ax.set_facecolor("#f8f9fa")
    fig.patch.set_facecolor("#f8f9fa")
    ax.plot(angles, values, color=grade_color, linewidth=2)
    ax.fill(angles, values, color=grade_color, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=8)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], size=7)
    ax.grid(color="gray", linestyle="--", linewidth=0.4, alpha=0.5)
    st.pyplot(fig, use_container_width=True)
    plt.close()

st.divider()

# ═══════════════════════════════════════════════════════════════════
# DETAILED FAULT REPORTS (tabs)
# ═══════════════════════════════════════════════════════════════════
st.subheader("Detailed Fault Analysis")

tabs = st.tabs([
    "D1 Completeness", "D2 Uniqueness", "D3 Consistency",
    "D4 Validity", "D5 Accuracy", "D6 Structure", "D7 Correlation",
    "Full Report"
])

# ── D1: Completeness ─────────────────────────────────────────────
with tabs[0]:
    r = r_complete
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total missing",   f"{r['total_missing']:,}")
    c2.metric("Missing rate",    f"{r['missing_rate']}%")
    c3.metric("Columns affected",f"{r['columns_with_missing']}")
    c4.metric("Fully empty cols",f"{r['fully_empty_cols']}")

    st.caption(f"NaN/None: {r['null_count']:,}  |  Empty strings: {r['empty_str_count']:,}  |  Placeholders: {r['placeholder_count']:,}  |  Whitespace-only: {r['whitespace_count']:,}")

    if r["per_column"]:
        st.markdown("**Columns with missing values:**")
        df_miss = pd.DataFrame(r["per_column"]).T.reset_index().rename(columns={"index": "column"})
        st.dataframe(df_miss, use_container_width=True)

        fig, ax = plt.subplots(figsize=(10, 3))
        cols_sorted = sorted(r["per_column"].items(), key=lambda x: -x[1]["missing_%"])[:20]
        names  = [c[0] for c in cols_sorted]
        values = [c[1]["missing_%"] for c in cols_sorted]
        colors = ["#e74c3c" if v > 50 else "#f39c12" if v > 20 else "#f0d060" for v in values]
        ax.barh(names, values, color=colors)
        ax.set_xlabel("Missing %")
        ax.set_title("Top columns by missing rate")
        ax.axvline(x=20, color="orange", linestyle="--", alpha=0.5, label="20% threshold")
        ax.axvline(x=50, color="red",    linestyle="--", alpha=0.5, label="50% threshold")
        ax.legend(fontsize=8)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close()
    else:
        st.success("No missing values detected!")

# ── D2: Uniqueness ───────────────────────────────────────────────
with tabs[1]:
    r = r_unique
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Exact duplicates",    f"{r['exact_duplicates']:,}")
    c2.metric("Duplicate rate",      f"{r['exact_dupe_rate_%']}%")
    c3.metric("Duplicate columns",   f"{len(r['duplicate_columns'])}")
    c4.metric("Constant columns",    f"{len(r['constant_columns'])}")

    if r["exact_duplicates"] > 0:
        st.warning(f"{r['exact_duplicates']} exact duplicate rows found. "
                   f"These represent {r['exact_dupe_rate_%']}% of all data.")
        with st.expander("Show duplicate rows (first 50)"):
            dupes = df[df.duplicated(keep=False)].head(50)
            st.dataframe(dupes, use_container_width=True)
    else:
        st.success("No exact duplicate rows found.")

    if r["duplicate_columns"]:
        st.warning("Duplicate columns detected (identical values, different names):")
        for a, b in r["duplicate_columns"]:
            st.write(f"  • `{a}` = `{b}`")

    if r["constant_columns"]:
        st.warning("Constant columns (zero variance — carry no information):")
        st.write(", ".join([f"`{c}`" for c in r["constant_columns"]]))

# ── D3: Consistency ──────────────────────────────────────────────
with tabs[2]:
    r = r_consist
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mixed-type cols",     f"{len(r['mixed_type_columns'])}")
    c2.metric("Date format cols",    f"{len(r['date_format_columns'])}")
    c3.metric("Case-issue cols",     f"{len(r['case_issue_columns'])}")
    c4.metric("Encoding issues",     f"{len(r['encoding_issues'])}")

    if r["mixed_type_columns"]:
        st.warning("Columns with mixed data types (numbers AND strings):")
        st.dataframe(pd.DataFrame(r["mixed_type_columns"]), use_container_width=True)

    if r["date_format_columns"]:
        st.warning("Columns with inconsistent date formats:")
        for d in r["date_format_columns"]:
            st.write(f"  • `{d['column']}` — {d['formats_found']} different formats found")

    if r["case_issue_columns"]:
        st.warning("Columns with case inconsistency (e.g. 'Male' vs 'male' vs 'MALE'):")
        st.dataframe(pd.DataFrame(r["case_issue_columns"]), use_container_width=True)

    if r["encoding_issues"]:
        st.warning("Encoding / special character issues found:")
        st.dataframe(pd.DataFrame(r["encoding_issues"]), use_container_width=True)

    if not any([r["mixed_type_columns"], r["date_format_columns"],
                r["case_issue_columns"], r["encoding_issues"]]):
        st.success("No consistency issues detected!")

# ── D4: Validity ─────────────────────────────────────────────────
with tabs[3]:
    r = r_valid
    c1, c2, c3 = st.columns(3)
    c1.metric("Outlier columns",     f"{len(r['outlier_columns'])}")
    c2.metric("Outlier cells",       f"{r['total_outlier_cells']:,}")
    c3.metric("Impossible values",   f"{len(r['impossible_values'])}")

    if r["outlier_columns"]:
        st.warning(f"Outliers detected (3×IQR method):")
        df_out = pd.DataFrame(r["outlier_columns"])
        st.dataframe(df_out, use_container_width=True)

        # Boxplots for top 6 outlier columns
        top_cols = [o["column"] for o in sorted(r["outlier_columns"],
                    key=lambda x: -x["outlier_%"])[:6]]
        if top_cols:
            fig, axes = plt.subplots(1, len(top_cols), figsize=(3 * len(top_cols), 3))
            if len(top_cols) == 1:
                axes = [axes]
            for ax, col in zip(axes, top_cols):
                ax.boxplot(df[col].dropna(), patch_artist=True,
                           boxprops=dict(facecolor="#f39c12", alpha=0.5))
                ax.set_title(col, fontsize=9)
                ax.set_xticks([])
            plt.suptitle("Outlier columns — boxplots", fontsize=10, y=1.02)
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close()

    if r["impossible_values"]:
        st.error("Impossible / domain-invalid values:")
        st.dataframe(pd.DataFrame(r["impossible_values"]), use_container_width=True)

    if r["future_date_columns"]:
        st.warning("Future dates found (possible data entry errors):")
        st.dataframe(pd.DataFrame(r["future_date_columns"]), use_container_width=True)

    if not any([r["outlier_columns"], r["impossible_values"], r["future_date_columns"]]):
        st.success("No validity issues detected!")

# ── D5: Accuracy ─────────────────────────────────────────────────
with tabs[4]:
    r = r_accuracy
    c1, c2 = st.columns(2)
    c1.metric("Highly skewed cols",  f"{len(r['skewed_columns'])}")
    c2.metric("Imbalanced cat. cols",f"{len(r['imbalanced_columns'])}")

    if r["skewed_columns"]:
        st.warning("Highly skewed numeric columns (|skewness| > 2):")
        st.dataframe(pd.DataFrame(r["skewed_columns"]), use_container_width=True)

    if r["imbalanced_columns"]:
        st.warning("Heavily imbalanced categorical columns (one class > 85%):")
        st.dataframe(pd.DataFrame(r["imbalanced_columns"]), use_container_width=True)

    if not r["skewed_columns"] and not r["imbalanced_columns"]:
        st.success("No significant accuracy issues detected!")

# ── D6: Structure ────────────────────────────────────────────────
with tabs[5]:
    r = r_struct
    c1, c2, c3 = st.columns(3)
    c1.metric("Bad column names",   f"{len(r['bad_column_names'])}")
    c2.metric("Wrong-type cols",    f"{len(r['wrong_type_cols'])}")
    c3.metric("Row/col ratio",      f"{r['row_col_ratio']}")

    if r["bad_column_names"]:
        st.warning("Column naming issues:")
        st.dataframe(pd.DataFrame(r["bad_column_names"]), use_container_width=True)

    if r["wrong_type_cols"]:
        st.warning("Columns stored as wrong type:")
        st.dataframe(pd.DataFrame(r["wrong_type_cols"]), use_container_width=True)

    for issue in r["general_issues"]:
        st.warning(issue)

    if not any([r["bad_column_names"], r["wrong_type_cols"], r["general_issues"]]):
        st.success("No structural issues detected!")

# ── D7: Correlation ──────────────────────────────────────────────
with tabs[6]:
    r = r_corr
    st.metric("High-corr pairs (>0.95)", f"{r['n_high_corr_pairs']}")

    if r["high_correlation_pairs"]:
        st.warning("Highly correlated feature pairs — potential redundancy or data leakage:")
        st.dataframe(pd.DataFrame(r["high_correlation_pairs"]), use_container_width=True)

    if r["redundant_columns"]:
        st.error("Redundant columns (near-perfect correlation > 0.999) — consider removing:")
        st.write(", ".join([f"`{c}`" for c in r["redundant_columns"]]))

    # Full correlation heatmap
    num_df = df.select_dtypes("number")
    if num_df.shape[1] >= 2:
        with st.expander("Show full correlation heatmap"):
            fig, ax = plt.subplots(figsize=(max(6, num_df.shape[1] * 0.7),
                                           max(5, num_df.shape[1] * 0.6)))
            import matplotlib.colors as mcolors
            corr_mat = num_df.corr()
            cmap = plt.cm.RdYlGn
            im   = ax.imshow(corr_mat, cmap=cmap, vmin=-1, vmax=1)
            ax.set_xticks(range(len(corr_mat.columns)))
            ax.set_yticks(range(len(corr_mat.columns)))
            ax.set_xticklabels(corr_mat.columns, rotation=45, ha="right", fontsize=8)
            ax.set_yticklabels(corr_mat.columns, fontsize=8)
            for i in range(len(corr_mat)):
                for j in range(len(corr_mat)):
                    val = corr_mat.iloc[i, j]
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                            fontsize=6, color="black" if abs(val) < 0.7 else "white")
            plt.colorbar(im, ax=ax, shrink=0.8)
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close()

    if not r["high_correlation_pairs"]:
        st.success("No high-correlation issues detected!")

# ── Full Report ──────────────────────────────────────────────────
with tabs[7]:
    st.subheader("Complete Quality Report")

    st.markdown(f"""
### Dataset Quality Score: **{dqs} / 100** — {grade}

**Formula applied:**
```
DQS = (Σ Wᵢ × Dᵢ) × Size_Factor × Diversity_Bonus
    = {raw_score:.2f} × {size_factor} × {diversity_bonus}
    = {dqs}
```

| Factor | Value | Explanation |
|--------|-------|-------------|
| Raw weighted score | {raw_score} | Weighted average of all 7 dimension scores |
| Size factor | {size_factor} | log₁₀({len(df)}+1)/4 — penalizes tiny datasets |
| Diversity bonus | {diversity_bonus} | {df.dtypes.nunique()} dtype(s) in schema |
| **Final DQS** | **{dqs}** | Clamped to [0, 100] |
""")

    st.markdown("### Dimension scores summary")
    summary_data = {
        "Dimension":   ["Completeness", "Uniqueness", "Consistency",
                         "Validity", "Accuracy", "Structure", "Correlation"],
        "Weight":      [round(WEIGHTS[k], 3) for k in WEIGHTS],
        "Score":       [r_complete["score"], r_unique["score"], r_consist["score"],
                         r_valid["score"], r_accuracy["score"], r_struct["score"], r_corr["score"]],
        "Weighted contribution": [round(WEIGHTS[k] * scores_dict[k], 2) for k in WEIGHTS],
        "Status":      []
    }
    for s in summary_data["Score"]:
        summary_data["Status"].append(
            "✅ Excellent" if s >= 90 else
            "🟢 Good"      if s >= 75 else
            "🟡 Fair"      if s >= 60 else
            "🟠 Poor"      if s >= 40 else
            "🔴 Critical"
        )
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

    st.markdown("### Recommended fixes (prioritized by weight × severity)")
    fixes = []
    if r_complete["missing_rate"] > 5:
        fixes.append(("🔴 HIGH",  "Completeness", f"Handle {r_complete['total_missing']:,} missing values — impute, drop, or flag"))
    if r_unique["exact_duplicates"] > 0:
        fixes.append(("🔴 HIGH",  "Uniqueness",   f"Remove {r_unique['exact_duplicates']:,} exact duplicate rows"))
    if r_consist["case_issue_columns"]:
        fixes.append(("🟡 MED",   "Consistency",  "Standardize text case — call .str.lower().str.strip() on categorical columns"))
    if r_valid["impossible_values"]:
        fixes.append(("🔴 HIGH",  "Validity",     "Investigate & remove impossible values (negative ages, prices, out-of-range percents)"))
    if r_valid["outlier_columns"]:
        fixes.append(("🟡 MED",   "Validity",     "Investigate outliers — use IQR capping or log-transform for skewed features"))
    if r_struct["wrong_type_cols"]:
        fixes.append(("🟡 MED",   "Structure",    "Convert text-stored numbers: pd.to_numeric(df[col], errors='coerce')"))
    if r_corr["redundant_columns"]:
        fixes.append(("🟢 LOW",   "Correlation",  f"Drop redundant columns: {r_corr['redundant_columns']}"))
    if r_accuracy["skewed_columns"]:
        fixes.append(("🟢 LOW",   "Accuracy",     "Apply log/sqrt transform to highly skewed numeric columns before ML"))

    if fixes:
        fix_df = pd.DataFrame(fixes, columns=["Priority", "Dimension", "Recommended Action"])
        st.dataframe(fix_df, use_container_width=True)
    else:
        st.success("Dataset looks clean — no critical fixes required!")

    # Download report as CSV
    report_rows = []
    for dim, score, w in zip(
        ["Completeness","Uniqueness","Consistency","Validity","Accuracy","Structure","Correlation"],
        [r_complete["score"], r_unique["score"], r_consist["score"],
         r_valid["score"], r_accuracy["score"], r_struct["score"], r_corr["score"]],
        list(WEIGHTS.values())
    ):
        report_rows.append({"Dimension": dim, "Weight": round(w,3),
                             "Score": score, "Weighted": round(w*score,2)})
    report_rows.append({"Dimension": "DQS (Final)", "Weight": "",
                         "Score": dqs, "Weighted": ""})
    report_df = pd.DataFrame(report_rows)
    st.download_button(
        "Download full quality report (CSV)",
        report_df.to_csv(index=False).encode(),
        f"quality_report_{file.name.split('.')[0]}.csv",
        "text/csv"
    )