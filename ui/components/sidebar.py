"""
SkyNex UI Sidebar Component
Renders the dark navy sidebar with branding, navigation items, user profile, and copyright.
"""

from pathlib import Path
import streamlit as st
import base64


def get_base64_image(image_path: Path) -> str:
    """Encodes an image to base64 for reliable HTML embedding in Streamlit."""
    if image_path.exists():
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""


def render_sidebar(current_page: str = "Dashboard") -> str:
    """
    Renders the SkyNex aerospace dark navy sidebar.
    Returns the selected navigation page.
    """
    logo_path = Path("assets/skynex_logo.png")
    if not logo_path.exists():
        logo_path = Path("assets/skynex logo.jpeg")
    logo_base64 = get_base64_image(logo_path)

    with st.sidebar:
        # Custom CSS injection for sidebar styling
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] {
                background-color: #071026 !important;
                color: #FFFFFF !important;
            }
            [data-testid="stSidebar"] hr {
                border-color: rgba(255, 255, 255, 0.1) !important;
            }
            .sidebar-logo-container {
                text-align: center;
                padding-top: 10px;
                padding-bottom: 8px;
            }
            .sidebar-logo-img {
                width: 88px;
                height: 88px;
                border-radius: 50%;
                object-fit: cover;
                margin: 0 auto;
                display: block;
                box-shadow: 0 0 25px rgba(29, 99, 255, 0.4);
                border: 2px solid rgba(255, 255, 255, 0.15);
            }
            .sidebar-title {
                font-size: 24px;
                font-weight: 800;
                letter-spacing: 3px;
                margin-top: 10px;
                margin-bottom: 2px;
                color: #FFFFFF;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            }
            .sidebar-title .orange-n {
                color: #F97316;
            }
            .sidebar-title .green-x {
                color: #22C55E;
            }
            .sidebar-subtitle {
                font-size: 9px;
                font-weight: 600;
                letter-spacing: 2px;
                color: #94A3B8;
                text-transform: uppercase;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                margin-bottom: 8px;
            }
            .sidebar-subtitle::before, .sidebar-subtitle::after {
                content: '';
                display: inline-block;
                width: 20px;
                height: 1px;
                background-color: rgba(255, 255, 255, 0.2);
            }
            .sidebar-tagline {
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 1.5px;
                color: #64748B;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
            }
            .sidebar-tagline span {
                color: #94A3B8;
            }
            .user-profile-card {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                padding: 10px 14px;
                display: flex;
                align-items: center;
                gap: 12px;
                margin-top: 25px;
                margin-bottom: 12px;
            }
            .user-avatar {
                width: 36px;
                height: 36px;
                border-radius: 50%;
                background: #10B981;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                font-weight: bold;
                color: #FFFFFF;
                border: 2px solid #FFFFFF;
            }
            .user-info {
                flex: 1;
            }
            .user-name {
                font-size: 13px;
                font-weight: 700;
                color: #FFFFFF;
                line-height: 1.2;
            }
            .user-role {
                font-size: 11px;
                color: #94A3B8;
                line-height: 1.2;
            }
            .sidebar-footer {
                text-align: left;
                font-size: 11px;
                color: #64748B;
                padding-left: 4px;
                padding-bottom: 10px;
                line-height: 1.4;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Header Branding
        if logo_base64:
            st.markdown(
                f"""
                <div class="sidebar-logo-container">
                    <img src="data:image/png;base64,{logo_base64}" class="sidebar-logo-img" alt="SkyNex Logo" />
                    <div class="sidebar-title">SKY<span class="orange-n">N</span>E<span class="green-x">X</span></div>
                    <div class="sidebar-subtitle">ANOMALY DETECTION SYSTEM</div>
                    <div class="sidebar-tagline">
                        <span style="color:#F97316;">🎯 DETECT</span> | 
                        <span style="color:#10B981;">🛡️ PROTECT</span> | 
                        <span style="color:#38BDF8;">🪐 SPACE</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="sidebar-logo-container">
                    <div class="sidebar-title">SKY<span class="orange-n">N</span>E<span class="green-x">X</span></div>
                    <div class="sidebar-subtitle">ANOMALY DETECTION SYSTEM</div>
                    <div class="sidebar-tagline">
                        <span>🎯 DETECT</span> | <span>🛡️ PROTECT</span> | <span>🪐 SPACE</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Navigation Items
        nav_items = [
            ("Dashboard", "🏠", "Dashboard"),
            ("Anomaly Detection", "〰️", "Anomaly Detection"),
            ("Drift Prediction", "📈", "Drift Prediction"),
            ("Risk Assessment", "🛡️", "Risk Assessment"),
            ("Reports", "📄", "Reports"),
            ("QA Decision", "👤", "QA Decision"),
            ("Audit Trail", "📋", "Audit Trail"),
            ("Settings", "⚙️", "Settings"),
        ]

        if "nav_page" not in st.session_state:
            st.session_state.nav_page = current_page

        selected_page = st.session_state.nav_page

        for label, icon, key_name in nav_items:
            is_active = (selected_page == label)
            btn_style = "primary" if is_active else "secondary"
            if st.button(
                f"{icon}  {label}",
                key=f"nav_btn_{key_name}",
                use_container_width=True,
                type=btn_style,
            ):
                st.session_state.nav_page = label
                st.rerun()

        # QA Engineer Profile Card at bottom
        st.markdown(
            """
            <div class="user-profile-card">
                <div class="user-avatar">👨‍🔬</div>
                <div class="user-info">
                    <div class="user-name">QA Engineer</div>
                    <div class="user-role">Admin</div>
                </div>
                <div style="color:#94A3B8; font-size:12px;">▼</div>
            </div>
            <div class="sidebar-footer">
                © 2026 SkyNex<br>
                All rights reserved.
            </div>
            """,
            unsafe_allow_html=True,
        )

    return st.session_state.get("nav_page", "Dashboard")

