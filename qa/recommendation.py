"""
QA Recommendation Engine Module
Translates screening analytics, risk levels, and anomaly flags into actionable automated QA recommendations.
"""

from typing import Dict, Any
import pandas as pd


def generate_recommendation(
    risk_level: str,
    flag_module_a: bool = False,
    flag_module_b: bool = False,
    anomaly_score: float = 0.0,
) -> str:
    """
    Determines automated QA action recommendation based on risk posture and failure indicators.
    
    Recommendations:
    - PASS: Component meets reliability criteria.
    - EXTEND_BURN_IN: Marginal or inconclusive trend; observe for additional burn-in cycles.
    - RETEST: Suspected probe/contact variance or isolated outlier; re-measure.
    - REJECT: High risk of early life failure / latent defect.
    """
    if risk_level == "CRITICAL":
        return "REJECT"
    elif risk_level == "HIGH":
        if flag_module_b and not flag_module_a:
            return "RETEST"
        return "REJECT"
    elif risk_level == "MEDIUM":
        if anomaly_score > 35.0:
            return "EXTEND_BURN_IN"
        return "RETEST"
    else:
        return "PASS"


def add_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    """Computes automated QA recommendation column for a DataFrame."""
    out = df.copy()
    recs = []
    for _, row in out.iterrows():
        rec = generate_recommendation(
            risk_level=row.get("risk_level", "LOW"),
            flag_module_a=bool(row.get("flag_module_a", False)),
            flag_module_b=bool(row.get("flag_module_b", False)),
            anomaly_score=float(row.get("anomaly_score", 0.0)),
        )
        recs.append(rec)
    out["recommendation"] = recs
    return out

