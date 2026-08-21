"""Minimalist Header Component (No Unnecessary Tags, No Emojis, No Gradients)."""

import textwrap

import streamlit as st


def render_header(selected_class: str = "All Classes", student_id: str = "student_001") -> None:
    """Renders the clean, modern top header with student details."""
    class_label = selected_class if selected_class != "All Classes" else "Class 9 & 10"

    html = textwrap.dedent(f"""\
<div class="hero-header-container">
<div class="hero-title">NCERT Academic Science Assistant</div>
<div class="hero-subtitle">Student: <b>{student_id}</b> | Grade: <b>{class_label}</b></div>
</div>\
""")
    st.markdown(html, unsafe_allow_html=True)
