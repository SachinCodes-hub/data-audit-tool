#all the constants the placeholders which are frequently used will be defined here and used everytime.


import pandas as pd
import numpy as np

# This placeholder set is used in both fault_detection and cleaning
PLACEHOLDERS = {
    "n/a", "na", "none", "null", "nil", "-", "--", "?",
    "unknown", "undefined", "missing", "tbd", "tbc", "#n/a"
}

def load_file(uploaded_file):
    """Load CSV or Excel file into a DataFrame."""
    if uploaded_file.name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError("Unsupported file format.")

def get_memory_usage(df):
    """Return memory usage as a readable string."""
    return f"{df.memory_usage(deep=True).sum():,} bytes"

def compute_dqs(scores: dict) -> dict:
    """
    Given a dict of dimension scores (0-100),
    return raw_score, size_factor, diversity_bonus, and final DQS.
    """
    WEIGHTS = {
        "completeness": 0.28,
        "uniqueness":   0.18,
        "consistency":  0.16,
        "validity":     0.16,
        "accuracy":     0.10,
        "structure":    0.07,
        "correlation":  0.05,
    }
    df_ref = scores.get("_df")  # pass df as "_df" key
    raw = sum(WEIGHTS[k] * scores[k] for k in WEIGHTS if k in scores)
    size_factor = max(0.5, min(1.0, np.log10(len(df_ref) + 1) / 4.0)) if df_ref is not None else 1.0
    diversity_bonus = min(1.05, 1 + (df_ref.dtypes.nunique() - 1) * 0.01) if df_ref is not None else 1.0
    dqs = round(min(100, max(0, raw * size_factor * diversity_bonus)), 2)
    return {
        "raw": round(raw, 2),
        "size_factor": size_factor,
        "diversity_bonus": diversity_bonus,
        "dqs": dqs
    }