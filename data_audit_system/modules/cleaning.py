import streamlit as st
import pandas as pd
import numpy as np
from utils.helpers import PLACEHOLDERS, compute_dqs
from modules.runcleaningpipeline import run_cleaning_pipeline_ui
import io

def show_cleaning(df, uploaded_file):
    st.header("⚡ CleanIQ Pipeline")
    st.info("This will automatically clean your dataset using 8 steps. The cleaned file is available for download.")

    
    _, col_c, _ = st.columns([1.5, 2, 1.5])
    with col_c:
        st.markdown('<div class="launch-btn">', unsafe_allow_html=True)
        launch = st.button("⚡ Launch CleanIQ", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if launch:
        
        run_cleaning_pipeline_ui(df)

        
        df_cleaned = df.copy()

        # Step 1 — Column names
        df_cleaned.columns = (
            df_cleaned.columns
            .str.strip().str.lower()
            .str.replace(r"[^a-z0-9_]", "_", regex=True)
            .str.replace(r"_+", "_", regex=True)
            .str.strip("_")
        )

        # Step 2 — Empty rows
        df_cleaned = df_cleaned.dropna(how="all").reset_index(drop=True)

        # Step 3 — Placeholders → NaN
        for col in df_cleaned.select_dtypes("object").columns:
            df_cleaned[col] = df_cleaned[col].apply(
                lambda x: np.nan if str(x).strip().lower() in PLACEHOLDERS else x)

        # Step 4 — Drop columns >70% missing
        df_cleaned = df_cleaned.dropna(thresh=int(0.3 * len(df_cleaned)), axis=1)

        # Step 5 — Fill missing values
        for col in df_cleaned.select_dtypes("number").columns:
            df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].median())
        for col in df_cleaned.select_dtypes("object").columns:
            mode = df_cleaned[col].mode()
            df_cleaned[col] = df_cleaned[col].fillna(mode[0] if not mode.empty else "unknown")

        # Step 6 — Duplicates
        df_cleaned = df_cleaned.drop_duplicates(keep="first").reset_index(drop=True)

        # Step 7 — Formatting
        for col in df_cleaned.select_dtypes("object").columns:
            df_cleaned[col] = df_cleaned[col].astype(str).str.strip().str.lower()

        # Step 8 — Outlier capping
        for col in df_cleaned.select_dtypes("number").columns:
            Q1, Q3 = df_cleaned[col].quantile(0.25), df_cleaned[col].quantile(0.75)
            IQR = Q3 - Q1
            if IQR > 0:
                df_cleaned[col] = df_cleaned[col].clip(Q1 - 3*IQR, Q3 + 3*IQR)

        # Save to session state 
        st.session_state['cleaned_df'] = df_cleaned
        st.session_state['original_name'] = uploaded_file.name.rsplit(".", 1)[0]

        # Before vs After 
        st.subheader("Before vs After")
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", df.shape[0], delta=df_cleaned.shape[0] - df.shape[0])
        col2.metric("Columns", df.shape[1], delta=df_cleaned.shape[1] - df.shape[1])
        col3.metric("Missing Cells", int(df.isnull().sum().sum()),
                    delta=int(df_cleaned.isnull().sum().sum() - df.isnull().sum().sum()))

        # DQS Comparison
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

        #  Preview 
        st.subheader("Cleaned Dataset Preview")
        st.dataframe(df_cleaned.head(20), use_container_width=True)

    #  Download 
    if st.session_state.get('cleaned_df') is not None:
        df_cleaned  = st.session_state['cleaned_df']
        original_name = st.session_state.get('original_name', 'dataset')

        st.subheader("⬇️ Export Cleaned Dataset")
        fmt = st.radio("Download format", ["CSV", "Excel"], horizontal=True)

        if fmt == "CSV":
            data  = df_cleaned.to_csv(index=False).encode("utf-8")
            fname = f"{original_name}_cleaniq.csv"
            mime  = "text/csv"
        else:
            output = io.BytesIO()
            df_cleaned.to_excel(output, index=False, engine="openpyxl")
            output.seek(0)
            data  = output
            fname = f"{original_name}_cleaniq.xlsx"
            mime  = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        _, dl_col, _ = st.columns([1.5, 2, 1.5])
        with dl_col:
            st.download_button(
                "⬇️ Download Audit-Cleaned File",
                data=data,
                file_name=fname,
                mime=mime,
                use_container_width=True
            )