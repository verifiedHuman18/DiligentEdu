"""Minimalist Header Component (No Unnecessary Tags, No Emojis, No Gradients)."""

import textwrap

import streamlit as st


def render_header(selected_class: str = "Class 10", student_id: str = "student_001") -> None:
    """Renders the clean, modern top header with student details."""
    from frontend.state import get_student_class_level

    cls_int = get_student_class_level()
    class_label = f"Class {cls_int}"

    html = textwrap.dedent(f"""\
<div class="hero-header-container">
<div class="hero-title">NCERT Academic Science Assistant</div>
<div class="hero-subtitle">Student: <b>{student_id}</b> | Class: <b>{class_label}</b></div>
</div>\
""")
    st.markdown(html, unsafe_allow_html=True)
