import streamlit as st
import pandas as pd
from utils.helpers import get_memory_usage

def show_overview(df, file_name: str, file_size: int):

    # ── Page header ───────────────────────────────────────────────
    st.markdown(f"""
    <div style='margin-bottom: 28px'>
        <span class='das-label'>DATASET OVERVIEW</span>
        <div style='display: flex; align-items: center; gap: 8px; flex-wrap: wrap'>
            <span style='font-family: "JetBrains Mono", monospace;
                         font-size: 14px; font-weight: 600'>
                {file_name}
            </span>
            <span class='das-pill'>{file_size:,} bytes</span>
            <span class='das-pill'>{df.shape[0]:,} rows</span>
            <span class='das-pill'>{df.shape[1]} cols</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI row ───────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Rows",       f"{df.shape[0]:,}")
    c2.metric("Columns",    df.shape[1])
    c3.metric("Memory",     get_memory_usage(df))
    c4.metric("Null Cells", f"{df.isnull().sum().sum():,}")
    c5.metric("Duplicates", f"{df.duplicated().sum():,}")

    st.divider()

    # ── Preview ───────────────────────────────────────────────────
    st.markdown("#### Preview")
    tab_head, tab_tail = st.tabs(["First 5 rows", "Last 5 rows"])
    with tab_head:
        st.dataframe(df.head(), use_container_width=True)
    with tab_tail:
        st.dataframe(df.tail(), use_container_width=True)

    st.divider()

    # ── Column Details ────────────────────────────────────────────
    st.markdown("#### Column Details")
    details = pd.DataFrame({
        "Column":   df.columns,
        "Dtype":    df.dtypes.astype(str).values,
        "Non-Null": df.notnull().sum().values,
        "Null %":   (df.isnull().mean() * 100).round(2).values,
        "Unique":   df.nunique().values,
        "Sample":   [str(df[c].dropna().iloc[0])
                     if df[c].dropna().shape[0] > 0 else "—"
                     for c in df.columns],
    })
    st.dataframe(details, use_container_width=True)

    st.divider()

    # ── Statistical Summary ───────────────────────────────────────
    st.markdown("#### Statistical Summary")
    st.dataframe(df.describe(include="all"), use_container_width=True)