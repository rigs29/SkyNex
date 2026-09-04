"""
SkyNex Machine Learning Modules Package
- Module A: Dynamic lot-level outlier & anomaly detection
- Module B: Early burn-in time-series drift prediction
"""

from ml.anomaly_detection import run_module_a, zscore_flags, iqr_flags, isolation_forest_flags
from ml.drift_prediction import (
    engineer_features,
    train_models,
    compute_safety_slope,
    predict_and_flag,
)

__all__ = [
    "run_module_a",
    "zscore_flags",
    "iqr_flags",
    "isolation_forest_flags",
    "engineer_features",
    "train_models",
    "compute_safety_slope",
    "predict_and_flag",
]

