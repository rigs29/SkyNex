"""
SkyNex UI Priority Components Table Component
Renders the high-risk priority component inspection table with badges, severity bars,
pagination, and interactive REVIEW action drawer powered directly by analyze_component().
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
from engine.skynex_engine import analyze_component, get_engine
from qa.decision import create_decision
from qa.database import QADatabase

try:
    from config import DEFAULT_ENGINEER_ID
except ImportError:
    DEFAULT_ENGINEER_ID = "QA_ENG_ADMIN"


def get_real_priority_rows(df: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
    """Returns the top priority high-risk components directly from the processed dataset."""
    if df is None or df.empty:
        engine = get_engine()
        df = engine.processed_df

    db = QADatabase()

    # Sort by risk_score descending to bubble up highest severity components
    sorted_df = df.sort_values(by="risk_score", ascending=False).head(20)

    rows = []
    border_palette = ["#1D63FF", "#8B5CF6", "#F97316", "#EF4444", "#06B6D4"]

    for idx, (_, row) in enumerate(sorted_df.iterrows()):
        cid = str(row["component_id"])
        latest_qa = db.get_latest_decision(cid)
        qa_status_display = latest_qa["decision"] if latest_qa else "PENDING"

        rows.append(
            {
                "component_id": cid,
                "backend_id": cid,
                "lot_id": str(row["lot_id"]),
                "anomaly": "HIGH" if bool(row.get("flag_module_a", False)) else "LOW",
                "drift": "HIGH" if bool(row.get("flag_module_b", False)) else "LOW",
                "risk_score": int(round(float(row.get("risk_score", 0)))),
                "risk_level": str(row.get("risk_level", "LOW")),
                "qa_status": qa_status_display,
                "border_color": border_palette[idx % len(border_palette)],
            }
        )

    return rows


def render_badge(text: str, badge_type: str) -> str:
    """Generates styled HTML badge for Anomaly, Drift, Risk, or QA Status."""
    if badge_type == "HIGH" or text in ["HIGH", "CRITICAL", "FAIL"]:
        return f'<span style="background:#FEE2E2; color:#DC2626; padding:3px 10px; border-radius:6px; font-weight:700; font-size:11px; display:inline-block;">{text}</span>'
    elif badge_type == "MEDIUM" or text in ["MEDIUM", "HOLD", "PENDING"]:
        return f'<span style="background:#FEF3C7; color:#D97706; padding:3px 10px; border-radius:6px; font-weight:700; font-size:11px; display:inline-block;">{text}</span>'
    elif badge_type == "LOW" or text in ["LOW", "PASS"]:
        return f'<span style="background:#DCFCE7; color:#16A34A; padding:3px 10px; border-radius:6px; font-weight:700; font-size:11px; display:inline-block;">{text}</span>'
    return f"<span>{text}</span>"


def render_priority_table(df: Optional[pd.DataFrame] = None):
    """
    Renders the Priority Components card and table with interactive REVIEW buttons.
    """
    st.markdown(
        """
        <style>
        .priority-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 16px 20px 8px 20px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
            margin-top: 14px;
        }
        .priority-title {
            font-size: 14px;
            font-weight: 800;
            letter-spacing: 0.5px;
            color: #0F172A;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            gap: 8px;
            padding-top: 6px;
        }
        .table-header-row {
            display: flex;
            align-items: center;
            padding: 10px 14px;
            background: #F8FAFC;
            border-radius: 8px;
            font-size: 11px;
            font-weight: 700;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }
        .pagination-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 6px 4px 6px;
            font-size: 12px;
            color: #64748B;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Card Container Header
    head_col1, head_col2, head_col3 = st.columns([3, 1.2, 0.8])
    with head_col1:
        st.markdown(
            """
            <div class="priority-title">
                <span style="color:#EF4444; font-size:18px; line-height:1;">🔔</span> PRIORITY COMPONENTS
            </div>
            """,
            unsafe_allow_html=True,
        )
    with head_col2:
        risk_filter = st.selectbox(
            "Filter Risk",
            ["All Risk Levels", "High / Critical Only", "Medium Risk Only"],
            label_visibility="collapsed",
            key="priority_risk_filter",
        )
    with head_col3:
        view_all = st.button("View All", key="btn_view_all", use_container_width=True)

    if view_all or st.session_state.get("show_dataset_browser", False):
        st.session_state.show_dataset_browser = True
        render_dataset_inspector_box()

    # Table Column Headers
    st.markdown(
        """
        <div class="table-header-row">
            <div style="flex:1.4;">Component ID</div>
            <div style="flex:1.0;">Lot ID</div>
            <div style="flex:1.2;">Anomaly</div>
            <div style="flex:1.2;">Drift</div>
            <div style="flex:1.2;">Risk Score</div>
            <div style="flex:1.2;">Risk Level</div>
            <div style="flex:1.4;">QA Status</div>
            <div style="flex:1.6; text-align:right; padding-right:25px;">Action</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    all_rows = get_real_priority_rows(df)

    # Filter rows
    if risk_filter == "High / Critical Only":
        rows = [r for r in all_rows if r["risk_level"] in ["HIGH", "CRITICAL"]]
    elif risk_filter == "Medium Risk Only":
        rows = [r for r in all_rows if r["risk_level"] == "MEDIUM"]
    else:
        rows = all_rows

    display_rows = rows[:4]  # Page 1 displays top 4 priority components

    for idx, r in enumerate(display_rows):
        cid = r["component_id"]
        lot = r["lot_id"]
        score = r["risk_score"]
        score_color = "#DC2626" if score >= 70 else "#D97706"
        border_col = r["border_color"]

        # Grid row
        r_cols = st.columns([1.4, 1.0, 1.2, 1.2, 1.2, 1.2, 1.4, 1.2, 0.4])

        with r_cols[0]:
            st.markdown(
                f"""
                <div style="border-left: 3px solid {border_col}; padding-left: 10px; font-weight:700; color:#0F172A; font-size:13px; line-height:36px;">
                    {cid}
                </div>
                """,
                unsafe_allow_html=True,
            )
        with r_cols[1]:
            st.markdown(f"<div style='line-height:36px; color:#334155; font-weight:600;'>{lot}</div>", unsafe_allow_html=True)
        with r_cols[2]:
            st.markdown(f"<div style='line-height:36px;'>{render_badge(r['anomaly'], r['anomaly'])}</div>", unsafe_allow_html=True)
        with r_cols[3]:
            st.markdown(f"<div style='line-height:36px;'>{render_badge(r['drift'], r['drift'])}</div>", unsafe_allow_html=True)
        with r_cols[4]:
            st.markdown(f"<div style='line-height:36px; font-weight:800; color:{score_color}; font-size:14px;'>{score}</div>", unsafe_allow_html=True)
        with r_cols[5]:
            st.markdown(f"<div style='line-height:36px;'>{render_badge(r['risk_level'], r['risk_level'])}</div>", unsafe_allow_html=True)
        with r_cols[6]:
            st.markdown(f"<div style='line-height:36px;'>{render_badge(r['qa_status'], r['qa_status'])}</div>", unsafe_allow_html=True)
        with r_cols[7]:
            if st.button(f"👁 REVIEW", key=f"review_{cid}_{idx}", use_container_width=True):
                st.session_state.selected_component = r["backend_id"]
                st.session_state.selected_display_id = cid
                st.session_state.selected_lot_id = lot
                st.rerun()
        with r_cols[8]:
            st.markdown("<div style='line-height:36px; color:#94A3B8; text-align:center;'>⋮</div>", unsafe_allow_html=True)

    # Footer & Pagination
    st.markdown(
        f"""
        <div class="pagination-container">
            <div>Showing 1 to {len(display_rows)} of {len(rows)} priority components</div>
            <div style="font-weight:700; color:#1D63FF;">
                <span style="color:#94A3B8; margin-right:12px; cursor:pointer;">&lt;</span>
                <span style="background:#1D63FF; color:#FFFFFF; padding:4px 10px; border-radius:6px; margin-right:6px;">1</span>
                <span style="color:#64748B; margin-right:8px; cursor:pointer;">2</span>
                <span style="color:#64748B; margin-right:8px; cursor:pointer;">3</span>
                <span style="color:#94A3B8; margin-right:8px; cursor:pointer;">&gt;</span>
                <span style="color:#94A3B8; cursor:pointer;">&gt;&gt;</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # If a component has been selected for REVIEW, render the Live Inspection Drawer
    if st.session_state.get("selected_component"):
        render_component_inspection_drawer()


def render_dataset_inspector_box():
    """Renders a quick component lookup selector from the actual raw dataset."""
    st.markdown(
        """
        <div style="background:#F1F5F9; border:1px solid #CBD5E1; border-radius:10px; padding:12px; margin-bottom:12px;">
            <div style="font-size:12px; font-weight:700; color:#334155; margin-bottom:6px;">
                📂 DATASET COMPONENT INSPECTOR (Raw Dataset: burnin_data_wide.csv)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c_sel, c_btn, c_close = st.columns([3, 1, 1])
    with c_sel:
        engine = get_engine()
        all_ids = engine.raw_df["component_id"].tolist() if engine.raw_df is not None else ["C_00001", "C_00009"]
        chosen_id = st.selectbox("Select Component from Dataset:", all_ids, key="dataset_comp_selector")
    with c_btn:
        if st.button("Inspect Live", key="btn_inspect_live", type="primary", use_container_width=True):
            st.session_state.selected_component = chosen_id
            st.session_state.selected_display_id = chosen_id
            st.rerun()
    with c_close:
        if st.button("Hide Browser", key="btn_hide_browser", use_container_width=True):
            st.session_state.show_dataset_browser = False
            st.rerun()


def render_component_inspection_drawer():
    """
    Renders an in-depth component investigation panel connected directly to backend analyze_component().
    Clearly distinguishes SkyNex AI Recommendation from Human QA Engineer Decision.
    """
    comp_id = st.session_state.selected_component
    disp_id = st.session_state.get("selected_display_id", comp_id)
    db = QADatabase()

    st.markdown("---")
    st.markdown(
        f"""
        <div style="background:#F8FAFC; border:2px solid #1D63FF; border-radius:12px; padding:18px; margin-top:10px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div style="font-size:16px; font-weight:800; color:#0F172A;">
                    🔍 COMPONENT INVESTIGATION: <span style="color:#1D63FF;">{disp_id}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        data = analyze_component(comp_id)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Anomaly Score", f"{data['anomaly_score']:.1f}/100", delta="Module A Flagged" if data['anomaly_status'] else "Normal")
        with c2:
            st.metric("Drift Rate", f"{data['drift_rate']:.4f}/hr", delta="Excessive Drift" if data['drift_status'] else "Stable")
        with c3:
            st.metric("Predicted 168h", f"{data['predicted_168h']:.2f} µA")
        with c4:
            st.metric("Risk Score & Level", f"{data['risk_score']:.1f} ({data['risk_level']})")

        st.markdown(f"**Root-Cause Engineering Explanation:**")
        st.info(data["explanation"])

        # Clearly separated AI Recommendation
        st.markdown("### 🤖 SkyNex AI Recommendation")
        ai_rec = data["recommendation"]
        badge_color = "#DC2626" if ai_rec == "REJECT" else ("#D97706" if ai_rec in ["RETEST", "EXTEND_BURN_IN"] else "#16A34A")
        st.markdown(
            f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:10px 14px; margin-bottom:12px; display:flex; align-items:center; gap:10px;">
                <span style="font-size:12px; font-weight:700; color:#64748B;">Automated Action:</span>
                <span style="font-weight:800; font-size:14px; color:{badge_color};">{ai_rec}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Clearly separated Human QA Engineer Decision & Audit Trail
        st.markdown("### 👨‍🔬 QA Engineer Decision (Human-in-the-Loop)")
        
        # Check if already reviewed
        existing_dec = db.get_latest_decision(comp_id)
        if existing_dec:
            st.success(f"**Existing Recorded Decision**: `{existing_dec['decision']}` by `{existing_dec['engineer_id']}` on `{existing_dec['timestamp']}`\n\n*Remarks*: {existing_dec['notes']}")

        remarks_input = st.text_input(
            "QA Engineer Inspection Remarks / Notes:",
            value=existing_dec['notes'] if existing_dec else "",
            key=f"remarks_input_{comp_id}",
            placeholder="Enter engineering rationale for PASS / HOLD / FAIL...",
        )

        qa_col1, qa_col2, qa_col3, qa_col4 = st.columns([1.5, 1.5, 1.5, 1.5])
        with qa_col1:
            if st.button("✅ Record PASS", key=f"btn_pass_{comp_id}", type="primary", use_container_width=True):
                db.record_decision(create_decision(comp_id, "PASS", DEFAULT_ENGINEER_ID, remarks_input or "Component verified healthy."))
                st.success(f"Recorded PASS decision for {disp_id}")
                st.rerun()
        with qa_col2:
            if st.button("⏸ Record HOLD", key=f"btn_hold_{comp_id}", use_container_width=True):
                db.record_decision(create_decision(comp_id, "HOLD", DEFAULT_ENGINEER_ID, remarks_input or "Held for extended observation."))
                st.warning(f"Recorded HOLD decision for {disp_id}")
                st.rerun()
        with qa_col3:
            if st.button("❌ Record FAIL", key=f"btn_fail_{comp_id}", use_container_width=True):
                db.record_decision(create_decision(comp_id, "FAIL", DEFAULT_ENGINEER_ID, remarks_input or "Component rejected."))
                st.error(f"Recorded FAIL decision for {disp_id}")
                st.rerun()
        with qa_col4:
            if st.button("✖ Close Panel", key="btn_close_drawer", use_container_width=True):
                st.session_state.selected_component = None
                st.rerun()

    except Exception as e:
        st.error(f"Error loading component analytics: {e}")
