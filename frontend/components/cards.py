"""Reusable Minimalist Cards and Badges UI Components (Flat, No Heavy Boxes)."""

from typing import Any, List, Optional

import streamlit as st


def render_metric_card(label: str, value: Any, delta: Optional[str] = None) -> None:
    """Renders a flat minimalist metric with clean typography (no box)."""
    delta_html = (
        f'<div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.15rem;">{delta}</div>'
        if delta
        else ""
    )
    html = f"""
    <div class="metric-flat">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_citation_box(
    chapter: str,
    class_level: int,
    pages: Optional[List[Any]] = None,
    explanation: Optional[str] = None,
) -> None:
    """Renders a clean citation line with textbook references (no chunky box)."""
    pages_str = ", ".join(str(p) for p in pages) if pages else "Referenced in Chapter"
    exp_html = f"<div style='margin-bottom: 0.25rem;'>{explanation}</div>" if explanation else ""
    html = f"""
    <div class="citation-clean">
        <div class="citation-title">
            NCERT Class {class_level} Science — {chapter}
        </div>
        {exp_html}
        <div style="font-size: 0.8rem; color: var(--text-muted);">
            Source Pages: <b>{pages_str}</b>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def get_status_badge_html(status: str) -> str:
    """Returns HTML for a simple textual status badge."""
    status_lower = status.lower()
    if status_lower in ["strong", "performing_well"]:
        return '<span class="minimal-badge badge-accent">STRONG</span>'
    elif status_lower in ["average", "monitor", "improving"]:
        return '<span class="minimal-badge">AVERAGE</span>'
    elif status_lower in ["weak", "intervention_needed"]:
        return '<span class="minimal-badge" style="color: var(--danger-text);">WEAK</span>'
    return f'<span class="minimal-badge">{status.upper()}</span>'
