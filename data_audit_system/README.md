# ⬡ AuditIQ — Data Quality Platform

> **Know your data. Before it breaks your model.**

AuditIQ is an open-source, ISO 25012-aligned data quality platform built on Streamlit and Pandas. Upload any CSV or Excel dataset and receive a full audit — completeness scoring, statistical exploration, fault detection, and an automated 8-stage cleaning pipeline — all in one interface.

🔗 **Live Demo:** [auditiq-v094.onrender.com](https://auditiq-v094.onrender.com)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [CleanIQ Pipeline](#cleaniq-pipeline)
- [DQS Scoring](#dqs-scoring)
- [Screenshots](#screenshots)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Data quality is the single biggest bottleneck in ML pipelines. AuditIQ was built to solve this — giving data scientists, analysts, and ML engineers a fast, visual, and reproducible way to audit and clean their datasets before modelling.

AuditIQ computes a **Data Quality Score (DQS)** across 7 ISO 25012 dimensions, visualises distributions and outliers, detects structural faults, and runs an automated cleaning pipeline — outputting an ML-ready file in CSV or Excel format.

---

## Features

| Module | Description |
|---|---|
| 📋 **Data Profile** | Schema, data types, memory footprint, null counts, statistical summary |
| 📡 **Statistical Explorer** | Distributions, correlations, outliers, column deep dive |
| ⚠️ **Fault Detection** | ISO 25012-compliant DQS scoring across 7 quality dimensions |
| ⚡ **CleanIQ Pipeline** | Automated 8-stage remediation pipeline with before/after comparison |

**Key highlights:**
- ISO 25012 aligned DQS scoring
- 8-step automated cleaning pipeline (CleanIQ Engine)
- Before vs After cleaning comparison with delta metrics
- Export cleaned dataset as CSV or Excel
- Supports files up to 500MB
- Dark mode UI with professional design system
- Deployed and accessible via browser — no installation needed

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit |
| Data Processing | Pandas, NumPy |
| Visualisation | Plotly, Matplotlib |
| File Handling | openpyxl, io |
| Deployment | Render |
| Language | Python 3.10+ |

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/auditiq.git
cd auditiq

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`

### Requirements

```
streamlit
pandas
numpy
plotly
openpyxl
Pillow
```

---

## Project Structure

```
auditiq/
├── app.py                        # Main entry point, routing, sidebar
├── requirements.txt
├── assets/
│   ├── style.css                 # Global design system
│   └── iqlogofinal.jpeg          # App icon
├── modules/
│   ├── overview.py               # Data Profile tab
│   ├── explorer.py               # Statistical Explorer tab
│   ├── fault_detection.py        # Fault Detection & DQS tab
│   ├── cleaning.py               # CleanIQ Pipeline tab
│   └── runcleaningpipeline.py    # Terminal-style pipeline UI
└── utils/
    └── helpers.py                # DQS computation, file loading, constants
```

---

## How It Works

### Upload
Drag and drop any CSV or Excel file (up to 500MB) into the sidebar. AuditIQ automatically detects file type, loads it into a Pandas DataFrame, and displays file metadata.

### Audit Flow
```
Ingest → Profile → Remediate → Export
```

1. **Ingest** — File uploaded, parsed, stored in session state
2. **Profile** — Schema analysis, null counts, type detection, memory usage
3. **Remediate** — CleanIQ 8-step pipeline runs automatically
4. **Export** — Download cleaned file as CSV or Excel with `_cleaniq` suffix

---

## CleanIQ Pipeline

The CleanIQ Engine runs 8 automated remediation steps in sequence:

| Step | Operation | Detail |
|---|---|---|
| 1 | Column Name Standardisation | Strip, lowercase, replace special chars with `_` |
| 2 | Empty Row Removal | Drop rows where all values are null |
| 3 | Placeholder → NaN | Convert `"n/a"`, `"null"`, `"-"`, `"unknown"` etc. to `NaN` |
| 4 | High-Missing Column Drop | Drop columns with >70% missing values |
| 5 | Missing Value Imputation | Numeric → median fill, Categorical → mode fill |
| 6 | Duplicate Removal | Drop exact duplicate rows, keep first |
| 7 | Text Formatting | Strip whitespace, lowercase all string columns |
| 8 | Outlier Capping | Winsorize at 3×IQR per numeric column |

Each step is displayed in a terminal-style log UI so you can see exactly what is happening to your data in real time.

---

## DQS Scoring

AuditIQ computes a **Data Quality Score (DQS)** aligned with the ISO/IEC 25012 standard across 7 dimensions:

| Dimension | Formula |
|---|---|
| Completeness | `max(0, 100 - missing_rate × 150)` |
| Uniqueness | `max(0, 100 - duplicate_rate × 200)` |
| Consistency | Based on type uniformity and formatting |
| Validity | Value range and constraint checks |
| Accuracy | Cross-column logical checks |
| Structure | Schema regularity score |
| Correlation | Feature relationship health |

**Final DQS** is a weighted average across all 7 dimensions, scored out of 100.

After running CleanIQ, AuditIQ shows DQS Before vs After with delta, giving you a measurable proof of data quality improvement.

---

## Roadmap

- [ ] Support for JSON and Parquet file formats
- [ ] Column-level DQS drill-down
- [ ] Custom cleaning rules configuration
- [ ] PDF audit report export
- [ ] Multi-file comparison mode
- [ ] REST API endpoint for pipeline automation

---

## Contributing

Contributions are welcome. To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

Please follow PEP8 and keep functions modular.

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.

---

## Author

**sachin karale**

Built by a open source contributor passionate about data quality and ML engineering.

🔗 [Live App](https://auditiq-v094.onrender.com) · [LinkedIn](#) · [GitHub](#)

---

*AuditIQ · Data Quality Platform · v1.0.0 · Built on Streamlit & Pandas*