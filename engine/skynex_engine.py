"""
SkyNex Unified Analytics Engine
Orchestrates the end-to-end burn-in & screening pipeline:
Module A (Anomaly) -> Module B (Drift) -> Risk Engine -> Explanation -> QA Recommendation -> Reports.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Union
import pandas as pd

try:
    from config import (
        WIDE_DATA_PATH,
        XGB_MODEL_PATH,
        FINAL_REPORT_PATH,
        SAFETY_SLOPE_PERCENTILE,
    )
    from ml.anomaly_detection import run_module_a
    from ml.drift_prediction import (
        compute_safety_slope,
        load_or_train_xgb_model,
        predict_and_flag,
    )
    from engine.risk_engine import calculate_risk_scores
    from engine.explanation import add_explanations
    from qa.recommendation import add_recommendations
    from qa.database import QADatabase
except ImportError:
    from ..config import (
        WIDE_DATA_PATH,
        XGB_MODEL_PATH,
        FINAL_REPORT_PATH,
        SAFETY_SLOPE_PERCENTILE,
    )
    from ..ml.anomaly_detection import run_module_a
    from ..ml.drift_prediction import (
        compute_safety_slope,
        load_or_train_xgb_model,
        predict_and_flag,
    )
    from ..engine.risk_engine import calculate_risk_scores
    from ..engine.explanation import add_explanations
    from ..qa.recommendation import add_recommendations
    from ..qa.database import QADatabase


class SkyNexEngine:
    """Core SkyNex Pipeline Engine."""

    def __init__(
        self,
        data_path: Union[str, Path] = WIDE_DATA_PATH,
        model_path: Union[str, Path] = XGB_MODEL_PATH,
        auto_run: bool = True,
    ):
        self.data_path = Path(data_path)
        self.model_path = Path(model_path)
        self.qa_db = QADatabase()
        self.raw_df: Optional[pd.DataFrame] = None
        self.processed_df: Optional[pd.DataFrame] = None
        self.safety_slope: float = 0.0
        self.model = None

        if auto_run and self.data_path.exists():
            self.run_pipeline()

    def load_data(self) -> pd.DataFrame:
        """Loads the raw screening dataset."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Screening dataset not found at {self.data_path}")
        self.raw_df = pd.read_csv(self.data_path)
        return self.raw_df

    def run_pipeline(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Executes the unified SkyNex architecture:
        1. Module A: Lot-level Dynamic Outlier Detection
        2. Module B: Early Burn-in 168h Drift Forecasting
        3. Risk Engine: Composite Risk Scoring & Classification
        4. Explanation Engine: Multi-factor root-cause synthesis
        5. QA Recommendation: Automated decision recommendations
        """
        if df is None:
            if self.raw_df is None:
                self.load_data()
            input_df = self.raw_df.copy()
        else:
            input_df = df.copy()

        # Step 1: Module A - Anomaly Detection
        df_a = run_module_a(input_df)

        # Step 2: Module B - Drift Prediction
        self.safety_slope = compute_safety_slope(input_df, percentile=SAFETY_SLOPE_PERCENTILE)
        self.model = load_or_train_xgb_model(input_df, model_path=self.model_path)
        df_b = predict_and_flag(df_a, self.model, self.safety_slope)

        # Combined final flag
        df_b["final_flag"] = df_b["flag_module_a"] | df_b["flag_module_b"]

        # Step 3: Risk Engine
        df_risk = calculate_risk_scores(df_b, safety_slope_threshold=self.safety_slope)

        # Step 4: Explanation Engine
        df_exp = add_explanations(df_risk)

        # Step 5: QA Recommendation Engine
        self.processed_df = add_recommendations(df_exp)
        return self.processed_df

    def analyze_component(self, component_id: str) -> Dict[str, Any]:
        """
        Primary interface: Analyzes a specific component and returns the unified result payload.
        """
        if self.processed_df is None:
            self.run_pipeline()

        row_matches = self.processed_df[self.processed_df["component_id"] == component_id]
        if row_matches.empty:
            raise KeyError(f"Component '{component_id}' not found in dataset.")

        row = row_matches.iloc[0].to_dict()

        # Retrieve any logged QA decision
        qa_record = self.qa_db.get_latest_decision(component_id)
        qa_decision_val = qa_record["decision"] if qa_record else None

        # Build flags dictionary
        flags_dict = {
            "flag_zscore": bool(row.get("flag_zscore", False)),
            "flag_iqr": bool(row.get("flag_iqr", False)),
            "flag_isoforest": bool(row.get("flag_isoforest", False)),
            "flag_module_a": bool(row.get("flag_module_a", False)),
            "flag_module_b": bool(row.get("flag_module_b", False)),
            "final_flag": bool(row.get("final_flag", False)),
        }

        # Format unified response schema
        unified_result = {
            "component_id": str(row.get("component_id")),
            "lot_id": str(row.get("lot_id")),
            "anomaly_score": float(row.get("anomaly_score", 0.0)),
            "anomaly_status": bool(row.get("flag_module_a", False)),
            "drift_rate": float(row.get("predicted_slope", 0.0)),
            "drift_status": bool(row.get("flag_module_b", False)),
            "predicted_168h": float(row.get("predicted_168h", 0.0)),
            "prediction_status": "COMPLETED" if "predicted_168h" in row else "PENDING",
            "risk_score": float(row.get("risk_score", 0.0)),
            "risk_level": str(row.get("risk_level", "LOW")),
            "flags": flags_dict,
            "explanation": str(row.get("explanation", "")),
            "recommendation": str(row.get("recommendation", "PASS")),
            "qa_decision": qa_decision_val,
        }

        return unified_result

    def analyze_lot(self, lot_id: str) -> pd.DataFrame:
        """Returns all processed component records for a specific manufacturing lot."""
        if self.processed_df is None:
            self.run_pipeline()
        return self.processed_df[self.processed_df["lot_id"] == lot_id].copy()


# Global Singleton / Helper Instance
_engine_instance: Optional[SkyNexEngine] = None


def get_engine() -> SkyNexEngine:
    """Returns or initializes the global SkyNexEngine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = SkyNexEngine()
    return _engine_instance


def analyze_component(component_id: str) -> Dict[str, Any]:
    """
    Direct function interface for single-component analysis.
    Returns the unified SkyNex component result dictionary.
    """
    engine = get_engine()
    return engine.analyze_component(component_id)


if __name__ == "__main__":
    engine = get_engine()
    print("Pipeline executed successfully.")
    sample_normal = engine.analyze_component("C_00001")
    print("\n--- Sample Normal Component (C_00001) ---")
    for k, v in sample_normal.items():
        print(f"  {k}: {v}")

    sample_anomalous = engine.analyze_component("C_00009")
    print("\n--- Sample Anomalous Component (C_00009) ---")
    for k, v in sample_anomalous.items():
        print(f"  {k}: {v}")

