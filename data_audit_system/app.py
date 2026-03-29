import streamlit as st
from utils.helpers import load_file
from modules.overview import show_overview
from modules.fault_detection import show_fault_detection
from modules.cleaning import show_cleaning
from modules.explorer import show_explorer

# ── Page Config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Data Audit System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Session State ─────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = None
if "file_name" not in st.session_state:
    st.session_state.file_name = None
if "file_size" not in st.session_state:
    st.session_state.file_size = None

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

    if uploaded is not None:
        # Only reload if it's a new file
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
            st.session_state.df        = None
            st.session_state.file_name = None
            st.session_state.file_size = None
            st.rerun()

    st.divider()
    st.caption("Built with Streamlit + Pandas")

# ── Main ──────────────────────────────────────────────────────────────
if st.session_state.df is None:
    st.title("🔍 Data Audit System")
    st.markdown("### Upload a dataset from the sidebar to begin.")
    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    col1.info("**📊 Overview**\nShape, types, memory, statistics")
    col2.success("**🔬 Explorer**\nDistributions, correlations, deep dive")
    col3.warning("**🚨 Fault Detection**\nDQS Score · ISO 25012 · 7 dimensions")
    col4.error("**🧹 Cleaning**\n8-step auto pipeline + download")

else:
    df = st.session_state.df

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview",
        "🔬 Data Explorer",
        "🚨 Fault Detection",
        "🧹 Cleaning Pipeline",
    ])

    with tab1:
        show_overview(df, st.session_state.file_name, st.session_state.file_size)
    with tab2:
        show_explorer(df)
    with tab3:
        show_fault_detection(df)
    with tab4:
        show_cleaning(df)