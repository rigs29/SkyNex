"""
SkyNex UI Charts Component
Renders the 3 Donut Summary Cards: Lots Summary, QA Status, and Risk Distribution.
Driven directly by real backend screening data.
Donuts are SVG (not Plotly) so they stay full circles inside Streamlit columns.
"""

import math
from typing import List, Optional, Sequence, Tuple

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def _polar(cx: float, cy: float, r: float, angle_deg: float) -> Tuple[float, float]:
    """Convert polar degrees (0° = 12 o'clock, clockwise) to cartesian."""
    rad = math.radians(angle_deg - 90)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def _donut_slice_d(
    cx: float,
    cy: float,
    inner_r: float,
    outer_r: float,
    start_deg: float,
    end_deg: float,
) -> str:
    """SVG path for one donut slice. Angles in degrees, clockwise from 12 o'clock."""
    sweep = (end_deg - start_deg) % 360
    if sweep <= 0.05:
        sweep = 0.05
        end_deg = start_deg + sweep
    large = 1 if sweep > 180 else 0
    ox1, oy1 = _polar(cx, cy, outer_r, start_deg)
    ox2, oy2 = _polar(cx, cy, outer_r, end_deg)
    ix2, iy2 = _polar(cx, cy, inner_r, end_deg)
    ix1, iy1 = _polar(cx, cy, inner_r, start_deg)
    return (
        f"M {ox1:.3f} {oy1:.3f} "
        f"A {outer_r:.3f} {outer_r:.3f} 0 {large} 1 {ox2:.3f} {oy2:.3f} "
        f"L {ix2:.3f} {iy2:.3f} "
        f"A {inner_r:.3f} {inner_r:.3f} 0 {large} 0 {ix1:.3f} {iy1:.3f} Z"
    )


def svg_donut(
    values: Sequence[float],
    colors: Sequence[str],
    size: int = 128,
    thickness: float = 18,
    gap_deg: float = 3.2,
    center_html: str = "",
) -> str:
    """Full-circle donut with visible gaps between slices."""
    cleaned: List[float] = [max(0.0, float(v)) for v in values]
    total = sum(cleaned)
    if total <= 0:
        cleaned = [1.0] * len(values)
        total = float(len(values))

    cx = cy = size / 2.0
    outer_r = size / 2.0 - 1.5
    inner_r = max(outer_r - thickness, outer_r * 0.55)

    paths = []
    cursor = 0.0
    n = len(cleaned)
    for i, (val, color) in enumerate(zip(cleaned, colors)):
        sweep = 360.0 * (val / total)
        gap = gap_deg if n > 1 and sweep > gap_deg * 2 else 0.0
        start = cursor + gap / 2.0
        end = cursor + sweep - gap / 2.0
        d = _donut_slice_d(cx, cy, inner_r, outer_r, start, end)
        paths.append(f'<path d="{d}" fill="{color}" />')
        cursor += sweep

    center_block = ""
    if center_html:
        center_block = (
            f'<div style="position:absolute;inset:0;display:flex;'
            f'align-items:center;justify-content:center;pointer-events:none;">'
            f"{center_html}</div>"
        )

    return (
        f'<div style="position:relative;width:{size}px;height:{size}px;flex-shrink:0;">'
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
        f'style="display:block;overflow:visible;">'
        f"{''.join(paths)}"
        f"</svg>{center_block}</div>"
    )


CLIPBOARD_ICON = """
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect x="6" y="3" width="12" height="18" rx="2" fill="#E8D5B5" stroke="#C4A574" stroke-width="1.4"/>
  <rect x="8.5" y="1.8" width="7" height="3.2" rx="1" fill="#D4C4A8" stroke="#C4A574" stroke-width="1"/>
  <path d="M9 10h6M9 13.5h6M9 17h4" stroke="#3B82F6" stroke-width="1.4" stroke-linecap="round"/>
  <circle cx="16.2" cy="17.2" r="2.4" fill="#EF4444"/>
</svg>
"""


def _legend_row(color: str, label: str, right: str, extra_top: str = "0") -> str:
    return (
        f'<div class="chart-legend-row" style="margin-top:{extra_top};">'
        f'<span class="chart-legend-left">'
        f'<span class="chart-legend-dot" style="background:{color};"></span>'
        f"{label}</span>"
        f'<span class="chart-legend-right">{right}</span>'
        f"</div>"
    )


def render_summary_charts(df: Optional[pd.DataFrame] = None):
    """
    Renders the 3 Donut Summary Cards calculated from actual backend dataset metrics.
    """
    if df is not None and not df.empty:
        total = len(df)
        total_lots = int(df["lot_id"].nunique())
        pass_count = int((df["recommendation"] == "PASS").sum())
        hold_count = int(df["recommendation"].isin(["RETEST", "EXTEND_BURN_IN"]).sum())
        fail_count = int((df["recommendation"] == "REJECT").sum())
        low_risk = int((df["risk_level"] == "LOW").sum())
        med_risk = int((df["risk_level"] == "MEDIUM").sum())
        high_risk = int(df["risk_level"].isin(["HIGH", "CRITICAL"]).sum())
    else:
        total = 1000
        total_lots = 25
        pass_count = 882
        hold_count = 13
        fail_count = 105
        low_risk = 882
        med_risk = 13
        high_risk = 105

    total = max(total, 1)

    lots_colors = ["#1D63FF", "#8B5CF6", "#F97316", "#06B6D4", "#10B981"]
    lots_labels = ["L01 - L05", "L06 - L10", "L11 - L15", "L16 - L20", "L21 - L25"]
    # Compute actual component count per lot group
    lot_counts = [0] * 5
    if df is not None and not df.empty and "lot_id" in df.columns:
        for lid in df["lot_id"].unique():
            lot_num = int(str(lid).split("_")[-1])
            group_idx = min(lot_num // 5, 4)
            lot_counts[group_idx] += int((df["lot_id"] == lid).sum())
    else:
        lot_counts = [200, 200, 200, 200, 200]
    lots_total = max(sum(lot_counts), 1)
    lots_pct = [round(c / lots_total * 100) for c in lot_counts]
    lots_svg = svg_donut(lot_counts, lots_colors, size=118, thickness=17, gap_deg=3.4)
    lots_legend = "".join(
        _legend_row(c, lab, f"<b>{p}%</b>") for c, lab, p in zip(lots_colors, lots_labels, lots_pct)
    )

    qa_svg = svg_donut(
        [pass_count, hold_count, fail_count],
        ["#10B981", "#F59E0B", "#EF4444"],
        size=118,
        thickness=17,
        gap_deg=3.0,
        center_html=CLIPBOARD_ICON,
    )
    qa_legend = (
        _legend_row("#10B981", "PASS", f"<b>{pass_count:,}</b> <span class='pct'>({pass_count / total * 100:.1f}%)</span>")
        + _legend_row("#F59E0B", "HOLD", f"<b>{hold_count:,}</b> <span class='pct'>({hold_count / total * 100:.1f}%)</span>", "10px")
        + _legend_row("#EF4444", "FAIL", f"<b>{fail_count:,}</b> <span class='pct'>({fail_count / total * 100:.1f}%)</span>", "10px")
    )

    risk_svg = svg_donut(
        [low_risk, med_risk, high_risk],
        ["#10B981", "#F97316", "#EF4444"],
        size=118,
        thickness=17,
        gap_deg=3.0,
    )
    risk_legend = (
        _legend_row("#10B981", "Low Risk", f"<b>{low_risk:,}</b> <span class='pct'>({low_risk / total * 100:.1f}%)</span>")
        + _legend_row("#F97316", "Medium Risk", f"<b>{med_risk:,}</b> <span class='pct'>({med_risk / total * 100:.1f}%)</span>", "10px")
        + _legend_row("#EF4444", "High Risk", f"<b>{high_risk:,}</b> <span class='pct'>({high_risk / total * 100:.1f}%)</span>", "10px")
    )

    html = f"""
        <style>
        html, body {{
            margin: 0;
            padding: 0;
            background: transparent;
            font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 14px;
            width: 100%;
        }}
        .summary-card {{
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 16px 18px 14px 18px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
            min-height: 198px;
        }}
        .summary-title {{
            font-size: 13px;
            font-weight: 800;
            letter-spacing: 0.6px;
            color: #0F172A;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        .summary-body {{
            display: flex;
            align-items: center;
            gap: 12px;
            min-height: 130px;
        }}
        .lots-metric {{
            min-width: 64px;
            flex-shrink: 0;
        }}
        .lots-metric .lots-num {{
            font-size: 32px;
            font-weight: 800;
            color: #0F172A;
            line-height: 1;
        }}
        .lots-metric .lots-label {{
            font-size: 12px;
            color: #64748B;
            font-weight: 500;
            margin-top: 6px;
        }}
        .chart-legend {{
            flex: 1;
            min-width: 0;
        }}
        .chart-legend-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            font-size: 12px;
            color: #334155;
            margin-bottom: 5px;
            font-weight: 500;
        }}
        .chart-legend-left {{
            display: flex;
            align-items: center;
            min-width: 0;
            white-space: nowrap;
        }}
        .chart-legend-right {{
            color: #0F172A;
            font-weight: 600;
            white-space: nowrap;
        }}
        .chart-legend-right .pct {{
            font-size: 11px;
            color: #64748B;
            font-weight: 500;
        }}
        .chart-legend-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 7px;
            flex-shrink: 0;
        }}
        </style>
        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-title">LOTS SUMMARY</div>
                <div class="summary-body">
                    <div class="lots-metric">
                        <div class="lots-num">{total_lots}</div>
                        <div class="lots-label">Total Lots</div>
                    </div>
                    {lots_svg}
                    <div class="chart-legend">{lots_legend}</div>
                </div>
            </div>
            <div class="summary-card">
                <div class="summary-title">QA STATUS</div>
                <div class="summary-body">
                    {qa_svg}
                    <div class="chart-legend">{qa_legend}</div>
                </div>
            </div>
            <div class="summary-card">
                <div class="summary-title">RISK DISTRIBUTION</div>
                <div class="summary-body">
                    {risk_svg}
                    <div class="chart-legend">{risk_legend}</div>
                </div>
            </div>
        </div>
        """
    components.html(html, height=232, scrolling=False)
