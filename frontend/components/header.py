"""Minimalist Header Component (No Emojis, No Gradients)."""

import streamlit as st
from frontend.styles import get_current_theme


def render_header(selected_class: str = "All Classes", student_id: str = "student_001") -> None:
    """Renders the clean, modern top header with status badges."""
    current_theme = get_current_theme()
    theme_name = current_theme.get("name", "Dark")

    class_label = selected_class if selected_class != "All Classes" else "Class 9 & 10"
    
    html = f"""
    <div class="hero-header-container">
        <div class="hero-title">NCERT Academic Science Assistant</div>
        <div class="hero-subtitle">
            Grounded Agentic RAG Tutor and Adaptive Practice for <b>Class 9</b> & <b>Class 10</b> NCERT Science with Exact Page Citations
        </div>
        <div class="hero-badges-row">
            <span class="minimal-badge badge-accent">
                {class_label}
            </span>
            <span class="minimal-badge">
                Student ID: {student_id}
            </span>
            <span class="minimal-badge">
                Theme: {theme_name}
            </span>
            <span class="minimal-badge badge-success">
                Pinecone + Gemini RAG
            </span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
