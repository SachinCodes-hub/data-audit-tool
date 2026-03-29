import pandas as pd
import numpy as np
import streamlit as st

PLACEHOLDERS = {
    "n/a", "na", "none", "null", "nil", "-", "--", "?",
    "unknown", "undefined", "missing", "tbd", "tbc", "#n/a"
}

MAX_FILE_SIZE_MB = 100  # change this if you want to allow bigger files
MAX_ROWS = 500_000      # safety cap — beyond this pandas gets slow


def load_file(uploaded_file) -> pd.DataFrame:
    """
    Robust file loader.
    Handles: CSV, Excel (single + multi-sheet), size limits,
    empty files, bad formats, encoding issues.
    Returns a clean DataFrame or raises a descriptive ValueError.
    """

    # ── 1. File size check ───────────────────────────────────────
    # Why: A 500MB file will crash Streamlit Cloud (only 1GB RAM)
    size_mb = uploaded_file.size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(
            f"File is {size_mb:.1f} MB — limit is {MAX_FILE_SIZE_MB} MB. "
            f"Try uploading a sample or subset of your data."
        )

    name = uploaded_file.name.lower()

    # ── 2. CSV loading ───────────────────────────────────────────
    if name.endswith(".csv"):
        df = _load_csv(uploaded_file)

    # ── 3. Excel loading ─────────────────────────────────────────
    elif name.endswith((".xlsx", ".xls")):
        df = _load_excel(uploaded_file)

    else:
        raise ValueError(
            f"Unsupported format: '{uploaded_file.name}'. "
            f"Please upload a .csv or .xlsx file."
        )

    # ── 4. Empty file check ──────────────────────────────────────
    # Why: An empty DataFrame will crash every downstream function
    if df is None or df.empty:
        raise ValueError(
            "The file appears to be empty — no rows of data found. "
            "Please check the file and try again."
        )

    # ── 5. Minimum viable shape ──────────────────────────────────
    # Why: A file with 0 columns (just whitespace) is useless
    if df.shape[1] == 0:
        raise ValueError(
            "No columns detected. The file may be blank or incorrectly formatted."
        )

    # ── 6. Row cap ───────────────────────────────────────────────
    # Why: 1M row files won't crash but will be very slow
    if len(df) > MAX_ROWS:
        df = df.head(MAX_ROWS)
        st.warning(
            f"⚠️ Your file has more than {MAX_ROWS:,} rows. "
            f"Only the first {MAX_ROWS:,} rows are loaded for performance."
        )

    return df


def _load_csv(uploaded_file) -> pd.DataFrame:
    """
    Try multiple encodings. Why: files from Excel/Windows often
    use latin-1 instead of UTF-8 and will crash pd.read_csv.
    """
    encodings = ["utf-8", "latin-1", "cp1252", "utf-8-sig"]

    for enc in encodings:
        try:
            uploaded_file.seek(0)  # reset pointer before each attempt
            df = pd.read_csv(uploaded_file, encoding=enc)
            return df
        except UnicodeDecodeError:
            continue  # try next encoding
        except pd.errors.EmptyDataError:
            raise ValueError("CSV file is empty — no data found.")
        except pd.errors.ParserError as e:
            raise ValueError(f"CSV could not be parsed — it may be corrupted. Detail: {e}")

    raise ValueError(
        "Could not read CSV with any known encoding (tried UTF-8, Latin-1, CP1252). "
        "Try saving the file as UTF-8 CSV from Excel."
    )


def _load_excel(uploaded_file) -> pd.DataFrame:
    """
    Handle single and multi-sheet Excel files.
    Why: pd.read_excel only reads sheet 0 by default —
    users with data on other sheets get an empty result silently.
    """
    try:
        uploaded_file.seek(0)
        xl = pd.ExcelFile(uploaded_file)
    except Exception as e:
        raise ValueError(f"Could not open Excel file — it may be corrupted. Detail: {e}")

    sheet_names = xl.sheet_names

    # Single sheet — just load it
    if len(sheet_names) == 1:
        df = xl.parse(sheet_names[0])
        return df

    # Multiple sheets — let user pick
    # Why: silently picking sheet 0 is a hidden bug
    st.info(f"📋 This Excel file has **{len(sheet_names)} sheets**: {', '.join(sheet_names)}")
    chosen = st.selectbox(
        "Which sheet contains your data?",
        options=sheet_names,
        key="sheet_selector"
    )

    # st.stop() trick: don't proceed until user picks
    # (selectbox always has a value so just parse chosen)
    df = xl.parse(chosen)
    return df


def get_memory_usage(df: pd.DataFrame) -> str:
    return f"{df.memory_usage(deep=True).sum():,} bytes"


def compute_dqs(scores: dict) -> dict:
    WEIGHTS = {
        "completeness": 0.28,
        "uniqueness":   0.18,
        "consistency":  0.16,
        "validity":     0.16,
        "accuracy":     0.10,
        "structure":    0.07,
        "correlation":  0.05,
    }
    df_ref = scores.get("_df")
    raw = sum(WEIGHTS[k] * scores[k] for k in WEIGHTS if k in scores)
    size_factor     = max(0.5, min(1.0, np.log10(len(df_ref) + 1) / 4.0)) if df_ref is not None else 1.0
    diversity_bonus = min(1.05, 1 + (df_ref.dtypes.nunique() - 1) * 0.01) if df_ref is not None else 1.0
    dqs = round(min(100, max(0, raw * size_factor * diversity_bonus)), 2)
    return {
        "raw":             round(raw, 2),
        "size_factor":     size_factor,
        "diversity_bonus": diversity_bonus,
        "dqs":             dqs
    }