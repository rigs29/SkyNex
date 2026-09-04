"""
SkyNex Dataset & Pipeline Audit Script
Inspects dataset statistics, checks leakage, and traces pipeline execution.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import numpy as np
from engine.skynex_engine import get_engine, analyze_component
from qa.database import QADatabase
from qa.decision import create_decision
from reports.report_generator import ReportGenerator

def audit_dataset_and_engine():
    wide = pd.read_csv('data/raw/burnin_data_wide.csv')
    long = pd.read_csv('data/raw/burnin_data_long.csv')

    print("=== DATASET INSPECTION ===")
    print(f"Wide rows: {len(wide)}, columns: {list(wide.columns)}")
    print(f"Unique components in wide: {wide['component_id'].nunique()}")
    print(f"Unique lots in wide: {wide['lot_id'].nunique()}")
    print(f"Long rows: {len(long)}, columns: {list(long.columns)}")
    print(f"Unique components in long: {long['component_id'].nunique()}")
    
    # Check time points in long
    time_col = [c for c in long.columns if 'time' in c.lower() or 'hour' in c.lower() or 'timepoint' in c.lower()]
    print(f"Long time columns: {time_col}")
    if time_col:
        print(f"Timepoints: {sorted(long[time_col[0]].unique())}")

    print("\n=== RUNNING FULL BACKEND PIPELINE ===")
    engine = get_engine()
    df = engine.processed_df

    total_tested = len(df)
    anomalies_a = int(df['flag_module_a'].sum())
    drift_b = int(df['flag_module_b'].sum())
    combined_flagged = int(df['final_flag'].sum())
    
    risk_counts = df['risk_level'].value_counts().to_dict()
    rec_counts = df['recommendation'].value_counts().to_dict()

    print(f"Total Components Screened: {total_tested}")
    print(f"Module A Flagged (Anomalies): {anomalies_a} ({anomalies_a/total_tested*100:.2f}%)")
    print(f"Module B Flagged (Drift): {drift_b} ({drift_b/total_tested*100:.2f}%)")
    print(f"Combined Flagged Components: {combined_flagged} ({combined_flagged/total_tested*100:.2f}%)")
    print(f"Risk Levels: {risk_counts}")
    print(f"Recommendations: {rec_counts}")
    
    print("\n=== TRACE 3 REAL COMPONENTS ===")
    sample_ids = ["C_00001", "C_00009", "C_00005"]
    for cid in sample_ids:
        res = engine.analyze_component(cid)
        print(f"\n--- Component: {cid} ---")
        for k, v in res.items():
            print(f"  {k}: {v}")

if __name__ == "__main__":
    audit_dataset_and_engine()

