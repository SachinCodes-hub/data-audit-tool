# upload --- overview ---- analysis


import streamlit as st
from utils.helpers import get_memory_usage

def show_overview(df, file):
    st.header("📊 Dataset Overview")

    # ── File Info ──────────────────────────────────────────────────
    st.subheader("File Info")
    col1, col2 = st.columns(2)
    col1.write(f"**File name:** {file.name}")
    col2.write(f"**File size:** {file.size:,} bytes")

    # ── Shape ──────────────────────────────────────────────────────
    st.subheader("Shape")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Rows", f"{df.shape[0]:,}")
    c2.metric("Total Columns", df.shape[1])
    c3.metric("Memory Usage", get_memory_usage(df))

    # ── Preview ────────────────────────────────────────────────────
    st.subheader("Preview")
    tab_head, tab_tail = st.tabs(["First 5 rows", "Last 5 rows"])
    with tab_head:
        st.dataframe(df.head(), use_container_width=True)
    with tab_tail:
        st.dataframe(df.tail(), use_container_width=True)

    # ── Column Details ─────────────────────────────────────────────
    st.subheader("Column Details")
    import pandas as pd
    details = pd.DataFrame({
        "Column":    df.columns,
        "Dtype":     df.dtypes.values,
        "Non-Null":  df.notnull().sum().values,
        "Null %":    (df.isnull().mean() * 100).round(2).values,
        "Unique":    df.nunique().values,
    })
    st.dataframe(details, use_container_width=True)

    # ── Statistical Summary ────────────────────────────────────────
    st.subheader("Statistical Summary")
    st.dataframe(df.describe(include="all"), use_container_width=True)