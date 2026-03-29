#navigation 


import streamlit as st
from utils.helpers import load_file
from modules.overview import show_overview
from modules.fault_detection import show_fault_detection
from modules.cleaning import show_cleaning

# ── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Data Audit System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 Data Audit System")
    st.caption("Upload → Analyse → Clean → Download")
    st.divider()

    uploaded = st.file_uploader(
        "Upload Dataset",
        type=["csv", "xlsx"],
        help="Supports CSV and Excel files"
    )

    if uploaded:
        st.success(f"✅ {uploaded.name}")

    st.divider()
    st.caption("Built with Streamlit + Pandas")

# ── Main ──────────────────────────────────────────────────────────────
if uploaded is None:
    st.title("🔍 Data Audit System")
    st.markdown("### Upload a dataset from the sidebar to begin.")

    col1, col2, col3 = st.columns(3)
    col1.info("**📊 Phase 1**\nDataset overview, shape, types, statistics")
    col2.warning("**🚨 Phase 2**\n7-dimension fault detection + DQS Score")
    col3.success("**🧹 Phase 3**\nAutomated 8-step cleaning pipeline")

else:
    # ── Load file with error handling ─────────────────────────────
    try:
        df = load_file(uploaded)
    except Exception as e:
        st.error(f"❌ Failed to read file: {e}")
        st.stop()

    # ── Tabs ──────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "📊 Overview",
        "🚨 Fault Detection",
        "🧹 Cleaning Pipeline"
    ])

    with tab1:
        show_overview(df, uploaded)

    with tab2:
        show_fault_detection(df)

    with tab3:
        show_cleaning(df)