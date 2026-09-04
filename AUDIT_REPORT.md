# 🛰️ SkyNex — Final End-to-End Consistency Audit Report

**SIH 2026 Problem Statement 26170: AI-Driven Anomaly Detection in Component Burn-In & Screening**  
**Audit Protocol**: `INSPECT → TEST → IDENTIFY → RESOLVE → VERIFY`  
**Timestamp**: September 2026  
**Final Verdict**: **🟢 READY FOR DEMO**

---

## 1. 📊 Dataset Actual Statistics

The screening dataset was audited across raw wide (`burnin_data_wide.csv`) and time-series long (`burnin_data_long.csv`) formats:

| Metric                         | Actual Dataset Value                                                                    | Verification Source                                       |
| ------------------------------ | --------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| **Total Unique Components**    | `1,000`                                                                                 | `burnin_data_wide.csv` (`C_00001` to `C_01000`)           |
| **Total Unique Lots**          | `25`                                                                                    | Lots `LOT_000` through `LOT_024` (40 parts/lot)           |
| **Total Long Observations**    | `4,000`                                                                                 | `burnin_data_long.csv` (1,000 parts × 4 time checkpoints) |
| **Time Checkpoints**           | `0h, 24h, 96h, 168h`                                                                    | Burn-in chamber inspection intervals                      |
| **Module A Anomalies Flagged** | `105` (10.50%)                                                                          | Dynamic Lot Z-Score, IQR & Isolation Forest               |
| **Module B Drift Flagged**     | `60` (6.00%)                                                                            | 0h–24h Early Drift to 168h XGBoost Regressor              |
| **Combined Final Flagged**     | `105` (10.50%)                                                                          | Flagged by Module A OR Module B                           |
| **Risk Distribution**          | Low: `882` (88.2%)<br>Medium: `13` (1.3%)<br>High: `45` (4.5%)<br>Critical: `60` (6.0%) | Composite 0–100 Risk Engine Scoring                       |
| **SkyNex AI Recommendations**  | `PASS`: 882 (88.2%)<br>`RETEST`: 13 (1.3%)<br>`REJECT`: 105 (10.5%)                     | Automated Action Decision Rules                           |

---

## 2. 🖥️ Dashboard Statistics vs Dataset Ground Truth

| Dashboard Item        | Reference Mock Value | Real Ground Truth (Current Dashboard)       | Resolution / Source                                                    |
| --------------------- | -------------------- | ------------------------------------------- | ---------------------------------------------------------------------- |
| **TESTED**            | `1,248`              | `1,000`                                     | Connected to `len(engine.processed_df)`                                |
| **ANOMALIES**         | `47`                 | `105`                                       | Connected to `df['flag_module_a'].sum()`                               |
| **HIGH RISK**         | `18`                 | `105` (45 High + 60 Critical)               | Connected to `df['risk_level'].isin(['HIGH', 'CRITICAL'])`             |
| **QA PASS (AI REC.)** | `1,130` (90.7%)      | `882` (88.2%)                               | Connected to `(df['recommendation'] == 'PASS').sum()`                  |
| **QA HOLD (AI REC.)** | `76` (6.1%)          | `13` (1.3%)                                 | Connected to `df['recommendation'].isin(['RETEST', 'EXTEND_BURN_IN'])` |
| **QA FAIL (AI REC.)** | `42` (3.4%)          | `105` (10.5%)                               | Connected to `(df['recommendation'] == 'REJECT').sum()`                |
| **LOTS SUMMARY**      | `25 Lots`            | `25 Lots` (20% per 5-lot bucket)            | Computed dynamically across `LOT_000` to `LOT_024`                     |
| **PRIORITY TABLE**    | 4 static rows        | Real high-risk components (`C_00009`, etc.) | Sorted by `risk_score DESC` from dataset                               |

---

## 3. 🔍 Mismatches Found & Root Causes

1. **Dashboard Calculation Decoupling** _(HIGH Severity)_:
   - _Issue_: KPI cards and donut charts initially displayed static reference mock numbers rather than dynamically reflecting the loaded screening dataset.
   - _Root Cause_: `render_kpi_cards()` and `render_summary_charts()` were called without passing the live `processed_df`.
   - _Resolution_: Updated `ui/app.py` to pass `engine.processed_df` into all UI components, ensuring 100% data traceability.

2. **QA Decision Validation Enum** _(CRITICAL Severity)_:
   - _Issue_: `qa/decision.py` rejected `"PASS"` and `"FAIL"` string inputs during QA engineer decision creation, only accepting `"APPROVE"`.
   - _Root Cause_: `VALID_DECISIONS` set was missing `"PASS"` and `"FAIL"`.
   - _Resolution_: Updated `VALID_DECISIONS` in `qa/decision.py` to accept `"PASS"`, `"HOLD"`, `"FAIL"`, `"APPROVE"`, `"REJECT"`, and `"REQUEST_RETEST"`.

3. **Streamlit Top Header Clipping** _(HIGH Severity)_:
   - _Issue_: Streamlit default toolbar overlapped the workspace title and controls on certain resolutions.
   - _Root Cause_: Fixed header bar height and block container top padding conflict.
   - _Resolution_: Added `.streamlit/config.toml` and transparent header CSS with `2.2rem` top padding in `ui/app.py`.

---

## 4. 🔬 Single Component End-to-End Traces

Three real components were traced through all pipeline stages:

### Trace 1: Normal Low-Risk Part (`C_00001`)

- **Dataset**: `Value_0h`: 10.98 µA, `Value_24h`: 10.95 µA, `Value_96h`: 11.10 µA, `Value_168h`: 10.99 µA, `lot_id`: `LOT_000`
- **Module A**: `zscore_168h`: -0.25, `flag_zscore`: False, `flag_iqr`: False, `flag_isoforest`: False, `anomaly_score`: 17.0
- **Module B**: `predicted_168h`: 11.40 µA, `predicted_slope`: 0.00319 µA/hr, `flag_module_b`: False
- **Risk Engine**: `risk_score`: 17.3, `risk_level`: `LOW`
- **Explanation**: _"No issues detected. Component parameters and drift are within normal lot tolerances."_
- **SkyNex AI Recommendation**: `PASS`
- **QA Engineer Action**: `PASS` recorded in SQLite with remarks _"Verified baseline stable drift."_
- **Report**: Exported row exactly matches `analyze_component('C_00001')`.

### Trace 2: Critical Outlier & Degradation Part (`C_00009`)

- **Dataset**: `Value_0h`: 9.82 µA, `Value_24h`: 14.57 µA, `Value_96h`: 21.32 µA, `Value_168h`: 26.51 µA, `lot_id`: `LOT_000`
- **Module A**: `zscore_168h`: +3.81 (vs lot mean 11.95), `flag_zscore`: True, `flag_iqr`: True, `flag_isoforest`: True, `anomaly_score`: 64.0
- **Module B**: `delta_24h`: +4.75 µA, `predicted_168h`: 26.71 µA, `predicted_slope`: 0.0843 µA/hr, `flag_module_b`: True (exceeds safety threshold 0.0064)
- **Risk Engine**: `risk_score`: 88.8, `risk_level`: `CRITICAL`
- **Explanation**: _"[Module A Outlier]: 168h value is 3.8 standard deviations from lot mean (26.51 vs mean 11.95); and 168h value (26.51) falls outside lot IQR bounds [9.38, 12.61]; and multivariate trajectory across 0h-168h checkpoints is anomalous relative to lot peers. [Module B Drift]: Early drift (delta_24h=+4.750) forecasts an excessive 168h drift rate (slope=0.0843/hr, predicted 168h=26.71) exceeding the safety threshold."_
- **SkyNex AI Recommendation**: `REJECT`
- **QA Engineer Action**: `FAIL` recorded in SQLite with remarks _"Thermal runaway early degradation confirmed."_
- **Report**: Exported row exactly matches `analyze_component('C_00009')`.

### Trace 3: Stable Boundary Part (`C_00005`)

- **Dataset**: `Value_0h`: 10.89 µA, `Value_24h`: 11.33 µA, `Value_96h`: 11.53 µA, `Value_168h`: 11.61 µA, `lot_id`: `LOT_000`
- **Module A**: `zscore_168h`: -0.09, `flag_module_a`: False, `anomaly_score`: 18.7
- **Module B**: `predicted_168h`: 11.48 µA, `predicted_slope`: 0.00104 µA/hr, `flag_module_b`: False
- **Risk Engine**: `risk_score`: 11.5, `risk_level`: `LOW`
- **SkyNex AI Recommendation**: `PASS`
- **QA Engineer Action**: `HOLD` recorded in SQLite with remarks _"Extended 24h burn-in requested."_
- **Report**: Exported row matches engine data.

---

## 5. 🛡️ Data Leakage & ML Safety Audit

- **Ground Truth Isolation**: Confirmed `is_defective` is never used as an input feature for inference in Module A or Module B.
- **Temporal Checkpoint Separation**: Module B features strictly use early readings (`Value_0h`, `Value_24h`, `delta_24h`, `pct_change_24h`, `slope_0_24`, `lot_mean_0h`). Future readings (`Value_96h`, `Value_168h`) are never present in `FEATURE_COLS`.
- **Identity Isolation**: `component_id` and raw lot labels are excluded from feature vectors.
- **Model Storage**: Pretrained XGBoost model loads directly from `models/xgb_model.joblib`.

---

## 6. 🤝 Separation of AI Recommendation vs QA Engineer Decision

The system enforces strict conceptual separation:

- **SkyNex AI Recommendation**: Derived purely from statistical models and drift predictions (`PASS`, `EXTEND_BURN_IN`, `RETEST`, `REJECT`).
- **QA Engineer Decision**: Human-in-the-loop engineering actions (`PASS`, `HOLD`, `FAIL`, `APPROVE`, `REJECT`, `REQUEST_RETEST`) with mandatory audit notes, user ID, and ISO timestamps stored in SQLite (`qa/qa_decisions.db`).

---

## 7. 🧪 Test Suite & Verification Results

### Automated Discovery Tests:

```bash
python -m unittest discover tests
Ran 7 tests in 41.382s — OK
```

### End-to-End Audit Tests:

```bash
python -m unittest tests/audit_trace_test.py
Ran 5 tests in 25.027s — OK
```

### Python Syntax & Compilation:

```bash
python -m py_compile ui/app.py ui/components/*.py
All scripts compiled cleanly (0 errors).
```

---

## 8. 📋 Final Audit Verification Summary

| Check                         | Status   | Evidence                                                                                          |
| ----------------------------- | -------- | ------------------------------------------------------------------------------------------------- |
| **Dataset Consistency**       | **PASS** | 1,000 unique components, 25 lots, 4,000 observations verified in wide & long data.                |
| **Dashboard Consistency**     | **PASS** | UI cards, donuts, and priority table dynamically driven by `SkyNexEngine.processed_df`.           |
| **Module A (Anomaly)**        | **PASS** | Exact Z-Score, IQR, and Isolation Forest algorithms preserved; flags 105 outliers.                |
| **Module B (Drift)**          | **PASS** | 0h–24h early drift accurately forecasts 168h value; flags 60 high-drift parts.                    |
| **Risk Engine**               | **PASS** | 0–100 composite scoring verified across Low (882), Medium (13), High (45), Critical (60).         |
| **Explanation Engine**        | **PASS** | Generates clear multi-factor root-cause engineering explanations.                                 |
| **Recommendation Engine**     | **PASS** | Outputs `PASS` (882), `RETEST` (13), and `REJECT` (105) without mixing QA decisions.              |
| **QA Decision & Audit Trail** | **PASS** | SQLite persistence verified for `PASS`, `HOLD`, and `FAIL` with engineer remarks & timestamps.    |
| **Report Consistency**        | **PASS** | CSV, JSON, and lot yield reports match `analyze_component()` with 100% column fidelity.           |
| **Data Leakage Safety**       | **PASS** | Zero ground truth or future timepoint leakage in early prediction feature sets.                   |
| **UI Runtime & Aesthetics**   | **PASS** | Streamlit loads cleanly, dark navy sidebar, Plotly sparklines, and interactive `[REVIEW]` drawer. |
| **End-to-End Trace**          | **PASS** | Tested on normal, boundary, and critical components without identity or metric drift.             |
| **Test Suite**                | **PASS** | 12 total automated test cases executed across suites with zero failures.                          |

---

## 🏁 Final Verdict

# **🟢 READY FOR DEMO**

The SkyNex platform is consistent, fully verified against ground truth, zero-leakage compliant, and ready for end-to-end hackathon demonstration.
