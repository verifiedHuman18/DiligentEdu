"""Minimalist Design System & Two-Theme (Dark / Light) Manager (No Gradients, No Emojis)."""

from typing import Dict, Any
import streamlit as st

THEMES: Dict[str, Dict[str, str]] = {
    "Dark": {
        "name": "Dark",
        "bg_app": "#0f172a",
        "bg_surface": "#1e293b",
        "bg_card": "#1e293b",
        "bg_card_hover": "#283548",
        "bg_input": "#0f172a",
        "border_color": "#334155",
        "border_focus": "#3b82f6",
        "text_primary": "#f8fafc",
        "text_secondary": "#94a3b8",
        "text_muted": "#64748b",
        "accent_primary": "#3b82f6",
        "accent_hover": "#2563eb",
        "accent_secondary": "#0ea5e9",
        "badge_bg": "#1e3a5f",
        "badge_text": "#93c5fd",
        "success_bg": "#064e3b",
        "success_text": "#6ee7b7",
        "warning_bg": "#78350f",
        "warning_text": "#fcd34d",
        "danger_bg": "#7f1d1d",
        "danger_text": "#fca5a5",
        "shadow_sm": "none",
        "shadow_md": "none",
    },
    "Light": {
        "name": "Light",
        "bg_app": "#ffffff",
        "bg_surface": "#f8fafc",
        "bg_card": "#ffffff",
        "bg_card_hover": "#f1f5f9",
        "bg_input": "#f8fafc",
        "border_color": "#e2e8f0",
        "border_focus": "#2563eb",
        "text_primary": "#0f172a",
        "text_secondary": "#475569",
        "text_muted": "#94a3b8",
        "accent_primary": "#2563eb",
        "accent_hover": "#1d4ed8",
        "accent_secondary": "#0284c7",
        "badge_bg": "#eff6ff",
        "badge_text": "#1d4ed8",
        "success_bg": "#ecfdf5",
        "success_text": "#047857",
        "warning_bg": "#fffbeb",
        "warning_text": "#b45309",
        "danger_bg": "#fef2f2",
        "danger_text": "#b91c1c",
        "shadow_sm": "none",
        "shadow_md": "none",
    },
}


def get_current_theme() -> Dict[str, str]:
    """Retrieves the active theme dictionary from session state."""
    theme_name = st.session_state.get("theme", "Dark")
    if theme_name not in THEMES:
        theme_name = "Dark"
        st.session_state.theme = "Dark"
    return THEMES[theme_name]


def inject_custom_css(theme_name: str = None) -> None:
    """Injects clean, solid-color CSS with no gradients."""
    if theme_name and theme_name in THEMES:
        t = THEMES[theme_name]
    else:
        t = get_current_theme()

    css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@500;600;700&display=swap');

:root {{
    --bg-app: {t['bg_app']};
    --bg-surface: {t['bg_surface']};
    --bg-card: {t['bg_card']};
    --bg-card-hover: {t['bg_card_hover']};
    --bg-input: {t['bg_input']};
    --border-color: {t['border_color']};
    --border-focus: {t['border_focus']};
    --text-primary: {t['text_primary']};
    --text-secondary: {t['text_secondary']};
    --text-muted: {t['text_muted']};
    --accent-primary: {t['accent_primary']};
    --accent-hover: {t['accent_hover']};
    --accent-secondary: {t['accent_secondary']};
    --badge-bg: {t['badge_bg']};
    --badge-text: {t['badge_text']};
    --success-bg: {t['success_bg']};
    --success-text: {t['success_text']};
    --warning-bg: {t['warning_bg']};
    --warning-text: {t['warning_text']};
    --danger-bg: {t['danger_bg']};
    --danger-text: {t['danger_text']};
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 10px;
    --radius-full: 9999px;
}}

/* Base Styles */
html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: 'Outfit', 'Inter', sans-serif !important;
    letter-spacing: -0.01em;
    font-weight: 600;
}}

/* Header Styling */
.hero-header-container {{
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: center;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem;
    background: var(--bg-surface);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    text-align: left;
}}

.hero-title {{
    font-size: 1.75rem;
    font-weight: 700;
    margin: 0 0 0.35rem 0;
    color: var(--text-primary);
    display: block;
}}

.hero-subtitle {{
    font-size: 0.92rem;
    color: var(--text-secondary);
    margin: 0 0 0.85rem 0;
    line-height: 1.5;
}}

.hero-badges-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: center;
}}

/* Status & Filter Badges */
.minimal-badge {{
    display: inline-flex;
    align-items: center;
    padding: 0.2rem 0.65rem;
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    border: 1px solid var(--border-color);
    background: var(--bg-card);
    color: var(--text-primary);
}}

.badge-accent {{
    background: var(--badge-bg);
    color: var(--badge-text);
    border-color: var(--border-color);
}}

.badge-success {{
    background: var(--success-bg);
    color: var(--success-text);
    border-color: transparent;
}}

.badge-warning {{
    background: var(--warning-bg);
    color: var(--warning-text);
    border-color: transparent;
}}

.badge-danger {{
    background: var(--danger-bg);
    color: var(--danger-text);
    border-color: transparent;
}}

/* Minimal Metric Card */
.metric-card {{
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 1rem 1.15rem;
    margin-bottom: 0.75rem;
}}

.metric-label {{
    font-size: 0.75rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
    margin-bottom: 0.3rem;
}}

.metric-value {{
    font-family: 'Outfit', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.1;
}}

.metric-delta {{
    font-size: 0.75rem;
    margin-top: 0.3rem;
    color: var(--text-muted);
}}

/* Citation Box */
.citation-box {{
    background: var(--bg-surface);
    border: 1px solid var(--border-color);
    border-left: 3px solid var(--accent-primary);
    border-radius: var(--radius-sm);
    padding: 0.75rem 1rem;
    margin: 0.75rem 0;
    font-size: 0.85rem;
    color: var(--text-secondary);
}}

.citation-title {{
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
}}

/* Modern Minimalist Tabs (Flat, Solid) */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0.25rem;
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-color) !important;
    padding: 0.25rem !important;
    border-radius: var(--radius-md) !important;
    margin-bottom: 1.25rem !important;
}}

.stTabs [data-baseweb="tab"] {{
    flex: 1 !important;
    text-align: center !important;
    padding: 0.5rem 0.75rem !important;
    background: transparent !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    transition: background-color 0.15s ease, color 0.15s ease !important;
}}

.stTabs [data-baseweb="tab"]:hover {{
    color: var(--text-primary) !important;
    background: var(--bg-card-hover) !important;
}}

.stTabs [data-baseweb="tab"][aria-selected="true"] {{
    background: var(--accent-primary) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
}}

.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {{
    display: none !important;
}}

/* Buttons */
.stButton > button {{
    border-radius: var(--radius-sm) !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    transition: background-color 0.15s ease !important;
}}

.stButton > button[kind="primary"] {{
    background: var(--accent-primary) !important;
    border: 1px solid var(--accent-primary) !important;
    color: #ffffff !important;
}}

.stButton > button[kind="primary"]:hover {{
    background: var(--accent-hover) !important;
    border-color: var(--accent-hover) !important;
}}

.stButton > button[kind="secondary"] {{
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
}}

.stButton > button[kind="secondary"]:hover {{
    background: var(--bg-card-hover) !important;
    border-color: var(--border-focus) !important;
}}

/* Expander styling */
.streamlit-expanderHeader {{
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
}}

/* Chat message bubbles */
[data-testid="stChatMessage"] {{
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius-md) !important;
    padding: 0.85rem 1rem !important;
    margin-bottom: 0.65rem !important;
}}

/* Radio and Input containers */
div[data-testid="stRadio"] > div {{
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 0.75rem 1rem;
}}

/* Hide unnecessary default Streamlit decoration */
#MainMenu, footer {{
    visibility: hidden;
}}
header {{
    background: transparent !important;
}}
</style>
    """
    st.markdown(css, unsafe_allow_html=True)
