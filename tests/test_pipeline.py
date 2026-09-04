"""
SkyNex Integration and Unit Test Suite
Verifies pipeline components, interfaces, ML models, and QA recommendations.
Uses standard library unittest for zero-dependency test execution.
"""

import unittest
from pathlib import Path
import pandas as pd

from config import WIDE_DATA_PATH
from ml.anomaly_detection import run_module_a
from ml.drift_prediction import (
    engineer_features,
    compute_safety_slope,
    load_or_train_xgb_model,
    predict_and_flag,
)
from engine.risk_engine import compute_component_risk_score, determine_risk_level, calculate_risk_scores
from engine.explanation import generate_component_explanation
from qa.recommendation import generate_recommendation
from qa.decision import create_decision
from qa.database import QADatabase
from engine.skynex_engine import SkyNexEngine, analyze_component
from reports.report_generator import ReportGenerator


class TestSkyNexPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.raw_df = pd.read_csv(WIDE_DATA_PATH)
        cls.engine = SkyNexEngine(auto_run=True)

    def test_module_a(self):
        """Verifies Module A anomaly detection on raw data."""
        df_a = run_module_a(self.raw_df)
        self.assertIn("flag_module_a", df_a.columns)
        self.assertIn("anomaly_score", df_a.columns)
        self.assertIn("flag_zscore", df_a.columns)
        self.assertIn("flag_iqr", df_a.columns)
        self.assertIn("flag_isoforest", df_a.columns)
        self.assertTrue(df_a["anomaly_score"].between(0.0, 100.0).all())

    def test_module_b(self):
        """Verifies Module B drift predictor on raw data."""
        safety_slope = compute_safety_slope(self.raw_df, percentile=95.0)
        self.assertGreater(safety_slope, 0)
        model = load_or_train_xgb_model(self.raw_df)
        df_b = predict_and_flag(self.raw_df, model, safety_slope)
        self.assertIn("predicted_168h", df_b.columns)
        self.assertIn("predicted_slope", df_b.columns)
        self.assertIn("flag_module_b", df_b.columns)

    def test_risk_engine(self):
        """Verifies composite risk scoring and classification."""
        low_risk = compute_component_risk_score(
            anomaly_score=10.0,
            flag_module_a=False,
            flag_module_b=False,
            predicted_slope=0.001,
            safety_slope_threshold=0.01,
        )
        self.assertLessEqual(low_risk, 25.0)
        self.assertEqual(determine_risk_level(low_risk), "LOW")

        high_risk = compute_component_risk_score(
            anomaly_score=75.0,
            flag_module_a=True,
            flag_module_b=True,
            predicted_slope=0.08,
            safety_slope_threshold=0.01,
        )
        self.assertGreaterEqual(high_risk, 75.0)
        self.assertEqual(determine_risk_level(high_risk), "CRITICAL")

    def test_explanation_engine(self):
        """Verifies explanation generator for normal and defective parts."""
        normal_row = {"flag_module_a": False, "flag_module_b": False}
        exp_normal = generate_component_explanation(normal_row)
        self.assertIn("No issues detected", exp_normal)

        anomaly_row = {
            "flag_module_a": True,
            "flag_zscore": True,
            "zscore_168h": 4.2,
            "Value_168h": 25.0,
            "lot_mean_168h": 11.5,
            "flag_module_b": False,
        }
        exp_anomaly = generate_component_explanation(anomaly_row)
        self.assertIn("[Module A Outlier]", exp_anomaly)

    def test_qa_decision_and_db(self):
        """Verifies QA Decision recording and database audit trail."""
        test_db_path = Path("qa/test_qa_decisions.db")
        if test_db_path.exists():
            try:
                test_db_path.unlink()
            except PermissionError:
                pass

        try:
            qa_db = QADatabase(db_path=test_db_path)
            decision = create_decision(
                component_id="C_00009",
                decision="REJECT",
                engineer_id="QA_ENG_42",
                notes="Severe 24h drift observed.",
            )
            qa_db.record_decision(decision)

            retrieved = qa_db.get_latest_decision("C_00009")
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved["component_id"], "C_00009")
            self.assertEqual(retrieved["decision"], "REJECT")
            self.assertEqual(retrieved["engineer_id"], "QA_ENG_42")
        finally:
            if test_db_path.exists():
                try:
                    test_db_path.unlink()
                except PermissionError:
                    pass

    def test_analyze_component_interface(self):
        """
        Verifies the primary required interface analyze_component(component_id)
        returns the exact unified result payload with all 14 required fields.
        """
        sample_id = self.raw_df["component_id"].iloc[0]
        result = self.engine.analyze_component(sample_id)

        required_fields = [
            "component_id",
            "lot_id",
            "anomaly_score",
            "anomaly_status",
            "drift_rate",
            "drift_status",
            "predicted_168h",
            "prediction_status",
            "risk_score",
            "risk_level",
            "flags",
            "explanation",
            "recommendation",
            "qa_decision",
        ]

        for field in required_fields:
            self.assertIn(field, result, f"Field '{field}' missing from analyze_component result")

        self.assertIsInstance(result["flags"], dict)
        self.assertIn("flag_module_a", result["flags"])
        self.assertIn("flag_module_b", result["flags"])
        self.assertIn(result["risk_level"], ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.assertIn(result["recommendation"], ["PASS", "EXTEND_BURN_IN", "RETEST", "REJECT"])

    def test_report_generation(self):
        """Verifies CSV, JSON, and lot summary export functionality."""
        df = self.engine.processed_df
        test_out_dir = Path("reports/test_output")
        test_out_dir.mkdir(parents=True, exist_ok=True)

        try:
            rep_gen = ReportGenerator(output_dir=test_out_dir)
            csv_path = rep_gen.export_csv(df, "test_report.csv")
            self.assertTrue(csv_path.exists())

            json_path = rep_gen.export_json(df, "test_report.json")
            self.assertTrue(json_path.exists())

            lot_summary = rep_gen.generate_lot_summary(df, "test_lot_summary.csv")
            self.assertIn("yield_percentage", lot_summary.columns)
            self.assertGreater(len(lot_summary), 0)
        finally:
            import shutil
            if test_out_dir.exists():
                shutil.rmtree(test_out_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

