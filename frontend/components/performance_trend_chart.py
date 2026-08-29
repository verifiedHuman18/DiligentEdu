"""Performance Over Time and Trend Chart Component (Teacher Portal).

Renders a high-tech interactive line graph with date X-axis, percentage Y-axis,
interactive hover tooltips, and an executive trend summary card.
"""

import json
import logging
import textwrap
from typing import Any, Dict, Optional

import streamlit as st
import streamlit.components.v1 as components

from backend.analytics.performance_trend import get_student_performance_trend

logger = logging.getLogger(__name__)


def _generate_trend_chart_html(trend_data: Dict[str, Any]) -> str:
    """Generates a responsive, cyber-slate SVG line chart with interactive hover tooltips."""
    points = trend_data.get("points", [])
    trend = trend_data.get("trend", {})
    status = trend.get("status", "stagnant")

    # Determine theme accent colors based on trend status
    if status == "improving":
        line_color = "#10b981"
        line_glow = "rgba(16, 185, 129, 0.45)"
        point_fill = "#064e3b"
        point_stroke = "#34d399"
    elif status == "declining":
        line_color = "#ef4444"
        line_glow = "rgba(239, 68, 68, 0.45)"
        point_fill = "#450a0a"
        point_stroke = "#f87171"
    else:  # stagnant or insufficient
        line_color = "#f59e0b"
        line_glow = "rgba(245, 158, 11, 0.45)"
        point_fill = "#451a03"
        point_stroke = "#fbbf24"

    points_json = json.dumps(points)

    html_code = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8" />
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            background: #090d16;
            overflow: hidden;
            user-select: none;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }}
        .chart-viewport {{
            position: relative;
            width: 100%;
            height: 100%;
            min-height: 290px;
            background: radial-gradient(circle at 15% 25%, rgba(14, 165, 233, 0.05) 0%, transparent 45%),
                        radial-gradient(circle at 85% 75%, rgba(99, 102, 241, 0.05) 0%, transparent 45%),
                        #090d16;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.4);
        }}
        .chart-background {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            background-image:
                radial-gradient(rgba(148, 163, 184, 0.18) 1px, transparent 1px),
                linear-gradient(to right, rgba(255, 255, 255, 0.02) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
            background-size: 24px 24px;
            pointer-events: none;
        }}
        svg#trend-svg {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            background: transparent;
        }}
        .grid-line {{
            stroke: rgba(148, 163, 184, 0.12);
            stroke-width: 1;
            stroke-dasharray: 4 4;
        }}
        .axis-label {{
            font-size: 10px;
            font-weight: 600;
            fill: #94a3b8;
        }}
        .axis-title {{
            font-size: 9.5px;
            font-weight: 700;
            fill: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .trend-area {{
            fill: url(#areaGradient);
            opacity: 0.25;
        }}
        .trend-line {{
            fill: none;
            stroke: {line_color};
            stroke-width: 3;
            stroke-linecap: round;
            stroke-linejoin: round;
            filter: drop-shadow(0 0 8px {line_glow});
        }}
        .chart-point {{
            cursor: pointer;
            transition: transform 0.2s, r 0.2s, filter 0.2s;
        }}
        .chart-point:hover {{
            r: 7.5;
            stroke-width: 3.5;
            filter: drop-shadow(0 0 10px {line_color});
        }}
        /* Precision Tooltip */
        .tooltip {{
            position: absolute;
            background: rgba(15, 23, 42, 0.96);
            border: 1px solid rgba(56, 189, 248, 0.45);
            backdrop-filter: blur(12px);
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 11.5px;
            color: #f8fafc;
            pointer-events: none;
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.7), 0 0 14px rgba(56, 189, 248, 0.2);
            display: none;
            z-index: 1000;
            width: 220px;
            opacity: 0;
            transition: opacity 0.15s ease-out;
        }}
        .tooltip.visible {{
            display: block;
            opacity: 1;
        }}
    </style>
    </head>
    <body>
    <div id="chart-viewport" class="chart-viewport">
        <div class="chart-background"></div>

        <svg id="trend-svg" viewBox="0 0 840 280" preserveAspectRatio="none">
            <defs>
                <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="{line_color}" stop-opacity="0.45" />
                    <stop offset="100%" stop-color="{line_color}" stop-opacity="0.0" />
                </linearGradient>
            </defs>

            <!-- Y Axis Grid Lines & Labels (0% to 100%) -->
            <!-- Canvas margins: Top=30, Bottom=230, Left=60, Right=800 -->
            <!-- Height span = 200px (100% at y=30, 0% at y=230) -->
            <g id="grid-layer">
                <!-- 100% -->
                <line x1="60" y1="30" x2="800" y2="30" class="grid-line" />
                <text x="50" y="34" class="axis-label" text-anchor="end">100%</text>

                <!-- 75% -->
                <line x1="60" y1="80" x2="800" y2="80" class="grid-line" />
                <text x="50" y="84" class="axis-label" text-anchor="end">75%</text>

                <!-- 50% -->
                <line x1="60" y1="130" x2="800" y2="130" class="grid-line" />
                <text x="50" y="134" class="axis-label" text-anchor="end">50%</text>

                <!-- 25% -->
                <line x1="60" y1="180" x2="800" y2="180" class="grid-line" />
                <text x="50" y="184" class="axis-label" text-anchor="end">25%</text>

                <!-- 0% Baseline -->
                <line x1="60" y1="230" x2="800" y2="230" stroke="rgba(148, 163, 184, 0.3)" stroke-width="1.5" />
                <text x="50" y="234" class="axis-label" text-anchor="end">0%</text>
            </g>

            <g id="chart-data-layer"></g>
            <g id="x-axis-layer"></g>
        </svg>

        <div id="tooltip" class="tooltip"></div>
    </div>

    <script>
        const points = {points_json};
        const viewport = document.getElementById('chart-viewport');
        const dataLayer = document.getElementById('chart-data-layer');
        const xAxisLayer = document.getElementById('x-axis-layer');
        const tooltip = document.getElementById('tooltip');

        if (points && points.length > 0) {{
            const xMin = 80;
            const xMax = 780;
            const yTop = 30;
            const yBottom = 230;
            const yRange = yBottom - yTop; // 200px for 0..100%

            const count = points.length;
            const xStep = count > 1 ? (xMax - xMin) / (count - 1) : 0;

            const coords = points.map((p, idx) => {{
                const cx = count === 1 ? (xMin + xMax) / 2 : xMin + (idx * xStep);
                const cy = yBottom - ((Math.min(100, Math.max(0, p.performance)) / 100) * yRange);
                return {{ ...p, cx, cy }};
            }});

            // Draw connecting path & gradient area
            if (coords.length > 1) {{
                // Area path
                let areaD = `M ${{coords[0].cx}} ${{yBottom}} L ${{coords[0].cx}} ${{coords[0].cy}}`;
                for (let i = 1; i < coords.length; i++) {{
                    areaD += ` L ${{coords[i].cx}} ${{coords[i].cy}}`;
                }}
                areaD += ` L ${{coords[coords.length - 1].cx}} ${{yBottom}} Z`;

                const areaPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                areaPath.setAttribute('d', areaD);
                areaPath.setAttribute('class', 'trend-area');
                dataLayer.appendChild(areaPath);

                // Line path
                let lineD = `M ${{coords[0].cx}} ${{coords[0].cy}}`;
                for (let i = 1; i < coords.length; i++) {{
                    lineD += ` L ${{coords[i].cx}} ${{coords[i].cy}}`;
                }}

                const linePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                linePath.setAttribute('d', lineD);
                linePath.setAttribute('class', 'trend-line');
                dataLayer.appendChild(linePath);
            }}

            // Draw Points and X-Axis Labels
            coords.forEach((pt, idx) => {{
                // X-Axis Tick Label
                const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                label.setAttribute('x', pt.cx);
                label.setAttribute('y', 255);
                label.setAttribute('class', 'axis-label');
                label.setAttribute('text-anchor', 'middle');
                label.textContent = pt.date;
                xAxisLayer.appendChild(label);

                // Circle Point
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', pt.cx);
                circle.setAttribute('cy', pt.cy);
                circle.setAttribute('r', '5.5');
                circle.setAttribute('fill', '{point_fill}');
                circle.setAttribute('stroke', '{point_stroke}');
                circle.setAttribute('stroke-width', '2.5');
                circle.setAttribute('class', 'chart-point');

                // Hover interaction
                circle.addEventListener('mouseenter', (e) => {{
                    tooltip.innerHTML = `
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-weight:800; color:#38bdf8; font-size:12px;">${{pt.date}}</span>
                            <span style="font-size:10px; font-weight:700; color:#94a3b8;">${{pt.difficulty}}</span>
                        </div>
                        <div style="font-weight:700; color:#f1f5f9; font-size:11.5px; margin-bottom:6px; line-height:1.3;">${{pt.chapter}}</div>
                        <div style="border-top:1px solid rgba(255,255,255,0.12); padding-top:4px; display:flex; justify-content:space-between; font-size:11px; color:#ffffff;">
                            <span>Score: <strong>${{pt.performance}}%</strong></span>
                            <span>Correct: <strong>${{pt.score_fraction}}</strong></span>
                        </div>
                    `;

                    tooltip.style.display = 'block';
                    const rect = viewport.getBoundingClientRect();
                    const pointRect = circle.getBoundingClientRect();

                    const tipWidth = 220;
                    const tipHeight = tooltip.offsetHeight || 80;

                    let left = (pointRect.left + pointRect.right) / 2 - rect.left - (tipWidth / 2);
                    if (left < 10) left = 10;
                    if (left + tipWidth > rect.width - 10) left = rect.width - tipWidth - 10;

                    let top = pointRect.top - rect.top - tipHeight - 10;
                    if (top < 10) top = pointRect.bottom - rect.top + 10;

                    tooltip.style.left = Math.round(left) + 'px';
                    tooltip.style.top = Math.round(top) + 'px';
                    tooltip.classList.add('visible');
                }});

                circle.addEventListener('mouseleave', () => {{
                    tooltip.classList.remove('visible');
                    tooltip.style.display = 'none';
                }});

                dataLayer.appendChild(circle);
            }});
        }}
    </script>
    </body>
    </html>
    """
    return html_code


def render_performance_trend_section(
    student_id: str,
    class_level: Optional[int] = None,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> None:
    """Renders the executive Performance Over Time section in the Teacher Portal."""
    trend_data = get_student_performance_trend(
        student_id=student_id,
        class_level=class_level,
        subject=subject,
        db_path=db_path,
    )

    points = trend_data.get("points", [])
    trend = trend_data.get("trend", {})
    status = trend.get("status", "insufficient_data")
    status_label = trend.get("status_label", "⚪ Insufficient Data")
    curr_score = trend.get("current_performance", 0.0)
    prev_avg = trend.get("previous_average", 0.0)
    change_pp = trend.get("change_pct_points", 0.0)
    explanation = trend.get("explanation", "")
    n_assessments = trend.get("assessment_count", 0)

    st.markdown(
        """
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">Performance Over Time & Trend Analytics</h4>
                <div class="section-subtitle-text">Chronological assessment trajectory, OLS regression slope, and performance progression.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not trend_data.get("has_data") or len(points) == 0:
        st.info(
            f"No quiz assessment records found for this student in {subject}. "
            "As the student completes chapter quizzes, their chronological trajectory and trend line will be rendered here."
        )
        return

    # Trend Summary Card
    if status == "improving":
        card_border = "#10b981"
        badge_bg = "#064e3b"
        badge_color = "#34d399"
    elif status == "declining":
        card_border = "#ef4444"
        badge_bg = "#450a0a"
        badge_color = "#f87171"
    elif status == "stagnant":
        card_border = "#f59e0b"
        badge_bg = "#451a03"
        badge_color = "#fbbf24"
    else:
        card_border = "rgba(148, 163, 184, 0.25)"
        badge_bg = "#1e293b"
        badge_color = "#94a3b8"

    change_sign = "+" if change_pp > 0 else ""
    change_str = f"{change_sign}{change_pp:.1f} pp" if n_assessments >= 2 else "—"

    summary_html = textwrap.dedent(f"""\
<div style="background: var(--surface-container-low); border: 1px solid {card_border}; border-radius: 10px; padding: 14px 18px; margin-bottom: 14px;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 8px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="background: {badge_bg}; color: {badge_color}; border: 1px solid {card_border}; font-size: 0.82rem; font-weight: 800; padding: 3px 10px; border-radius: 8px; letter-spacing: 0.5px;">
                {status_label}
            </span>
            <span style="font-size: 0.88rem; font-weight: 600; color: var(--on-surface);">
                Performance Trajectory ({n_assessments} Assessment{"s" if n_assessments != 1 else ""})
            </span>
        </div>
        <div style="display: flex; gap: 18px; font-size: 0.84rem; color: var(--on-surface-variant); font-weight: 600;">
            <div>Latest: <strong style="color: var(--on-surface);">{curr_score}%</strong></div>
            <div>Baseline Avg: <strong style="color: var(--on-surface);">{prev_avg}%</strong></div>
            <div>Window Change: <strong style="color: {badge_color};">{change_str}</strong></div>
        </div>
    </div>
    <div style="font-size: 0.82rem; color: var(--on-surface-variant); line-height: 1.4; border-top: 1px dashed var(--outline-variant); padding-top: 8px;">
        {explanation}
    </div>
</div>
""")
    st.markdown(summary_html, unsafe_allow_html=True)

    # Line Chart Component
    chart_html = _generate_trend_chart_html(trend_data)
    components.html(chart_html, height=295, scrolling=False)
