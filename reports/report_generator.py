"""
SkyNex Report Generator Module
Exports unified screening reports in CSV, JSON, and aggregated Lot-level summaries.
"""

from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd

try:
    from config import OUTPUT_DIR, FINAL_REPORT_PATH
except ImportError:
    OUTPUT_DIR = Path("reports/output")
    FINAL_REPORT_PATH = OUTPUT_DIR / "final_report.csv"


class ReportGenerator:
    """Handles report generation and summary exports for burn-in QA."""

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_csv(
        self,
        df: pd.DataFrame,
        filename: str = "final_report.csv",
    ) -> Path:
        """Exports the full pipeline DataFrame to CSV."""
        out_path = self.output_dir / filename
        df.to_csv(out_path, index=False)
        return out_path

    def export_json(
        self,
        df: pd.DataFrame,
        filename: str = "final_report.json",
    ) -> Path:
        """Exports the full pipeline DataFrame to JSON."""
        out_path = self.output_dir / filename
        df.to_json(out_path, orient="records", indent=2)
        return out_path

    def generate_lot_summary(
        self,
        df: pd.DataFrame,
        filename: Optional[str] = "lot_summary_report.csv",
    ) -> pd.DataFrame:
        """
        Aggregates screening yield, anomaly rates, and average risk by lot.
        """
        summary = (
            df.groupby("lot_id")
            .agg(
                total_components=("component_id", "count"),
                flagged_module_a=("flag_module_a", "sum"),
                flagged_module_b=("flag_module_b", "sum"),
                total_flagged=("final_flag", "sum"),
                avg_risk_score=("risk_score", "mean"),
                max_risk_score=("risk_score", "max"),
                avg_anomaly_score=("anomaly_score", "mean"),
            )
            .reset_index()
        )

        summary["yield_percentage"] = (
            (summary["total_components"] - summary["total_flagged"])
            / summary["total_components"]
            * 100
        ).round(2)
        summary["avg_risk_score"] = summary["avg_risk_score"].round(1)
        summary["avg_anomaly_score"] = summary["avg_anomaly_score"].round(1)

        if filename:
            out_path = self.output_dir / filename
            summary.to_csv(out_path, index=False)

        return summary

    def get_executive_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generates top-level KPI metrics for engineering management."""
        total = len(df)
        flagged = int(df["final_flag"].sum()) if "final_flag" in df else 0
        passed = total - flagged
        critical = int((df["risk_level"] == "CRITICAL").sum()) if "risk_level" in df else 0
        high = int((df["risk_level"] == "HIGH").sum()) if "risk_level" in df else 0

        summary = {
            "total_screened": total,
            "passed": passed,
            "flagged": flagged,
            "screening_yield_pct": round((passed / total * 100), 2) if total > 0 else 0.0,
            "critical_risk_count": critical,
            "high_risk_count": high,
            "avg_fleet_risk": round(float(df["risk_score"].mean()), 1) if "risk_score" in df else 0.0,
        }
        return summary

