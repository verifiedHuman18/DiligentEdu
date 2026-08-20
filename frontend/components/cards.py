"""Reusable Minimalist Cards and Badges UI Components (No Emojis, No Gradients)."""

from typing import List, Optional, Any
import streamlit as st


def render_metric_card(label: str, value: Any, delta: Optional[str] = None) -> None:
    """Renders a minimalist metric card with clean typography."""
    delta_html = f'<div class="metric-delta">{delta}</div>' if delta else ""
    html = f"""
    <div class="metric-card">
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
    """Renders a citation callout box with textbook references."""
    pages_str = ", ".join(str(p) for p in pages) if pages else "Referenced in Chapter"
    exp_html = f"<div style='margin-bottom: 0.4rem;'>{explanation}</div>" if explanation else ""
    html = f"""
    <div class="citation-box">
        <div class="citation-title">
            NCERT Class {class_level} Science — {chapter}
        </div>
        {exp_html}
        <div style="font-weight: 500; font-size: 0.8rem; opacity: 0.85;">
            Verified Source Pages: <b>{pages_str}</b>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def get_status_badge_html(status: str) -> str:
    """Returns HTML for a colored status pill without emojis."""
    status_lower = status.lower()
    if status_lower in ["strong", "performing_well"]:
        return '<span class="minimal-badge badge-success">STRONG</span>'
    elif status_lower in ["average", "monitor", "improving"]:
        return '<span class="minimal-badge badge-warning">AVERAGE</span>'
    elif status_lower in ["weak", "intervention_needed"]:
        return '<span class="minimal-badge badge-danger">WEAK</span>'
    return f'<span class="minimal-badge">{status.upper()}</span>'
