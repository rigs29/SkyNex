"""
Module B: Time-Series Drift Predictor.

Takes early burn-in readings (0h, 24h) and forecasts the 168h value.
If the predicted drift slope exceeds a safety threshold (derived from
the known-good population), the component is flagged for early
rejection -- without waiting out the full 168h burn-in.
"""

from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor

try:
    from config import (
        FEATURE_COLS,
        SAFETY_SLOPE_PERCENTILE,
        RANDOM_STATE,
        XGB_MODEL_PATH,
        LINEAR_MODEL_PATH,
    )
except ImportError:
    FEATURE_COLS = [
        "Value_0h",
        "Value_24h",
        "delta_24h",
        "pct_change_24h",
        "slope_0_24",
        "lot_mean_0h",
    ]
    SAFETY_SLOPE_PERCENTILE = 95.0
    RANDOM_STATE = 42
    XGB_MODEL_PATH = Path("models/xgb_model.joblib")
    LINEAR_MODEL_PATH = Path("models/linear_model.joblib")


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive drift-behavior features from the raw early readings."""
    out = df.copy()
    out["delta_24h"] = out["Value_24h"] - out["Value_0h"]
    out["pct_change_24h"] = out["delta_24h"] / out["Value_0h"].replace(0, np.nan)
    out["pct_change_24h"] = out["pct_change_24h"].fillna(0)
    out["slope_0_24"] = out["delta_24h"] / 24.0

    lot_mean_0h = out.groupby("lot_id")["Value_0h"].transform("mean")
    out["lot_mean_0h"] = lot_mean_0h
    return out


def train_models(df: pd.DataFrame, random_state: int = RANDOM_STATE) -> tuple:
    """
    Trains both a Linear Regression baseline and an XGBoost model to
    predict Value_168h from early-reading features. Returns both
    fitted models plus a held-out evaluation report.
    """
    df = engineer_features(df)
    X = df[FEATURE_COLS]
    y = df["Value_168h"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )

    lin_model = LinearRegression()
    lin_model.fit(X_train, y_train)
    lin_preds = lin_model.predict(X_test)
    lin_mae = mean_absolute_error(y_test, lin_preds)

    xgb_model = XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        random_state=random_state,
    )
    xgb_model.fit(X_train, y_train)
    xgb_preds = xgb_model.predict(X_test)
    xgb_mae = mean_absolute_error(y_test, xgb_preds)

    report = {
        "linear_regression_mae": round(lin_mae, 4),
        "xgboost_mae": round(xgb_mae, 4),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "linear_coefficients": dict(zip(FEATURE_COLS, lin_model.coef_.round(4))),
    }
    return lin_model, xgb_model, report


def compute_safety_slope(
    df: pd.DataFrame,
    percentile: float = SAFETY_SLOPE_PERCENTILE,
) -> float:
    """
    Derives the safety slope threshold empirically from the
    KNOWN-GOOD population's actual (0h->168h) drift slope, at the
    given percentile. Any predicted slope beyond this is flagged.
    """
    good = df[~df["is_defective"]] if "is_defective" in df.columns else df
    actual_slope = (good["Value_168h"] - good["Value_24h"]) / (168 - 24)
    threshold = np.percentile(actual_slope, percentile)
    return round(float(threshold), 5)


def load_or_train_xgb_model(
    df: pd.DataFrame = None,
    model_path: Path = XGB_MODEL_PATH,
    random_state: int = RANDOM_STATE,
) -> object:
    """Loads existing pre-trained XGBoost model or trains and saves if not present."""
    if Path(model_path).exists():
        return joblib.load(model_path)
    if df is None:
        raise ValueError("Model file not found and no training data provided.")
    _, xgb_model, _ = train_models(df, random_state=random_state)
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(xgb_model, model_path)
    return xgb_model


def predict_and_flag(
    df: pd.DataFrame,
    model,
    safety_slope_threshold: float,
) -> pd.DataFrame:
    """Runs predictions for every component and applies the
    safety-slope early-rejection rule."""
    df = engineer_features(df)
    X = df[FEATURE_COLS]

    df["predicted_168h"] = model.predict(X)
    df["predicted_slope"] = (df["predicted_168h"] - df["Value_24h"]) / (168 - 24)
    df["flag_module_b"] = df["predicted_slope"] > safety_slope_threshold
    return df


if __name__ == "__main__":
    from config import WIDE_DATA_PATH
    wide_df = pd.read_csv(WIDE_DATA_PATH)
    lin_model, xgb_model, report = train_models(wide_df)
    print("Training report:", report)
    safety_slope = compute_safety_slope(wide_df, percentile=95.0)
    print(f"Safety slope threshold: {safety_slope} uA/hour")
    result = predict_and_flag(wide_df, xgb_model, safety_slope)
    print(f"Flagged Module B: {result['flag_module_b'].sum()} / {len(result)}")

