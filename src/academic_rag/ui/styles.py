"""Custom CSS styling and design system for DiligentEdu."""

import streamlit as st


def inject_custom_css() -> None:
    """Injects custom dark theme CSS and typography."""
    st.markdown(
        """
<style>
.main-header {
    font-size: 2.4rem;
    color: #f6ad55;
    text-align: center;
    margin-bottom: 0.5rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.sub-header {
    font-size: 1.1rem;
    color: #cbd5e1;
    text-align: center;
    margin-bottom: 1.5rem;
}

.grade-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.85rem;
    margin-right: 0.5rem;
}

.badge-class9 {
    background-color: #3b82f6;
    color: white;
}

.badge-class10 {
    background-color: #10b981;
    color: white;
}

.subject-badge {
    padding: 0.75rem;
    margin: 0.4rem 0;
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-left: 4px solid #f6ad55;
    border-radius: 8px;
    border: 1px solid #334155;
    color: white;
    font-weight: 500;
    font-size: 0.9rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    transition: all 0.2s ease;
}

.subject-badge:hover {
    transform: translateX(3px);
    border-left: 4px solid #38bdf8;
}

.citation-card {
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid #3b82f6;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-top: 0.75rem;
    color: #e2e8f0;
}

.prompt-chip {
    display: inline-block;
    background-color: #1e293b;
    border: 1px solid #475569;
    border-radius: 20px;
    padding: 6px 14px;
    margin: 4px;
    font-size: 0.85rem;
    color: #94a3b8;
    cursor: pointer;
    transition: all 0.2s;
}

.prompt-chip:hover {
    background-color: #334155;
    color: #f6ad55;
    border-color: #f6ad55;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    justify-content: center !important;
    align-items: center !important;
    width: 100% !important;
    background-color: transparent !important;
}

.stTabs [data-baseweb="tab"] {
    flex: 1 !important;
    text-align: center !important;
    padding: 0.6rem 0.25rem !important;
    background-color: #1e293b !important;
    border: none !important;
    border-bottom: 3px solid #334155 !important;
    color: #94a3b8 !important;
    font-weight: 500 !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: #0f172a !important;
    border-bottom-color: #f6ad55 !important;
    color: #f6ad55 !important;
    font-weight: 600 !important;
}
</style>
""",
        unsafe_allow_html=True,
    )
