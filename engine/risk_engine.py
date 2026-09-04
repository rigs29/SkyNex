"""
Risk Engine Module
Computes multidimensional composite risk scores and classifies components into risk levels.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Union

try:
    from config import RISK_THRESHOLDS
except ImportError:
    RISK_THRESHOLDS = {
        "LOW": 25.0,
        "MEDIUM": 50.0,
        "HIGH": 75.0,
        "CRITICAL": 100.0,
    }


def compute_component_risk_score(
    anomaly_score: float,
    flag_module_a: bool,
    flag_module_b: bool,
    predicted_slope: float,
    safety_slope_threshold: float,
    zscore: float = 0.0,
) -> float:
    """
    Computes a normalized composite risk score (0 - 100) for an individual component.
    
    Factors:
    1. Module A dynamic outlier score (0-100 scale, weighted 45%)
    2. Module B drift slope magnitude relative to safety threshold (weighted 40%)
    3. Multi-module intersection penalty (weighted 15%)
    """
    # Base outlier risk from Module A
    outlier_part = np.clip(anomaly_score, 0.0, 100.0)

    # Drift risk from Module B slope
    if safety_slope_threshold > 0:
        drift_ratio = max(0.0, predicted_slope) / safety_slope_threshold
    else:
        drift_ratio = 1.0 if flag_module_b else 0.0
    drift_part = np.clip(drift_ratio * 50.0, 0.0, 100.0)

    # Intersection penalty if both modules detect anomalies
    intersection_penalty = 20.0 if (flag_module_a and flag_module_b) else 0.0

    # Composite weighted formula
    raw_risk = (0.45 * outlier_part) + (0.40 * drift_part) + intersection_penalty
    
    # Floor / Ceiling enforcement based on flags
    if flag_module_a and flag_module_b:
        raw_risk = max(raw_risk, 75.0)
    elif flag_module_a or flag_module_b:
        raw_risk = max(raw_risk, 50.0)
    elif anomaly_score < 20.0 and not flag_module_b:
        raw_risk = min(raw_risk, 25.0)

    return round(float(np.clip(raw_risk, 0.0, 100.0)), 1)


def determine_risk_level(risk_score: float) -> str:
    """Classifies risk score into standardized risk levels."""
    if risk_score < RISK_THRESHOLDS["LOW"]:
        return "LOW"
    elif risk_score < RISK_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    elif risk_score < RISK_THRESHOLDS["HIGH"]:
        return "HIGH"
    else:
        return "CRITICAL"


def calculate_risk_scores(
    df: pd.DataFrame,
    safety_slope_threshold: float,
) -> pd.DataFrame:
    """Calculates risk_score and risk_level across an entire batch DataFrame."""
    out = df.copy()

    risk_scores = []
    risk_levels = []

    for _, row in out.iterrows():
        score = compute_component_risk_score(
            anomaly_score=row.get("anomaly_score", 0.0),
            flag_module_a=bool(row.get("flag_module_a", False)),
            flag_module_b=bool(row.get("flag_module_b", False)),
            predicted_slope=row.get("predicted_slope", 0.0),
            safety_slope_threshold=safety_slope_threshold,
            zscore=row.get("zscore_168h", 0.0),
        )
        level = determine_risk_level(score)
        risk_scores.append(score)
        risk_levels.append(level)

    out["risk_score"] = risk_scores
    out["risk_level"] = risk_levels
    return out

