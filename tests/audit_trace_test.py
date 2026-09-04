"""
SkyNex Comprehensive End-to-End Audit & Verification Suite
Tests dataset consistency, data leakage, single component trace, QA decisions, and report integrity.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import unittest
import pandas as pd
import numpy as np

from config import WIDE_DATA_PATH, LONG_DATA_PATH
from engine.skynex_engine import get_engine, analyze_component, SkyNexEngine
from ml.anomaly_detection import run_module_a, VALUE_COLS
from ml.drift_prediction import engineer_features, FEATURE_COLS, compute_safety_slope
from engine.risk_engine import compute_component_risk_score, determine_risk_level
from qa.decision import create_decision, VALID_DECISIONS
from qa.database import QADatabase
from reports.report_generator import ReportGenerator


class TestSkyNexComprehensiveAudit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = get_engine()
        cls.raw_df = cls.engine.raw_df
        cls.processed_df = cls.engine.processed_df

    def test_1_dataset_consistency(self):
        """Audit 1: Verify dataset shape, columns, and uniqueness."""
        self.assertEqual(len(self.raw_df), 1000)
        self.assertEqual(self.raw_df['component_id'].nunique(), 1000)
        self.assertEqual(self.raw_df['lot_id'].nunique(), 25)

        # Check required columns
        for col in ["component_id", "lot_id", "Value_0h", "Value_24h", "Value_96h", "Value_168h"]:
            self.assertIn(col, self.raw_df.columns)

        # Check long dataset
        long_df = pd.read_csv(LONG_DATA_PATH)
        self.assertEqual(len(long_df), 4000)
        self.assertEqual(long_df['component_id'].nunique(), 1000)

    def test_2_data_leakage_safety(self):
        """Audit 2: Ensure zero data leakage in feature engineering."""
        # 1. Module B features must NOT include future timepoints or ground truth
        self.assertNotIn("Value_96h", FEATURE_COLS)
        self.assertNotIn("Value_168h", FEATURE_COLS)
        self.assertNotIn("is_defective", FEATURE_COLS)
        self.assertNotIn("component_id", FEATURE_COLS)

        # 2. Test feature engineering on raw data
        feats_df = engineer_features(self.raw_df)
        for f in FEATURE_COLS:
            self.assertIn(f, feats_df.columns)

        # 3. Module A must not use is_defective as feature
        self.assertNotIn("is_defective", VALUE_COLS)

    def test_3_three_component_trace(self):
        """Audit 3: Detailed end-to-end trace of 3 real components."""
        # Component 1: Normal Low Risk (C_00001)
        res_normal = self.engine.analyze_component("C_00001")
        self.assertEqual(res_normal["component_id"], "C_00001")
        self.assertEqual(res_normal["lot_id"], "LOT_000")
        self.assertFalse(res_normal["anomaly_status"])
        self.assertFalse(res_normal["drift_status"])
        self.assertEqual(res_normal["risk_level"], "LOW")
        self.assertEqual(res_normal["recommendation"], "PASS")

        # Component 2: High/Critical Risk (C_00009)
        res_anom = self.engine.analyze_component("C_00009")
        self.assertEqual(res_anom["component_id"], "C_00009")
        self.assertEqual(res_anom["lot_id"], "LOT_000")
        self.assertTrue(res_anom["anomaly_status"])
        self.assertTrue(res_anom["drift_status"])
        self.assertEqual(res_anom["risk_level"], "CRITICAL")
        self.assertEqual(res_anom["recommendation"], "REJECT")
        self.assertIn("[Module A Outlier]", res_anom["explanation"])
        self.assertIn("[Module B Drift]", res_anom["explanation"])

        # Component 3: Boundary / Normal part (C_00005)
        res_c5 = self.engine.analyze_component("C_00005")
        self.assertEqual(res_c5["component_id"], "C_00005")
        self.assertEqual(res_c5["risk_level"], "LOW")
        self.assertEqual(res_c5["recommendation"], "PASS")

    def test_4_human_in_the_loop_qa_workflow(self):
        """Audit 4: Test QA engineer decisions (PASS, HOLD, FAIL) in SQLite."""
        test_db_path = Path("qa/test_audit_qa.db")
        if test_db_path.exists():
            test_db_path.unlink()

        try:
            db = QADatabase(db_path=test_db_path)

            # Record PASS decision
            d_pass = create_decision(
                component_id="C_00001",
                decision="PASS",
                engineer_id="QA_CHIEF_01",
                notes="Verified baseline stable drift."
            )
            db.record_decision(d_pass)

            # Record HOLD decision
            d_hold = create_decision(
                component_id="C_00005",
                decision="HOLD",
                engineer_id="QA_CHIEF_01",
                notes="Extended 24h burn-in requested."
            )
            db.record_decision(d_hold)

            # Record FAIL decision
            d_fail = create_decision(
                component_id="C_00009",
                decision="FAIL",
                engineer_id="QA_CHIEF_01",
                notes="Thermal runaway early degradation confirmed."
            )
            db.record_decision(d_fail)

            # Verify retrieval
            rec_pass = db.get_latest_decision("C_00001")
            self.assertIsNotNone(rec_pass)
            self.assertEqual(rec_pass["decision"], "PASS")
            self.assertEqual(rec_pass["notes"], "Verified baseline stable drift.")

            rec_hold = db.get_latest_decision("C_00005")
            self.assertIsNotNone(rec_hold)
            self.assertEqual(rec_hold["decision"], "HOLD")

            rec_fail = db.get_latest_decision("C_00009")
            self.assertIsNotNone(rec_fail)
            self.assertEqual(rec_fail["decision"], "FAIL")

            all_decs = db.get_all_decisions()
            self.assertEqual(len(all_decs), 3)
        finally:
            if test_db_path.exists():
                try:
                    test_db_path.unlink()
                except PermissionError:
                    pass

    def test_5_report_and_engine_consistency(self):
        """Audit 5: Verify exported report matches analyze_component() exactly."""
        rep_dir = Path("reports/test_audit_output")
        rep_dir.mkdir(parents=True, exist_ok=True)
        try:
            gen = ReportGenerator(output_dir=rep_dir)
            csv_path = gen.export_csv(self.processed_df, "audit_report.csv")
            self.assertTrue(csv_path.exists())

            report_df = pd.read_csv(csv_path)
            self.assertEqual(len(report_df), 1000)

            # Pick a component from report and compare with analyze_component
            test_row = report_df[report_df["component_id"] == "C_00009"].iloc[0]
            eng_res = self.engine.analyze_component("C_00009")

            self.assertEqual(test_row["component_id"], eng_res["component_id"])
            self.assertEqual(test_row["lot_id"], eng_res["lot_id"])
            self.assertAlmostEqual(test_row["anomaly_score"], eng_res["anomaly_score"], places=1)
            self.assertAlmostEqual(test_row["predicted_168h"], eng_res["predicted_168h"], places=2)
            self.assertAlmostEqual(test_row["risk_score"], eng_res["risk_score"], places=1)
            self.assertEqual(test_row["risk_level"], eng_res["risk_level"])
            self.assertEqual(test_row["recommendation"], eng_res["recommendation"])
            self.assertEqual(test_row["explanation"], eng_res["explanation"])
        finally:
            import shutil
            if rep_dir.exists():
                shutil.rmtree(rep_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

