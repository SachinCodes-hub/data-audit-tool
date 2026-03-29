#DQS calcualtion quality score checker - formula

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re
from utils.helpers import PLACEHOLDERS, compute_dqs

def show_fault_detection(df):
    st.header("🚨 Fault Detection — Data Quality Score")

    scores = {"_df": df}

    # ── D1: Completeness ──────────────────────────────────────────
    with st.expander("D1 — Completeness (Weight: 28%)", expanded=True):
        null_count = df.isnull().sum().sum()
        empty_str = placeholder_count = whitespace_count = 0
        for col in df.select_dtypes("object").columns:
            vals = df[col].dropna().astype(str)
            empty_str         += (vals.str.strip() == "").sum()
            whitespace_count  += vals.str.strip().eq("").sum() - (vals == "").sum()
            placeholder_count += vals.str.strip().str.lower().isin(PLACEHOLDERS).sum()

        total_missing = null_count + empty_str + whitespace_count + placeholder_count
        missing_rate  = total_missing / (df.shape[0] * df.shape[1])
        scores["completeness"] = max(0, 100 - missing_rate * 100 * 1.5)

        col1, col2 = st.columns(2)
        col1.metric("Total Missing Values", int(total_missing))
        col2.metric("Score", f"{scores['completeness']:.1f} / 100")

        miss_per_col = df.isnull().sum()
        miss_per_col = miss_per_col[miss_per_col > 0]
        if not miss_per_col.empty:
            fig = px.bar(miss_per_col.reset_index(),
                         x="index", y=0,
                         labels={"index": "Column", "0": "Missing Count"},
                         title="Missing Values per Column",
                         color=0, color_continuous_scale="Reds")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ No missing values!")

    # ── D2: Uniqueness ────────────────────────────────────────────
    with st.expander("D2 — Uniqueness (Weight: 18%)"):
        exact_dupes = df.duplicated().sum()
        dupe_rate   = exact_dupes / len(df)
        scores["uniqueness"] = max(0, 100 - dupe_rate * 100 * 2)

        col1, col2 = st.columns(2)
        col1.metric("Duplicate Rows", int(exact_dupes))
        col2.metric("Score", f"{scores['uniqueness']:.1f} / 100")

        if exact_dupes > 0:
            st.warning(f"⚠️ {exact_dupes} duplicate rows ({dupe_rate:.1%} of dataset)")
        else:
            st.success("✅ No duplicate rows!")

    # ── D3: Consistency ───────────────────────────────────────────
    with st.expander("D3 — Consistency (Weight: 16%)"):
        mixed_type_cols = []
        case_issue_cols = []
        for col in df.select_dtypes("object").columns:
            vals = df[col].dropna()
            if len(vals) == 0:
                continue
            numeric = pd.to_numeric(vals, errors="coerce").notnull().sum()
            strings = vals.astype(str).str.match(r"^[A-Za-z]").sum()
            if 0 < numeric < len(vals) and strings > 0:
                mixed_type_cols.append(col)
            if df[col].nunique() <= 100:
                if vals.astype(str).str.strip().str.lower().nunique() < vals.astype(str).str.strip().nunique():
                    case_issue_cols.append(col)

        total_issues = len(mixed_type_cols) + len(case_issue_cols)
        scores["consistency"] = max(0, 100 - (total_issues / df.shape[1]) * 100 * 1.8)

        col1, col2 = st.columns(2)
        col1.metric("Consistency Issues", total_issues)
        col2.metric("Score", f"{scores['consistency']:.1f} / 100")

        if mixed_type_cols:
            st.warning(f"Mixed-type columns: {', '.join(mixed_type_cols)}")
        if case_issue_cols:
            st.warning(f"Case inconsistency in: {', '.join(case_issue_cols)}")
        if total_issues == 0:
            st.success("✅ No consistency issues!")

    # ── D4: Validity ──────────────────────────────────────────────
    with st.expander("D4 — Validity (Weight: 16%)"):
        outlier_cols = []
        impossible = []
        for col in df.select_dtypes("number").columns:
            data = df[col].dropna()
            if len(data) < 4:
                continue
            Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
            IQR = Q3 - Q1
            if IQR > 0:
                n_out = ((data < Q1 - 3*IQR) | (data > Q3 + 3*IQR)).sum()
                if n_out > 0:
                    outlier_cols.append({"Column": col, "Outliers": int(n_out)})
            c = col.lower()
            if any(k in c for k in ["age", "years"]) and ((data < 0) | (data > 150)).any():
                impossible.append(col)
            if any(k in c for k in ["price", "salary", "cost", "amount"]) and (data < 0).any():
                impossible.append(col)

        total_outliers = sum(o["Outliers"] for o in outlier_cols)
        total_num_cells = sum(df[c].dropna().shape[0] for c in df.select_dtypes("number").columns)
        outlier_rate = total_outliers / max(1, total_num_cells)
        scores["validity"] = max(0, 100 - outlier_rate * 60 - len(impossible) / max(1, len(df)) * 100)

        col1, col2 = st.columns(2)
        col1.metric("Outlier Cells Found", total_outliers)
        col2.metric("Score", f"{scores['validity']:.1f} / 100")

        if outlier_cols:
            st.dataframe(pd.DataFrame(outlier_cols), use_container_width=True)
        if impossible:
            st.error(f"Impossible values in: {', '.join(impossible)}")
        if not outlier_cols and not impossible:
            st.success("✅ No validity issues!")

    # ── D5: Accuracy ──────────────────────────────────────────────
    with st.expander("D5 — Accuracy (Weight: 10%)"):
        skewed_cols = []
        imbalanced = []
        for col in df.select_dtypes("number").columns:
            sk = df[col].dropna().skew()
            if abs(sk) > 2.0:
                skewed_cols.append({"Column": col, "Skewness": round(float(sk), 3)})
        for col in df.select_dtypes("object").columns:
            vc = df[col].value_counts(normalize=True)
            if len(vc) >= 2 and float(vc.iloc[0]) > 0.85:
                imbalanced.append(col)

        skew_penalty = sum(min(abs(s["Skewness"]) / 20, 0.05) for s in skewed_cols)
        cat_cols = df.select_dtypes("object").shape[1]
        imbalance_penalty = (len(imbalanced) / cat_cols * 20) if cat_cols > 0 else 0
        scores["accuracy"] = max(0, 100 - skew_penalty * 100 - imbalance_penalty)

        col1, col2 = st.columns(2)
        col1.metric("Skewed Columns", len(skewed_cols))
        col2.metric("Score", f"{scores['accuracy']:.1f} / 100")

        if skewed_cols:
            st.dataframe(pd.DataFrame(skewed_cols), use_container_width=True)
        if imbalanced:
            st.warning(f"Imbalanced categoricals: {', '.join(imbalanced)}")

    # ── D6: Structure ─────────────────────────────────────────────
    with st.expander("D6 — Structure (Weight: 7%)"):
        bad_col_names = [c for c in df.columns
                         if str(c).strip() == "" or re.match(r"^Unnamed", str(c))
                         or re.search(r"[^a-zA-Z0-9_ ]", str(c))]
        wrong_type_cols = [c for c in df.select_dtypes("object").columns
                           if pd.to_numeric(df[c], errors="coerce").notnull().mean() > 0.95]

        struct_penalty = (len(bad_col_names) + len(wrong_type_cols)) / df.shape[1] * 30
        ratio_penalty  = 10 if (df.shape[0] / df.shape[1]) < 5 else 0
        scores["structure"] = max(0, 100 - struct_penalty - ratio_penalty)

        col1, col2 = st.columns(2)
        col1.metric("Structural Issues", len(bad_col_names) + len(wrong_type_cols))
        col2.metric("Score", f"{scores['structure']:.1f} / 100")

        if bad_col_names:
            st.warning(f"Bad column names: {bad_col_names}")
        if wrong_type_cols:
            st.warning(f"Should be numeric: {wrong_type_cols}")
        if not bad_col_names and not wrong_type_cols:
            st.success("✅ Structure looks clean!")

    # ── D7: Correlation ───────────────────────────────────────────
    with st.expander("D7 — Correlation (Weight: 5%)"):
        high_corr_pairs = []
        num_df = df.select_dtypes("number").dropna(axis=1, how="all")
        if num_df.shape[1] >= 2:
            corr = num_df.corr().abs()
            c = corr.columns
            for i in range(len(c)):
                for j in range(i + 1, len(c)):
                    r = float(corr.iloc[i, j])
                    if r > 0.95:
                        high_corr_pairs.append({"Col A": c[i], "Col B": c[j], "r": round(r, 4)})

            fig = px.imshow(num_df.corr(), text_auto=".2f",
                            color_continuous_scale="RdBu_r",
                            title="Correlation Matrix")
            st.plotly_chart(fig, use_container_width=True)

        scores["correlation"] = max(0, 100 - len(high_corr_pairs) * 3)
        col1, col2 = st.columns(2)
        col1.metric("High Correlation Pairs (>0.95)", len(high_corr_pairs))
        col2.metric("Score", f"{scores['correlation']:.1f} / 100")

        if high_corr_pairs:
            st.dataframe(pd.DataFrame(high_corr_pairs), use_container_width=True)

    # ── DQS Final Score ───────────────────────────────────────────
    st.divider()
    st.subheader("🏆 Dataset Quality Score (DQS)")

    result = compute_dqs(scores)
    dqs = result["dqs"]
    grade = "A 🟢" if dqs >= 85 else "B 🟡" if dqs >= 70 else "C 🟠" if dqs >= 50 else "D 🔴"
    color = "#00c853" if dqs >= 85 else "#ffd600" if dqs >= 70 else "#ff6d00" if dqs >= 50 else "#d50000"

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"""
        <div style='text-align:center;padding:30px;border-radius:16px;
                    background:{color}22;border:2px solid {color}'>
            <div style='font-size:56px;font-weight:bold;color:{color}'>{dqs}</div>
            <div style='font-size:22px;color:{color}'>Grade: {grade}</div>
            <div style='color:#888'>out of 100</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        dim_scores = {k: v for k, v in scores.items() if k != "_df"}
        fig = px.bar(
            x=list(dim_scores.keys()),
            y=list(dim_scores.values()),
            labels={"x": "Dimension", "y": "Score"},
            color=list(dim_scores.values()),
            color_continuous_scale="RdYlGn",
            range_y=[0, 100],
            title="Score by Dimension"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.info(f"Raw: {result['raw']} | Size Factor: {result['size_factor']} | Diversity Bonus: {result['diversity_bonus']}")