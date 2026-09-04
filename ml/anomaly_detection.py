"""
Module A: Dynamic Outlier and Anomaly Detection.

Compares each component against its OWN LOT's statistical behavior,
not just the fixed datasheet limit. Two layers:

1. Per-lot Z-score / IQR on individual parameters (fast, explainable)
2. Isolation Forest across multiple parameters jointly, fit per lot
   (catches multivariate anomalies a single-parameter check would miss)
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

try:
    from config import (
        VALUE_COLS,
        ZSCORE_THRESHOLD,
        IQR_K,
        ISO_FOREST_CONTAMINATION,
        RANDOM_STATE,
    )
except ImportError:
    VALUE_COLS = ["Value_0h", "Value_24h", "Value_96h", "Value_168h"]
    ZSCORE_THRESHOLD = 3.0
    IQR_K = 1.5
    ISO_FOREST_CONTAMINATION = 0.08
    RANDOM_STATE = 42


def zscore_flags(df: pd.DataFrame, threshold: float = ZSCORE_THRESHOLD) -> pd.DataFrame:
    """
    Per-lot Z-score outlier detection on the 168h value (the
    checkpoint most indicative of accumulated drift).

    Returns df with added columns: lot_mean_168h, lot_std_168h,
    zscore_168h, flag_zscore
    """
    out = df.copy()
    lot_stats = out.groupby("lot_id")["Value_168h"].agg(["mean", "std"]).reset_index()
    lot_stats.columns = ["lot_id", "lot_mean_168h", "lot_std_168h"]
    out = out.merge(lot_stats, on="lot_id", how="left")

    # guard against zero std (tiny lots / identical values)
    safe_std = out["lot_std_168h"].replace(0, np.nan)
    out["zscore_168h"] = (out["Value_168h"] - out["lot_mean_168h"]) / safe_std
    out["zscore_168h"] = out["zscore_168h"].fillna(0)
    out["flag_zscore"] = out["zscore_168h"].abs() >= threshold
    return out


def iqr_flags(df: pd.DataFrame, k: float = IQR_K) -> pd.DataFrame:
    """
    Per-lot IQR outlier detection on the 168h value. Robust to a
    few extreme points skewing the mean/std the way Z-score can be.
    """
    out = df.copy()

    def _iqr_bounds(group):
        q1, q3 = group.quantile(0.25), group.quantile(0.75)
        iqr = q3 - q1
        return q1 - k * iqr, q3 + k * iqr

    bounds = out.groupby("lot_id")["Value_168h"].apply(_iqr_bounds)
    lower = bounds.apply(lambda x: x[0]).rename("iqr_lower")
    upper = bounds.apply(lambda x: x[1]).rename("iqr_upper")
    out = out.merge(lower, on="lot_id", how="left").merge(upper, on="lot_id", how="left")
    out["flag_iqr"] = (out["Value_168h"] < out["iqr_lower"]) | (out["Value_168h"] > out["iqr_upper"])
    return out


def isolation_forest_flags(
    df: pd.DataFrame,
    contamination: float = ISO_FOREST_CONTAMINATION,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """
    Fits a separate Isolation Forest PER LOT across all four time-point
    readings jointly, so a part that looks fine on any single reading
    but is an odd combination across readings still gets caught.

    Returns df with added columns: if_score (lower = more anomalous),
    flag_isoforest
    """
    out = df.copy()
    out["if_score"] = np.nan
    out["flag_isoforest"] = False

    for lot_id, group in out.groupby("lot_id"):
        if len(group) < 10:
            # too few parts in this lot for a meaningful model; skip
            continue
        X = group[VALUE_COLS].values
        model = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            random_state=random_state,
        )
        model.fit(X)
        scores = model.decision_function(X)  # higher = more normal
        preds = model.predict(X)  # -1 = anomaly, 1 = normal

        out.loc[group.index, "if_score"] = scores
        out.loc[group.index, "flag_isoforest"] = preds == -1

    return out


def run_module_a(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full Module A pipeline: Z-score + IQR + Isolation Forest,
    combined into a single anomaly_score and final flag_module_a.
    """
    out = zscore_flags(df)
    out = iqr_flags(out)
    out = isolation_forest_flags(out)

    # Combined rule: flagged if ANY method flags it (biases toward
    # recall since a false negative here is the costly failure mode
    # per the evaluation criteria)
    out["flag_module_a"] = out["flag_zscore"] | out["flag_iqr"] | out["flag_isoforest"]

    # A simple 0-100 anomaly score for the dashboard, blending zscore
    # magnitude and isolation forest score
    z_component = out["zscore_168h"].abs().clip(0, 6) / 6
    if_component = (1 - (out["if_score"].fillna(out["if_score"].median()) + 0.5)).clip(0, 1)
    out["anomaly_score"] = (0.5 * z_component + 0.5 * if_component).clip(0, 1) * 100
    out["anomaly_score"] = out["anomaly_score"].round(1)

    return out


if __name__ == "__main__":
    from config import WIDE_DATA_PATH
    wide_df = pd.read_csv(WIDE_DATA_PATH)
    result = run_module_a(wide_df)

    print(f"Flagged {result['flag_module_a'].sum()} / {len(result)} components")
    if "is_defective" in result.columns:
        tp = ((result["flag_module_a"]) & (result["is_defective"])).sum()
        fn = ((~result["flag_module_a"]) & (result["is_defective"])).sum()
        fp = ((result["flag_module_a"]) & (~result["is_defective"])).sum()
        tn = ((~result["flag_module_a"]) & (~result["is_defective"])).sum()
        recall = tp / (tp + fn) if (tp + fn) else 0
        precision = tp / (tp + fp) if (tp + fp) else 0
        print(f"True Positives:  {tp}")
        print(f"False Negatives: {fn}")
        print(f"False Positives: {fp}")
        print(f"True Negatives:  {tn}")
        print(f"Recall (catch rate): {recall:.1%}")
        print(f"Precision: {precision:.1%}")

