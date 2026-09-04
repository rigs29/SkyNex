"""
Unit tests for Module A (Anomaly Detection) in SkyNex.
"""

import unittest
import numpy as np
import pandas as pd
from ml.anomaly_detection import (
    zscore_flags,
    iqr_flags,
    isolation_forest_flags,
    run_module_a,
)
from engine.skynex_engine import analyze_component


class TestModuleAAnomalyDetection(unittest.TestCase):

    def setUp(self):
        # Construct synthetic testing DataFrame with 2 lots
        np.random.seed(42)
        lot_001 = pd.DataFrame({
            "component_id": [f"C_A_{i:03d}" for i in range(12)],
            "lot_id": ["LOT_001"] * 12,
            "Value_0h": np.random.normal(10.0, 0.2, 12),
            "Value_24h": np.random.normal(10.2, 0.2, 12),
            "Value_96h": np.random.normal(10.5, 0.2, 12),
            "Value_168h": np.random.normal(10.8, 0.2, 12),
            "is_defective": [False] * 12,
        })
        # Add a clear outlier to LOT_001
        lot_001.loc[11, "Value_168h"] = 25.0
        lot_001.loc[11, "is_defective"] = True

        # Small lot (5 items)
        lot_002 = pd.DataFrame({
            "component_id": [f"C_B_{i:03d}" for i in range(5)],
            "lot_id": ["LOT_002"] * 5,
            "Value_0h": [10.0] * 5,
            "Value_24h": [10.1] * 5,
            "Value_96h": [10.2] * 5,
            "Value_168h": [10.3] * 5,
            "is_defective": [False] * 5,
        })

        self.df = pd.concat([lot_001, lot_002], ignore_index=True)

    def test_zscore_flags(self):
        res = zscore_flags(self.df, threshold=3.0)
        self.assertIn("zscore_168h", res.columns)
        self.assertIn("flag_zscore", res.columns)
        # C_A_011 (index 11) should be flagged by Z-score
        self.assertTrue(res.loc[11, "flag_zscore"])
        # Normal item should not be flagged
        self.assertFalse(res.loc[0, "flag_zscore"])

    def test_iqr_flags(self):
        res = iqr_flags(self.df, k=1.5)
        self.assertIn("iqr_lower", res.columns)
        self.assertIn("iqr_upper", res.columns)
        self.assertIn("flag_iqr", res.columns)
        self.assertTrue(res.loc[11, "flag_iqr"])

    def test_isolation_forest_small_lot_handling(self):
        res = isolation_forest_flags(self.df)
        # LOT_002 has 5 items (<10), so flag_isoforest should be False and if_score NaN
        lot_002_res = res[res["lot_id"] == "LOT_002"]
        self.assertTrue(lot_002_res["if_score"].isnull().all())
        self.assertFalse(lot_002_res["flag_isoforest"].any())

    def test_zero_std_handling(self):
        zero_std_df = pd.DataFrame({
            "component_id": ["C_Z_001", "C_Z_002"],
            "lot_id": ["LOT_ZERO", "LOT_ZERO"],
            "Value_0h": [10.0, 10.0],
            "Value_24h": [10.0, 10.0],
            "Value_96h": [10.0, 10.0],
            "Value_168h": [10.0, 10.0],
        })
        res = zscore_flags(zero_std_df)
        self.assertFalse(res["zscore_168h"].isnull().any())
        self.assertFalse(np.isinf(res["zscore_168h"]).any())

    def test_run_module_a_score_and_flags(self):
        res = run_module_a(self.df)
        self.assertIn("anomaly_score", res.columns)
        self.assertIn("flag_module_a", res.columns)
        self.assertFalse(res["anomaly_score"].isnull().any())
        self.assertFalse(np.isinf(res["anomaly_score"]).any())
        # C_A_011 score >= 40
        self.assertGreaterEqual(res.loc[11, "anomaly_score"], 40.0)

    def test_skynex_engine_integration(self):
        res = analyze_component("C_00001")
        self.assertIn("anomaly_score", res)
        self.assertIn("anomaly_status", res)
        self.assertIn("flags", res)
        self.assertIn("explanation", res)


if __name__ == "__main__":
    unittest.main()
