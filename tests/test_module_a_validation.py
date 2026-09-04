"""
Comprehensive Unit & Integration Test Suite for SkyNex Module A (Anomaly Detection).
"""

import unittest
import numpy as np
import pandas as pd
from ml.anomaly_detection import (
    zscore_flags,
    iqr_flags,
    isolation_forest_flags,
    run_module_a,
    generate_anomaly_explanation,
)
from engine.skynex_engine import analyze_component, SkyNexEngine


class TestModuleAValidation(unittest.TestCase):

    def setUp(self):
        # Create synthetic dataset for isolation testing
        self.synthetic_df = pd.DataFrame({
            "component_id": [f"C_{i:05d}" for i in range(1, 21)],
            "lot_id": ["LOT_001"] * 10 + ["LOT_002"] * 10,
            "Value_0h": [10.0] * 20,
            "Value_24h": [10.1] * 20,
            "Value_96h": [10.2] * 20,
            "Value_168h": [10.5] * 9 + [25.0] + [12.0] * 10,  # C_00010 is outlier in LOT_001
            "is_defective": [False] * 9 + [True] + [False] * 10,
        })

    def test_normal_and_known_anomaly(self):
        res = run_module_a(self.synthetic_df)
        normal_row = res[res["component_id"] == "C_00001"].iloc[0]
        anom_row = res[res["component_id"] == "C_00010"].iloc[0]

        self.assertFalse(normal_row["flag_module_a"])
        self.assertTrue(anom_row["flag_module_a"])
        self.assertGreater(anom_row["anomaly_score"], 50.0)

    def test_missing_values_and_nan(self):
        df_nan = self.synthetic_df.copy()
        df_nan.loc[0, "Value_168h"] = np.nan
        res = run_module_a(df_nan)
        self.assertFalse(np.isnan(res.loc[0, "anomaly_score"]))

    def test_zero_std_handling(self):
        df_zero_std = pd.DataFrame({
            "component_id": [f"C_Z{i}" for i in range(10)],
            "lot_id": ["LOT_ZERO"] * 10,
            "Value_0h": [10.0] * 10,
            "Value_24h": [10.0] * 10,
            "Value_96h": [10.0] * 10,
            "Value_168h": [10.0] * 10,
        })
        res = zscore_flags(df_zero_std)
        self.assertTrue((res["zscore_168h"] == 0).all())
        self.assertFalse(res["flag_zscore"].any())

    def test_zero_iqr_handling(self):
        df_zero_iqr = pd.DataFrame({
            "component_id": [f"C_I{i}" for i in range(10)],
            "lot_id": ["LOT_IQR"] * 10,
            "Value_0h": [10.0] * 10,
            "Value_24h": [10.0] * 10,
            "Value_96h": [10.0] * 10,
            "Value_168h": [10.0] * 10,
        })
        res = iqr_flags(df_zero_iqr)
        self.assertFalse(res["flag_iqr"].any())

    def test_small_lot_handling(self):
        df_small = pd.DataFrame({
            "component_id": [f"C_S{i}" for i in range(5)],  # < 10 items
            "lot_id": ["LOT_SMALL"] * 5,
            "Value_0h": [10.0] * 5,
            "Value_24h": [10.1] * 5,
            "Value_96h": [10.2] * 5,
            "Value_168h": [10.5] * 5,
        })
        res = isolation_forest_flags(df_small)
        self.assertFalse(res.iloc[0]["isoforest_evaluated"])
        self.assertFalse(res.iloc[0]["flag_isoforest"])

    def test_reproducibility(self):
        res1 = run_module_a(self.synthetic_df)
        res2 = run_module_a(self.synthetic_df)
        pd.testing.assert_frame_equal(res1["anomaly_score"].to_frame(), res2["anomaly_score"].to_frame())

    def test_no_data_leakage(self):
        # Verify is_defective is not used in run_module_a
        df_no_gt = self.synthetic_df.drop(columns=["is_defective"])
        res = run_module_a(df_no_gt)
        self.assertIn("anomaly_score", res.columns)

    def test_skynex_engine_integration(self):
        res_c9 = analyze_component("C_00009")
        self.assertIn("anomaly_score", res_c9)
        self.assertIn("flags", res_c9)
        self.assertTrue(res_c9["flags"]["flag_module_a"])
        self.assertIn("explanation", res_c9)


if __name__ == "__main__":
    unittest.main()
