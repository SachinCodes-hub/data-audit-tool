import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.helpers import PLACEHOLDERS



def classify_columns(df: pd.DataFrame) -> dict:
    """
    Returns a dict: column_name → tag
    Tags: 'id', 'constant', 'target_candidate', 'numeric',
          'categorical', 'datetime', 'high_cardinality', 'text'
    """
    tags = {}
    n = len(df)

    for col in df.columns:
        series = df[col]
        nunique = series.nunique(dropna=True)
        col_lower = col.lower().strip()

        # Constant — zero information
        if nunique <= 1:
            tags[col] = "constant"
            continue

        # ID-like — all or nearly all unique + name hint
        id_keywords = ["id", "index", "uuid", "key", "code", "no", "num", "number", "ref"]
        is_id_name  = any(col_lower == k or col_lower.endswith(f"_{k}") or
                          col_lower.startswith(f"{k}_") for k in id_keywords)
        if nunique / n > 0.95 and (is_id_name or series.dtype == object):
            tags[col] = "id"
            continue

        # Datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            tags[col] = "datetime"
            continue
        if series.dtype == object:
            sample = series.dropna().astype(str).head(100)
            parsed = pd.to_datetime(sample, errors="coerce", infer_datetime_format=True)
            if parsed.notnull().mean() > 0.7:
                tags[col] = "datetime"
                continue

        # Numeric
        if pd.api.types.is_numeric_dtype(series):
            if nunique == 2:
                tags[col] = "binary"
            elif nunique <= 15:
                tags[col] = "categorical"   # low-cardinality numeric → treat as cat
            else:
                tags[col] = "numeric"
            continue

        # Categorical vs high-cardinality vs free text
        if series.dtype == object:
            if nunique <= 20:
                tags[col] = "categorical"
            elif nunique / n > 0.5:
                tags[col] = "text"          # too many unique → probably free text
            else:
                tags[col] = "high_cardinality"
            continue

        tags[col] = "unknown"

    return tags



# MAIN EXPLORER PAGE


def show_explorer(df: pd.DataFrame):
    st.header("🔬 Data Explorer")
    st.caption("Visual deep-dive into every column and relationship")

    tags = classify_columns(df)

    #  Column Type Summary 
    st.subheader("🏷️ Smart Column Classifier")
    st.caption("Auto-detected column roles — helps you know what to use in your model")

    TAG_META = {
        "numeric":          ("🔢", "Numeric Feature",       "#4fc3f7"),
        "categorical":      ("🔤", "Categorical Feature",   "#81c784"),
        "binary":           ("⚡", "Binary",                "#fff176"),
        "id":               ("🪪", "ID / Index (drop this)","#ef9a9a"),
        "constant":         ("⛔", "Constant (useless)",    "#ef9a9a"),
        "datetime":         ("📅", "DateTime",              "#ce93d8"),
        "high_cardinality": ("⚠️", "High Cardinality",      "#ffb74d"),
        "text":             ("📝", "Free Text",              "#a5d6a7"),
        "unknown":          ("❓", "Unknown",               "#eeeeee"),
    }

    # Build summary table
    rows = []
    for col, tag in tags.items():
        emoji, label, color = TAG_META.get(tag, ("❓", tag, "#eee"))
        null_pct = round(df[col].isnull().mean() * 100, 1)
        nunique  = df[col].nunique(dropna=True)
        rows.append({
            "Column":    col,
            "Type":      f"{emoji} {label}",
            "Null %":    f"{null_pct}%",
            "Unique":    nunique,
            "Sample":    str(df[col].dropna().iloc[0]) if df[col].dropna().shape[0] > 0 else "—",
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    # Warnings for ML-dangerous columns
    id_cols       = [c for c, t in tags.items() if t == "id"]
    constant_cols = [c for c, t in tags.items() if t == "constant"]
    text_cols     = [c for c, t in tags.items() if t == "text"]

    if id_cols:
        st.warning(f"🪪 **ID columns detected** — drop before training: `{'`, `'.join(id_cols)}`")
    if constant_cols:
        st.error(f"⛔ **Constant columns** — zero information, always drop: `{'`, `'.join(constant_cols)}`")
    if text_cols:
        st.info(f"📝 **Free text columns** — need NLP encoding before use: `{'`, `'.join(text_cols)}`")

    st.divider()

    #  Section tabs
    t1, t2, t3, t4, t5 = st.tabs([
        "📊 Distributions",
        "📦 Box Plots",
        "🔗 Correlations",
        "🎯 Target Analysis",
        "🔍 Column Deep Dive",
    ])

    with t1:
        _show_distributions(df, tags)

    with t2:
        _show_boxplots(df, tags)

    with t3:
        _show_correlations(df, tags)

    with t4:
        _show_target_analysis(df, tags)

    with t5:
        _show_column_deep_dive(df, tags)


#
# TAB 1 — DISTRIBUTIONS


def _show_distributions(df, tags):
    st.subheader("Distribution of Every Column")
    st.caption("Histogram + KDE for numeric · Bar chart for categorical")

    numeric_cols     = [c for c, t in tags.items() if t in ("numeric", "binary")]
    categorical_cols = [c for c, t in tags.items() if t in ("categorical", "high_cardinality")]

    if not numeric_cols and not categorical_cols:
        st.info("No plottable columns found.")
        return

    # Numeric distributions — grid layout
    if numeric_cols:
        st.markdown("#### Numeric Columns")
        cols_per_row = 2
        for i in range(0, len(numeric_cols), cols_per_row):
            row_cols = st.columns(cols_per_row)
            for j, col in enumerate(numeric_cols[i:i+cols_per_row]):
                with row_cols[j]:
                    data = df[col].dropna()
                    fig = px.histogram(
                        data, x=data,
                        nbins=min(50, data.nunique()),
                        marginal="box",          # box plot on top
                        title=f"{col}",
                        labels={"x": col},
                        color_discrete_sequence=["#4fc3f7"],
                    )
                    fig.update_layout(
                        showlegend=False,
                        margin=dict(t=40, b=10, l=10, r=10),
                        height=300,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Key stats under the chart
                    sk = round(float(data.skew()), 2)
                    sk_label = "⚠️ Right skew" if sk > 1 else "⚠️ Left skew" if sk < -1 else "✅ Normal-ish"
                    st.caption(f"Mean: {data.mean():.2f} · Median: {data.median():.2f} · "
                               f"Std: {data.std():.2f} · Skew: {sk} {sk_label}")

    # Categorical distributions
    if categorical_cols:
        st.markdown("#### Categorical Columns")
        cols_per_row = 2
        for i in range(0, len(categorical_cols), cols_per_row):
            row_cols = st.columns(cols_per_row)
            for j, col in enumerate(categorical_cols[i:i+cols_per_row]):
                with row_cols[j]:
                    vc = df[col].value_counts().head(20)
                    fig = px.bar(
                        x=vc.index.astype(str),
                        y=vc.values,
                        title=f"{col}",
                        labels={"x": col, "y": "Count"},
                        color=vc.values,
                        color_continuous_scale="Teal",
                    )
                    fig.update_layout(
                        showlegend=False,
                        margin=dict(t=40, b=10, l=10, r=10),
                        height=300,
                        coloraxis_showscale=False,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    top_val  = vc.index[0]
                    top_pct  = round(vc.values[0] / len(df) * 100, 1)
                    imb_warn = " ⚠️ Imbalanced!" if top_pct > 80 else ""
                    st.caption(f"Top value: '{top_val}' ({top_pct}%){imb_warn} · "
                               f"{df[col].nunique()} unique values")



# TAB 2 — BOX PLOTS


def _show_boxplots(df, tags):
    st.subheader("Outlier Visualisation — Box Plots")
    st.caption("IQR-based outlier detection · Points beyond whiskers = outliers")

    numeric_cols = [c for c, t in tags.items() if t == "numeric"]

    if not numeric_cols:
        st.info("No numeric columns found for box plot analysis.")
        return

    # All columns in one combined box plot
    st.markdown("#### All Numeric Columns — Combined View")
    fig = go.Figure()
    for col in numeric_cols:
        fig.add_trace(go.Box(
            y=df[col].dropna(),
            name=col,
            boxpoints="outliers",
            marker=dict(size=3, opacity=0.5),
            line=dict(width=1.5),
        ))
    fig.update_layout(
        height=450,
        title="Box Plot — All Numeric Columns",
        showlegend=False,
        margin=dict(t=50, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Per-column detail with outlier rows
    st.markdown("#### Inspect Outlier Rows")
    selected = st.selectbox("Pick a column to inspect its outliers", numeric_cols, key="box_col")

    if selected:
        data = df[selected].dropna()
        Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
        IQR = Q3 - Q1
        lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR

        outlier_mask = (df[selected] < lower) | (df[selected] > upper)
        outlier_rows = df[outlier_mask]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Outliers", len(outlier_rows))
        col2.metric("Lower Bound", f"{lower:.2f}")
        col3.metric("Upper Bound", f"{upper:.2f}")
        col4.metric("% of Column", f"{len(outlier_rows)/len(df)*100:.1f}%")

        if not outlier_rows.empty:
            st.markdown(f"**Outlier rows for `{selected}`:**")
            st.dataframe(outlier_rows.head(50), use_container_width=True)
        else:
            st.success("✅ No outliers in this column at 1.5×IQR threshold")



# TAB 3 — CORRELATIONS


def _show_correlations(df, tags):
    st.subheader("Correlation Analysis")

    numeric_cols = [c for c, t in tags.items() if t in ("numeric", "binary")]

    if len(numeric_cols) < 2:
        st.info("Need at least 2 numeric columns for correlation analysis.")
        return

    # Heatmap
    st.markdown("#### Correlation Heatmap")
    corr = df[numeric_cols].corr()
    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        title="Pearson Correlation Matrix",
        aspect="auto",
    )
    fig.update_layout(margin=dict(t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # Scatter plot — user picks 2 columns
    st.markdown("#### Scatter Plot — Pick Any Two Columns")
    col1, col2 = st.columns(2)
    with col1:
        x_col = st.selectbox("X axis", numeric_cols, key="scatter_x")
    with col2:
        y_col = st.selectbox("Y axis", numeric_cols,
                             index=min(1, len(numeric_cols)-1), key="scatter_y")

    # Optional colour by categorical
    cat_cols = [c for c, t in tags.items() if t == "categorical"]
    color_col = st.selectbox("Colour by (optional)",
                             ["None"] + cat_cols, key="scatter_color")

    if x_col and y_col:
        r = df[[x_col, y_col]].corr().iloc[0, 1]
        try:
            fig2 = px.scatter(
                df,
                x=x_col,
                y=y_col,
                trendline="ols",
                opacity=0.6,
    )
        except Exception:
            fig2 = px.scatter(
            df,
            x=x_col,
            y=y_col,
            opacity=0.6,
    )
        fig2.update_layout(height=450)
        st.plotly_chart(fig2, use_container_width=True)

        # Interpretation
        if abs(r) > 0.9:
            st.error(f"⚠️ r = {r:.2f} — Very high correlation. Risk of multicollinearity in models.")
        elif abs(r) > 0.7:
            st.warning(f"🟡 r = {r:.2f} — Strong correlation. Consider dropping one for linear models.")
        elif abs(r) > 0.4:
            st.info(f"🔵 r = {r:.2f} — Moderate correlation.")
        else:
            st.success(f"✅ r = {r:.2f} — Weak/no linear correlation.")



# TAB 4 — TARGET COLUMN ANALYSIS


def _show_target_analysis(df, tags):
    st.subheader("🎯 Target Column Analysis")
    st.caption("Pick your ML target column — we'll analyse it for model readiness")

    # Exclude IDs and constants from target options
    valid_targets = [c for c, t in tags.items() if t not in ("id", "constant", "text")]

    if not valid_targets:
        st.warning("No valid target columns found.")
        return

    target = st.selectbox("Select your target column", valid_targets, key="target_col")

    if not target:
        return

    tag = tags[target]
    st.markdown(f"**Detected type:** `{tag}`")

    # ── Classification target ─────────────────────────────────────
    if tag in ("categorical", "binary"):
        vc = df[target].value_counts()
        total = vc.sum()

        st.markdown("#### Class Distribution")
        fig = px.bar(
            x=vc.index.astype(str), y=vc.values,
            labels={"x": "Class", "y": "Count"},
            color=vc.values,
            color_continuous_scale="RdYlGn",
            title=f"Class Distribution — {target}"
        )
        fig.update_layout(coloraxis_showscale=False, height=350)
        st.plotly_chart(fig, use_container_width=True)

        # Imbalance metrics
        majority_pct = vc.values[0] / total * 100
        minority_pct = vc.values[-1] / total * 100
        imbalance_ratio = vc.values[0] / max(vc.values[-1], 1)

        col1, col2, col3 = st.columns(3)
        col1.metric("Classes", len(vc))
        col2.metric("Majority Class %", f"{majority_pct:.1f}%")
        col3.metric("Imbalance Ratio", f"{imbalance_ratio:.1f}x")

        # Verdict
        if imbalance_ratio > 10:
            st.error("🔴 **Severe class imbalance** — use SMOTE, class weights, or oversample minority class before training.")
        elif imbalance_ratio > 3:
            st.warning("🟡 **Moderate imbalance** — consider `class_weight='balanced'` in your model.")
        else:
            st.success("✅ **Classes are reasonably balanced** — good to train.")

        # Pie chart
        fig2 = px.pie(
            values=vc.values, names=vc.index.astype(str),
            title="Class Share", hole=0.4
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Regression target 
    elif tag == "numeric":
        data = df[target].dropna()

        st.markdown("#### Target Distribution")
        fig = px.histogram(
            data, x=data, nbins=50,
            marginal="violin",
            title=f"Distribution — {target}",
            color_discrete_sequence=["#4fc3f7"],
        )
        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Mean",   f"{data.mean():.2f}")
        col2.metric("Median", f"{data.median():.2f}")
        col3.metric("Std",    f"{data.std():.2f}")
        col4.metric("Skew",   f"{data.skew():.2f}")

        sk = data.skew()
        if abs(sk) > 2:
            st.warning(f"🟡 Target is heavily skewed (skew={sk:.2f}). "
                       f"Consider log-transforming before regression.")
        else:
            st.success("✅ Target distribution looks suitable for regression.")

    else:
        st.info(f"Target column type `{tag}` — detailed analysis not available for this type.")



# TAB 5 — COLUMN DEEP DIVE


def _show_column_deep_dive(df, tags):
    st.subheader("🔍 Column Deep Dive")
    st.caption("Full report for any single column — stats, distribution, ML encoding suggestion")

    selected = st.selectbox("Pick a column", df.columns.tolist(), key="deep_dive_col")

    if not selected:
        return

    tag  = tags.get(selected, "unknown")
    data = df[selected]

    # Header info 
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Detected Type", tag)
    col2.metric("Null %", f"{data.isnull().mean()*100:.1f}%")
    col3.metric("Unique Values", data.nunique())
    col4.metric("Total Rows", len(data))

    st.divider()

    #  Encoding suggestion 
    ENCODING_ADVICE = {
        "numeric":          ("✅ Ready to use", "No encoding needed. Scale with StandardScaler or MinMaxScaler if needed."),
        "binary":           ("✅ Ready to use", "Binary column. Encode as 0/1 if not already numeric."),
        "categorical":      ("🔤 One-Hot Encode", "Low cardinality. Use `pd.get_dummies()` or `OneHotEncoder`."),
        "high_cardinality": ("⚠️ Target Encode", "High cardinality. Avoid one-hot — use Target Encoding or frequency encoding."),
        "id":               ("🗑️ Drop this column", "ID columns leak into models and destroy generalisation. Always drop."),
        "constant":         ("🗑️ Drop this column", "Zero variance — no information for any model."),
        "datetime":         ("📅 Feature Engineer", "Extract: year, month, day, weekday, hour. Drop the raw column."),
        "text":             ("📝 NLP Encoding", "Use TF-IDF, Word2Vec, or a sentence transformer."),
        "unknown":          ("❓ Review manually", "Type could not be determined automatically."),
    }

    advice_title, advice_body = ENCODING_ADVICE.get(tag, ("❓", "Review manually"))
    st.markdown(f"**ML Encoding Advice:** {advice_title}")
    st.info(advice_body)

    st.divider()

    # Visual + stats 
    if tag in ("numeric",):
        clean = data.dropna()
        fig = px.histogram(clean, x=clean, nbins=50, marginal="box",
                           color_discrete_sequence=["#4fc3f7"],
                           title=f"Distribution — {selected}")
        st.plotly_chart(fig, use_container_width=True)

        stat_df = pd.DataFrame({
            "Statistic": ["Count", "Mean", "Median", "Std", "Min", "Max",
                          "Skewness", "Kurtosis", "Q1 (25%)", "Q3 (75%)"],
            "Value": [
                len(clean), round(clean.mean(), 4), round(clean.median(), 4),
                round(clean.std(), 4), round(clean.min(), 4), round(clean.max(), 4),
                round(float(clean.skew()), 4), round(float(clean.kurt()), 4),
                round(clean.quantile(0.25), 4), round(clean.quantile(0.75), 4),
            ]
        })
        st.dataframe(stat_df, use_container_width=True)

    elif tag in ("categorical", "binary", "high_cardinality"):
        vc = data.value_counts().head(30)
        fig = px.bar(x=vc.index.astype(str), y=vc.values,
                     labels={"x": selected, "y": "Count"},
                     color=vc.values, color_continuous_scale="Teal",
                     title=f"Top Values — {selected}")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Value Counts (top 20):**")
        vc_df = data.value_counts().head(20).reset_index()
        vc_df.columns = ["Value", "Count"]
        vc_df["% of Total"] = (vc_df["Count"] / len(df) * 100).round(1)
        st.dataframe(vc_df, use_container_width=True)

    elif tag == "datetime":
        st.info("Datetime column — parse and extract features: year, month, day, weekday.")

    else:
        st.markdown("**Sample values:**")
        st.write(data.dropna().unique()[:30])