import streamlit as st
import os
from utils.helpers import load_file
from modules.overview import show_overview
from modules.fault_detection import show_fault_detection
from modules.cleaning import show_cleaning
from modules.explorer import show_explorer
from PIL import Image

icon_path = os.path.join(os.path.dirname(__file__), "assets", "iqlogofinal.jpeg")
page_icon = Image.open(icon_path) if os.path.exists(icon_path) else "🔭"

st.set_page_config(
    page_title="AuditIQ — Data Audit System",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)


css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


if "df" not in st.session_state:
    st.session_state.df = None
if "file_name" not in st.session_state:
    st.session_state.file_name = None
if "file_size" not in st.session_state:
    st.session_state.file_size = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0  


with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px;">
        <svg width="32" height="32" viewBox="0 0 60 60">
            <polygon points="30,5 50,15 50,45 30,55 10,45 10,15" 
                fill="#8B5CF6" stroke="#8B5CF6" stroke-width="2"/>
            <text x="30" y="30" text-anchor="middle" dominant-baseline="central"
                fill="white" font-size="14" font-weight="700">IQ</text>
        </svg>
        <span style="font-size:20px; font-weight:600;">AuditIQ</span>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Ingest → Profile → Remediate → Export")
    st.divider()

    uploaded = st.file_uploader(
        "Upload Dataset",
        type=["csv", "xlsx"],
        help="Supports CSV and Excel files",
        key=f"uploader_{st.session_state.uploader_key}"  # key changes on clear
    )

    if uploaded is not None:
        if uploaded.name != st.session_state.file_name:
            try:
                st.session_state.df        = load_file(uploaded)
                st.session_state.file_name = uploaded.name
                st.session_state.file_size = uploaded.size
            except ValueError as e:
                st.error(f"❌ {e}")
                st.session_state.df = None
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
                st.session_state.df = None

    if st.session_state.df is not None:
        st.success(f"✅ {st.session_state.file_name}")
        st.caption(f"Size: {st.session_state.file_size:,} bytes")
        st.caption(f"Shape: {st.session_state.df.shape[0]:,} rows × {st.session_state.df.shape[1]} cols")

        if st.button("🗑️ Clear file"):
            st.session_state.df          = None
            st.session_state.file_name   = None
            st.session_state.file_size   = None
            st.session_state.uploader_key += 1  
            st.rerun()

    st.divider()
    st.caption("AuditIQ © 2025 · Built on Streamlit & Pandas")


if st.session_state.df is None:

    
    st.markdown("""
    <div style='padding: 56px 0 36px 0'>
        <span class='das-label'>AUDITIQ · DATA QUALITY PLATFORM · v1.0.0</span>
        <h1 style='font-size: 2.8rem; font-weight: 700;
                   letter-spacing: -0.05em; line-height: 1.15;
                   margin: 0 0 16px 0'>
            Know your data.<br>
            <span style='color: #3b82f6'>Before it breaks your model.</span>
        </h1>
        <p style='font-size: 14px; opacity: 0.55; max-width: 480px;
                  line-height: 1.75; margin: 0 0 48px 0;
                  font-family: "DM Sans", sans-serif'>
            Upload any CSV or Excel file and get a full quality audit —
            ISO 25012 aligned DQS score, visual explorer, and a
            cleaned dataset ready for ML.
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    cards = [
        (c1, "📋", "Data Profile",        "Schema, data types, memory footprint, completeness metrics", "#3b82f6"),
        (c2, "📡", "Quality Assessment",   "Distributions, correlations, outliers, column deep dive", "#22c55e"),
        (c3, "⚠ ", "Statistical Explorer", "ISO 25012-compliant DQS scoring across 7 quality dimensions",     "#eab308"),
        (c4, "⚙️", "CleanIQ",        "Automated 8-stage remediation pipeline with audit trail",       "#a855f7"),
    ]
    for col, icon, title, desc, color in cards:
        col.markdown(f"""
        <div class='das-card'>
            <span class='das-icon'>{icon}</span>
            <p class='das-title' style='color:{color}'>{title}</p>
            <p class='das-desc'>{desc}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style='margin-top: 40px; opacity: 0.4;
                font-family: "JetBrains Mono", monospace; font-size: 12px'>
        ← Upload a CSV or Excel file from the sidebar to begin
    </div>
    """, unsafe_allow_html=True)

else:
    df = st.session_state.df

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Overview",
        "📡 Data Explorer",
        "⚠️ Fault Detection",
        "⚡ CleanIQ Pipeline",
    ])

    with tab1:
        show_overview(df, st.session_state.file_name, st.session_state.file_size)
    with tab2:
        show_explorer(df)
    with tab3:
        show_fault_detection(df)
    with tab4:
        show_cleaning(df, uploaded)
