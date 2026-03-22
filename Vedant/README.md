# ◈ Data Audit System v3.0

Professional data quality analysis platform built with Streamlit.

## Project Structure

```
data_audit_system/
│
├── app.py                  ← Main application (run this)
│
├── frontend/
│   ├── style.css           ← Complete dark-theme stylesheet
│   │                          Syne + Inter + JetBrains Mono fonts
│   │                          Glassmorphism cards, animations, all components
│   │
│   └── threejs.html        ← WebGL background + all interactive JS
│                              Three.js particles + floating wireframes
│                              Animated score ring (Canvas 2D)
│                              Particle burst on upload
│                              Live sparklines (Canvas 2D)
│                              Mouse cursor glow
│
└── README.md               ← This file
```

## Quick Start

### 1. Install dependencies

```bash
pip install streamlit pandas numpy matplotlib seaborn openpyxl
```

### 2. Run the app

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`

---

## Features

| Feature | Description |
|---|---|
| **WebGL Background** | 2200 colored particles + 6 floating wireframe 3D shapes |
| **DQS Score Ring** | Animated Canvas ring with tick marks and glow |
| **Particle Burst** | 80 physics particles explode on file upload |
| **Live Sparklines** | Animated Canvas charts per numeric column |
| **Cursor Glow** | Radial blue glow follows mouse cursor |
| **7 Dimension Audit** | Completeness, Uniqueness, Consistency, Validity, Accuracy, Structure, Correlation |
| **Key Findings** | Auto-detected issues with inline Python fix code |
| **Column Health Grid** | Per-column health score |
| **Live Audit Log** | Terminal-style feed showing audit progress |
| **Visualizations** | Distributions, Correlation Heatmap, Boxplots, Missing Value charts |
| **Audit Report CSV** | Downloadable CSV with Issue ID, Severity, Value Examples, Fix Recommendations |

## Supported File Types

- CSV (`.csv`)
- Excel (`.xlsx`)
- Max size: 1 GB

## Dataset Quality Score (DQS)

Weighted score across 7 dimensions:

| Dimension     | Weight |
|---------------|--------|
| Completeness  | 28%    |
| Uniqueness    | 18%    |
| Consistency   | 16%    |
| Validity      | 16%    |
| Accuracy      | 10%    |
| Structure     | 7%     |
| Correlation   | 5%     |

**Grade Scale:** A (≥85) · B (≥70) · C (≥55) · D (≥40) · F (<40)

## Audit Report CSV Columns

| Column | Description |
|---|---|
| `Issue_ID` | Unique code (e.g. `COMP-001`, `VALD-OUT-003`) |
| `Dimension` | Quality dimension |
| `Severity` | HIGH / MEDIUM / LOW |
| `Column` | Affected column name |
| `Issue_Type` | Category of issue |
| `Detail` | Full description with counts/stats |
| `Affected_Rows` | Number of impacted rows |
| `Value_Example` | Actual values from your data |
| `Fix_Recommendation` | Python code to fix the issue |
