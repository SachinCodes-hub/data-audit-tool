# DataLens — Data Audit System

> **Know your data. Before it breaks your model.**

A professional-grade data quality auditing tool built for ML engineers, data scientists, and analysts. Upload any CSV or Excel file and get a complete quality audit in seconds — no code required.

**🔗 Live Demo:** [your-app.streamlit.app](https://your-app.streamlit.app)

---

## What is DataLens?

DataLens is an end-to-end data auditing tool that takes any raw dataset and gives you:

- A **Data Quality Score (DQS)** out of 100, aligned with the ISO 25012 standard
- A **7-dimension fault report** telling you exactly what's wrong and why
- A **visual explorer** with distributions, correlations, outlier maps, and column deep dives
- A **smart column classifier** that detects IDs, targets, constants, and high-cardinality columns
- A **cleaned dataset** ready to drop straight into your ML pipeline

---

## Features

### 📊 Dataset Overview
- Shape, memory usage, null counts, duplicate detection
- Full column details — dtype, null %, unique values, sample
- Statistical summary for all columns

### 🔭 Data Explorer
- **Smart Column Classifier** — auto-tags every column as numeric, categorical, ID, constant, datetime, high cardinality, or free text
- **Distribution plots** — histogram + KDE for numeric, bar charts for categorical
- **Box plot gallery** — visualise outliers across all numeric columns, inspect outlier rows
- **Correlation heatmap** — Pearson matrix + interactive scatter plot with regression line
- **Target column analyser** — class imbalance checker, distribution analysis, model readiness verdict
- **Column deep dive** — full single-column report with ML encoding recommendation

### 🚨 Fault Detection — ISO 25012 Aligned
Scores your dataset across 7 dimensions with a weighted **Data Quality Score (DQS)**:

| # | Dimension | Weight | What it checks |
|---|-----------|--------|----------------|
| D1 | Completeness | 28% | Null values, empty strings, disguised nulls (N/A, unknown, -, etc.) |
| D2 | Uniqueness | 18% | Duplicate rows, constant columns, identical column pairs |
| D3 | Consistency | 16% | Mixed types, case inconsistency, mixed date formats, encoding corruption |
| D4 | Validity | 16% | Extreme outliers (3×IQR), impossible domain values (negative age, etc.) |
| D5 | Accuracy | 10% | Heavy skew (>3.0), label noise (male vs m vs Male) |
| D6 | Structure | 7% | Bad column names, wrong dtypes, unnamed columns, low row/col ratio |
| D7 | Correlation | 5% | Highly correlated pairs (r > 0.95), near-duplicate columns (r > 0.999) |

Every dimension shows:
- A score out of 100
- Colour-coded findings explaining exactly what was found
- A radar chart showing your quality profile
- A priority action table — sorted by impact on your DQS

### 🧹 Cleaning Pipeline
8-step automated cleaning in one click:

1. Standardise column names (lowercase, no special characters)
2. Remove fully empty rows
3. Replace placeholder values with NaN
4. Drop columns with >70% missing data
5. Fill remaining nulls (median for numeric, mode for categorical)
6. Remove duplicate rows
7. Standardise text formatting (strip, lowercase)
8. Cap outliers at 3×IQR (Winsorize)

Before/after comparison with DQS improvement metric + one-click download of cleaned file.

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI Framework | Streamlit |
| Data Processing | Pandas, NumPy |
| Visualisation | Plotly |
| File Support | CSV, Excel (.xlsx, .xls) |
| Standard | ISO 25012 Data Quality |
| Language | Python 3.9+ |

---

## Project Structure

```
data-audit-system/
│
├── app.py                  ← main entry point + navigation
│
├── modules/
│   ├── overview.py         ← dataset overview (Phase 1)
│   ├── fault_detection.py  ← DQS engine D1–D7 (Phase 2)
│   ├── explorer.py         ← visual explorer + ML readiness (Phase 3)
│   └── cleaning.py         ← cleaning pipeline (Phase 4)
│
├── utils/
│   └── helpers.py          ← shared: file loader, DQS calculator, constants
│
├── assets/
│   └── style.css           ← custom theme (dark/light adaptive)
│
├── requirements.txt
└── README.md
```

---

## Getting Started

### Run locally

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/data-audit-system.git
cd data-audit-system

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

App opens at `http://localhost:8501`

### requirements.txt

```
streamlit>=1.32.0
pandas>=2.0.0
numpy>=1.26.0
plotly>=5.20.0
openpyxl>=3.1.0
```

---

## How the DQS Works

The **Data Quality Score** is a weighted average across 7 dimensions, aligned with ISO 25012:

```
DQS = (D1 × 0.28) + (D2 × 0.18) + (D3 × 0.16) +
      (D4 × 0.16) + (D5 × 0.10) + (D6 × 0.07) + (D7 × 0.05)
```

Each dimension uses **tiered penalties** — not linear deductions. A dataset with 1% missing values is treated very differently from one with 40% missing. The score is purely based on data quality — small clean datasets score just as high as large ones.

| Score | Grade | Meaning |
|---|---|---|
| 85–100 | A 🟢 | High quality — ready for ML |
| 70–84 | B 🟡 | Good — minor issues to fix |
| 50–69 | C 🟠 | Moderate — clean before training |
| 0–49 | D 🔴 | Poor — significant work needed |

---

## Supported File Formats

| Format | Notes |
|---|---|
| `.csv` | Auto-detects encoding (UTF-8, Latin-1, CP1252) |
| `.xlsx` | Multi-sheet support — pick your sheet |
| `.xls` | Legacy Excel format |

**Limits:** Max 100MB per file · Max 500,000 rows loaded (with warning)

---

## Screenshots

> *(Add screenshots here after deployment)*

| Welcome Screen | Fault Detection | Data Explorer |
|---|---|---|
| ![welcome](screenshots/welcome.png) | ![faults](screenshots/faults.png) | ![explorer](screenshots/explorer.png) |

---

## Roadmap

- [ ] PDF audit report export
- [ ] ML Readiness Score (dedicated tab)
- [ ] Excel audit report download (one sheet per dimension)
- [ ] Theme toggle (dark/light) inside the app
- [ ] Column encoding suggestions for sklearn pipelines
- [ ] Data leakage detector

---

## About

Built as a portfolio project to demonstrate end-to-end data engineering and Streamlit development skills.

**Author:** [Your Name]
**LinkedIn:** [your linkedin]
**GitHub:** [your github]

---

## License

MIT License — free to use, modify, and distribute.

---

*Built with Python · Streamlit · Pandas · Plotly*