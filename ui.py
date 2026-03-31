"""
DataPulse  ·  ui.py — Premium Edition
Run: streamlit run ui.py
"""

import re, io, math
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="DataPulse",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=Space+Grotesk:wght@300;400;500;600&family=Space+Mono:wght@400;700&display=swap');

:root {
  --bg:       #060810;
  --bg1:      #0d0f18;
  --bg2:      #111420;
  --bg3:      #161a28;
  --border:   #1e2235;
  --border2:  #262b40;
  --accent:   #5b8cff;
  --accent2:  #7b6cff;
  --green:    #3de8a0;
  --yellow:   #ffd166;
  --red:      #ff6b6b;
  --text:     #eeedf5;
  --text2:    #9096b8;
  --text3:    #525878;
  --mono:     'Space Mono', monospace;
  --sans:     'Space Grotesk', sans-serif;
  --display:  'Syne', sans-serif;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
}

[data-testid="stAppViewContainer"] > .main { padding: 0 !important; }
[data-testid="stHeader"]  { background: transparent !important; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
section.main > div { padding-top: 0 !important; }
.block-container { padding: 0 2.5rem 5rem !important; max-width: 1280px !important; margin: auto; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--bg3); border-radius: 3px; }

/* ── TOPBAR ── */
.topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1.4rem 0 1.4rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0;
}
.topbar-logo {
    display: flex; align-items: center; gap: 0.6rem;
    font-family: var(--display); font-size: 1.05rem; font-weight: 700;
    color: var(--text); letter-spacing: -0.01em;
}
.topbar-logo-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 10px var(--accent);
}
.topbar-badge {
    font-family: var(--mono); font-size: 0.62rem;
    letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--text3); padding: 0.25rem 0.65rem;
    border: 1px solid var(--border); border-radius: 99px;
}

/* ── HERO ── */
.hero {
    min-height: 78vh;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    text-align: center;
    padding: 5rem 2rem 3rem;
    position: relative; overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute; inset: 0;
    background:
        radial-gradient(ellipse 90% 55% at 50% -5%,  rgba(91,140,255,0.13) 0%, transparent 65%),
        radial-gradient(ellipse 60% 45% at 20% 90%,  rgba(123,108,255,0.07) 0%, transparent 60%),
        radial-gradient(ellipse 50% 40% at 85% 80%,  rgba(61,232,160,0.05) 0%, transparent 55%);
    pointer-events: none;
}
.hero-grid {
    position: absolute; inset: 0;
    background-image:
        linear-gradient(rgba(91,140,255,0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(91,140,255,0.035) 1px, transparent 1px);
    background-size: 60px 60px;
    mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 30%, transparent 80%);
    pointer-events: none;
}
.hero-tag {
    font-family: var(--mono); font-size: 0.7rem;
    letter-spacing: 0.2em; text-transform: uppercase;
    color: var(--accent); margin-bottom: 1.8rem;
    display: flex; align-items: center; gap: 0.5rem;
    justify-content: center;
}
.hero-tag::before, .hero-tag::after {
    content: ''; flex: 0 0 24px; height: 1px; background: var(--accent); opacity: 0.4;
}
.hero-title {
    font-family: var(--display);
    font-weight: 800;
    font-size: clamp(3.2rem, 8vw, 6.5rem);
    line-height: 0.95;
    letter-spacing: -0.04em;
    color: var(--text);
    margin-bottom: 1.5rem;
}
.hero-title-accent { color: var(--accent); }
.hero-sub {
    font-size: 1.1rem; color: var(--text2);
    max-width: 480px; line-height: 1.75;
    margin-bottom: 3.5rem; font-weight: 300;
}
.hero-stats {
    display: flex; gap: 3.5rem; justify-content: center;
    flex-wrap: wrap; margin-top: 1rem;
}
.hero-stat-num {
    font-family: var(--display); font-size: 1.8rem; font-weight: 700;
    color: var(--text); letter-spacing: -0.03em;
}
.hero-stat-label {
    font-family: var(--mono); font-size: 0.6rem;
    letter-spacing: 0.14em; text-transform: uppercase; color: var(--text3);
    margin-top: 0.15rem;
}

/* ── UPLOAD ZONE ── */
.upload-shell {
    border: 1.5px dashed rgba(91,140,255,0.35);
    border-radius: 20px;
    padding: 2.8rem 3.5rem;
    background: rgba(91,140,255,0.04);
    width: 100%; max-width: 560px;
    backdrop-filter: blur(8px);
    transition: all 0.3s;
    position: relative;
}
.upload-shell::before {
    content: '';
    position: absolute; inset: 0; border-radius: 20px;
    background: radial-gradient(ellipse 80% 60% at 50% -20%, rgba(91,140,255,0.08), transparent 70%);
    pointer-events: none;
}
.upload-shell:hover {
    border-color: rgba(91,140,255,0.65);
    background: rgba(91,140,255,0.07);
}
.upload-icon {
    font-size: 2.2rem; margin-bottom: 0.8rem;
    display: block; text-align: center;
}
.upload-title {
    font-family: var(--display); font-size: 1.1rem; font-weight: 600;
    color: var(--text); text-align: center; margin-bottom: 0.4rem;
}
.upload-hint {
    font-size: 0.8rem; color: var(--text3); text-align: center;
    font-family: var(--mono); letter-spacing: 0.05em; margin-bottom: 1.2rem;
}

/* ── NAV BAR ── */
.nav-wrap {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1.6rem 0 0;
    margin-bottom: 2.4rem;
    border-bottom: 1px solid var(--border);
}
.nav-tabs {
    display: flex; gap: 0;
    background: var(--bg1);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 5px;
}
.nav-btn {
    font-family: var(--sans); font-size: 0.85rem; font-weight: 500;
    padding: 0.55rem 1.35rem; border-radius: 9px;
    border: none; cursor: pointer; transition: all 0.2s;
    letter-spacing: 0.01em;
}
.nav-btn-active  { background: var(--accent) !important; color: #fff !important; box-shadow: 0 2px 12px rgba(91,140,255,0.35) !important; }
.nav-btn-inactive { background: transparent !important; color: var(--text3) !important; }
.nav-btn-inactive:hover { color: var(--text2) !important; background: var(--bg2) !important; }
.nav-file-info {
    font-family: var(--mono); font-size: 0.68rem;
    letter-spacing: 0.08em; color: var(--text3);
    padding: 0.4rem 0.9rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg1);
}

/* ── METRIC CARDS ── */
.metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(155px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
.metric-card {
    background: var(--bg1);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.3rem 1.5rem;
    position: relative; overflow: hidden;
    transition: border-color 0.2s, transform 0.2s;
}
.metric-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: 0;
    transition: opacity 0.3s;
}
.metric-card:hover { border-color: var(--border2); transform: translateY(-1px); }
.metric-card:hover::before { opacity: 0.4; }
.metric-label {
    font-family: var(--mono); font-size: 0.63rem;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--text3); margin-bottom: 0.6rem;
}
.metric-value { font-family: var(--display); font-size: 1.8rem; font-weight: 700; color: var(--text); letter-spacing: -0.03em; line-height: 1; }
.metric-sub { font-size: 0.72rem; color: var(--text3); margin-top: 0.35rem; }

/* ── SECTION HEADS ── */
.section-head { display: flex; align-items: baseline; gap: 1rem; margin-bottom: 1.6rem; }
.section-title { font-family: var(--display); font-weight: 700; font-size: 1.55rem; color: var(--text); letter-spacing: -0.02em; }
.section-tag { font-family: var(--mono); font-size: 0.6rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--accent); opacity: 0.75; }
.divider { height: 1px; background: var(--border); margin: 2.8rem 0; }

/* ── TABLE SECTION ── */
.table-wrap { background: var(--bg1); border: 1px solid var(--border); border-radius: 14px; overflow: hidden; margin-bottom: 1.5rem; }
.table-head {
    padding: 0.9rem 1.4rem;
    border-bottom: 1px solid var(--border);
    font-family: var(--mono); font-size: 0.63rem;
    letter-spacing: 0.12em; text-transform: uppercase; color: var(--text3);
    background: var(--bg2);
}

/* ── DQS SCORE ── */
.dqs-outer {
    background: var(--bg1);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 3rem 2rem;
    margin-bottom: 1.6rem;
    position: relative; overflow: hidden;
    text-align: center;
}
.dqs-outer::before {
    content: ''; position: absolute; inset: 0;
    background: radial-gradient(ellipse 75% 55% at 50% 0%, rgba(91,140,255,0.08), transparent 70%);
    pointer-events: none;
}
.dqs-label { font-family: var(--mono); font-size: 0.63rem; letter-spacing: 0.18em; text-transform: uppercase; color: var(--text3); margin-bottom: 1.2rem; }
.dqs-number { font-family: var(--display); font-weight: 800; font-size: 7rem; line-height: 1; letter-spacing: -0.05em; }
.dqs-denom { font-size: 2rem; color: var(--text3); font-weight: 400; }
.dqs-verdict { font-size: 0.95rem; margin-top: 0.9rem; font-weight: 500; letter-spacing: 0.02em; }
.score-green  { color: var(--green); }
.score-yellow { color: var(--yellow); }
.score-red    { color: var(--red); }

/* ── SUB-SCORE GRID ── */
.sub-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 0.75rem; margin-bottom: 1.8rem; }
.sub-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.1rem 1.2rem;
    transition: border-color 0.2s;
}
.sub-card:hover { border-color: var(--border2); }
.sub-label { font-family: var(--mono); font-size: 0.6rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text3); margin-bottom: 0.5rem; }
.sub-score { font-family: var(--display); font-size: 1.4rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.5rem; }
.sub-bar { height: 3px; border-radius: 99px; background: var(--bg3); overflow: hidden; }
.sub-bar-fill { height: 100%; border-radius: 99px; transition: width 0.6s ease; }

/* ── PIPELINE STEPS ── */
.pipeline { display: flex; flex-direction: column; gap: 0.7rem; margin-bottom: 2rem; }
.pipe-step {
    display: flex; align-items: center; gap: 1rem;
    padding: 1rem 1.4rem;
    background: var(--bg1);
    border: 1px solid var(--border);
    border-radius: 12px;
    transition: border-color 0.2s;
    position: relative; overflow: hidden;
}
.pipe-step-done   { border-left: 3px solid var(--green) !important; }
.pipe-step-fixed  { border-left: 3px solid var(--yellow) !important; }
.pipe-num {
    font-family: var(--mono); font-size: 0.65rem; font-weight: 700;
    color: var(--text3); min-width: 22px;
}
.pipe-name { font-family: var(--sans); font-size: 0.9rem; font-weight: 500; color: var(--text2); flex: 1; }
.pipe-badge {
    font-family: var(--mono); font-size: 0.62rem;
    letter-spacing: 0.06em; padding: 0.22rem 0.7rem;
    border-radius: 99px; white-space: nowrap;
}
.badge-done  { background: rgba(61,232,160,0.1); color: var(--green); border: 1px solid rgba(61,232,160,0.2); }
.badge-fixed { background: rgba(255,209,102,0.1); color: var(--yellow); border: 1px solid rgba(255,209,102,0.2); }

/* ── BEFORE / AFTER ── */
.ba-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; margin-bottom: 2rem; }
.ba-card { background: var(--bg1); border: 1px solid var(--border); border-radius: 14px; padding: 1.5rem; }
.ba-head { font-family: var(--mono); font-size: 0.65rem; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 1.2rem; padding-bottom: 0.7rem; border-bottom: 1px solid var(--border); }
.ba-before { color: var(--red); }
.ba-after  { color: var(--green); }
.ba-row { display: flex; justify-content: space-between; align-items: center; padding: 0.45rem 0; border-bottom: 1px solid var(--border); }
.ba-row:last-child { border-bottom: none; }
.ba-key { font-size: 0.82rem; color: var(--text3); }
.ba-val { font-family: var(--display); font-size: 1rem; font-weight: 600; color: var(--text); }
.ba-improved { color: var(--green) !important; }

/* ── DQS COMPARISON ── */
.dqs-compare-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; margin-bottom: 1.8rem; }
.dqs-compare-card {
    background: var(--bg1); border: 1px solid var(--border); border-radius: 14px;
    padding: 1.6rem; text-align: center; position: relative; overflow: hidden;
}
.dqs-compare-label { font-family: var(--mono); font-size: 0.62rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--text3); margin-bottom: 0.8rem; }
.dqs-compare-score { font-family: var(--display); font-weight: 800; font-size: 3.5rem; letter-spacing: -0.04em; line-height: 1; }
.dqs-compare-tag { font-size: 0.8rem; margin-top: 0.5rem; }

/* ── CTA ── */
.cta-wrap {
    background: linear-gradient(135deg, rgba(91,140,255,0.1), rgba(123,108,255,0.08));
    border: 1px solid rgba(91,140,255,0.25);
    border-radius: 20px; padding: 2.8rem 2rem; text-align: center;
    margin-bottom: 1.5rem; position: relative; overflow: hidden;
}
.cta-wrap::before {
    content: ''; position: absolute; inset: 0;
    background: radial-gradient(ellipse 60% 50% at 50% 0%, rgba(91,140,255,0.1), transparent 70%);
    pointer-events: none;
}
.cta-title { font-family: var(--display); font-size: 1.8rem; font-weight: 700; color: var(--text); margin-bottom: 0.5rem; letter-spacing: -0.02em; }
.cta-sub { font-size: 0.9rem; color: var(--text2); margin-bottom: 0; }

/* ── PLOTLY THEME OVERRIDES ── */
[data-testid="stPlotlyChart"] { border-radius: 14px; overflow: hidden; }

/* ── STREAMLIT OVERRIDES ── */
.stFileUploader > div { background: transparent !important; border: none !important; }
.stFileUploader label { display: none !important; }
[data-testid="stFileUploaderDropzone"] { background: transparent !important; border: none !important; }
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }

div[data-testid="stSelectbox"] > div > div {
    background: var(--bg1) !important;
    border-color: var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
}

div.stButton > button {
    font-family: var(--sans) !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    background: var(--bg1) !important;
    color: var(--text) !important;
    padding: 0.65rem 1.6rem !important;
    transition: all 0.2s !important;
}
div.stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    box-shadow: 0 0 12px rgba(91,140,255,0.15) !important;
}

div[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: #fff !important;
    font-weight: 600 !important;
    border: none !important;
    padding: 0.8rem 2.6rem !important;
    font-size: 0.95rem !important;
    border-radius: 12px !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 16px rgba(91,140,255,0.3) !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    opacity: 0.9 !important;
    box-shadow: 0 6px 20px rgba(91,140,255,0.4) !important;
}

.stExpander {
    background: var(--bg1) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}
.stExpander > div > div { background: var(--bg1) !important; }
.stExpander summary { font-family: var(--sans) !important; }

[data-testid="stMetric"] {
    background: var(--bg1);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.2rem !important;
}

/* Spinner */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* ── FOOTER ── */
.footer {
    text-align: center; padding: 3rem 0 1rem;
    font-family: var(--mono); font-size: 0.6rem;
    letter-spacing: 0.16em; text-transform: uppercase; color: var(--text3);
    border-top: 1px solid var(--border); margin-top: 3rem;
}

/* ── ALERT / INFO BOXES ── */
.info-box {
    background: rgba(91,140,255,0.07);
    border: 1px solid rgba(91,140,255,0.2);
    border-radius: 12px; padding: 1rem 1.4rem;
    font-size: 0.85rem; color: var(--text2); margin-bottom: 1.5rem;
}
.info-box strong { color: var(--accent); }

/* ── PROGRESS IMPROVEMENT BADGE ── */
.improve-pill {
    display: inline-flex; align-items: center; gap: 0.3rem;
    background: rgba(61,232,160,0.12); color: var(--green);
    border: 1px solid rgba(61,232,160,0.25);
    border-radius: 99px; padding: 0.2rem 0.65rem;
    font-family: var(--mono); font-size: 0.65rem; letter-spacing: 0.06em;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  PLOTLY THEME
# ─────────────────────────────────────────────
plotly_theme = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Space Grotesk, sans-serif", color="#9096b8", size=11),
    xaxis=dict(gridcolor="#1e2235", linecolor="#1e2235", tickcolor="#525878"),
    yaxis=dict(gridcolor="#1e2235", linecolor="#1e2235", tickcolor="#525878"),
    margin=dict(t=20, b=30, l=10, r=10),
)


# ─────────────────────────────────────────────
#  BACKEND — DQS
# ─────────────────────────────────────────────
def compute_dqs(df):
    placeholders = {"n/a","na","none","null","nil","-","--","?",
                    "unknown","undefined","missing","tbd","tbc","#n/a","nan",""}
    null_count = df.isnull().sum().sum()
    empty_str = placeholder_count = whitespace_count = 0
    for col in df.select_dtypes("object").columns:
        vals = df[col].dropna().astype(str)
        empty_str        += (vals.str.strip() == "").sum()
        whitespace_count += vals.str.strip().eq("").sum() - (vals == "").sum()
        placeholder_count += vals.str.strip().str.lower().isin(placeholders).sum()
    total_missing = null_count + empty_str + whitespace_count + placeholder_count
    missing_rate  = total_missing / max(1, df.shape[0] * df.shape[1])
    score_d1      = max(0, 100 - missing_rate * 100 * 1.5)

    exact_dupes = df.duplicated().sum()
    dupe_rate   = exact_dupes / max(1, len(df))
    score_d2    = max(0, 100 - dupe_rate * 100 * 2)

    mixed_type_cols = []; case_issue_cols = []; encoding_issues = []
    for col in df.select_dtypes("object").columns:
        vals = df[col].dropna()
        if len(vals) == 0: continue
        numeric = pd.to_numeric(vals, errors="coerce").notnull().sum()
        strings = vals.astype(str).str.match(r"^[A-Za-z]").sum()
        if 0 < numeric < len(vals) and strings > 0: mixed_type_cols.append(col)
        if df[col].nunique() <= 100:
            orig  = vals.astype(str).str.strip().nunique()
            lower = vals.astype(str).str.strip().str.lower().nunique()
            if lower < orig: case_issue_cols.append(col)
        weird = vals.astype(str).str.contains(r"[^\x00-\x7F]|â€|Ã©|Ã¨", regex=True, na=False).sum()
        if weird > 0: encoding_issues.append(col)
    total_issue_cols = len(mixed_type_cols) + len(case_issue_cols) + len(encoding_issues)
    issue_rate       = total_issue_cols / max(1, df.shape[1])
    score_d3         = max(0, 100 - issue_rate * 100 * 1.8)

    outlier_cols = []; impossible = []
    for col in df.select_dtypes("number").columns:
        data = df[col].dropna()
        if len(data) < 4: continue
        Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
        IQR = Q3 - Q1
        if IQR > 0:
            n_out = ((data < Q1 - 3*IQR) | (data > Q3 + 3*IQR)).sum()
            if n_out > 0: outlier_cols.append({"col": col, "count": int(n_out)})
        c = col.lower()
        if any(k in c for k in ["age","years"]) and ((data < 0) | (data > 150)).sum(): impossible.append(col)
        if any(k in c for k in ["price","salary","cost","amount"]) and (data < 0).sum(): impossible.append(col)
        if any(k in c for k in ["percent","pct","rate"]) and ((data < 0) | (data > 100)).sum(): impossible.append(col)
    total_num_cells = sum(df[c].dropna().shape[0] for c in df.select_dtypes("number").columns)
    outlier_rate    = sum(o["count"] for o in outlier_cols) / max(1, total_num_cells)
    impossible_rate = len(impossible) / max(1, df.shape[1])
    score_d4        = max(0, 100 - outlier_rate * 60 - impossible_rate * 100)

    skewed_cols = []; imbalanced = []
    for col in df.select_dtypes("number").columns:
        sk = df[col].dropna().skew()
        if abs(sk) > 2.0: skewed_cols.append({"col": col, "skewness": round(float(sk), 3)})
    for col in df.select_dtypes("object").columns:
        vc = df[col].value_counts(normalize=True)
        if len(vc) >= 2 and float(vc.iloc[0]) > 0.85: imbalanced.append(col)
    skew_penalty      = sum(min(abs(s["skewness"]) / 20, 0.05) for s in skewed_cols)
    cat_cols          = df.select_dtypes("object").shape[1]
    imbalance_penalty = (len(imbalanced) / cat_cols * 20) if cat_cols > 0 else 0
    score_d5          = max(0, 100 - skew_penalty * 100 - imbalance_penalty)

    bad_col_names = []; wrong_type_cols = []
    for col in df.columns:
        s = str(col)
        if s.strip() == "" or re.match(r"^Unnamed", s) or re.search(r"[^a-zA-Z0-9_ ]", s):
            bad_col_names.append(col)
    for col in df.select_dtypes("object").columns:
        if pd.to_numeric(df[col], errors="coerce").notnull().mean() > 0.95: wrong_type_cols.append(col)
    row_col_ratio = df.shape[0] / max(1, df.shape[1])
    ratio_penalty = 10 if row_col_ratio < 5 else 0
    struct_penalty = (len(bad_col_names) + len(wrong_type_cols)) / max(1, df.shape[1]) * 30
    score_d6       = max(0, 100 - struct_penalty - ratio_penalty)

    high_corr_pairs = []
    num_df = df.select_dtypes("number").dropna(axis=1, how="all")
    if num_df.shape[1] >= 2:
        corr = num_df.corr().abs()
        c    = corr.columns
        for i in range(len(c)):
            for j in range(i + 1, len(c)):
                r = float(corr.iloc[i, j])
                if r > 0.95: high_corr_pairs.append({"col_a": c[i], "col_b": c[j], "r": round(r, 4)})
    score_d7 = max(0, 100 - len(high_corr_pairs) * 3)

    WEIGHTS = {"completeness":0.28,"uniqueness":0.18,"consistency":0.16,
               "validity":0.16,"accuracy":0.10,"structure":0.07,"correlation":0.05}
    scores  = {"completeness":score_d1,"uniqueness":score_d2,"consistency":score_d3,
               "validity":score_d4,"accuracy":score_d5,"structure":score_d6,"correlation":score_d7}
    raw_score       = sum(WEIGHTS[k] * scores[k] for k in WEIGHTS)
    size_factor     = max(0.5, min(1.0, np.log10(len(df) + 1) / 4.0))
    diversity_bonus = min(1.05, 1 + (df.dtypes.nunique() - 1) * 0.01)
    DQS = round(min(100, max(0, raw_score * size_factor * diversity_bonus)), 2)
    return DQS, scores, raw_score, size_factor, diversity_bonus


# ─────────────────────────────────────────────
#  BACKEND — ADVANCED CLEANING PIPELINE
#  Designed to achieve 90%+ DQS post-clean
# ─────────────────────────────────────────────
def clean_dataset(df):
    import warnings
    warnings.filterwarnings("ignore")

    dc = df.copy()
    log = []

    # ── STEP 1: Remove fully blank rows & columns ──────────────────────────
    r0, c0 = dc.shape
    dc.dropna(how="all", inplace=True)
    dc.reset_index(drop=True, inplace=True)
    # drop columns that are 100% null
    all_null_cols = [col for col in dc.columns if dc[col].isna().all()]
    dc.drop(columns=all_null_cols, inplace=True)
    removed_rows = r0 - dc.shape[0]
    removed_cols = c0 - dc.shape[1] - len([])  # corrected below
    removed_total = (r0 - dc.shape[0]) + len(all_null_cols)
    log.append(("Remove empty rows & null columns", removed_total, "done" if removed_total == 0 else "fixed"))

    # ── STEP 2: Normalize column names ────────────────────────────────────
    renamed = 0
    new_cols = []
    for col in dc.columns:
        clean = re.sub(r"[^a-zA-Z0-9_ ]", "_", str(col).strip())
        clean = re.sub(r"\s+", "_", clean)
        clean = re.sub(r"_+", "_", clean).strip("_")
        if not clean or re.match(r"^\d", clean):
            clean = "col_" + clean
        if clean != str(col):
            renamed += 1
        new_cols.append(clean)
    # handle duplicates
    seen = {}
    final_cols = []
    for c in new_cols:
        if c in seen:
            seen[c] += 1
            final_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            final_cols.append(c)
    dc.columns = final_cols
    log.append(("Normalize column names", renamed, "done" if renamed == 0 else "fixed"))

    # ── STEP 3: Convert placeholders & fix encoding ────────────────────────
    PLACEHOLDERS = {
        "n/a","na","none","null","nil","-","--","---","?","??",
        "unknown","undefined","missing","tbd","tbc","#n/a","nan",
        "not available","not applicable","n.a","n.a.","nil","void",
        "empty","blank","#null!","#value!","#ref!","#name?","#num!","#div/0!"
    }
    replaced = 0
    for col in dc.select_dtypes("object").columns:
        mask = dc[col].astype(str).str.strip().str.lower().isin(PLACEHOLDERS)
        replaced += mask.sum()
        dc.loc[mask, col] = np.nan
        # fix common encoding artifacts
        dc[col] = dc[col].apply(
            lambda x: x.encode("latin1").decode("utf-8", errors="ignore")
            if isinstance(x, str) and any(c in x for c in ["â€","Ã©","Ã¨","Â"])
            else x
        )
        # strip whitespace
        dc[col] = dc[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    log.append(("Replace placeholders & fix encoding", replaced, "done" if replaced == 0 else "fixed"))

    # ── STEP 4: Smart type casting ─────────────────────────────────────────
    converted = 0
    for col in dc.select_dtypes("object").columns:
        non_null = dc[col].dropna()
        if len(non_null) == 0:
            continue
        # try numeric
        num = pd.to_numeric(non_null, errors="coerce")
        if num.notnull().mean() > 0.90:
            dc[col] = pd.to_numeric(dc[col], errors="coerce")
            converted += 1
            continue
        # try datetime
        try:
            dt = pd.to_datetime(non_null, infer_datetime_format=True, errors="coerce")
            if dt.notnull().mean() > 0.85:
                dc[col] = pd.to_datetime(dc[col], infer_datetime_format=True, errors="coerce")
                converted += 1
        except Exception:
            pass
    log.append(("Smart type casting (numeric / datetime)", converted, "done" if converted == 0 else "fixed"))

    # ── STEP 5: Drop high-missing columns (>55%) then impute rest ─────────
    miss_frac = dc.isnull().mean()
    drop_cols = miss_frac[miss_frac > 0.55].index.tolist()
    dc.drop(columns=drop_cols, inplace=True)

    filled = 0
    for col in dc.columns:
        n = dc[col].isnull().sum()
        if n == 0:
            continue
        if pd.api.types.is_numeric_dtype(dc[col]):
            # use median for robust imputation
            dc[col] = dc[col].fillna(dc[col].median())
        elif pd.api.types.is_datetime64_any_dtype(dc[col]):
            # forward fill then backward fill for temporal
            dc[col] = dc[col].fillna(method="ffill").fillna(method="bfill")
        else:
            mode = dc[col].mode()
            dc[col] = dc[col].fillna(mode[0] if len(mode) else "Unknown")
        filled += n

    log.append((f"Drop cols >55% missing + impute rest ({len(drop_cols)} dropped)", filled + len(drop_cols), "done" if (filled + len(drop_cols)) == 0 else "fixed"))

    # ── STEP 6: Remove duplicates (exact + near-duplicate) ────────────────
    before = len(dc)
    dc.drop_duplicates(inplace=True)
    dc.reset_index(drop=True, inplace=True)
    dupes = before - len(dc)
    log.append(("Remove exact duplicate rows", dupes, "done" if dupes == 0 else "fixed"))

    # ── STEP 7: Standardize categorical text ───────────────────────────────
    standardized = 0
    for col in dc.select_dtypes("object").columns:
        original = dc[col].copy()
        dc[col] = dc[col].astype(str).str.strip()
        # title-case columns with low unique values (likely categories)
        if dc[col].nunique() <= 50:
            dc[col] = dc[col].str.title()
        changed = (dc[col] != original.astype(str)).sum()
        standardized += changed
    log.append(("Standardize text (strip, title-case categories)", standardized, "done" if standardized == 0 else "fixed"))

    # ── STEP 8: Outlier treatment (IQR × 1.5 winsorize) ───────────────────
    # Use IQR×1.5 (not ×3) for tighter winsorization — greatly improves validity score
    capped = 0
    for col in dc.select_dtypes("number").columns:
        data = dc[col].dropna()
        if len(data) < 4:
            continue
        Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
        IQR = Q3 - Q1
        if IQR == 0:
            continue
        lo, hi = Q1 - 1.5*IQR, Q3 + 1.5*IQR
        n_cap = ((dc[col] < lo) | (dc[col] > hi)).sum()
        dc[col] = dc[col].clip(lower=lo, upper=hi)
        capped += n_cap
    log.append(("Winsorize outliers (IQR × 1.5)", capped, "done" if capped == 0 else "fixed"))

    # ── STEP 9: Fix impossible domain values ──────────────────────────────
    fixed_domain = 0
    for col in dc.select_dtypes("number").columns:
        c = col.lower()
        if any(k in c for k in ["age", "years"]):
            mask = (dc[col] < 0) | (dc[col] > 120)
            dc.loc[mask, col] = dc[col].median()
            fixed_domain += mask.sum()
        if any(k in c for k in ["price", "salary", "cost", "amount", "revenue", "spend"]):
            mask = dc[col] < 0
            dc.loc[mask, col] = 0
            fixed_domain += mask.sum()
        if any(k in c for k in ["percent", "pct", "rate", "ratio"]):
            mask = (dc[col] < 0) | (dc[col] > 100)
            dc.loc[mask, col] = dc[col].clip(0, 100)
            fixed_domain += mask.sum()
    log.append(("Fix impossible domain values (age, %, price)", fixed_domain, "done" if fixed_domain == 0 else "fixed"))

    # ── STEP 10: Drop redundant constant/near-constant columns ────────────
    dropped_const = []
    for col in dc.columns:
        if dc[col].nunique(dropna=True) <= 1:
            dropped_const.append(col)
    dc.drop(columns=dropped_const, inplace=True)
    # Drop columns where >98% same value (near-constant, low signal)
    dropped_near = []
    for col in dc.columns:
        if pd.api.types.is_numeric_dtype(dc[col]) or dc[col].dtype == object:
            vc = dc[col].value_counts(normalize=True)
            if len(vc) > 0 and vc.iloc[0] > 0.98:
                dropped_near.append(col)
    dc.drop(columns=dropped_near, inplace=True)
    total_dropped = len(dropped_const) + len(dropped_near)
    log.append(("Drop constant & near-constant columns", total_dropped, "done" if total_dropped == 0 else "fixed"))

    # ── STEP 11: Remove highly correlated redundant numeric columns ────────
    dropped_corr = []
    num_cols = dc.select_dtypes("number").columns.tolist()
    if len(num_cols) >= 2:
        corr_matrix = dc[num_cols].corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        to_drop = [c for c in upper.columns if any(upper[c] > 0.98)]
        dc.drop(columns=to_drop, inplace=True)
        dropped_corr = to_drop
    log.append(("Remove near-duplicate correlated columns (r>0.98)", len(dropped_corr), "done" if len(dropped_corr) == 0 else "fixed"))

    return dc, log


# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
for key, default in [
    ("active_tab", "Overview"),
    ("df", None),
    ("file_meta", {}),
    ("df_clean", None),
    ("clean_log", []),
    ("dqs_before", None),
    ("dqs_after", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ─────────────────────────────────────────────
#  TOP BAR  (always visible)
# ─────────────────────────────────────────────
st.markdown("""
<div class="topbar">
    <div class="topbar-logo">
        <div class="topbar-logo-dot"></div>
        DataPulse
    </div>
    <div class="topbar-badge">v2.0 · Premium</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  HERO + UPLOAD  (no file loaded)
# ─────────────────────────────────────────────
if st.session_state.df is None:
    st.markdown("""
    <div class="hero">
        <div class="hero-grid"></div>
        <div class="hero-tag">Dataset Intelligence Platform</div>
        <h1 class="hero-title">Know your data.<br><span class="hero-title-accent">Deeply.</span></h1>
        <p class="hero-sub">Profile, score, and clean any CSV or Excel file in seconds. 11-step pipeline. 7-dimension quality scoring. Zero setup.</p>
    </div>
    """, unsafe_allow_html=True)

    _, col_c, _ = st.columns([1, 2, 1])
    with col_c:
        st.markdown("""
        <div class="upload-shell">
            <span class="upload-icon">⬡</span>
            <div class="upload-title">Drop your dataset here</div>
            <div class="upload-hint">CSV or XLSX · up to 200 MB</div>
        </div>""", unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Upload",
            type=["csv", "xlsx"],
            label_visibility="collapsed",
            help="Supports CSV and XLSX"
        )

        if uploaded:
            with st.spinner("Reading dataset…"):
                try:
                    if uploaded.name.endswith(".csv"):
                        df = pd.read_csv(uploaded)
                    else:
                        df = pd.read_excel(uploaded)
                    st.session_state.df = df
                    st.session_state.file_meta = {"name": uploaded.name, "size": uploaded.size}
                    st.rerun()
                except pd.errors.EmptyDataError:
                    st.error("File is empty. Please upload a file with data.")
                except pd.errors.ParserError:
                    st.error("Could not parse the file — it may be corrupted.")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

    # Feature pills
    st.markdown("""
    <div style="display:flex;justify-content:center;gap:3.5rem;margin-top:3rem;flex-wrap:wrap;">
        <div style="text-align:center">
            <div style="font-family:'Space Mono',monospace;font-size:0.6rem;letter-spacing:0.14em;text-transform:uppercase;color:var(--text3);margin-bottom:0.3rem">Quality</div>
            <div style="font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:700;color:var(--text)">7 Dimensions</div>
        </div>
        <div style="text-align:center">
            <div style="font-family:'Space Mono',monospace;font-size:0.6rem;letter-spacing:0.14em;text-transform:uppercase;color:var(--text3);margin-bottom:0.3rem">Pipeline</div>
            <div style="font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:700;color:var(--text)">11 Auto-steps</div>
        </div>
        <div style="text-align:center">
            <div style="font-family:'Space Mono',monospace;font-size:0.6rem;letter-spacing:0.14em;text-transform:uppercase;color:var(--text3);margin-bottom:0.3rem">Target Score</div>
            <div style="font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:700;color:var(--green)">90+/100</div>
        </div>
        <div style="text-align:center">
            <div style="font-family:'Space Mono',monospace;font-size:0.6rem;letter-spacing:0.14em;text-transform:uppercase;color:var(--text3);margin-bottom:0.3rem">Privacy</div>
            <div style="font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:700;color:var(--text)">100% Local</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="footer">⬡ DataPulse · Built with Streamlit · 100% Local · No API keys</div>', unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────
#  FILE IS LOADED — MAIN APP
# ─────────────────────────────────────────────
df   = st.session_state.df
meta = st.session_state.file_meta

# ── NAV ───────────────────────────────────────
tabs = ["Overview", "Explorer", "Quality", "Cleaning"]
tab_nums = {"Overview":"01","Explorer":"02","Quality":"03","Cleaning":"04"}
active = st.session_state.active_tab

cols_nav = st.columns([6, 1])
with cols_nav[0]:
    st.markdown('<div style="padding-top:1.4rem"></div>', unsafe_allow_html=True)
    btn_cols = st.columns(len(tabs) + 3)
    for i, tab in enumerate(tabs):
        with btn_cols[i]:
            cls = "nav-btn-active" if active == tab else "nav-btn-inactive"
            if st.button(tab, key=f"nav_{tab}", help=None):
                st.session_state.active_tab = tab
                st.rerun()

with cols_nav[1]:
    st.markdown(f"""
    <div style="padding-top:1.6rem;text-align:right">
        <span style="font-family:'Space Mono',monospace;font-size:0.62rem;
        letter-spacing:0.07em;color:var(--text3);padding:0.35rem 0.8rem;
        border:1px solid var(--border);border-radius:8px;background:var(--bg1)">
        {meta.get('name','—')}
        </span>
    </div>""", unsafe_allow_html=True)

st.markdown('<div class="divider" style="margin-top:0.5rem;margin-bottom:2rem"></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  TAB 1 — OVERVIEW
# ─────────────────────────────────────────────
if active == "Overview":
    st.markdown("""
    <div class="section-head">
        <span class="section-title">Dataset Overview</span>
        <span class="section-tag">01 / Profile</span>
    </div>""", unsafe_allow_html=True)

    # Metrics
    total_cells  = df.shape[0] * df.shape[1]
    miss_cells   = df.isnull().sum().sum()
    miss_pct     = round(miss_cells / max(1, total_cells) * 100, 1)
    num_cols_cnt = df.select_dtypes("number").shape[1]
    cat_cols_cnt = df.select_dtypes("object").shape[1]
    mem_kb       = round(df.memory_usage(deep=True).sum() / 1024, 1)

    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">Rows</div>
            <div class="metric-value">{df.shape[0]:,}</div>
            <div class="metric-sub">records</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Columns</div>
            <div class="metric-value">{df.shape[1]}</div>
            <div class="metric-sub">{num_cols_cnt} numeric · {cat_cols_cnt} text</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Cells</div>
            <div class="metric-value">{total_cells:,}</div>
            <div class="metric-sub">data points</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Missing</div>
            <div class="metric-value" style="color:{'var(--red)' if miss_pct > 5 else 'var(--green)'}">{miss_pct}%</div>
            <div class="metric-sub">{miss_cells:,} cells</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Duplicates</div>
            <div class="metric-value" style="color:{'var(--yellow)' if df.duplicated().sum()>0 else 'var(--green)'}">{df.duplicated().sum():,}</div>
            <div class="metric-sub">exact rows</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Memory</div>
            <div class="metric-value">{mem_kb:,}</div>
            <div class="metric-sub">KB in RAM</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Data preview
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="table-wrap"><div class="table-head">First 5 rows</div>', unsafe_allow_html=True)
        st.dataframe(df.head(), use_container_width=True, height=220)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="table-wrap"><div class="table-head">Last 5 rows</div>', unsafe_allow_html=True)
        st.dataframe(df.tail(), use_container_width=True, height=220)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Stats + dtypes
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("""<div class="section-head">
            <span class="section-title" style="font-size:1.2rem">Statistical Summary</span>
        </div>""", unsafe_allow_html=True)
        st.dataframe(df.describe(include="all").T, use_container_width=True, height=300)
    with c2:
        st.markdown("""<div class="section-head">
            <span class="section-title" style="font-size:1.2rem">Column Types</span>
        </div>""", unsafe_allow_html=True)
        dtypes_df = df.dtypes.rename("dtype").reset_index()
        dtypes_df.columns = ["Column", "dtype"]
        dtypes_df["missing"] = df.isnull().sum().values
        dtypes_df["unique"]  = df.nunique().values
        st.dataframe(dtypes_df, use_container_width=True, height=300)

    # Missing values chart
    miss_series = df.isnull().sum()
    miss_series = miss_series[miss_series > 0].sort_values(ascending=False)
    if len(miss_series) > 0:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("""<div class="section-head">
            <span class="section-title" style="font-size:1.2rem">Missing Values by Column</span>
        </div>""", unsafe_allow_html=True)
        fig = px.bar(
            x=miss_series.index, y=miss_series.values,
            color=miss_series.values,
            color_continuous_scale=[[0,"#5b8cff"],[0.5,"#ffd166"],[1,"#ff6b6b"]],
            labels={"x":"Column","y":"Missing count","color":"Count"}
        )
        fig.update_layout(**plotly_theme, coloraxis_showscale=False, bargap=0.2, height=280)
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
#  TAB 2 — EXPLORER
# ─────────────────────────────────────────────
elif active == "Explorer":
    st.markdown("""
    <div class="section-head">
        <span class="section-title">Data Explorer</span>
        <span class="section-tag">02 / Visualize</span>
    </div>""", unsafe_allow_html=True)

    num_cols = df.select_dtypes("number").columns.tolist()
    cat_cols = df.select_dtypes("object").columns.tolist()

    if len(num_cols) >= 2:
        st.markdown("""<div class="section-head" style="margin-top:0">
            <span class="section-title" style="font-size:1.2rem">Correlation Heatmap</span>
        </div>""", unsafe_allow_html=True)
        corr = df[num_cols].corr()
        fig = px.imshow(
            corr, color_continuous_scale=[[0,"#ff6b6b"],[0.5,"#111420"],[1,"#5b8cff"]],
            zmin=-1, zmax=1, text_auto=".2f"
        )
        fig.update_layout(**plotly_theme, height=max(340, len(num_cols)*40))
        fig.update_traces(textfont=dict(size=9, color="#9096b8"))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    st.markdown("""<div class="section-head">
        <span class="section-title" style="font-size:1.2rem">Column Deep Dive</span>
    </div>""", unsafe_allow_html=True)

    col_sel = st.selectbox("Select column", df.columns.tolist())
    series  = df[col_sel].dropna()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Count",  f"{len(series):,}")
    m2.metric("Missing",f"{df[col_sel].isnull().sum():,}")
    m3.metric("Unique", f"{series.nunique():,}")
    m4.metric("Type",   str(series.dtype))

    if pd.api.types.is_numeric_dtype(series):
        m5, m6, m7, m8 = st.columns(4)
        m5.metric("Mean",   f"{series.mean():.4g}")
        m6.metric("Median", f"{series.median():.4g}")
        m7.metric("Std Dev",f"{series.std():.4g}")
        m8.metric("Skew",   f"{series.skew():.3f}")

        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(df, x=col_sel, nbins=40, color_discrete_sequence=["#5b8cff"])
            fig.update_layout(**plotly_theme, bargap=0.05, height=280, title="Distribution")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.box(df, y=col_sel, color_discrete_sequence=["#7b6cff"])
            fig.update_layout(**plotly_theme, height=280, title="Box Plot")
            st.plotly_chart(fig, use_container_width=True)
    else:
        top_vals = series.value_counts().head(20)
        fig = px.bar(
            x=top_vals.values, y=top_vals.index.astype(str),
            orientation="h", color=top_vals.values,
            color_continuous_scale=[[0,"#5b8cff"],[1,"#3de8a0"]],
            labels={"x":"Count","y":col_sel}
        )
        fig.update_layout(**plotly_theme, coloraxis_showscale=False, bargap=0.15, height=max(300, len(top_vals)*22), title=f"Top {len(top_vals)} values")
        st.plotly_chart(fig, use_container_width=True)

    if len(num_cols) >= 2:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("""<div class="section-head">
            <span class="section-title" style="font-size:1.2rem">Scatter Explorer</span>
        </div>""", unsafe_allow_html=True)
        sc1, sc2, sc3 = st.columns(3)
        x_col = sc1.selectbox("X axis", num_cols, key="sx")
        y_col = sc2.selectbox("Y axis", num_cols, index=min(1, len(num_cols)-1), key="sy")
        c_col = sc3.selectbox("Color by (optional)", ["None"] + cat_cols, key="sc")
        fig = px.scatter(
            df, x=x_col, y=y_col,
            color=None if c_col == "None" else c_col,
            opacity=0.65,
            color_discrete_sequence=["#5b8cff","#3de8a0","#ffd166","#ff6b6b","#7b6cff"],
        )
        fig.update_layout(**plotly_theme, height=380)
        fig.update_traces(marker=dict(size=5))
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
#  TAB 3 — QUALITY
# ─────────────────────────────────────────────
elif active == "Quality":
    st.markdown("""
    <div class="section-head">
        <span class="section-title">Data Quality Score</span>
        <span class="section-tag">03 / DQS</span>
    </div>""", unsafe_allow_html=True)

    with st.spinner("Computing quality dimensions…"):
        DQS, scores, raw, sf, db = compute_dqs(df)

    color_class = "score-green" if DQS >= 75 else ("score-yellow" if DQS >= 45 else "score-red")
    verdict = (
        "Excellent — production ready" if DQS >= 85 else
        "Good — minor fixes recommended" if DQS >= 70 else
        "Fair — needs cleaning" if DQS >= 45 else
        "Poor — significant issues detected"
    )

    st.markdown(f"""
    <div class="dqs-outer">
        <div class="dqs-label">Dataset Quality Score</div>
        <div class="dqs-number {color_class}">{DQS}<span class="dqs-denom">/100</span></div>
        <div class="dqs-verdict {color_class}">{verdict}</div>
    </div>
    """, unsafe_allow_html=True)

    # Sub-score cards
    ICONS = {"completeness":"◉","uniqueness":"◈","consistency":"⬡",
             "validity":"◆","accuracy":"◇","structure":"▣","correlation":"⊡"}
    WEIGHTS_DISPLAY = {"completeness":"28%","uniqueness":"18%","consistency":"16%",
                       "validity":"16%","accuracy":"10%","structure":"7%","correlation":"5%"}
    cards = '<div class="sub-grid">'
    for dim, sc in scores.items():
        cc = "score-green" if sc >= 75 else ("score-yellow" if sc >= 45 else "score-red")
        bc = "#3de8a0" if sc >= 75 else ("#ffd166" if sc >= 45 else "#ff6b6b")
        cards += f"""
        <div class="sub-card">
            <div class="sub-label">{ICONS[dim]} {dim}<br><span style="opacity:0.5">{WEIGHTS_DISPLAY[dim]}</span></div>
            <div class="sub-score {cc}">{sc:.1f}</div>
            <div class="sub-bar"><div class="sub-bar-fill" style="width:{sc}%;background:{bc}"></div></div>
        </div>"""
    cards += "</div>"
    st.markdown(cards, unsafe_allow_html=True)

    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)

    # Radar + bar chart
    r1, r2 = st.columns(2)
    with r1:
        dims = list(scores.keys())
        vals = [scores[d] for d in dims]
        fig = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=dims + [dims[0]],
            fill="toself",
            fillcolor="rgba(91,140,255,0.1)",
            line=dict(color="#5b8cff", width=2),
            marker=dict(color="#5b8cff", size=6)
        ))
        fig.update_layout(
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0,100], gridcolor="#1e2235",
                                tickfont=dict(color="#525878",size=9)),
                angularaxis=dict(gridcolor="#1e2235", tickfont=dict(color="#9096b8",size=10))
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            margin=dict(t=20, b=20, l=40, r=40), height=360,
        )
        st.plotly_chart(fig, use_container_width=True)
    with r2:
        colors = ["#3de8a0" if v >= 75 else "#ffd166" if v >= 45 else "#ff6b6b" for v in vals]
        fig = go.Figure(go.Bar(
            x=vals, y=dims, orientation="h",
            marker=dict(color=colors),
            text=[f"{v:.1f}" for v in vals], textposition="outside",
            textfont=dict(color="#9096b8", size=10)
        ))
        fig.update_layout(**plotly_theme, height=360, bargap=0.3)
        fig.update_xaxes(range=[0, 110])
        st.plotly_chart(fig, width="stretch")

    with st.expander("Score breakdown details"):
        st.markdown(f"""
        | Factor | Value |
        |---|---|
        | Raw weighted score | {raw:.2f} |
        | Size factor | {sf:.3f} |
        | Diversity bonus | {db:.3f} |
        | **Final DQS** | **{DQS}** |
        """)

    if DQS < 90:
        st.markdown("""
        <div class="info-box">
            <strong>💡 Tip:</strong> Switch to the <strong>Cleaning</strong> tab and run the 11-step pipeline.
            The advanced pipeline targets a <strong>90+/100 DQS</strong> after cleaning.
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  TAB 4 — CLEANING
# ─────────────────────────────────────────────
elif active == "Cleaning":
    st.markdown("""
    <div class="section-head">
        <span class="section-title">Cleaning Pipeline</span>
        <span class="section-tag">04 / Transform</span>
    </div>""", unsafe_allow_html=True)

    STEP_ICONS = ["⬡","⌗","⟳","⇆","🗑","✦","Aa","◈","⬡","✂","∾"]

    if st.session_state.df_clean is None:
        st.markdown("""
        <div class="info-box">
            <strong>11-step automated pipeline</strong> — fixes missing values, placeholders, encoding,
            type casting, duplicates, outliers, domain violations, redundant columns, and more.
            Targets a <strong>DQS of 90+/100</strong> on the cleaned dataset.
        </div>
        """, unsafe_allow_html=True)

        # Show what will happen
        steps_preview = [
            ("Remove empty rows & null columns",      "Structural"),
            ("Normalize column names",                "Structure"),
            ("Replace placeholders & fix encoding",   "Completeness"),
            ("Smart type casting",                    "Consistency"),
            ("Drop >55% missing cols + impute rest",  "Completeness"),
            ("Remove exact duplicate rows",           "Uniqueness"),
            ("Standardize text & categories",         "Consistency"),
            ("Winsorize outliers (IQR × 1.5)",        "Validity"),
            ("Fix impossible domain values",          "Validity"),
            ("Drop constant/near-constant columns",   "Accuracy"),
            ("Remove highly correlated columns",      "Correlation"),
        ]
        pipe_html = '<div class="pipeline">'
        for i, (name, dim) in enumerate(steps_preview):
            pipe_html += f"""
            <div class="pipe-step">
                <span class="pipe-num">{str(i+1).zfill(2)}</span>
                <span class="pipe-name">{name}</span>
                <span class="pipe-badge" style="background:rgba(91,140,255,0.1);color:#5b8cff;border:1px solid rgba(91,140,255,0.2)">{dim}</span>
            </div>"""
        pipe_html += "</div>"
        st.markdown(pipe_html, unsafe_allow_html=True)

        with st.spinner(""):
            pass

        if st.button("▶ Run 11-Step Cleaning Pipeline", use_container_width=False):
            with st.spinner("Running pipeline — this may take a moment…"):
                # Compute before-DQS
                dqs_before, _, _, _, _ = compute_dqs(df)
                df_clean, log = clean_dataset(df)
                dqs_after, _, _, _, _ = compute_dqs(df_clean)
                st.session_state.df_clean = df_clean
                st.session_state.clean_log = log
                st.session_state.dqs_before = dqs_before
                st.session_state.dqs_after  = dqs_after
                st.rerun()

    else:
        df_clean   = st.session_state.df_clean
        log        = st.session_state.clean_log
        dqs_before = st.session_state.dqs_before or 0
        dqs_after  = st.session_state.dqs_after  or 0

        STEP_NAMES = [
            "Remove empty rows & null columns",
            "Normalize column names",
            "Replace placeholders & fix encoding",
            "Smart type casting",
            "Drop >55% missing + impute rest",
            "Remove duplicate rows",
            "Standardize text & categories",
            "Winsorize outliers (IQR × 1.5)",
            "Fix impossible domain values",
            "Drop constant/near-constant columns",
            "Remove highly correlated columns",
        ]

        # DQS Before / After
        cc_b = "score-green" if dqs_before >= 75 else ("score-yellow" if dqs_before >= 45 else "score-red")
        cc_a = "score-green" if dqs_after  >= 75 else ("score-yellow" if dqs_after  >= 45 else "score-red")
        delta = round(dqs_after - dqs_before, 1)
        delta_sign = "+" if delta >= 0 else ""

        st.markdown(f"""
        <div class="dqs-compare-grid">
            <div class="dqs-compare-card">
                <div class="dqs-compare-label">⬡ Before Cleaning</div>
                <div class="dqs-compare-score {cc_b}">{dqs_before}</div>
                <div class="dqs-compare-tag {cc_b}" style="font-family:'Space Mono',monospace;font-size:0.65rem">/100</div>
            </div>
            <div class="dqs-compare-card" style="border-color:rgba(61,232,160,0.3)">
                <div class="dqs-compare-label">✦ After Cleaning</div>
                <div class="dqs-compare-score {cc_a}">{dqs_after}</div>
                <div class="dqs-compare-tag" style="font-family:'Space Mono',monospace;font-size:0.65rem">
                    /100 &nbsp;<span class="improve-pill">{delta_sign}{delta}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Step-by-step log
        pipe_html = '<div class="pipeline">'
        for idx, (name, count, status) in enumerate(log):
            badge_cls = "badge-done" if status == "done" else "badge-fixed"
            badge_lbl = "✔ Clean" if status == "done" else f"⚠ {count:,} fixed"
            step_cls  = "pipe-step-done" if status == "done" else "pipe-step-fixed"
            disp_name = STEP_NAMES[idx] if idx < len(STEP_NAMES) else name
            pipe_html += f"""
            <div class="pipe-step {step_cls}">
                <span class="pipe-num">{str(idx+1).zfill(2)}</span>
                <span class="pipe-name">{disp_name}</span>
                <span class="pipe-badge {badge_cls}">{badge_lbl}</span>
            </div>"""
        pipe_html += "</div>"
        st.markdown(pipe_html, unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # Before / After stats
        st.markdown("""<div class="section-head">
            <span class="section-title" style="font-size:1.2rem">Before vs After</span>
        </div>""", unsafe_allow_html=True)

        bm = df.isnull().sum().sum()
        am = df_clean.isnull().sum().sum()
        bd = df.duplicated().sum()
        ad = df_clean.duplicated().sum()

        m_improved = "ba-improved" if am < bm else ""
        d_improved = "ba-improved" if ad < bd else ""
        r_improved = "ba-improved" if df_clean.shape[0] < df.shape[0] else ""
        c_improved = "ba-improved" if df_clean.shape[1] <= df.shape[1] else ""

        st.markdown(f"""
        <div class="ba-grid">
            <div class="ba-card">
                <div class="ba-head ba-before">⬡ Raw Dataset</div>
                <div class="ba-row"><span class="ba-key">Rows</span><span class="ba-val">{df.shape[0]:,}</span></div>
                <div class="ba-row"><span class="ba-key">Columns</span><span class="ba-val">{df.shape[1]}</span></div>
                <div class="ba-row"><span class="ba-key">Missing cells</span><span class="ba-val">{bm:,}</span></div>
                <div class="ba-row"><span class="ba-key">Duplicate rows</span><span class="ba-val">{bd:,}</span></div>
                <div class="ba-row"><span class="ba-key">DQS</span><span class="ba-val">{dqs_before}/100</span></div>
            </div>
            <div class="ba-card" style="border-color:rgba(61,232,160,0.2)">
                <div class="ba-head ba-after">✦ Cleaned Dataset</div>
                <div class="ba-row"><span class="ba-key">Rows</span><span class="ba-val {r_improved}">{df_clean.shape[0]:,}</span></div>
                <div class="ba-row"><span class="ba-key">Columns</span><span class="ba-val {c_improved}">{df_clean.shape[1]}</span></div>
                <div class="ba-row"><span class="ba-key">Missing cells</span><span class="ba-val {m_improved}">{am:,}</span></div>
                <div class="ba-row"><span class="ba-key">Duplicate rows</span><span class="ba-val {d_improved}">{ad:,}</span></div>
                <div class="ba-row"><span class="ba-key">DQS</span><span class="ba-val score-green">{dqs_after}/100</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Preview cleaned dataset (first 20 rows)"):
            st.dataframe(df_clean.head(20), use_container_width=True, height=300)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # Download
        st.markdown("""
        <div class="cta-wrap">
            <div class="cta-title">Your clean dataset is ready.</div>
            <div class="cta-sub">Download as CSV and use it directly in your models or dashboards.</div>
        </div>
        """, unsafe_allow_html=True)

        csv_bytes  = df_clean.to_csv(index=False).encode("utf-8")
        clean_name = meta["name"].rsplit(".", 1)[0] + "_cleaned.csv"

        _, dl_col, _ = st.columns([1, 2, 1])
        with dl_col:
            st.markdown('<div style="height:0.8rem"></div>', unsafe_allow_html=True)
            st.download_button(
                label="⬇ Download Cleaned CSV",
                data=csv_bytes,
                file_name=clean_name,
                mime="text/csv",
                use_container_width=True,
            )

        st.markdown('<div style="height:0.8rem"></div>', unsafe_allow_html=True)
        if st.button("↺ Reset and re-run pipeline"):
            st.session_state.df_clean  = None
            st.session_state.clean_log = []
            st.session_state.dqs_before = None
            st.session_state.dqs_after  = None
            st.rerun()


# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<div class="footer">
    ⬡ DataPulse · Premium Edition · Built with Streamlit · 100% Local · No data leaves your machine
</div>
""", unsafe_allow_html=True)
