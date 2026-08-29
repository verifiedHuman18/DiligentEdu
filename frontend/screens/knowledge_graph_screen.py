"""Interactive Concept-Level Knowledge Graph / Knowledge Map Screen (Phases 1-31).

Provides intra-chapter concept mapping, interactive neural network visualization,
color-coded mastery states, unattempted concept isolation, and one-click learning actions.
"""

import json
import logging
import textwrap
from typing import Any, Dict, Optional

import streamlit as st
import streamlit.components.v1 as components

from backend.analytics.knowledge_graph import (
    get_available_knowledge_map_chapters,
    get_chapter_knowledge_graph,
)
from frontend.components.navigation import render_back_to_home
from frontend.state import get_student_class_level

logger = logging.getLogger(__name__)


def _generate_interactive_graph_html(graph_data: Dict[str, Any], theme_mode: str = "dark") -> str:
    """Generates a clean high-tech interactive SVG/Canvas graph visualization with glowing pathways, tier headers, and boundary-aware tooltips."""
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)

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
        /* Authoritative Single Viewport for Graph & Background - High-Tech Slate Glass */
        .graph-viewport {{
            position: relative;
            width: 100%;
            height: 100%;
            min-height: 560px;
            background: radial-gradient(circle at 10% 20%, rgba(14, 165, 233, 0.07) 0%, transparent 40%),
                        radial-gradient(circle at 90% 80%, rgba(99, 102, 241, 0.07) 0%, transparent 40%),
                        #090d16;
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 16px 36px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }}
        /* Fixed Decorative Viewport Background - Uniform High-Tech Grid */
        .graph-background {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            background-position: 0 0;
            background-image:
                radial-gradient(rgba(148, 163, 184, 0.22) 1.2px, transparent 1.2px),
                linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
            background-size: 32px 32px;
            pointer-events: none;
            z-index: 1;
        }}
        /* Tier Column Guides */
        .tier-guide-layer {{
            position: absolute;
            inset: 0;
            display: flex;
            pointer-events: none;
            z-index: 1;
        }}
        .tier-col {{
            flex: 1;
            border-right: 1px dashed rgba(148, 163, 184, 0.08);
            padding-top: 14px;
            text-align: center;
        }}
        .tier-col:last-child {{ border-right: none; }}
        .tier-col-label {{
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1px;
            text-transform: uppercase;
            color: rgba(148, 163, 184, 0.45);
            background: rgba(15, 23, 42, 0.7);
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.12);
        }}
        svg#graph-svg {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            z-index: 2;
            background: transparent;
        }}
        /* Edge Connections with Flow Animation */
        .edge-line {{
            fill: none;
            stroke: rgba(148, 163, 184, 0.35);
            stroke-width: 2;
            stroke-dasharray: 6 4;
            animation: flowDash 30s linear infinite;
            transition: stroke 0.25s, stroke-width 0.25s, filter 0.25s, opacity 0.25s;
        }}
        .edge-line.highlighted {{
            stroke: #38bdf8 !important;
            stroke-width: 3.5 !important;
            stroke-dasharray: none;
            filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.85));
            opacity: 1 !important;
        }}
        .edge-line.dimmed {{
            opacity: 0.15;
        }}
        @keyframes flowDash {{
            to {{ stroke-dashoffset: -1000; }}
        }}
        .node-group {{
            cursor: pointer;
            transition: opacity 0.25s, transform 0.2s;
        }}
        .node-group.dimmed {{
            opacity: 0.25;
        }}
        .node-group.focused .node-card {{
            stroke-width: 3.5 !important;
            filter: drop-shadow(0 0 18px rgba(56, 189, 248, 0.95)) !important;
        }}
        .node-card {{
            rx: 12;
            ry: 12;
            transition: stroke-width 0.2s, filter 0.2s, fill 0.2s, transform 0.2s;
        }}
        /* Strong Concept Node */
        .node-strong .node-card {{
            fill: #064e3b;
            stroke: #10b981;
            stroke-width: 2;
            filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.45));
        }}
        .node-strong:hover .node-card {{
            stroke-width: 3;
            filter: drop-shadow(0 0 16px rgba(16, 185, 129, 0.85));
            fill: #065f46;
        }}
        /* Moderate Concept Node */
        .node-moderate .node-card {{
            fill: #451a03;
            stroke: #f59e0b;
            stroke-width: 2;
            filter: drop-shadow(0 0 8px rgba(245, 158, 11, 0.45));
        }}
        .node-moderate:hover .node-card {{
            stroke-width: 3;
            filter: drop-shadow(0 0 16px rgba(245, 158, 11, 0.85));
            fill: #592405;
        }}
        /* Weak Concept Node */
        .node-weak .node-card {{
            fill: #450a0a;
            stroke: #ef4444;
            stroke-width: 2;
            filter: drop-shadow(0 0 10px rgba(239, 68, 68, 0.6));
        }}
        .node-weak:hover .node-card {{
            stroke-width: 3;
            filter: drop-shadow(0 0 18px rgba(239, 68, 68, 0.9));
            fill: #5c0e0e;
        }}
        /* Unattempted Concept Node */
        .node-unattempted .node-card {{
            fill: #1e293b;
            stroke: #64748b;
            stroke-width: 1.5;
            stroke-dasharray: 4 2;
        }}
        .node-unattempted:hover .node-card {{
            stroke-width: 2.5;
            stroke: #94a3b8;
            stroke-dasharray: none;
            filter: drop-shadow(0 0 12px rgba(148, 163, 184, 0.65));
            fill: #293548;
        }}
        svg text {{
            fill: #ffffff !important;
        }}
        .node-text-title {{
            font-size: 11.5px;
            font-weight: 700;
            fill: #ffffff !important;
            pointer-events: none;
        }}
        .node-text-sub {{
            font-size: 9.5px;
            font-weight: 600;
            fill: #94a3b8 !important;
            pointer-events: none;
        }}
        .node-text-mastery {{
            font-size: 11px;
            font-weight: 800;
            pointer-events: none;
        }}
        .node-tier-badge {{
            font-size: 9px;
            font-weight: 700;
            fill: #cbd5e1 !important;
            opacity: 0.85;
            pointer-events: none;
        }}
        /* Precision Tooltip */
        .tooltip {{
            position: absolute;
            background: rgba(15, 23, 42, 0.97);
            border: 1px solid rgba(56, 189, 248, 0.45);
            backdrop-filter: blur(14px);
            padding: 12px 16px;
            border-radius: 10px;
            font-size: 11.5px;
            color: #f8fafc;
            pointer-events: none;
            box-shadow: 0 14px 32px rgba(0, 0, 0, 0.75), 0 0 16px rgba(56, 189, 248, 0.25);
            display: none;
            z-index: 1000;
            width: 270px;
            opacity: 0;
            transition: opacity 0.15s ease-out;
        }}
        .tooltip.visible {{
            display: block;
            opacity: 1;
        }}
        .legend-bar {{
            position: absolute;
            bottom: 12px;
            left: 14px;
            display: flex;
            gap: 14px;
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.12);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            backdrop-filter: blur(6px);
            z-index: 5;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
            color: #cbd5e1;
        }}
        .dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }}
        .dot-strong {{ background: #10b981; box-shadow: 0 0 6px #10b981; }}
        .dot-moderate {{ background: #f59e0b; box-shadow: 0 0 6px #f59e0b; }}
        .dot-weak {{ background: #ef4444; box-shadow: 0 0 6px #ef4444; }}
        .dot-unatt {{ background: #64748b; }}
    </style>
    </head>
    <body>
    <div id="graph-viewport" class="graph-viewport">
        <div class="graph-background"></div>

        <div class="tier-guide-layer">
            <div class="tier-col"><span class="tier-col-label">Tier 1 · Foundations</span></div>
            <div class="tier-col"><span class="tier-col-label">Tier 2 · Core Mechanisms</span></div>
            <div class="tier-col"><span class="tier-col-label">Tier 3 · Advanced Analysis</span></div>
            <div class="tier-col"><span class="tier-col-label">Tier 4 · Systems & Synthesis</span></div>
        </div>

        <svg id="graph-svg" viewBox="0 0 1160 480" preserveAspectRatio="xMidYMid meet">
            <defs>
                <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="rgba(148, 163, 184, 0.6)" />
                </marker>
                <marker id="arrow-active" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#38bdf8" />
                </marker>
            </defs>
            <g id="edges-layer"></g>
            <g id="nodes-layer"></g>
        </svg>

        <div class="legend-bar">
            <div class="legend-item"><span class="dot dot-strong"></span> Strong (&ge;80%)</div>
            <div class="legend-item"><span class="dot dot-moderate"></span> Moderate (60-79%)</div>
            <div class="legend-item"><span class="dot dot-weak"></span> Weak (&lt;60%)</div>
            <div class="legend-item"><span class="dot dot-unatt"></span> Unattempted</div>
            <div style="margin-left: 10px; color: #94a3b8; font-size: 10px;">💡 Click any node to focus · Hover for details</div>
        </div>

        <div id="tooltip" class="tooltip"></div>
    </div>

    <script>
        const nodes = {nodes_json};
        const edges = {edges_json};

        const nodeMap = {{}};
        nodes.forEach(n => {{ nodeMap[n.id] = n; }});

        const graphViewport = document.getElementById('graph-viewport');
        const svg = document.getElementById('graph-svg');
        const edgesLayer = document.getElementById('edges-layer');
        const nodesLayer = document.getElementById('nodes-layer');
        const tooltip = document.getElementById('tooltip');
        let focusedNodeId = null;

        // Draw Directed Edges with Smooth Bezier Curves
        edges.forEach(e => {{
            const s = nodeMap[e.source];
            const t = nodeMap[e.target];
            if (!s || !t) return;

            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            const sx = s.pos_x + 190, sy = s.pos_y + 32;
            const tx = t.pos_x - 4, ty = t.pos_y + 32;

            const dx = tx - sx;
            const cx1 = sx + dx * 0.45;
            const cy1 = sy;
            const cx2 = tx - dx * 0.45;
            const cy2 = ty;

            const d = `M ${{sx}} ${{sy}} C ${{cx1}} ${{cy1}}, ${{cx2}} ${{cy2}}, ${{tx}} ${{ty}}`;
            path.setAttribute('d', d);
            path.setAttribute('class', 'edge-line');
            path.setAttribute('fill', 'none');
            path.setAttribute('marker-end', 'url(#arrow)');
            path.setAttribute('data-source', e.source);
            path.setAttribute('data-target', e.target);
            edgesLayer.appendChild(path);
        }});

        // Function: Position Tooltip
        function showNodeTooltip(nodeElem, n) {{
            const containerRect = graphViewport.getBoundingClientRect();
            const nodeRect = nodeElem.getBoundingClientRect();

            const mStr = n.mastery !== null ? `${{Math.round(n.mastery)}}% (${{n.status.toUpperCase()}})` : 'Unattempted (No quiz taken)';
            const statusColor = n.status === 'strong' ? '#34d399' : (n.status === 'moderate' ? '#fbbf24' : (n.status === 'weak' ? '#f87171' : '#94a3b8'));

            tooltip.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <span style="font-weight:700; color:#38bdf8; font-size:12.5px;">${{n.name}}</span>
                    <span style="font-size:9.5px; font-weight:800; color:${{statusColor}}; text-transform:uppercase; border:1px solid ${{statusColor}}; padding:1px 6px; border-radius:8px;">${{n.status}}</span>
                </div>
                <div style="color:#cbd5e1; font-size:11px; margin-bottom:8px; line-height:1.4;">${{n.description}}</div>
                <div style="border-top:1px solid rgba(255,255,255,0.12); padding-top:6px; font-size:10.5px; display:flex; justify-content:space-between; color:#ffffff;">
                    <span><strong>Mastery:</strong> ${{mStr}}</span>
                    <span><strong>Assessed:</strong> ${{n.attempts}} (${{n.correct}} ✓)</span>
                </div>
            `;

            tooltip.style.display = 'block';
            const tipWidth = 270;
            const tipHeight = tooltip.offsetHeight || 105;

            const nodeCenterX = (nodeRect.left + nodeRect.right) / 2 - containerRect.left;
            let left = nodeCenterX - (tipWidth / 2);

            if (left < 10) left = 10;
            if (left + tipWidth > containerRect.width - 10) {{
                left = containerRect.width - tipWidth - 10;
            }}

            const nodeTopY = nodeRect.top - containerRect.top;
            const nodeBottomY = nodeRect.bottom - containerRect.top;
            let top = nodeTopY - tipHeight - 10;

            if (top < 10) {{
                top = nodeBottomY + 10; // Flip below
            }}

            tooltip.style.left = Math.round(left) + 'px';
            tooltip.style.top = Math.round(top) + 'px';
            tooltip.classList.add('visible');
        }}

        function hideNodeTooltip() {{
            tooltip.classList.remove('visible');
            tooltip.style.display = 'none';
        }}

        // Draw Nodes
        nodes.forEach(n => {{
            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            g.setAttribute('class', `node-group node-${{n.status}}`);
            g.setAttribute('transform', `translate(${{n.pos_x}}, ${{n.pos_y}})`);
            g.setAttribute('data-id', n.id);
            g.setAttribute('data-status', n.status);
            g.setAttribute('data-tier', n.tier || 1);

            const card = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            card.setAttribute('class', 'node-card');
            card.setAttribute('width', '190');
            card.setAttribute('height', '64');

            // Tier pill badge
            const tierText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            tierText.setAttribute('class', 'node-tier-badge');
            tierText.setAttribute('x', '178');
            tierText.setAttribute('y', '20');
            tierText.setAttribute('text-anchor', 'end');
            tierText.textContent = `T${{n.tier || 1}}`;

            // Node Title
            const title = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            title.setAttribute('class', 'node-text-title');
            title.setAttribute('x', '12');
            title.setAttribute('y', '26');
            title.setAttribute('style', 'fill: #ffffff !important;');
            const dispName = n.name.length > 21 ? n.name.substring(0, 20) + '…' : n.name;
            title.textContent = dispName;

            // Subtitle / Section
            const sub = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            sub.setAttribute('class', 'node-text-sub');
            sub.setAttribute('x', '12');
            sub.setAttribute('y', '48');
            sub.setAttribute('style', 'fill: #94a3b8 !important;');
            sub.textContent = n.section ? `Sec ${{n.section}}` : 'Core Concept';

            // Mastery badge
            const mastery = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            mastery.setAttribute('class', 'node-text-mastery');
            mastery.setAttribute('x', '178');
            mastery.setAttribute('y', '48');
            mastery.setAttribute('text-anchor', 'end');

            if (n.status === 'unattempted') {{
                mastery.textContent = '○ New';
                mastery.setAttribute('style', 'fill: #94a3b8 !important;');
            }} else {{
                mastery.textContent = `${{Math.round(n.mastery)}}%`;
                mastery.setAttribute('style', `fill: ${{n.status === 'strong' ? '#34d399' : (n.status === 'moderate' ? '#fbbf24' : '#f87171')}} !important;`);
            }}

            g.appendChild(card);
            g.appendChild(tierText);
            g.appendChild(title);
            g.appendChild(sub);
            g.appendChild(mastery);

            // Hover interactions: isolate & highlight connected learning pathway
            g.addEventListener('mouseenter', () => {{
                const connectedNodeIds = new Set([n.id]);

                document.querySelectorAll('.edge-line').forEach(el => {{
                    const s = el.getAttribute('data-source');
                    const t = el.getAttribute('data-target');
                    if (s === n.id || t === n.id) {{
                        el.classList.add('highlighted');
                        el.classList.remove('dimmed');
                        el.setAttribute('marker-end', 'url(#arrow-active)');
                        connectedNodeIds.add(s);
                        connectedNodeIds.add(t);
                    }} else {{
                        el.classList.add('dimmed');
                        el.classList.remove('highlighted');
                    }}
                }});

                // Dim non-connected nodes
                document.querySelectorAll('.node-group').forEach(ng => {{
                    if (connectedNodeIds.has(ng.getAttribute('data-id'))) {{
                        ng.classList.remove('dimmed');
                    }} else {{
                        ng.classList.add('dimmed');
                    }}
                }});

                showNodeTooltip(g, n);
            }});

            g.addEventListener('mouseleave', () => {{
                document.querySelectorAll('.edge-line').forEach(el => {{
                    el.classList.remove('highlighted', 'dimmed');
                    el.setAttribute('marker-end', 'url(#arrow)');
                }});
                document.querySelectorAll('.node-group').forEach(ng => {{
                    ng.classList.remove('dimmed');
                }});
                hideNodeTooltip();
            }});

            // Click interaction: Focus node
            g.addEventListener('click', () => {{
                document.querySelectorAll('.node-group').forEach(ng => ng.classList.remove('focused'));
                if (focusedNodeId === n.id) {{
                    focusedNodeId = null;
                }} else {{
                    focusedNodeId = n.id;
                    g.classList.add('focused');
                }}
            }});

            nodesLayer.appendChild(g);
        }});

        window.addEventListener('resize', hideNodeTooltip);
    </script>
    </body>
    </html>
    """
    return html_code


def render_knowledge_graph_screen(
    student_id: str = "student_001",
    user_api_key: Optional[str] = None,
) -> None:
    """Renders the Interactive Concept-Level Knowledge Graph screen."""
    render_back_to_home("knowledge_graph")

    from frontend.state import get_student_subject

    class_level = get_student_class_level()
    subject = get_student_subject()

    st.write("")
    header_html = textwrap.dedent("""\
<div class="section-header-bar">
    <div>
        <h3 style="margin:0; font-size: 1.45rem; font-weight: 700; color: var(--on-surface);">
             Knowledge Map
        </h3>
        <div class="section-subtitle-text">
            Explore deep concept-level dependency maps, assess mastery across subtopics, and target weak areas with one-click practice.
        </div>
    </div>
</div>
""")
    st.markdown(header_html, unsafe_allow_html=True)
    st.write("")

    # Available chapters for this class and subject
    avail_chapters = get_available_knowledge_map_chapters(class_level=class_level, subject=subject)
    if not avail_chapters:
        st.warning("No registered concept maps found.")
        return

    chapter_options = [ch["chapter"] for ch in avail_chapters]

    # Clean chapter selector
    default_idx = 0
    req_ch = st.session_state.get("selected_graph_chapter")
    if req_ch and req_ch in chapter_options:
        default_idx = chapter_options.index(req_ch)

    selected_chapter = st.selectbox(
        f"Select Chapter to Map ({subject})",
        options=chapter_options,
        index=default_idx,
        key=f"knowledge_graph_chapter_select_{subject}",
        help="Choose any NCERT chapter to view its internal concept hierarchy and mastery.",
    )

    # Fetch knowledge graph data for selected chapter, subject, and student
    graph_data = get_chapter_knowledge_graph(
        student_id=student_id,
        class_level=class_level,
        chapter_name=selected_chapter,
        subject=subject,
    )

    st.write("")

    # Chapter Mastery Progress Bar HUD
    total_c = graph_data.get("total_concepts", len(graph_data.get("nodes", [])))
    strong_c = graph_data.get("strong_count", 0)
    mod_c = graph_data.get("moderate_count", 0)
    weak_c = graph_data.get("weak_count", 0)
    unatt_c = graph_data.get("unattempted_count", 0)
    overall_m = graph_data.get("overall_mastery")

    pct_strong = (strong_c / total_c * 100) if total_c > 0 else 0
    pct_mod = (mod_c / total_c * 100) if total_c > 0 else 0
    pct_weak = (weak_c / total_c * 100) if total_c > 0 else 0
    pct_unatt = (unatt_c / total_c * 100) if total_c > 0 else 100

    mastery_badge = (
        f"{overall_m:.1f}% Active Mastery" if overall_m is not None else "Unassessed Chapter"
    )

    st.markdown(
        f"""
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 10px; padding: 10px 16px; margin-bottom: 12px; display: flex; flex-direction: column; gap: 6px;">
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.82rem; font-weight: 700; color: var(--on-surface);">
                <span>📊 Curriculum Coverage & Mastery Index</span>
                <span style="color: #38bdf8; font-weight: 800;">{mastery_badge} ({total_c} Subtopics Registered)</span>
            </div>
            <div style="width: 100%; height: 8px; border-radius: 4px; overflow: hidden; display: flex; background: #1e293b;">
                <div style="width: {pct_strong}%; background: #10b981; transition: width 0.4s;"></div>
                <div style="width: {pct_mod}%; background: #f59e0b; transition: width 0.4s;"></div>
                <div style="width: {pct_weak}%; background: #ef4444; transition: width 0.4s;"></div>
                <div style="width: {pct_unatt}%; background: #475569; transition: width 0.4s;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Interactive Graph Visualization Component
    graph_html = _generate_interactive_graph_html(graph_data)
    components.html(graph_html, height=580, scrolling=False)

    st.write("")

    # Concept Inspector & Target Practice removed per user request
