#dataset cleaning - accuracy and comparison . 


import streamlit as st
import pandas as pd
import numpy as np
import re
from utils.helpers import PLACEHOLDERS, compute_dqs
from modules.runcleaningpipeline import run_cleaning_pipeline_ui
def show_cleaning(df):
    st.header("🧹 Cleaning Pipeline")
    st.info("This will automatically clean your dataset using 8 steps. The cleaned file is available for download.")

    if st.button("▶ Run Cleaning Pipeline"):
        run_cleaning_pipeline_ui(df)
        # your actual cleaning logic here
        cleaned_df = your_existing_clean_function(df)
        st.session_state['cleaned_df'] = cleaned_df
        with st.status("Cleaning in progress...", expanded=True) as status:

            # Step 1 — Column names
            st.write("Step 1: Standardizing column names...")
            df_cleaned.columns = (
                df_cleaned.columns
                .str.strip().str.lower()
                .str.replace(r"[^a-z0-9_]", "_", regex=True)
                .str.replace(r"_+", "_", regex=True)
                .str.strip("_")
            )

            # Step 2 — Empty rows
            st.write("Step 2: Removing fully empty rows...")
            df_cleaned = df_cleaned.dropna(how="all").reset_index(drop=True)

            # Step 3 — Placeholders → NaN
            st.write("Step 3: Converting placeholders to NaN...")
            for col in df_cleaned.select_dtypes("object").columns:
                df_cleaned[col] = df_cleaned[col].apply(
                    lambda x: np.nan if str(x).strip().lower() in PLACEHOLDERS else x)

            # Step 4 — Drop columns >70% missing
            st.write("Step 4: Dropping columns with >70% missing...")
            df_cleaned = df_cleaned.dropna(thresh=int(0.3 * len(df_cleaned)), axis=1)

            # Step 5 — Fill missing values
            st.write("Step 5: Filling remaining missing values...")
            for col in df_cleaned.select_dtypes("number").columns:
                df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].median())
            for col in df_cleaned.select_dtypes("object").columns:
                mode = df_cleaned[col].mode()
                df_cleaned[col] = df_cleaned[col].fillna(mode[0] if not mode.empty else "unknown")

            # Step 6 — Duplicates
            st.write("Step 6: Removing duplicates...")
            df_cleaned = df_cleaned.drop_duplicates(keep="first").reset_index(drop=True)

            # Step 7 — Formatting
            st.write("Step 7: Standardizing text formatting...")
            for col in df_cleaned.select_dtypes("object").columns:
                df_cleaned[col] = df_cleaned[col].astype(str).str.strip().str.lower()

            # Step 8 — Outlier capping
            st.write("Step 8: Capping outliers (Winsorize at 3×IQR)...")
            for col in df_cleaned.select_dtypes("number").columns:
                Q1, Q3 = df_cleaned[col].quantile(0.25), df_cleaned[col].quantile(0.75)
                IQR = Q3 - Q1
                if IQR > 0:
                    df_cleaned[col] = df_cleaned[col].clip(Q1 - 3*IQR, Q3 + 3*IQR)

            status.update(label="✅ Cleaning complete!", state="complete")

        # ── Before vs After ───────────────────────────────────────
        st.subheader("Before vs After")
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", df.shape[0], delta=df_cleaned.shape[0] - df.shape[0])
        col2.metric("Columns", df.shape[1], delta=df_cleaned.shape[1] - df.shape[1])
        col3.metric("Missing Cells", int(df.isnull().sum().sum()),
                    delta=int(df_cleaned.isnull().sum().sum() - df.isnull().sum().sum()))

        # ── DQS Comparison ────────────────────────────────────────
        st.subheader("DQS: Before vs After Cleaning")

        def quick_dqs(d):
            miss = d.isnull().sum().sum() / (d.shape[0] * d.shape[1])
            dup  = d.duplicated().sum() / len(d)
            return compute_dqs({
                "_df": d,
                "completeness": max(0, 100 - miss * 150),
                "uniqueness":   max(0, 100 - dup * 200),
                "consistency":  80,
                "validity":     80,
                "accuracy":     80,
                "structure":    80,
                "correlation":  80,
            })["dqs"]

        dqs_before = quick_dqs(df)
        dqs_after  = quick_dqs(df_cleaned)

        c1, c2 = st.columns(2)
        c1.metric("DQS Before", f"{dqs_before} / 100")
        c2.metric("DQS After",  f"{dqs_after} / 100",
                  delta=round(dqs_after - dqs_before, 2))

        # ── Preview ───────────────────────────────────────────────
        st.subheader("Cleaned Dataset Preview")
        st.dataframe(df_cleaned.head(20), use_container_width=True)

        # ── Download ──────────────────────────────────────────────
        csv = df_cleaned.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Cleaned Dataset (.csv)",
            data=csv,
            file_name="cleaned_dataset.csv",
            mime="text/csv",
        )