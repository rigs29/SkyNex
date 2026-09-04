"""
Explanation Engine Module
Generates actionable, human-readable engineering explanations for component screening anomalies and drift predictions.
"""

from typing import Dict, Any, List
import pandas as pd


def generate_component_explanation(row: Dict[str, Any]) -> str:
    """
    Synthesizes Module A statistical flags and Module B drift forecasts
    into an explainable engineering root-cause narrative.
    """
    flag_a = bool(row.get("flag_module_a", False))
    flag_b = bool(row.get("flag_module_b", False))

    if not flag_a and not flag_b:
        return "No issues detected. Component parameters and drift are within normal lot tolerances."

    explanations: List[str] = []

    # Module A details
    if flag_a:
        module_a_reasons = []
        if row.get("flag_zscore", False):
            z = row.get("zscore_168h", 0.0)
            val_168 = row.get("Value_168h", 0.0)
            mean_168 = row.get("lot_mean_168h", 0.0)
            module_a_reasons.append(
                f"168h value is {z:.1f} standard deviations from lot mean ({val_168:.2f} vs mean {mean_168:.2f})"
            )
        if row.get("flag_iqr", False):
            val_168 = row.get("Value_168h", 0.0)
            iqr_l = row.get("iqr_lower", 0.0)
            iqr_u = row.get("iqr_upper", 0.0)
            module_a_reasons.append(
                f"168h value ({val_168:.2f}) falls outside lot IQR bounds [{iqr_l:.2f}, {iqr_u:.2f}]"
            )
        if row.get("flag_isoforest", False):
            module_a_reasons.append(
                "multivariate trajectory across 0h-168h checkpoints is anomalous relative to lot peers"
            )

        if module_a_reasons:
            explanations.append(f"[Module A Outlier]: {'; and '.join(module_a_reasons)}.")

    # Module B details
    if flag_b:
        slope = row.get("predicted_slope", 0.0)
        pred_168 = row.get("predicted_168h", 0.0)
        v24 = row.get("Value_24h", 0.0)
        delta_24 = row.get("delta_24h", (v24 - row.get("Value_0h", 0.0)))
        explanations.append(
            f"[Module B Drift]: Early drift (delta_24h={delta_24:+.3f}) forecasts an excessive 168h drift rate "
            f"(slope={slope:.4f}/hr, predicted 168h={pred_168:.2f}) exceeding the safety threshold."
        )

    return " ".join(explanations)


def add_explanations(df: pd.DataFrame) -> pd.DataFrame:
    """Adds explanation strings for all rows in a DataFrame."""
    out = df.copy()
    explanations = []
    for _, row in out.iterrows():
        explanations.append(generate_component_explanation(row.to_dict()))
    out["explanation"] = explanations
    return out

