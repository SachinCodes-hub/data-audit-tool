import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
from utils.helpers import PLACEHOLDERS

def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"
        
        
        
def show_fault_detection(df):
    st.header("🚨 Fault Detection — Data Quality Score")
    st.caption("Scoring aligned with ISO 25012 Data Quality Standard")

    scores = {}      
    findings = {}    

    
    # D1 — COMPLETENESS (28%)
    # ISO def: degree to which data has values for all expected attributes
    
    with st.expander("D1 — Completeness (28%)", expanded=True):

        null_count = df.isnull().sum().sum()
        total_cells = df.shape[0] * df.shape[1]

        # Detect disguised nulls (placeholders + empty strings)
        disguised = 0
        for col in df.select_dtypes("object").columns:
            vals = df[col].dropna().astype(str)
            disguised += vals.str.strip().str.lower().isin(PLACEHOLDERS).sum()
            disguised += (vals.str.strip() == "").sum()

        true_missing = null_count + disguised
        missing_rate = true_missing / total_cells

        # Tiered penalty — not linear
        # Why: 2% missing is noise, 40% missing is a crisis
        if missing_rate == 0:
            score = 100.0
        elif missing_rate < 0.01:      # <1% missing → tiny penalty
            score = 98.0
        elif missing_rate < 0.05:      # 1–5%
            score = 90 - (missing_rate * 200)
        elif missing_rate < 0.20:      # 5–20%
            score = 80 - (missing_rate * 150)
        else:                          # >20% → severe
            score = max(0, 50 - (missing_rate * 100))

        scores["completeness"] = round(score, 2)

        # Per-column breakdown
        col_missing = (df.isnull().sum() / len(df) * 100).round(1)
        col_missing = col_missing[col_missing > 0].sort_values(ascending=False)

        f = []
        critical = col_missing[col_missing > 40]
        moderate = col_missing[(col_missing > 5) & (col_missing <= 40)]
        if len(critical):
            f.append(f"🔴 {len(critical)} column(s) missing >40% of values: {', '.join(critical.index.tolist())}")
        if len(moderate):
            f.append(f"🟡 {len(moderate)} column(s) missing 5–40%: {', '.join(moderate.index.tolist())}")
        if disguised:
            f.append(f"🟠 {disguised:,} cells contain disguised nulls (e.g. 'N/A', 'unknown', empty strings)")
        if not f:
            f.append("✅ No missing or disguised null values found")
        findings["completeness"] = f

        _render_dimension("D1 — Completeness", scores["completeness"], findings["completeness"])

        if not col_missing.empty:
            fig = px.bar(
                col_missing.reset_index(),
                x="index", y=col_missing.name,
                labels={"index": "Column", col_missing.name: "Missing %"},
                color=col_missing.values,
                color_continuous_scale="Reds",
                title="Missing % per Column"
            )
            st.plotly_chart(fig, use_container_width=True)

    
    # D2 — UNIQUENESS (18%)
    # ISO def: degree to which data is free from duplication
    
    with st.expander("D2 — Uniqueness (18%)"):

        exact_dupes = df.duplicated().sum()
        dupe_rate   = exact_dupes / len(df)

        # Constant columns — zero information value
        constant_cols = [c for c in df.columns if df[c].nunique(dropna=True) <= 1]

        # Near-duplicate columns (same data, different name)
        dup_col_pairs = []
        cols = list(df.columns)
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                try:
                    if df[cols[i]].equals(df[cols[j]]):
                        dup_col_pairs.append((cols[i], cols[j]))
                except Exception:
                    pass

        # Scoring — row duplication is worse than column duplication
        row_penalty   = min(dupe_rate * 150, 60)
        col_penalty   = min(len(constant_cols) * 5 + len(dup_col_pairs) * 8, 30)
        scores["uniqueness"] = round(max(0, 100 - row_penalty - col_penalty), 2)

        f = []
        if exact_dupes:
            f.append(f"🔴 {exact_dupes:,} exact duplicate rows ({dupe_rate:.1%} of dataset)")
        if constant_cols:
            f.append(f"🟡 {len(constant_cols)} constant column(s) — zero variation: {', '.join(constant_cols)}")
        if dup_col_pairs:
            f.append(f"🟠 {len(dup_col_pairs)} identical column pair(s): " +
                     ", ".join(f"'{a}' = '{b}'" for a, b in dup_col_pairs))
        if not f:
            f.append("✅ No duplicate rows or redundant columns")
        findings["uniqueness"] = f

        _render_dimension("D2 — Uniqueness", scores["uniqueness"], findings["uniqueness"])

   
    # D3 — CONSISTENCY (16%)
    # ISO def: degree to which data is free from contradiction
    
    with st.expander("D3 — Consistency (16%)"):

        mixed_type_cols  = []
        case_issue_cols  = []
        date_format_cols = []
        encoding_cols    = []

        date_patterns = [
            r"\d{4}-\d{2}-\d{2}",           # 2024-01-12
            r"\d{2}/\d{2}/\d{4}",           # 12/01/2024
            r"\d{2}-\d{2}-\d{4}",           # 12-01-2024
            r"\d{1,2} \w+ \d{4}",           # 12 January 2024
        ]

        for col in df.select_dtypes("object").columns:
            vals = df[col].dropna().astype(str)
            if len(vals) == 0:
                continue

            # Mixed types
            numeric_like = pd.to_numeric(vals, errors="coerce").notnull().sum()
            alpha_like   = vals.str.match(r"^[A-Za-z]").sum()
            if 0 < numeric_like < len(vals) and alpha_like > 0:
                mixed_type_cols.append(col)

            # Case inconsistency (only check low-cardinality cols)
            if df[col].nunique() <= 50:
                if vals.str.strip().str.lower().nunique() < vals.str.strip().nunique():
                    case_issue_cols.append(col)

            
            if df[col].nunique() > 5:
                matched_patterns = set()
                sample = vals.head(200)
                for pat in date_patterns:
                    if sample.str.match(pat).sum() > 2:
                        matched_patterns.add(pat)
                if len(matched_patterns) > 1:
                    date_format_cols.append(col)

            
            if vals.str.contains(r"â€|Ã©|Ã¨|Â|ï»¿", regex=True, na=False).sum() > 0:
                encoding_cols.append(col)

        total_issues = len(mixed_type_cols) + len(case_issue_cols) + len(date_format_cols) + len(encoding_cols)
        issue_rate   = total_issues / df.shape[1]
        scores["consistency"] = round(max(0, 100 - issue_rate * 120), 2)

        f = []
        if mixed_type_cols:
            f.append(f"🔴 Mixed data types in: {', '.join(mixed_type_cols)}")
        if date_format_cols:
            f.append(f"🟠 Inconsistent date formats in: {', '.join(date_format_cols)}")
        if case_issue_cols:
            f.append(f"🟡 Case inconsistency in: {', '.join(case_issue_cols)} (e.g. 'Yes' vs 'yes')")
        if encoding_cols:
            f.append(f"🟠 Encoding corruption in: {', '.join(encoding_cols)}")
        if not f:
            f.append("✅ No consistency issues detected")
        findings["consistency"] = f

        _render_dimension("D3 — Consistency", scores["consistency"], findings["consistency"])

    
    # D4 — VALIDITY (16%)
    # ISO def: degree to which data values are in the correct range
    # and format for their domain
    
    with st.expander("D4 — Validity (16%)"):

        outlier_info  = []
        impossible    = []

        for col in df.select_dtypes("number").columns:
            data = df[col].dropna()
            if len(data) < 4:
                continue

            Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
            IQR = Q3 - Q1

            if IQR > 0:
                # Using 3×IQR (extreme outliers only — not just unusual values)
                n_out = ((data < Q1 - 3*IQR) | (data > Q3 + 3*IQR)).sum()
                if n_out > 0:
                    pct = n_out / len(data) * 100
                    outlier_info.append({
                        "Column": col,
                        "Outliers": int(n_out),
                        "% of column": f"{pct:.1f}%",
                        "Severity": "🔴 High" if pct > 5 else "🟡 Low"
                    })

            # Domain-specific impossible values
            c = col.lower()
            if any(k in c for k in ["age", "years"]):
                bad = ((data < 0) | (data > 150)).sum()
                if bad:
                    impossible.append(f"'{col}' has {bad} values outside 0–150")
            if any(k in c for k in ["price", "salary", "cost", "amount", "revenue"]):
                bad = (data < 0).sum()
                if bad:
                    impossible.append(f"'{col}' has {bad} negative values")
            if any(k in c for k in ["percent", "pct", "rate", "ratio"]):
                bad = ((data < 0) | (data > 100)).sum()
                if bad:
                    impossible.append(f"'{col}' has {bad} values outside 0–100%")
            if any(k in c for k in ["month"]):
                bad = ((data < 1) | (data > 12)).sum()
                if bad:
                    impossible.append(f"'{col}' has {bad} invalid month values")

        total_outlier_cells = sum(o["Outliers"] for o in outlier_info)
        total_num_cells = sum(df[c].dropna().shape[0]
                              for c in df.select_dtypes("number").columns)
        outlier_rate   = total_outlier_cells / max(1, total_num_cells)
        impossible_pen = min(len(impossible) * 10, 40)
        scores["validity"] = round(max(0, 100 - outlier_rate * 80 - impossible_pen), 2)

        f = []
        if impossible:
            for msg in impossible:
                f.append(f"🔴 Impossible value: {msg}")
        if outlier_info:
            high = [o for o in outlier_info if "High" in o["Severity"]]
            low  = [o for o in outlier_info if "Low"  in o["Severity"]]
            if high:
                f.append(f"🔴 {len(high)} column(s) with >5% extreme outliers")
            if low:
                f.append(f"🟡 {len(low)} column(s) with minor outliers")
        if not f:
            f.append("✅ No validity issues found")
        findings["validity"] = f

        _render_dimension("D4 — Validity", scores["validity"], findings["validity"])
        if outlier_info:
            st.dataframe(pd.DataFrame(outlier_info), use_container_width=True)

    
    # D5 — ACCURACY (10%)
    # ISO def: degree to which data correctly represents the
    # real-world values it is meant to model
    # NOTE: True accuracy needs a reference dataset. Without one,
    # we check statistical proxies: extreme skew + label noise.
    
    with st.expander("D5 — Accuracy (10%)"):

        skewed_cols  = []
        label_noise  = []  # categoricals with near-duplicate labels

        for col in df.select_dtypes("number").columns:
            sk = df[col].dropna().skew()
            if abs(sk) > 3.0:   # raised from 2.0 — less noise
                skewed_cols.append({"Column": col, "Skewness": round(float(sk), 2)})

        for col in df.select_dtypes("object").columns:
            vals = df[col].dropna().astype(str).str.strip().str.lower()
            unique_vals = vals.unique()
            # Check for near-duplicate labels e.g. "male" vs "m" vs "Male"
            if 2 <= len(unique_vals) <= 30:
                seen = []
                for v in unique_vals:
                    # Flag if a short version of a longer label exists
                    for s in seen:
                        if (v.startswith(s[:2]) and v != s and len(s) > 1):
                            label_noise.append(
                                f"'{col}': '{v}' and '{s}' may be the same category"
                            )
                            break
                    seen.append(v)

        skew_pen  = min(len(skewed_cols) * 4, 30)
        noise_pen = min(len(label_noise) * 8, 40)
        scores["accuracy"] = round(max(0, 100 - skew_pen - noise_pen), 2)

        f = []
        if skewed_cols:
            f.append(f"🟡 {len(skewed_cols)} heavily skewed column(s) (|skew| > 3.0) — "
                     f"may distort analysis: {', '.join(s['Column'] for s in skewed_cols)}")
        if label_noise:
            for msg in label_noise[:5]:   # show max 5
                f.append(f"🟠 Possible label noise: {msg}")
        if not f:
            f.append("✅ No accuracy issues detected")
        findings["accuracy"] = f

        _render_dimension("D5 — Accuracy", scores["accuracy"], findings["accuracy"])

    
    # D6 — STRUCTURE (7%)
    # ISO def: degree to which data follows schema conventions
    
    with st.expander("D6 — Structure (7%)"):

        bad_col_names   = []
        wrong_type_cols = []
        unnamed_cols    = []

        for col in df.columns:
            s = str(col)
            if re.match(r"^Unnamed", s):
                unnamed_cols.append(col)
            elif s.strip() == "" or re.search(r"[^a-zA-Z0-9_ ]", s):
                bad_col_names.append(col)

        for col in df.select_dtypes("object").columns:
            if pd.to_numeric(df[col], errors="coerce").notnull().mean() > 0.95:
                wrong_type_cols.append(col)

        # Row/col ratio — very wide datasets are suspicious
        ratio = df.shape[0] / max(df.shape[1], 1)
        ratio_flag = ratio < 3   # fewer than 3 rows per column

        total_issues = len(bad_col_names) + len(wrong_type_cols) + len(unnamed_cols)
        struct_pen   = min(total_issues / df.shape[1] * 60, 50)
        ratio_pen    = 15 if ratio_flag else 0
        scores["structure"] = round(max(0, 100 - struct_pen - ratio_pen), 2)

        f = []
        if unnamed_cols:
            f.append(f"🔴 {len(unnamed_cols)} unnamed column(s) — likely a parsing issue")
        if bad_col_names:
            f.append(f"🟡 {len(bad_col_names)} column(s) with special characters in name")
        if wrong_type_cols:
            f.append(f"🟠 {len(wrong_type_cols)} column(s) stored as text but are numeric: "
                     f"{', '.join(wrong_type_cols)}")
        if ratio_flag:
            f.append(f"🟡 Very low row/column ratio ({ratio:.1f}) — dataset may be too wide")
        if not f:
            f.append("✅ Structure looks clean")
        findings["structure"] = f

        _render_dimension("D6 — Structure", scores["structure"], findings["structure"])

    
    # D7 — CORRELATION / REDUNDANCY (5%)
    # ISO def: degree to which data is free from redundant
    # or linearly dependent attributes
   
    with st.expander("D7 — Correlation & Redundancy (5%)"):

        high_corr_pairs = []
        num_df = df.select_dtypes("number").dropna(axis=1, how="all")

        if num_df.shape[1] >= 2:
            corr = num_df.corr().abs()
            cols = corr.columns
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    r = float(corr.iloc[i, j])
                    if r > 0.95:
                        high_corr_pairs.append({
                            "Col A": cols[i],
                            "Col B": cols[j],
                            "Correlation": round(r, 4),
                            "Risk": "🔴 Near-duplicate" if r > 0.999 else "🟡 Highly correlated"
                        })

            fig = px.imshow(
                num_df.corr(),
                text_auto=".2f",
                color_continuous_scale="RdBu_r",
                title="Correlation Matrix"
            )
            st.plotly_chart(fig, use_container_width=True)

        scores["correlation"] = round(max(0, 100 - len(high_corr_pairs) * 5), 2)

        f = []
        if high_corr_pairs:
            near_dup = [p for p in high_corr_pairs if p["Correlation"] > 0.999]
            high     = [p for p in high_corr_pairs if p["Correlation"] <= 0.999]
            if near_dup:
                f.append(f"🔴 {len(near_dup)} near-identical column pair(s) — likely redundant")
            if high:
                f.append(f"🟡 {len(high)} highly correlated pair(s) (r > 0.95)")
            st.dataframe(pd.DataFrame(high_corr_pairs), use_container_width=True)
        else:
            f.append("✅ No redundant or highly correlated columns")
        findings["correlation"] = f

        _render_dimension("D7 — Correlation", scores["correlation"], findings["correlation"])

    
    # FINAL DQS
    
    st.divider()
    _render_dqs(scores, findings, df)




def _render_dimension(title: str, score: float, findings: list):
    """Shows score + colour-coded findings for one dimension."""
    color = "#00c853" if score >= 85 else "#ffd600" if score >= 60 else "#ff6d00" if score >= 40 else "#d50000"
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(f"""
        <div style='text-align:center;padding:16px;border-radius:12px;
                    background:{color}18;border:2px solid {color}'>
            <div style='font-size:32px;font-weight:bold;color:{color}'>{score}</div>
            <div style='font-size:11px;color:#888'>out of 100</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        for finding in findings:
            st.markdown(f"- {finding}")


def _render_dqs(scores: dict, findings: dict, df: pd.DataFrame):
    """Renders the final DQS score card + radar chart + full explanation."""
    WEIGHTS = {
        "completeness": 0.28,
        "uniqueness":   0.18,
        "consistency":  0.16,
        "validity":     0.16,
        "accuracy":     0.10,
        "structure":    0.07,
        "correlation":  0.05,
    }

    
    dqs = round(sum(WEIGHTS[k] * scores.get(k, 0) for k in WEIGHTS), 2)

    grade = ("A 🟢" if dqs >= 85 else "B 🟡" if dqs >= 70
             else "C 🟠" if dqs >= 50 else "D 🔴")
    color = ("#00c853" if dqs >= 85 else "#ffd600" if dqs >= 70
             else "#ff6d00" if dqs >= 50 else "#d50000")

    st.subheader("🏆 Dataset Quality Score (DQS)")
    st.caption("ISO 25012 aligned · Weighted across 7 dimensions")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"""
        <div style='text-align:center;padding:36px;border-radius:16px;
                    background:{color}18;border:3px solid {color}'>
            <div style='font-size:64px;font-weight:900;color:{color}'>{dqs}</div>
            <div style='font-size:24px;color:{color}'>{grade}</div>
            <div style='color:#888;font-size:13px'>out of 100</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Radar chart — much more readable than a bar chart for this
        dims   = list(scores.keys())
        vals   = [scores[d] for d in dims]
        

        fig = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=dims + [dims[0]],
            fill="toself",
            fillcolor=_hex_to_rgba(color, 0.15),
            line=dict(color=color, width=2),
))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            title="Quality Profile",
            margin=dict(t=40, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── What to fix — prioritised action list 
    st.subheader("📋 What to Fix — Priority Order")
    st.caption("Sorted by impact on your DQS score")

    action_items = []
    for dim, score in sorted(scores.items(), key=lambda x: x[1]):
        weight = WEIGHTS.get(dim, 0)
        impact = round((100 - score) * weight, 1)
        if impact > 0.5:
            worst_finding = next(
                (f for f in findings.get(dim, []) if not f.startswith("✅")),
                None
            )
            if worst_finding:
                action_items.append({
                    "Dimension": dim.capitalize(),
                    "Score": score,
                    "Score Impact": f"-{impact} pts",
                    "Top Issue": worst_finding
                })

    if action_items:
        st.dataframe(pd.DataFrame(action_items), use_container_width=True)
    else:
        st.success("🎉 No significant issues found! Your dataset is high quality.")

    #  Dimension breakdown bar 
    fig2 = px.bar(
        x=list(scores.keys()),
        y=list(scores.values()),
        labels={"x": "Dimension", "y": "Score"},
        color=list(scores.values()),
        color_continuous_scale="RdYlGn",
        range_y=[0, 100],
        title="Score Breakdown by Dimension"
    )
    st.plotly_chart(fig2, use_container_width=True)