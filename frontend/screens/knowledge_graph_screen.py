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
    """Generates a high-tech interactive SVG/Canvas graph visualization with boundary-aware tooltips and locked node coordinates."""
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    ch_title = graph_data.get("chapter", "")

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
            background: #0f172a;
            overflow: hidden;
            user-select: none;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }}
        /* Authoritative Single Viewport for Graph & Background - Seamless Continuous Dark Slate */
        .graph-viewport {{
            position: relative;
            width: 100%;
            height: 100%;
            min-height: 520px;
            background: #0f172a;
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            overflow: hidden;
        }}
        /* Fixed Decorative Viewport Background - Uniform Grid/Dots Across Full Canvas */
        .graph-background {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            background-position: 0 0;
            background-image:
                radial-gradient(rgba(148, 163, 184, 0.22) 1.2px, transparent 1.2px),
                linear-gradient(to right, rgba(255, 255, 255, 0.035) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(255, 255, 255, 0.035) 1px, transparent 1px);
            background-size: 28px 28px;
            pointer-events: none;
            z-index: 1;
        }}
        svg#graph-svg {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            z-index: 2;
            background: transparent;
        }}
        .edge-line {{
            fill: none;
            stroke: rgba(148, 163, 184, 0.38);
            stroke-width: 2;
            stroke-dasharray: 6 4;
            animation: flowDash 30s linear infinite;
            transition: stroke 0.25s, stroke-width 0.25s, filter 0.25s;
        }}
        .edge-line.highlighted {{
            fill: none;
            stroke: #38bdf8;
            stroke-width: 3.5;
            stroke-dasharray: none;
            filter: drop-shadow(0 0 6px rgba(56, 189, 248, 0.7));
        }}
        @keyframes flowDash {{
            to {{ stroke-dashoffset: -1000; }}
        }}
        .node-group {{
            cursor: pointer;
        }}
        .node-card {{
            rx: 10;
            ry: 10;
            transition: stroke-width 0.2s, filter 0.2s, fill 0.2s;
        }}
        /* Strong Concept Node */
        .node-strong .node-card {{
            fill: #064e3b;
            stroke: #10b981;
            stroke-width: 2;
            filter: drop-shadow(0 0 6px rgba(16, 185, 129, 0.45));
        }}
        .node-strong:hover .node-card {{
            stroke-width: 3;
            filter: drop-shadow(0 0 14px rgba(16, 185, 129, 0.8));
            fill: #065f46;
        }}
        /* Moderate Concept Node */
        .node-moderate .node-card {{
            fill: #451a03;
            stroke: #f59e0b;
            stroke-width: 2;
            filter: drop-shadow(0 0 6px rgba(245, 158, 11, 0.45));
        }}
        .node-moderate:hover .node-card {{
            stroke-width: 3;
            filter: drop-shadow(0 0 14px rgba(245, 158, 11, 0.8));
            fill: #592405;
        }}
        /* Weak Concept Node */
        .node-weak .node-card {{
            fill: #450a0a;
            stroke: #ef4444;
            stroke-width: 2;
            filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.55));
        }}
        .node-weak:hover .node-card {{
            stroke-width: 3;
            filter: drop-shadow(0 0 16px rgba(239, 68, 68, 0.85));
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
            filter: drop-shadow(0 0 10px rgba(148, 163, 184, 0.6));
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
            font-size: 10px;
            font-weight: 500;
            fill: #94a3b8;
            pointer-events: none;
        }}
        .node-text-mastery {{
            font-size: 10.5px;
            font-weight: 700;
            pointer-events: none;
        }}
        /* Precision Positioned Tooltip with Boundary Padding */
        .tooltip {{
            position: absolute;
            background: rgba(15, 23, 42, 0.96);
            border: 1px solid rgba(56, 189, 248, 0.4);
            backdrop-filter: blur(12px);
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 11.5px;
            color: #f8fafc;
            pointer-events: none;
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.65), 0 0 14px rgba(56, 189, 248, 0.2);
            display: none;
            z-index: 1000;
            width: 250px;
            opacity: 0;
            transition: opacity 0.15s ease-out;
        }}
        .tooltip.visible {{
            display: block;
            opacity: 1;
        }}
        .canvas-header {{
            position: absolute;
            top: 12px;
            left: 16px;
            font-size: 0.85rem;
            font-weight: 700;
            color: #94a3b8;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            z-index: 5;
        }}
        .legend-bar {{
            position: absolute;
            bottom: 12px;
            left: 16px;
            display: flex;
            gap: 14px;
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            backdrop-filter: blur(4px);
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
        <div class="canvas-header"> Intra-Chapter Concept Map · {ch_title}</div>

        <svg id="graph-svg" viewBox="0 0 1080 440" preserveAspectRatio="xMidYMid meet">
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

        // Draw Directed Edges with Smooth Bezier Curves (Strictly fill: none)
        edges.forEach(e => {{
            const s = nodeMap[e.source];
            const t = nodeMap[e.target];
            if (!s || !t) return;

            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            // Clean anchor from source right-edge to target left-edge
            const sx = s.pos_x + 180, sy = s.pos_y + 30;
            const tx = t.pos_x - 4, ty = t.pos_y + 30;

            // Curved Bezier calculation
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

        // Function: Position Tooltip relative to Node Element with Boundary Clamping
        function showNodeTooltip(nodeElem, n) {{
            const containerRect = graphViewport.getBoundingClientRect();
            const nodeRect = nodeElem.getBoundingClientRect();

            const mStr = n.mastery !== null ? `${{Math.round(n.mastery)}}% (${{n.status.toUpperCase()}})` : 'Unattempted (No quiz taken)';
            const statusColor = n.status === 'strong' ? '#34d399' : (n.status === 'moderate' ? '#fbbf24' : (n.status === 'weak' ? '#f87171' : '#94a3b8'));

            tooltip.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <span style="font-weight:700; color:#38bdf8; font-size:12px;">${{n.name}}</span>
                    <span style="font-size:9.5px; font-weight:700; color:${{statusColor}}; text-transform:uppercase;">${{n.status}}</span>
                </div>
                <div style="color:#cbd5e1; font-size:11px; margin-bottom:6px; line-height:1.4;">${{n.description}}</div>
                <div style="border-top:1px solid rgba(255,255,255,0.1); padding-top:4px; font-size:10.5px; display:flex; justify-content:space-between; color:#ffffff;">
                    <span><strong>Mastery:</strong> ${{mStr}}</span>
                    <span><strong>Assessed:</strong> ${{n.attempts}} (${{n.correct}} ✓)</span>
                </div>
            `;

            tooltip.style.display = 'block';
            const tipWidth = 250;
            const tipHeight = tooltip.offsetHeight || 96;

            // Calculate center X of node in container coordinates
            const nodeCenterX = (nodeRect.left + nodeRect.right) / 2 - containerRect.left;
            let left = nodeCenterX - (tipWidth / 2);

            // Boundary Detection: Clamp horizontal within container margins (10px)
            if (left < 10) left = 10;
            if (left + tipWidth > containerRect.width - 10) {{
                left = containerRect.width - tipWidth - 10;
            }}

            // Boundary Detection: Prefer above node; flip below if too close to top edge (< 12px)
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

            const card = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            card.setAttribute('class', 'node-card');
            card.setAttribute('width', '180');
            card.setAttribute('height', '60');

            const title = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            title.setAttribute('class', 'node-text-title');
            title.setAttribute('x', '12');
            title.setAttribute('y', '24');
            title.setAttribute('style', 'fill: #ffffff !important;');
            // Truncate title if long
            const dispName = n.name.length > 20 ? n.name.substring(0, 19) + '…' : n.name;
            title.textContent = dispName;

            const sub = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            sub.setAttribute('class', 'node-text-sub');
            sub.setAttribute('x', '12');
            sub.setAttribute('y', '44');
            sub.setAttribute('style', 'fill: #94a3b8 !important;');
            sub.textContent = n.section ? `Sec ${{n.section}}` : 'Core Concept';

            const mastery = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            mastery.setAttribute('class', 'node-text-mastery');
            mastery.setAttribute('x', '168');
            mastery.setAttribute('y', '44');
            mastery.setAttribute('text-anchor', 'end');

            if (n.status === 'unattempted') {{
                mastery.textContent = '○ New';
                mastery.setAttribute('style', 'fill: #94a3b8 !important;');
            }} else {{
                mastery.textContent = `${{Math.round(n.mastery)}}%`;
                mastery.setAttribute('style', `fill: ${{n.status === 'strong' ? '#34d399' : (n.status === 'moderate' ? '#fbbf24' : '#f87171')}} !important;`);
            }}

            g.appendChild(card);
            g.appendChild(title);
            g.appendChild(sub);
            g.appendChild(mastery);

            // Hover interactions (Client-side, 0 Streamlit reruns, 0 layout shifts)
            g.addEventListener('mouseenter', () => {{
                // Highlight connected incoming and outgoing edges
                document.querySelectorAll('.edge-line').forEach(el => {{
                    if (el.getAttribute('data-source') === n.id || el.getAttribute('data-target') === n.id) {{
                        el.classList.add('highlighted');
                        el.setAttribute('marker-end', 'url(#arrow-active)');
                    }}
                }});

                showNodeTooltip(g, n);
            }});

            g.addEventListener('mouseleave', () => {{
                document.querySelectorAll('.edge-line').forEach(el => {{
                    el.classList.remove('highlighted');
                    el.setAttribute('marker-end', 'url(#arrow)');
                }});
                hideNodeTooltip();
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
    header_html = textwrap.dedent(f"""\
<div class="section-header-bar">
    <div>
        <h3 style="margin:0; font-size: 1.45rem; font-weight: 700; color: var(--on-surface);">
             Knowledge Map — Class {class_level} · {subject}
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
        st.warning(f"No registered concept maps found for Class {class_level} {subject}.")
        return

    chapter_options = [ch["chapter"] for ch in avail_chapters]

    # Chapter selector bar
    col_sel, col_stats = st.columns([1.8, 3.2])

    with col_sel:
        # Check if a specific chapter was requested via navigation state
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

    with col_stats:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(" Strong", f"{graph_data.get('strong_count', 0)}")
        c2.metric(" Moderate", f"{graph_data.get('moderate_count', 0)}")
        c3.metric(" Weak", f"{graph_data.get('weak_count', 0)}")
        c4.metric(" Unattempted", f"{graph_data.get('unattempted_count', 0)}")

    st.write("")

    # Interactive Graph Visualization Component
    graph_html = _generate_interactive_graph_html(graph_data)
    components.html(graph_html, height=524, scrolling=False)

    st.write("")

    # Concept Inspector & Learning Action Panel
    st.markdown("####  Concept Inspector & Target Practice")
    nodes = graph_data.get("nodes", [])

    if not nodes:
        st.info("No concept nodes found for this chapter.")
        return

    node_dict = {n["name"]: n for n in nodes}
    node_names = list(node_dict.keys())

    selected_concept_name = st.selectbox(
        "Select Subtopic to Inspect & Practice:",
        options=node_names,
        key="kg_concept_inspector_select",
    )

    selected_node = node_dict.get(selected_concept_name, nodes[0])

    # Card layout for selected node
    stat_val = selected_node.get("status", "unattempted")
    if stat_val == "strong":
        badge_html = '<span style="background:#064e3b; color:#34d399; font-weight:700; padding:3px 10px; border-radius:12px; border:1px solid #10b981;"> STRONG</span>'
    elif stat_val == "moderate":
        badge_html = '<span style="background:#451a03; color:#fbbf24; font-weight:700; padding:3px 10px; border-radius:12px; border:1px solid #f59e0b;"> MODERATE</span>'
    elif stat_val == "weak":
        badge_html = '<span style="background:#450a0a; color:#f87171; font-weight:700; padding:3px 10px; border-radius:12px; border:1px solid #ef4444;"> WEAK GAP</span>'
    else:
        badge_html = '<span style="background:#1e293b; color:#94a3b8; font-weight:700; padding:3px 10px; border-radius:12px; border:1px solid #64748b;"> UNATTEMPTED</span>'

    col_details, col_action = st.columns([3.2, 1.8])

    with col_details:
        mastery_display = (
            f"**{selected_node.get('mastery')}%**"
            if selected_node.get("mastery") is not None
            else "*Unassessed (No quiz taken yet)*"
        )
        sec_display = (
            f"Section {selected_node.get('section')}"
            if selected_node.get("section")
            else "Core Concept"
        )

        card_html = textwrap.dedent(f"""\
<div style="background: var(--surface-container); border-radius: 12px; padding: 18px 20px; border: 1px solid var(--outline-variant); margin-bottom: 12px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <div style="font-size: 1.15rem; font-weight: 700; color: var(--on-surface);">
            {selected_node.get('name')} <span style="font-size: 0.82rem; color: var(--on-surface-variant); font-weight: 500;">· {sec_display}</span>
        </div>
        <div>{badge_html}</div>
    </div>
    <div style="font-size: 0.88rem; color: var(--on-surface-variant); margin-bottom: 12px; line-height: 1.5;">
        {selected_node.get('description')}
    </div>
    <div style="display: flex; gap: 18px; font-size: 0.82rem; color: var(--on-surface); font-weight: 600; border-top: 1px solid var(--outline-variant); padding-top: 10px;">
        <div> Mastery: {mastery_display}</div>
        <div> Attempts: {selected_node.get('attempts', 0)}</div>
        <div> Correct: {selected_node.get('correct', 0)}</div>
        <div> Confidence: {selected_node.get('confidence', 'Unassessed')}</div>
    </div>
</div>
""")
        st.markdown(card_html, unsafe_allow_html=True)

        # Linked Resources
        resources = selected_node.get("recommended_resources", [])
        if resources:
            st.markdown("##### :material/library_books: Recommended Study Materials")
            res_chips = []
            for r in resources:
                if r.get("source_type") == "ncert":
                    res_chips.append(
                        f'<span class="m3-chip m3-chip-primary"><span class="material-symbols-outlined" style="font-size: 1rem;">menu_book</span> {r.get("title")}</span>'
                    )
                else:
                    res_chips.append(
                        f'<span class="m3-chip m3-chip-cyan"><span class="material-symbols-outlined" style="font-size: 1rem;">auto_stories</span> {r.get("title")} (Uploaded)</span>'
                    )
            st.markdown(
                f'<div class="m3-chips-group" style="margin-bottom: 12px;">{"".join(res_chips)}</div>',
                unsafe_allow_html=True,
            )

    with col_action:
        st.write("")
        st.markdown(
            f"""
            <div style="background: var(--surface-container-low); border: 1px solid var(--outline-variant); border-radius: 12px; padding: 16px; text-align: center;">
                <div style="font-size: 0.88rem; font-weight: 700; color: var(--on-surface); margin-bottom: 6px;">Targeted Practice</div>
                <div style="font-size: 0.78rem; color: var(--on-surface-variant); margin-bottom: 14px;">
                    Take a focused quiz on <strong>{selected_node.get('name')}</strong> to strengthen mastery and update your knowledge graph.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")

        if st.button(
            f" Practice '{selected_node.get('name')}'",
            type="primary",
            use_container_width=True,
            key=f"btn_practice_kg_{selected_node.get('id')}",
        ):
            st.session_state["quiz_chapter"] = selected_chapter
            st.session_state["active_nav"] = "quiz"
            st.rerun()

        if st.button(
            f" Ask Tutor About '{selected_node.get('name')}'",
            type="secondary",
            use_container_width=True,
            key=f"btn_ask_tutor_kg_{selected_node.get('id')}",
        ):
            st.session_state["tutor_prefilled_prompt"] = (
                f"Explain {selected_node.get('name')} from Class {class_level} Science chapter {selected_chapter} with examples and key formulas."
            )
            st.session_state["active_nav"] = "tutor"
            st.rerun()
