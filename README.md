# SkyNex 🛰️

### AI-Driven Anomaly Detection in Component Burn-In & Screening

**Smart India Hackathon (SIH) 2026 — Problem Statement 26170**

---

## 📌 Architecture Overview

SkyNex provides an end-to-end intelligent screening foundation for electronics and semiconductor burn-in testing. It combines dynamic statistical outlier detection, early-reading machine learning drift forecasting, multidimensional risk assessment, and human-in-the-loop QA decision support.

```
Dataset (0h, 24h, 96h, 168h)
   │
   ▼
Module A — Dynamic Anomaly Detection (Z-Score + IQR + Isolation Forest per lot)
   │
   ▼
Module B — Time-Series Drift Predictor (XGBoost / Linear Early Drift to 168h)
   │
   ▼
Risk Engine (0 - 100 Risk Score & LOW / MEDIUM / HIGH / CRITICAL Classification)
   │
   ▼
SkyNex Unified Result Payload
   │
   ▼
QA Recommendation Engine (PASS / EXTEND_BURN_IN / RETEST / REJECT)
   │
   ▼
QA Engineer Decision & Audit Trail (SQLite Persistence)
   │
   ▼
Unified Reports & Analytics Export (CSV / JSON / Lot Summary)
```

---

## 📁 Project Structure

```
SkyNex/
│
├── data/
│   └── raw/                        # Raw screening datasets (wide & long formats)
│       ├── burnin_data_wide.csv
│       └── burnin_data_long.csv
│
├── models/                         # Pre-trained ML models
│   ├── linear_model.joblib
│   └── xgb_model.joblib
│
├── ml/                             # Core ML algorithms
│   ├── __init__.py
│   ├── anomaly_detection.py        # Module A: Lot-relative outlier detection
│   └── drift_prediction.py         # Module B: 0h-24h early drift forecast to 168h
│
├── engine/                         # Pipeline orchestration & reasoning
│   ├── __init__.py
│   ├── skynex_engine.py            # Primary pipeline and analyze_component() interface
│   ├── risk_engine.py              # Composite risk scoring
│   └── explanation.py              # Explainable AI engineering narratives
│
├── qa/                             # QA workflow and decision persistence
│   ├── __init__.py
│   ├── recommendation.py           # Automated action recommendation
│   ├── decision.py                 # Engineer decision models & actions
│   └── database.py                 # SQLite audit log
│
├── reports/                        # Report generation & exports
│   ├── __init__.py
│   └── report_generator.py         # CSV, JSON, and lot yield summaries
│
├── ui/                             # UI scaffolding
│   ├── __init__.py
│   └── app.py                      # UI entrypoint placeholder
│
├── assets/                         # Branding and visual assets
│   └── skynex_logo.png
│
├── tests/                          # Automated unit and integration test suite
│   ├── __init__.py
│   └── test_pipeline.py
│
├── requirements.txt                # Python package dependencies
├── config.py                       # Centralized configuration & parameters
└── README.md                       # Documentation
```

---

## 🔌 Primary Integration Interface: `analyze_component`

The main interface for analyzing individual components is `analyze_component(component_id: str)`:

```python
from engine.skynex_engine import analyze_component

result = analyze_component("C_00009")
print(result)
```

### Unified Result Schema:

```json
{
  "component_id": "C_00009",
  "lot_id": "LOT_000",
  "anomaly_score": 64.0,
  "anomaly_status": true,
  "drift_rate": 0.08427,
  "drift_status": true,
  "predicted_168h": 26.71,
  "prediction_status": "COMPLETED",
  "risk_score": 93.6,
  "risk_level": "CRITICAL",
  "flags": {
    "flag_zscore": true,
    "flag_iqr": true,
    "flag_isoforest": true,
    "flag_module_a": true,
    "flag_module_b": true,
    "final_flag": true
  },
  "explanation": "[Module A Outlier]: 168h value is 3.8 standard deviations from lot mean... [Module B Drift]: Early drift (delta_24h=+4.750) forecasts an excessive 168h drift rate...",
  "recommendation": "REJECT",
  "qa_decision": null
}
```

---

## 🚀 Quickstart & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Test Suite

```bash
python -m pytest tests/
```

### 3. Run Pipeline Execution

```bash
python -m engine.skynex_engine
```

---

## 🔒 Preserved ML Guarantees

- **Module A**: Dynamically computes statistical bounds per lot without hardcoding inflexible global limits.
- **Module B**: Utilizes early readings (0h -> 24h) to predict 168h degradation and flag early defectives, reducing unnecessary chamber hours.
