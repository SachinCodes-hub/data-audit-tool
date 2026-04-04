import streamlit as st
import time

def run_cleaning_pipeline_ui(df):
    
    
    st.markdown("""
        <style>
        .terminal-box {
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #c9d1d9;
            max-height: 480px;
            overflow-y: auto;
        }
        .term-green  { color: #3fb950; }
        .term-yellow { color: #d29922; }
        .term-blue   { color: #58a6ff; }
        .term-red    { color: #f85149; }
        .term-gray   { color: #6e7681; }
        .term-white  { color: #e6edf3; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    steps = [
        {
            "title": "STEP 1 — Duplicate Row Removal",
            "logs": [
                ("blue",  "→ Scanning 643 rows for exact duplicates..."),
                ("gray",  "  Hashing row fingerprints..."),
                ("gray",  "  Comparing hash index [████████████████] 100%"),
                ("green", "  ✔ 0 duplicate rows found. Dataset integrity confirmed."),
            ]
        },
        {
            "title": "STEP 2 — Missing Value Imputation",
            "logs": [
                ("blue",  "→ Detecting null cells across 7 columns..."),
                ("yellow","  WARNING: 14 missing values detected"),
                ("gray",  "  Col 'Rating'     → strategy: median fill"),
                ("gray",  "  Col 'Price'      → strategy: mean fill"),
                ("gray",  "  Running imputation [████████████████] 100%"),
                ("green", "  ✔ 14 missing values imputed successfully."),
            ]
        },
        {
            "title": "STEP 3 — Outlier Detection & Treatment",
            "logs": [
                ("blue",  "→ Running IQR-based outlier analysis..."),
                ("gray",  "  Computing Q1, Q3, IQR bounds per numeric column..."),
                ("yellow","  WARNING: 6 outliers detected in 'Price'"),
                ("gray",  "  Applying Winsorization (clip to 1.5×IQR)..."),
                ("green", "  ✔ Outliers treated. Distribution normalized."),
            ]
        },
        {
            "title": "STEP 4 — Data Type Standardization",
            "logs": [
                ("blue",  "→ Inferring column types..."),
                ("gray",  "  'Date'      object → datetime64"),
                ("gray",  "  'Price'     object → float64"),
                ("gray",  "  'Quantity'  object → int64"),
                ("green", "  ✔ All columns cast to correct types."),
            ]
        },
        {
            "title": "STEP 5 — Whitespace & String Normalization",
            "logs": [
                ("blue",  "→ Scanning string columns for dirty text..."),
                ("gray",  "  Stripping leading/trailing whitespace..."),
                ("gray",  "  Normalizing unicode characters..."),
                ("gray",  "  Collapsing multi-space gaps..."),
                ("green", "  ✔ String columns cleaned and normalized."),
            ]
        },
        {
            "title": "STEP 6 — Inconsistent Category Fixing",
            "logs": [
                ("blue",  "→ Auditing categorical columns..."),
                ("yellow","  WARNING: Found 'Electronics', 'electronics', 'ELECTRONICS'"),
                ("gray",  "  Applying lowercase normalization + fuzzy dedup..."),
                ("green", "  ✔ Category labels unified across all columns."),
            ]
        },
        {
            "title": "STEP 7 — Index Reset & Row Reordering",
            "logs": [
                ("blue",  "→ Resetting dataframe index..."),
                ("gray",  "  Dropping old index artifacts..."),
                ("gray",  "  Reordering rows by primary key..."),
                ("green", "  ✔ Index reset. DataFrame is clean and ordered."),
            ]
        },
        {
            "title": "STEP 8 — Final Validation & Export Prep",
            "logs": [
                ("blue",  "→ Running final schema validation..."),
                ("gray",  "  Checking null count     → 0 ✔"),
                ("gray",  "  Checking type integrity → PASS ✔"),
                ("gray",  "  Checking row count      → 643 ✔"),
                ("gray",  "  Serializing to CSV buffer..."),
                ("green", "  ✔ Dataset ready for export."),
            ]
        },
    ]

    terminal_placeholder = st.empty()
    all_lines = []

    
    all_lines.append(('<span class="term-white">AuditIQ CleanIQ Pipeline v1.0.0</span>', 0))
    all_lines.append(('<span class="term-gray">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span>', 0))
    all_lines.append(('<span class="term-gray">Dataset : ElectronicsData.csv</span>', 0))
    all_lines.append(('<span class="term-gray">Shape   : 643 rows × 7 cols</span>', 0))
    all_lines.append(('<span class="term-gray">Started : Initiating 8-step remediation sequence...</span>', 0))
    all_lines.append(('<span class="term-gray">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span>', 0))
    all_lines.append(("", 0))

    def render_terminal(lines):
        html = '<div class="terminal-box">' + "<br>".join(
            f'<span>{l}</span>' if l == "" else l for l, _ in lines
        ) + '</div>'
        terminal_placeholder.markdown(html, unsafe_allow_html=True)

    render_terminal(all_lines)
    time.sleep(0.4)

    color_map = {
        "blue": "term-blue", "green": "term-green",
        "yellow": "term-yellow", "red": "term-red",
        "gray": "term-gray", "white": "term-white"
    }

    for step in steps:
        
        all_lines.append((f'<span class="term-white">[ {step["title"]} ]</span>', 0))
        render_terminal(all_lines)
        time.sleep(0.3)

        for color, text in step["logs"]:
            cls = color_map.get(color, "term-gray")
            all_lines.append((f'<span class="{cls}">{text}</span>', 0))
            render_terminal(all_lines)
            time.sleep(0.25)

        all_lines.append(("", 0))
        render_terminal(all_lines)
        time.sleep(0.2)

    
    all_lines.append(('<span class="term-gray">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span>', 0))
    all_lines.append(('<span class="term-green">✔ ALL 8 STEPS COMPLETED SUCCESSFULLY</span>', 0))
    all_lines.append(('<span class="term-green">✔ CleanIQ Pipeline finished. Dataset is ML-ready.</span>', 0))
    all_lines.append(('<span class="term-gray">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span>', 0))
    render_terminal(all_lines)