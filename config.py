"""
SkyNex Configuration Module
Centralized configuration for paths, parameters, ML hyperparameters, and thresholds.
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
OUTPUT_DIR = REPORTS_DIR / "output"
QA_DIR = BASE_DIR / "qa"
ASSETS_DIR = BASE_DIR / "assets"

# File Paths
WIDE_DATA_PATH = RAW_DATA_DIR / "burnin_data_wide.csv"
LONG_DATA_PATH = RAW_DATA_DIR / "burnin_data_long.csv"
LINEAR_MODEL_PATH = MODELS_DIR / "linear_model.joblib"
XGB_MODEL_PATH = MODELS_DIR / "xgb_model.joblib"
QA_DB_PATH = QA_DIR / "qa_decisions.db"
FINAL_REPORT_PATH = OUTPUT_DIR / "final_report.csv"

# Dataset Columns
VALUE_COLS = ["Value_0h", "Value_24h", "Value_96h", "Value_168h"]
FEATURE_COLS = [
    "Value_0h",
    "Value_24h",
    "delta_24h",
    "pct_change_24h",
    "slope_0_24",
    "lot_mean_0h",
]

# Module A (Dynamic Anomaly Detection) Parameters
ZSCORE_THRESHOLD = 3.0
IQR_K = 1.5
ISO_FOREST_CONTAMINATION = 0.08
ISO_FOREST_N_ESTIMATORS = 200
RANDOM_STATE = 42

# Module B (Drift Predictor) Parameters
SAFETY_SLOPE_PERCENTILE = 95.0

# Risk Engine Thresholds (0 - 100 scale)
RISK_THRESHOLDS = {
    "LOW": 25.0,
    "MEDIUM": 50.0,
    "HIGH": 75.0,
    "CRITICAL": 100.0,
}

# Default QA Engineer Identity
DEFAULT_ENGINEER_ID = "QA_ENG_ADMIN"


def ensure_directories() -> None:
    """Explicitly creates required operational directories. Call at startup."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)


# Ensure required operational directories exist on import
ensure_directories()

