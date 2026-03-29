# 🔍 Data Audit System

A professional data quality auditing tool built with Python and Streamlit.

## What it does
- **Phase 1 — Overview:** Instantly understand any dataset — shape, types, memory, statistics
- **Phase 2 — Fault Detection:** Scores your data across 7 quality dimensions with a final DQS (Data Quality Score) out of 100
- **Phase 3 — Cleaning:** 8-step automated cleaning pipeline with before/after comparison and download

## The 7 Dimensions (D1–D7)
| # | Dimension | Weight |
|---|-----------|--------|
| D1 | Completeness | 28% |
| D2 | Uniqueness | 18% |
| D3 | Consistency | 16% |
| D4 | Validity | 16% |
| D5 | Accuracy | 10% |
| D6 | Structure | 7% |
| D7 | Correlation | 5% |

## Run Locally
```bash
git clone https://github.com/YOUR_USERNAME/data-audit-system
cd data-audit-system
pip install -r requirements.txt
streamlit run app.py
```

## Tech Stack
Python · Streamlit · Pandas · NumPy · Plotly