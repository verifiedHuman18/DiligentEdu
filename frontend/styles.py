"""Material Design 3 (M3) Design System with Translucent Background Vector Art & Cream/Brown Palettes."""

from typing import Dict

import streamlit as st

THEMES: Dict[str, Dict[str, str]] = {
    "Dark": {
        "name": "Dark",
        # Warm Rich Brown M3 Surfaces
        "bg_app": "#191310",
        "bg_surface": "#231b16",
        "surface_container_lowest": "#120d0b",
        "surface_container_low": "#231b16",
        "surface_container": "#2d231d",
        "surface_container_high": "#382c25",
        "surface_container_highest": "#45372e",
        "border_outline": "#6b584c",
        "border_outline_variant": "#3f3129",
        "text_primary": "#faf0e6",
        "text_secondary": "#dac7b8",
        "text_muted": "#a89587",
        # Warm Translucent Active Container (Zero Blue Background)
        "md_primary": "#fbbf24",
        "md_on_primary": "#191310",
        "md_primary_container": "rgba(250, 240, 230, 0.12)",
        "md_on_primary_container": "#faf0e6",
        "md_secondary": "#c084fc",
        "md_secondary_container": "#4c1d95",
        "md_on_secondary_container": "#f3e8ff",
        "md_tertiary": "#34d399",
        "md_tertiary_container": "#064e3b",
        "md_on_tertiary_container": "#d1fae5",
        "md_amber": "#fbbf24",
        "md_amber_container": "#78350f",
        "md_on_amber_container": "#fef3c7",
        "md_error": "#f87171",
        "md_error_container": "#7f1d1d",
        "md_on_error_container": "#fee2e2",
        "md_cyan": "#38bdf8",
        "md_cyan_container": "#0c4a6e",
        "md_on_cyan_container": "#e0f2fe",
        "card_shadow": "rgba(0, 0, 0, 0.45)",
        # Vibrant Module Buttons
        "btn_tutor_bg": "#172554",
        "btn_tutor_border": "#3b82f6",
        "btn_tutor_text": "#93c5fd",
        "btn_quiz_bg": "#3b0764",
        "btn_quiz_border": "#a855f7",
        "btn_quiz_text": "#e9d5ff",
        "btn_analytics_bg": "#022c22",
        "btn_analytics_border": "#10b981",
        "btn_analytics_text": "#6ee7b7",
        "btn_teacher_bg": "#451a03",
        "btn_teacher_border": "#f59e0b",
        "btn_teacher_text": "#fde68a",
    },
    "Light": {
        "name": "Light",
        # Warm Cream M3 Surfaces
        "bg_app": "#fcf9f2",
        "bg_surface": "#ffffff",
        "surface_container_lowest": "#ffffff",
        "surface_container_low": "#f8f3e9",
        "surface_container": "#f1e9dc",
        "surface_container_high": "#e8ddcc",
        "surface_container_highest": "#decbbe",
        "border_outline": "#9c8b7b",
        "border_outline_variant": "#dfd4c5",
        "text_primary": "#2a1f16",
        "text_secondary": "#574435",
        "text_muted": "#84705f",
        # Warm Translucent Active Container (Zero Blue Background)
        "md_primary": "#b45309",
        "md_on_primary": "#ffffff",
        "md_primary_container": "rgba(42, 31, 22, 0.08)",
        "md_on_primary_container": "#2a1f16",
        "md_secondary": "#7c3aed",
        "md_secondary_container": "#ede9fe",
        "md_on_secondary_container": "#4c1d95",
        "md_tertiary": "#059669",
        "md_tertiary_container": "#d1fae5",
        "md_on_tertiary_container": "#064e3b",
        "md_amber": "#d97706",
        "md_amber_container": "#fef3c7",
        "md_on_amber_container": "#78350f",
        "md_error": "#dc2626",
        "md_error_container": "#fee2e2",
        "md_on_error_container": "#7f1d1d",
        "md_cyan": "#0284c7",
        "md_cyan_container": "#e0f2fe",
        "md_on_cyan_container": "#0c4a6e",
        "card_shadow": "rgba(42, 31, 22, 0.08)",
        # Vibrant Module Buttons
        "btn_tutor_bg": "#eff6ff",
        "btn_tutor_border": "#2563eb",
        "btn_tutor_text": "#1d4ed8",
        "btn_quiz_bg": "#f5f3ff",
        "btn_quiz_border": "#7c3aed",
        "btn_quiz_text": "#6d28d9",
        "btn_analytics_bg": "#ecfdf5",
        "btn_analytics_border": "#059669",
        "btn_analytics_text": "#047857",
        "btn_teacher_bg": "#fffbeb",
        "btn_teacher_border": "#d97706",
        "btn_teacher_text": "#b45309",
    },
}


def get_current_theme() -> Dict[str, str]:
    """Retrieves the active theme dictionary from session state."""
    theme_name = st.session_state.get("theme", "Light")
    if theme_name not in THEMES:
        theme_name = "Light"
        st.session_state.theme = "Light"
    return THEMES[theme_name]


def inject_custom_css(theme_name: str = None) -> None:
    """Injects warm cream/brown M3 design tokens, translucent background vector styles, and clean module/settings separation."""
    if theme_name and theme_name in THEMES:
        t = THEMES[theme_name]
    else:
        t = get_current_theme()

    css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Outfit:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

:root {{
    --bg-app: {t["bg_app"]};
    --bg-surface: {t["bg_surface"]};
    --surface-container-lowest: {t["surface_container_lowest"]};
    --surface-container-low: {t["surface_container_low"]};
    --surface-container: {t["surface_container"]};
    --surface-container-high: {t["surface_container_high"]};
    --surface-container-highest: {t["surface_container_highest"]};
    --border-outline: {t["border_outline"]};
    --border-outline-variant: {t["border_outline_variant"]};
    --outline: {t["border_outline"]};
    --outline-variant: {t["border_outline_variant"]};
    --text-primary: {t["text_primary"]};
    --text-secondary: {t["text_secondary"]};
    --text-muted: {t["text_muted"]};
    --on-surface: {t["text_primary"]};
    --on-surface-variant: {t["text_secondary"]};
    --md-primary: {t["md_primary"]};
    --md-on-primary: {t["md_on_primary"]};
    --on-primary: {t["md_on_primary"]};
    --md-primary-container: {t["md_primary_container"]};
    --md-on-primary-container: {t["md_on_primary_container"]};
    --md-secondary: {t["md_secondary"]};
    --md-secondary-container: {t["md_secondary_container"]};
    --md-on-secondary-container: {t["md_on_secondary_container"]};
    --md-tertiary: {t["md_tertiary"]};
    --md-tertiary-container: {t["md_tertiary_container"]};
    --md-on-tertiary-container: {t["md_on_tertiary_container"]};
    --md-amber: {t["md_amber"]};
    --md-amber-container: {t["md_amber_container"]};
    --md-on-amber-container: {t["md_on_amber_container"]};
    --md-error: {t["md_error"]};
    --md-error-container: {t["md_error_container"]};
    --md-on-error-container: {t["md_on_error_container"]};
    --md-cyan: {t["md_cyan"]};
    --md-cyan-container: {t["md_cyan_container"]};
    --md-on-cyan-container: {t["md_on_cyan_container"]};
    --danger-text: {t["md_error"]};
    --card-shadow: {t["card_shadow"]};
    --btn-tutor-bg: {t["btn_tutor_bg"]};
    --btn-tutor-border: {t["btn_tutor_border"]};
    --btn-tutor-text: {t["btn_tutor_text"]};
    --btn-quiz-bg: {t["btn_quiz_bg"]};
    --btn-quiz-border: {t["btn_quiz_border"]};
    --btn-quiz-text: {t["btn_quiz_text"]};
    --btn-analytics-bg: {t["btn_analytics_bg"]};
    --btn-analytics-border: {t["btn_analytics_border"]};
    --btn-analytics-text: {t["btn_analytics_text"]};
    --btn-teacher-bg: {t["btn_teacher_bg"]};
    --btn-teacher-border: {t["btn_teacher_border"]};
    --btn-teacher-text: {t["btn_teacher_text"]};
    --radius-xs: 6px;
    --radius-sm: 10px;
    --radius-md: 14px;
    --radius-lg: 18px;
    --radius-xl: 24px;
    --radius-full: 9999px;
}}

/* Base Streamlit App Overrides (Cream & Brown) */
.stApp,
[data-testid="stAppViewContainer"],
.main,
header,
body {{
    background-color: var(--bg-app) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}}

[data-testid="stHeader"],
[data-testid="stToolbar"] {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
}}

.block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 5rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 1280px;
    background-color: transparent !important;
}}

/* Global Typography */
h1, h2, h3, h4, h5, h6 {{
    font-family: 'Outfit', 'Fredoka', sans-serif !important;
    letter-spacing: -0.01em;
    font-weight: 700;
    color: var(--text-primary) !important;
}}

p, span, label, [data-testid="stWidgetLabel"] p, [data-testid="stMarkdownContainer"] p {{
    color: var(--text-primary);
}}

small, .stCaption, [data-testid="stCaptionContainer"] {{
    color: var(--text-secondary) !important;
}}

/* Google Material Symbols Outlined */
.material-symbols-outlined {{
    font-family: 'Material Symbols Outlined' !important;
    font-weight: normal;
    font-style: normal;
    font-size: 1.35rem;
    line-height: 1;
    letter-spacing: normal;
    text-transform: none;
    display: inline-block;
    white-space: nowrap;
    word-wrap: normal;
    direction: ltr;
    -webkit-font-feature-settings: 'liga';
    -webkit-font-smoothing: antialiased;
    vertical-align: middle;
}}

/* Corner Brand Header */
.brand-corner {{
    font-family: 'Outfit', sans-serif;
    font-weight: 800;
    font-size: 1.5rem;
    color: var(--text-primary);
    letter-spacing: -0.03em;
}}

.brand-corner-accent {{
    color: var(--md-amber);
}}

.brand-corner-sub {{
    font-size: 0.78rem;
    color: var(--text-muted);
    font-weight: 700;
    margin-left: 0.4rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}

/* Clean Icon-only Settings Cog Button (No Background, No Border) */
div[data-testid="stHorizontalBlock"]:has(.brand-corner) button {{
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    color: var(--text-secondary) !important;
    padding: 0 !important;
    min-height: unset !important;
    height: 38px !important;
    width: 38px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    border-radius: var(--radius-full) !important;
    transition: color 0.15s ease, transform 0.25s ease !important;
    margin-left: auto !important;
}}

div[data-testid="stHorizontalBlock"]:has(.brand-corner) button [data-testid="stIconMaterial"] {{
    font-size: 1.85rem !important;
    color: var(--text-secondary) !important;
    transition: color 0.15s ease !important;
}}

div[data-testid="stHorizontalBlock"]:has(.brand-corner) button:hover {{
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    transform: rotate(45deg);
}}

div[data-testid="stHorizontalBlock"]:has(.brand-corner) button:hover [data-testid="stIconMaterial"] {{
    color: var(--text-primary) !important;
}}

/* M3 Elevated Hero Container with Translucent Background Vectors */
.m3-hero-card {{
    position: relative !important;
    overflow: hidden !important;
    background-color: var(--surface-container) !important;
    border: 1.5px solid var(--border-outline-variant) !important;
    border-radius: var(--radius-xl);
    padding: 2.25rem 2.25rem;
    margin-bottom: 2.5rem;
}}

.m3-hero-bg-svg {{
    position: absolute;
    right: 0;
    top: 0;
    width: 60%;
    height: 100%;
    pointer-events: none;
    opacity: 0.16;
    z-index: 0;
}}

.m3-hero-content {{
    position: relative;
    z-index: 1;
}}

.m3-hero-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 2.25rem;
    font-weight: 800;
    color: var(--text-primary) !important;
    line-height: 1.15;
    margin: 0 0 0.85rem 0;
    letter-spacing: -0.02em;
}}

/* Stacked Label Chips Group */
.m3-chips-group {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    align-items: center;
}}

.m3-chip {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.45rem 1rem;
    border-radius: var(--radius-full);
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.01em;
}}

.m3-chip-primary {{
    background-color: var(--surface-container-high) !important;
    color: var(--text-primary) !important;
    border: 1.5px solid var(--border-outline) !important;
}}

.m3-chip-purple {{
    background-color: var(--md-secondary-container) !important;
    color: var(--md-on-secondary-container) !important;
    border: 1.5px solid var(--md-secondary) !important;
}}

.m3-chip-tertiary {{
    background-color: var(--md-tertiary-container) !important;
    color: var(--md-on-tertiary-container) !important;
    border: 1.5px solid var(--md-tertiary) !important;
}}

/* M3 Metric Stats Grid */
.m3-stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1.25rem;
    padding-top: 1.5rem;
    margin-top: 1.5rem;
    border-top: 1.5px solid var(--border-outline-variant);
}}

.m3-stat-card {{
    background-color: var(--surface-container-low) !important;
    border: 1px solid var(--border-outline-variant) !important;
    border-radius: var(--radius-md);
    padding: 1.1rem 1.25rem;
    min-height: 90px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    transition: border-color 0.15s ease, transform 0.15s ease;
}}

.m3-stat-card:hover {{
    transform: translateY(-2px);
}}

.m3-stat-label {{
    font-size: 0.75rem;
    color: var(--text-muted) !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 700;
    margin-bottom: 0.35rem;
}}

.m3-stat-val {{
    font-family: 'Outfit', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.1;
}}

/* =============================================================
   1. MODULE ACTION BUTTONS (Identified by having Title + Subtext)
   ============================================================= */
button:has(p + p),
.stButton > button:has(p + p),
div[data-testid="column"] button:has(p + p) {{
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: left !important;
    gap: 1.1rem !important;
    padding: 1.35rem 1.45rem !important;
    min-height: 120px !important;
    height: auto !important;
    width: 100% !important;
    border-radius: var(--radius-lg) !important;
    cursor: pointer !important;
    white-space: normal !important;
    transition: background-color 0.15s ease, border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease !important;
}}

button:has(p + p):hover,
.stButton > button:has(p + p):hover,
div[data-testid="column"] button:has(p + p):hover {{
    transform: translateY(-4px) !important;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.09) !important;
}}

/* Large Material Symbols inside Module Buttons */
button:has(p + p) [data-testid="stIconMaterial"],
.stButton > button:has(p + p) [data-testid="stIconMaterial"] {{
    font-size: 2.25rem !important;
    width: 2.4rem !important;
    height: 2.4rem !important;
    min-width: 2.4rem !important;
    line-height: 1 !important;
    align-self: center !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
}}

button:has(p + p) [data-testid="stMarkdownContainer"],
.stButton > button:has(p + p) [data-testid="stMarkdownContainer"] {{
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
}}

button:has(p + p) p {{
    margin: 0 !important;
    line-height: 1.35 !important;
    width: 100% !important;
    font-size: 0.84rem !important;
    color: var(--text-secondary) !important;
}}

button:has(p + p) p strong {{
    font-family: 'Outfit', sans-serif !important;
    font-size: 1.18rem !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
    display: inline-flex !important;
    align-items: center !important;
    width: 100% !important;
    margin-bottom: 0.3rem !important;
}}

/* Smooth Slide-In Arrow on Hover for Module Cards */
button:has(p + p) p strong::after {{
    content: " →";
    opacity: 0;
    transform: translateX(-10px);
    transition: opacity 0.2s cubic-bezier(0.4, 0, 0.2, 1), transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    display: inline-block;
    margin-left: 0.4rem;
    font-size: 1.18rem;
}}

button:has(p + p):hover p strong::after {{
    opacity: 1;
    transform: translateX(0);
}}

/* 1. Tutor (Blue Accent) */
div[data-testid="column"]:nth-of-type(1) button:has(p + p) {{
    background-color: var(--btn-tutor-bg) !important;
    border: 1.5px solid var(--btn-tutor-border) !important;
    border-left: 6px solid var(--btn-tutor-border) !important;
}}
div[data-testid="column"]:nth-of-type(1) button:has(p + p):hover {{
    background-color: var(--surface-container-high) !important;
    border-color: var(--btn-tutor-border) !important;
}}
div[data-testid="column"]:nth-of-type(1) button:has(p + p) [data-testid="stIconMaterial"] {{
    color: var(--btn-tutor-border) !important;
}}
div[data-testid="column"]:nth-of-type(1) button:has(p + p) p strong {{
    color: var(--btn-tutor-text) !important;
}}

/* 2. Practice Quiz (Purple Accent) */
div[data-testid="column"]:nth-of-type(2) button:has(p + p) {{
    background-color: var(--btn-quiz-bg) !important;
    border: 1.5px solid var(--btn-quiz-border) !important;
    border-left: 6px solid var(--btn-quiz-border) !important;
}}
div[data-testid="column"]:nth-of-type(2) button:has(p + p):hover {{
    background-color: var(--surface-container-high) !important;
    border-color: var(--btn-quiz-border) !important;
}}
div[data-testid="column"]:nth-of-type(2) button:has(p + p) [data-testid="stIconMaterial"] {{
    color: var(--btn-quiz-border) !important;
}}
div[data-testid="column"]:nth-of-type(2) button:has(p + p) p strong {{
    color: var(--btn-quiz-text) !important;
}}

/* 3. Student Analytics (Emerald Accent) */
div[data-testid="column"]:nth-of-type(3) button:has(p + p) {{
    background-color: var(--btn-analytics-bg) !important;
    border: 1.5px solid var(--btn-analytics-border) !important;
    border-left: 6px solid var(--btn-analytics-border) !important;
}}
div[data-testid="column"]:nth-of-type(3) button:has(p + p):hover {{
    background-color: var(--surface-container-high) !important;
    border-color: var(--btn-analytics-border) !important;
}}
div[data-testid="column"]:nth-of-type(3) button:has(p + p) [data-testid="stIconMaterial"] {{
    color: var(--btn-analytics-border) !important;
}}
div[data-testid="column"]:nth-of-type(3) button:has(p + p) p strong {{
    color: var(--btn-analytics-text) !important;
}}

/* 4. Teacher View (Amber Accent) */
div[data-testid="column"]:nth-of-type(4) button:has(p + p) {{
    background-color: var(--btn-teacher-bg) !important;
    border: 1.5px solid var(--btn-teacher-border) !important;
    border-left: 6px solid var(--btn-teacher-border) !important;
}}
div[data-testid="column"]:nth-of-type(4) button:has(p + p):hover {{
    background-color: var(--surface-container-high) !important;
    border-color: var(--btn-teacher-border) !important;
}}
div[data-testid="column"]:nth-of-type(4) button:has(p + p) [data-testid="stIconMaterial"] {{
    color: var(--btn-teacher-border) !important;
}}
div[data-testid="column"]:nth-of-type(4) button:has(p + p) p strong {{
    color: var(--btn-teacher-text) !important;
}}

/* =============================================================
   2. SETTINGS CATEGORY SIDEBAR BUTTONS (Single-Line Buttons)
   ============================================================= */
div[data-testid="column"]:first-child:has(button[key^="btn_tab_"]) button:not(:has(p + p)),
button[key^="btn_tab_"],
button[key="btn_settings_logout"] {{
    min-height: 40px !important;
    height: 40px !important;
    padding: 0.35rem 0.95rem !important;
    font-size: 0.88rem !important;
    gap: 0.65rem !important;
    border-radius: var(--radius-sm) !important;
    margin-bottom: 0.35rem !important;
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: left !important;
    width: 100% !important;
}}

div[data-testid="column"]:first-child:has(button[key^="btn_tab_"]) button:not(:has(p + p)) [data-testid="stIconMaterial"],
button[key^="btn_tab_"] [data-testid="stIconMaterial"],
button[key="btn_settings_logout"] [data-testid="stIconMaterial"] {{
    font-size: 1.3rem !important;
    width: 1.35rem !important;
    height: 1.35rem !important;
    min-width: 1.35rem !important;
}}

/* Inactive category button: 100% transparent */
div[data-testid="column"]:first-child:has(button[key^="btn_tab_"]) button:not(:has(p + p))[kind="secondary"],
div[data-testid="column"]:first-child:has(button[key^="btn_tab_"]) button:not(:has(p + p))[data-testid="stBaseButton-secondary"],
button[key^="btn_tab_"][kind="secondary"],
button[key="btn_settings_logout"] {{
    background: transparent !important;
    background-color: transparent !important;
    border: 1px solid transparent !important;
    color: var(--text-secondary) !important;
}}

div[data-testid="column"]:first-child:has(button[key^="btn_tab_"]) button:not(:has(p + p))[kind="secondary"] *,
div[data-testid="column"]:first-child:has(button[key^="btn_tab_"]) button:not(:has(p + p))[data-testid="stBaseButton-secondary"] *,
button[key^="btn_tab_"][kind="secondary"] *,
button[key="btn_settings_logout"] * {{
    color: var(--text-secondary) !important;
}}

div[data-testid="column"]:first-child:has(button[key^="btn_tab_"]) button:not(:has(p + p))[kind="secondary"]:hover,
div[data-testid="column"]:first-child:has(button[key^="btn_tab_"]) button:not(:has(p + p))[data-testid="stBaseButton-secondary"]:hover,
button[key^="btn_tab_"][kind="secondary"]:hover,
button[key="btn_settings_logout"]:hover {{
    background: var(--surface-container) !important;
    background-color: var(--surface-container) !important;
    border-color: var(--border-outline-variant) !important;
    color: var(--text-primary) !important;
}}

/* Active category button: Translucent neutral container, ZERO blue */
div[data-testid="column"]:first-child:has(button[key^="btn_tab_"]) button:not(:has(p + p))[kind="primary"],
div[data-testid="column"]:first-child:has(button[key^="btn_tab_"]) button:not(:has(p + p))[data-testid="stBaseButton-primary"],
button[key^="btn_tab_"][kind="primary"],
button[key^="btn_tab_"][data-testid="stBaseButton-primary"] {{
    background: var(--md-primary-container) !important;
    background-color: var(--md-primary-container) !important;
    border: 1.5px solid var(--border-outline) !important;
    color: var(--text-primary) !important;
    font-weight: 700 !important;
}}

div[data-testid="column"]:first-child:has(button[key^="btn_tab_"]) button:not(:has(p + p))[kind="primary"] *,
div[data-testid="column"]:first-child:has(button[key^="btn_tab_"]) button:not(:has(p + p))[data-testid="stBaseButton-primary"] *,
button[key^="btn_tab_"][kind="primary"] *,
button[key^="btn_tab_"][data-testid="stBaseButton-primary"] * {{
    color: var(--text-primary) !important;
}}

/* =============================================================
   3. STREAMLIT & BASEWEB TOOLTIPS (Simple, Minimalist, Single Layer)
   ============================================================= */
[data-baseweb="tooltip"],
div[role="tooltip"]:not([data-baseweb="tooltip"] div[role="tooltip"]) {{
    background-color: #1f1f1f !important;
    color: #f3f3f3 !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
    border-radius: 4px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35) !important;
    font-size: 0.76rem !important;
    font-weight: 400 !important;
    padding: 5px 9px !important;
    max-width: 280px !important;
    z-index: 999999 !important;
    line-height: 1.35 !important;
}}

/* Ensure all nested children are completely transparent without extra padding/borders */
[data-baseweb="tooltip"] *,
div[role="tooltip"] *,
[data-testid="stTooltipContent"],
[data-testid="stTooltipContent"] *,
[data-testid="stTooltipErrorContent"],
[data-testid="stTooltipErrorContent"] * {{
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    color: #f3f3f3 !important;
    font-size: 0.76rem !important;
    line-height: 1.35 !important;
}}

/* Simple Tooltip Trigger Icon (Non-intrusive) */
[data-testid="stTooltipIcon"],
[data-testid="stTooltipHoverTarget"] {{
    color: var(--text-muted) !important;
    display: inline-flex !important;
    align-items: center !important;
    vertical-align: middle !important;
    cursor: help !important;
    opacity: 0.75 !important;
    transition: opacity 0.15s ease !important;
}}

[data-testid="stTooltipIcon"]:hover,
[data-testid="stTooltipHoverTarget"]:hover {{
    opacity: 1 !important;
}}

[data-testid="stTooltipIcon"] svg,
[data-testid="stTooltipIcon"] [data-testid="stIconMaterial"],
[data-testid="stTooltipHoverTarget"] svg {{
    fill: var(--text-muted) !important;
    color: var(--text-muted) !important;
    font-size: 1rem !important;
}}

[data-testid="stTooltipIcon"]:hover svg,
[data-testid="stTooltipIcon"]:hover [data-testid="stIconMaterial"],
[data-testid="stTooltipHoverTarget"]:hover svg {{
    fill: var(--text-primary) !important;
    color: var(--text-primary) !important;
}}

/* =============================================================
   4. METRIC CARDS & MINIMALIST BADGES (from cards.py)
   ============================================================= */
.metric-flat {{
    background-color: var(--surface-container-low) !important;
    border: 1px solid var(--border-outline-variant) !important;
    border-radius: var(--radius-md) !important;
    padding: 1.1rem 1.25rem !important;
    min-height: 90px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    transition: border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease !important;
}}

.metric-flat:hover {{
    transform: translateY(-2px) !important;
    border-color: var(--border-outline) !important;
    box-shadow: 0 4px 12px var(--card-shadow) !important;
}}

.metric-label {{
    font-size: 0.75rem !important;
    color: var(--text-muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    font-weight: 700 !important;
    margin-bottom: 0.35rem !important;
}}

.metric-value {{
    font-family: 'Outfit', sans-serif !important;
    font-size: 1.85rem !important;
    font-weight: 800 !important;
    line-height: 1.1 !important;
    color: var(--text-primary) !important;
}}

.minimal-badge {{
    display: inline-flex !important;
    align-items: center !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    padding: 2px 8px !important;
    border-radius: 4px !important;
    background: var(--surface-container-highest) !important;
    color: var(--text-secondary) !important;
    letter-spacing: 0.03em !important;
}}

.badge-accent {{
    background: var(--md-tertiary-container) !important;
    color: var(--md-on-tertiary-container) !important;
}}

/* =============================================================
   5. INPUTS, TEXTAREAS & SELECTBOXES
   ============================================================= */
input, textarea, [data-baseweb="input"], [data-baseweb="base-input"] {{
    background-color: var(--bg-surface) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-outline-variant) !important;
    border-radius: var(--radius-sm) !important;
}}

input:focus, textarea:focus, [data-baseweb="input"]:focus-within {{
    border-color: var(--md-primary) !important;
    box-shadow: 0 0 0 1px var(--md-primary) !important;
}}

input::placeholder, textarea::placeholder {{
    color: var(--text-muted) !important;
    opacity: 0.75;
}}

[data-baseweb="select"] > div {{
    background-color: var(--bg-surface) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-outline-variant) !important;
    border-radius: var(--radius-sm) !important;
}}

[data-baseweb="select"] span,
[data-baseweb="select"] div {{
    color: var(--text-primary) !important;
}}

[data-baseweb="select"] svg {{
    fill: var(--text-secondary) !important;
}}

[data-baseweb="popover"],
[data-baseweb="menu"],
ul[data-baseweb="menu"],
div[data-testid="stPopoverBody"] {{
    background-color: var(--bg-surface) !important;
    color: var(--text-primary) !important;
    border: 1.5px solid var(--border-outline-variant) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: 0 8px 24px var(--card-shadow) !important;
}}

li[data-baseweb="menu-item"] {{
    background-color: transparent !important;
    color: var(--text-primary) !important;
    padding: 0.55rem 0.95rem !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    transition: background-color 0.12s ease;
}}

li[data-baseweb="menu-item"] * {{
    color: var(--text-primary) !important;
}}

li[data-baseweb="menu-item"]:hover,
li[data-baseweb="menu-item"][aria-selected="true"] {{
    background-color: var(--surface-container) !important;
    color: var(--text-primary) !important;
}}

/* =============================================================
   6. GLOBAL PRIMARY BUTTONS & LINK BUTTONS
   ============================================================= */
button[kind="primary"],
button[data-testid="stBaseButton-primary"],
a[kind="primary"],
a[data-testid="stBaseButton-primary"],
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"],
div[data-testid="stLinkButton"] > a[data-testid="stBaseButton-primary"],
div[data-testid="stLinkButton"] > a,
div[data-testid="stDownloadButton"] > button[kind="primary"] {{
    background-color: var(--md-primary-container) !important;
    background: var(--md-primary-container) !important;
    border: 1.5px solid var(--border-outline) !important;
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    border-radius: var(--radius-md) !important;
    text-decoration: none !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: background-color 0.15s ease, border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease !important;
}}

button[kind="primary"] *,
button[data-testid="stBaseButton-primary"] *,
a[kind="primary"] *,
a[data-testid="stBaseButton-primary"] *,
.stButton > button[kind="primary"] *,
.stButton > button[data-testid="stBaseButton-primary"] *,
div[data-testid="stLinkButton"] > a * {{
    color: var(--text-primary) !important;
}}

button[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover,
a[kind="primary"]:hover,
a[data-testid="stBaseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover,
div[data-testid="stLinkButton"] > a:hover {{
    background-color: var(--surface-container-high) !important;
    background: var(--surface-container-high) !important;
    border-color: var(--border-outline) !important;
    color: var(--text-primary) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px var(--card-shadow) !important;
}}

/* =============================================================
   7. GLOBAL SECONDARY BUTTONS
   ============================================================= */
button[kind="secondary"],
button[data-testid="stBaseButton-secondary"],
a[kind="secondary"],
a[data-testid="stBaseButton-secondary"],
.stButton > button[kind="secondary"],
.stButton > button[data-testid="stBaseButton-secondary"],
div[data-testid="stDownloadButton"] > button[kind="secondary"],
div[data-testid="stDownloadButton"] > button {{
    background-color: var(--surface-container) !important;
    border: 1.5px solid var(--border-outline-variant) !important;
    color: var(--text-primary) !important;
    border-radius: var(--radius-md) !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    padding: 0.55rem 1.2rem !important;
    text-decoration: none !important;
    transition: background-color 0.15s ease, border-color 0.15s ease, transform 0.15s ease !important;
}}

button[kind="secondary"] *,
button[data-testid="stBaseButton-secondary"] *,
a[kind="secondary"] *,
a[data-testid="stBaseButton-secondary"] *,
div[data-testid="stDownloadButton"] > button * {{
    color: var(--text-primary) !important;
}}

button[kind="secondary"]:hover,
button[data-testid="stBaseButton-secondary"]:hover,
a[kind="secondary"]:hover,
a[data-testid="stBaseButton-secondary"]:hover,
.stButton > button[kind="secondary"]:hover,
.stButton > button[data-testid="stBaseButton-secondary"]:hover,
div[data-testid="stDownloadButton"] > button:hover {{
    background-color: var(--surface-container-high) !important;
    border-color: var(--border-outline) !important;
    color: var(--text-primary) !important;
    transform: translateY(-1px) !important;
}}

/* =============================================================
   8. CITATIONS, EXPANDERS & CHAT
   ============================================================= */
.citation-clean {{
    border-left: 4px solid var(--md-amber);
    background-color: var(--surface-container-low);
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    padding: 0.75rem 1.25rem;
    margin: 1rem 0;
    font-size: 0.88rem;
    color: var(--text-secondary);
}}

.citation-title {{
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.3rem;
}}

[data-testid="stExpander"],
[data-testid="stExpander"] details,
[data-testid="stExpander"] details[open] {{
    background-color: var(--surface-container) !important;
    background: var(--surface-container) !important;
    border: 1.5px solid var(--border-outline-variant) !important;
    border-radius: var(--radius-md) !important;
    margin-bottom: 0.85rem !important;
    overflow: hidden !important;
}}

summary[data-testid="stExpanderSummary"],
.streamlit-expanderHeader,
[data-testid="stExpander"] summary,
[data-testid="stExpander"] details summary,
[data-testid="stExpander"] details[open] > summary {{
    background-color: var(--surface-container) !important;
    background: var(--surface-container) !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-primary) !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    padding: 0.75rem 1.1rem !important;
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 0.6rem !important;
    cursor: pointer !important;
    outline: none !important;
    box-shadow: none !important;
    transition: color 0.15s ease, background-color 0.15s ease !important;
}}

summary[data-testid="stExpanderSummary"]:hover,
summary[data-testid="stExpanderSummary"]:focus,
summary[data-testid="stExpanderSummary"]:focus-visible,
summary[data-testid="stExpanderSummary"]:active,
.streamlit-expanderHeader:hover,
[data-testid="stExpander"] summary:hover,
[data-testid="stExpander"] summary:focus,
[data-testid="stExpander"] details[open] > summary:hover,
[data-testid="stExpander"] details[open] > summary:focus {{
    background-color: var(--surface-container-high) !important;
    background: var(--surface-container-high) !important;
    color: var(--md-primary) !important;
    outline: none !important;
    box-shadow: none !important;
}}

[data-testid="stExpander"] details[open] > summary,
[data-testid="stExpander"] details[open] > summary[data-testid="stExpanderSummary"],
[data-testid="stExpander"] details[open] > .streamlit-expanderHeader {{
    background-color: var(--surface-container) !important;
    background: var(--surface-container) !important;
    border-bottom: 1px solid var(--border-outline-variant) !important;
    border-bottom-left-radius: 0 !important;
    border-bottom-right-radius: 0 !important;
}}

summary[data-testid="stExpanderSummary"] *,
.streamlit-expanderHeader *,
[data-testid="stExpander"] summary *,
[data-testid="stExpander"] details[open] > summary * {{
    color: var(--text-primary) !important;
    background-color: transparent !important;
}}

summary[data-testid="stExpanderSummary"] p,
summary[data-testid="stExpanderSummary"] span,
summary[data-testid="stExpanderSummary"] [data-testid="stMarkdownContainer"],
summary[data-testid="stExpanderSummary"] [data-testid="stMarkdownContainer"] p {{
    color: var(--text-primary) !important;
    margin: 0 !important;
    padding: 0 !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    line-height: 1.35 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}

summary[data-testid="stExpanderSummary"] svg,
[data-testid="stExpanderToggleIcon"] svg,
[data-testid="stExpander"] summary svg {{
    fill: var(--text-secondary) !important;
    color: var(--text-secondary) !important;
    min-width: 18px !important;
    width: 18px !important;
    height: 18px !important;
    transition: fill 0.15s ease, color 0.15s ease !important;
}}

summary[data-testid="stExpanderSummary"]:hover svg,
[data-testid="stExpander"] summary:hover svg {{
    fill: var(--md-primary) !important;
    color: var(--md-primary) !important;
}}

[data-testid="stExpanderDetails"] {{
    background-color: var(--surface-container) !important;
    background: var(--surface-container) !important;
    color: var(--text-primary) !important;
    padding: 1.1rem 1.25rem 1.25rem 1.25rem !important;
    border: none !important;
}}

[data-testid="stExpanderDetails"] * {{
    color: var(--text-primary);
}}

[data-testid="stChatMessage"] {{
    background-color: var(--surface-container-low) !important;
    border: 1.5px solid var(--border-outline-variant) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.1rem 1.35rem !important;
    margin-bottom: 0.95rem !important;
    color: var(--text-primary) !important;
}}

[data-testid="stChatInput"] {{
    background-color: var(--bg-surface) !important;
    border: 1.5px solid var(--border-outline-variant) !important;
    border-radius: var(--radius-md) !important;
}}

[data-testid="stChatInput"]:focus-within {{
    border-color: var(--md-primary) !important;
}}

[data-testid="stChatInput"] textarea {{
    color: var(--text-primary) !important;
}}

/* =============================================================
   9. RADIO BUTTONS, SLIDERS, TABS, ALERTS & CODE
   ============================================================= */
div[data-testid="stRadio"] > div {{
    background-color: transparent !important;
    border: none !important;
    padding: 0.25rem 0 !important;
}}

div[data-testid="stRadio"] label,
div[data-testid="stRadio"] label p,
div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {{
    color: var(--text-primary) !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
}}

div[data-testid="stRadio"] input[type="radio"] {{
    accent-color: var(--md-primary) !important;
}}

/* Sliders */
div[data-testid="stSlider"] [data-baseweb="slider"] div {{
    color: var(--text-primary) !important;
}}

div[data-testid="stSlider"] div[role="slider"] {{
    background-color: var(--md-primary) !important;
    border: 2px solid var(--bg-surface) !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2) !important;
}}

/* Tabs */
button[data-baseweb="tab"] {{
    background-color: transparent !important;
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
    border: none !important;
    font-size: 0.92rem !important;
    padding: 0.6rem 1.1rem !important;
    transition: color 0.15s ease !important;
}}

button[data-baseweb="tab"]:hover {{
    color: var(--text-primary) !important;
}}

button[data-baseweb="tab"][aria-selected="true"] {{
    color: var(--md-primary) !important;
    font-weight: 700 !important;
}}

div[data-baseweb="tab-highlight"] {{
    background-color: var(--md-primary) !important;
}}

div[data-baseweb="tab-border"] {{
    background-color: var(--border-outline-variant) !important;
}}

/* Streamlit Alerts / Callouts */
[data-testid="stAlert"] {{
    background-color: var(--surface-container-low) !important;
    border: 1.5px solid var(--border-outline-variant) !important;
    border-radius: var(--radius-md) !important;
    padding: 0.9rem 1.25rem !important;
    color: var(--text-primary) !important;
}}

[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p,
[data-testid="stAlert"] [data-testid="stMarkdownContainer"] span {{
    color: var(--text-primary) !important;
}}

[data-testid="stAlert"]:has([data-testid="stNotificationContentSuccess"]) {{
    border-left: 5px solid var(--md-tertiary) !important;
}}

[data-testid="stAlert"]:has([data-testid="stNotificationContentInfo"]) {{
    border-left: 5px solid var(--md-cyan) !important;
}}

[data-testid="stAlert"]:has([data-testid="stNotificationContentWarning"]) {{
    border-left: 5px solid var(--md-amber) !important;
}}

[data-testid="stAlert"]:has([data-testid="stNotificationContentError"]) {{
    border-left: 5px solid var(--md-error) !important;
}}

/* Code & Inline Code */
code:not([class*="language-"]) {{
    background-color: var(--surface-container-high) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-outline-variant) !important;
    border-radius: var(--radius-xs) !important;
    padding: 0.15rem 0.4rem !important;
    font-size: 0.85em !important;
}}

pre {{
    background-color: var(--surface-container-low) !important;
    border: 1.5px solid var(--border-outline-variant) !important;
    border-radius: var(--radius-md) !important;
    padding: 1rem !important;
}}
}}

/* Clean Dividers */
hr {{
    border: none !important;
    border-top: 1px solid var(--border-outline-variant) !important;
    margin: 1.25rem 0 !important;
}}

/* SWAT Kanban Board Styles */
.swat-board-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-top: 10px;
    margin-bottom: 20px;
}}

@media (max-width: 960px) {{
    .swat-board-grid {{
        grid-template-columns: repeat(2, 1fr);
    }}
}}

@media (max-width: 580px) {{
    .swat-board-grid {{
        grid-template-columns: 1fr;
    }}
}}

.swat-col-card {{
    background: var(--surface-container-low);
    border: 1px solid var(--border-outline-variant);
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    height: 350px;
    overflow: hidden;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}}

.swat-col-card:hover {{
    border-color: var(--border-outline);
}}

.swat-col-header {{
    padding: 12px 14px 10px 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--border-outline-variant);
    font-weight: 700;
    font-size: 0.86rem;
}}

.swat-col-header-strong {{
    border-top: 3px solid var(--md-tertiary);
    color: var(--md-tertiary);
}}

.swat-col-header-average {{
    border-top: 3px solid var(--md-amber);
    color: var(--md-amber);
}}

.swat-col-header-weak {{
    border-top: 3px solid var(--md-error);
    color: var(--md-error);
}}

.swat-col-header-unattempted {{
    border-top: 3px solid var(--text-muted);
    color: var(--text-secondary);
}}

.swat-count-badge {{
    font-size: 0.72rem;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 10px;
    background: var(--surface-container-high);
    color: var(--text-primary);
}}

.swat-col-scroll {{
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}}

.swat-col-scroll::-webkit-scrollbar {{
    width: 5px;
}}

.swat-col-scroll::-webkit-scrollbar-track {{
    background: transparent;
}}

.swat-col-scroll::-webkit-scrollbar-thumb {{
    background: var(--border-outline-variant);
    border-radius: 4px;
}}

.swat-col-scroll::-webkit-scrollbar-thumb:hover {{
    background: var(--border-outline);
}}

.swat-item-card {{
    background: var(--surface-container);
    border: 1px solid var(--border-outline-variant);
    border-radius: 6px;
    padding: 7px 10px;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 8px;
    font-size: 0.83rem;
    transition: background 0.15s ease, border-color 0.15s ease;
}}

.swat-item-card:hover {{
    background: var(--surface-container-high);
    border-color: var(--border-outline);
}}

.swat-item-title {{
    flex: 1;
    min-width: 0;
    font-weight: 500;
    color: var(--text-primary);
    line-height: 1.35;
    word-break: break-word;
}}

.swat-item-num {{
    font-weight: 700;
    color: var(--text-muted);
    margin-right: 4px;
}}

.swat-item-score {{
    font-weight: 700;
    font-size: 0.78rem;
    padding: 1px 6px;
    border-radius: 4px;
    white-space: nowrap;
    flex-shrink: 0;
    margin-top: 1px;
}}

.swat-score-strong {{
    background: var(--surface-container-highest);
    color: var(--md-tertiary);
}}

.swat-score-average {{
    background: var(--surface-container-highest);
    color: var(--md-amber);
}}

.swat-score-weak {{
    background: var(--surface-container-highest);
    color: var(--md-error);
}}

.swat-empty-state {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    text-align: center;
    color: var(--text-muted);
    font-size: 0.8rem;
    padding: 20px 10px;
}}

/* Role Selection / Login Screen Styles */
.login-hero {{
    text-align: center;
    max-width: 760px;
    margin: 1.5rem auto 2.2rem auto;
    padding: 0 1rem;
}}

.login-brand {{
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--text-primary);
    line-height: 1.1;
    margin-bottom: 0.4rem;
}}

.login-brand-accent {{
    color: var(--md-primary);
}}

.login-tagline {{
    font-size: 1.1rem;
    color: var(--text-secondary);
    font-weight: 400;
    margin-bottom: 0.35rem;
}}

.login-subtagline {{
    font-size: 0.88rem;
    color: var(--text-muted);
}}

.role-card-box {{
    background: var(--surface-container-low);
    border: 1.5px solid var(--border-outline-variant);
    border-radius: 16px;
    padding: 1.6rem 1.6rem 1.2rem 1.6rem;
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    height: 100%;
    display: flex;
    flex-direction: column;
}}

.role-card-box:hover {{
    border-color: var(--md-primary);
    box-shadow: 0 8px 24px var(--card-shadow);
}}

.role-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 0.85rem;
}}

.role-icon-circle {{
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.role-icon-student {{
    background: var(--surface-container-highest);
    color: var(--md-primary);
}}

.role-icon-teacher {{
    background: var(--surface-container-highest);
    color: var(--md-tertiary);
}}

.role-title {{
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
}}

.role-desc {{
    font-size: 0.88rem;
    color: var(--text-secondary);
    line-height: 1.45;
    margin-bottom: 1.2rem;
    min-height: 48px;
}}

.login-form-card {{
    background: var(--surface-container-low);
    border: 1.5px solid var(--border-outline-variant);
    border-radius: 16px;
    padding: 2rem 2.2rem;
    margin: 1rem auto 2rem auto;
    box-shadow: 0 10px 30px var(--card-shadow);
}}

.login-form-header {{
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border-outline-variant);
}}

/* =============================================================
   10. SECTION BOUNDARIES & DISTINCT VISUAL CONTAINERS
   ============================================================= */
.section-card {{
    background: var(--surface-container-low);
    border: 1px solid var(--border-outline-variant);
    border-radius: var(--radius-lg);
    padding: 1.25rem 1.4rem;
    margin-bottom: 1.5rem;
}}

.section-header-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 0.85rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-outline-variant);
}}

.section-tag {{
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 2px 8px;
    border-radius: 4px;
    background: var(--surface-container-highest);
    color: var(--text-secondary);
}}

.section-title-text {{
    font-family: 'Outfit', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.01em;
    margin: 0;
}}

.section-subtitle-text {{
    font-size: 0.84rem;
    color: var(--text-secondary);
    margin-top: 2px;
}}

/* Socrates Learning System Mode Styling */
.socrates-banner {{
    background: linear-gradient(135deg, var(--surface-container-high) 0%, var(--surface-container) 100%);
    border: 1px solid var(--md-amber);
    border-radius: var(--radius-md);
    padding: 1.1rem 1.4rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 4px 14px var(--card-shadow);
}}

.socrates-avatar {{
    font-size: 2.2rem;
    line-height: 1;
    background: var(--md-amber-container);
    color: var(--md-on-amber-container);
    width: 52px;
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    border: 2px solid var(--md-amber);
    flex-shrink: 0;
}}

.socrates-banner-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--md-amber);
    margin: 0;
}}

.socrates-banner-sub {{
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin-top: 2px;
    font-style: italic;
}}

.socrates-hint-tier1 {{
    background: rgba(251, 191, 36, 0.09);
    border-left: 4px solid var(--md-amber);
    border-radius: var(--radius-sm);
    padding: 0.9rem 1.1rem;
    margin: 0.6rem 0;
    color: var(--text-primary);
    font-size: 0.92rem;
    line-height: 1.5;
}}

.socrates-hint-tier2 {{
    background: rgba(52, 211, 153, 0.09);
    border-left: 4px solid var(--md-tertiary);
    border-radius: var(--radius-sm);
    padding: 0.9rem 1.1rem;
    margin: 0.6rem 0;
    color: var(--text-primary);
    font-size: 0.92rem;
    line-height: 1.5;
}}

.socrates-hint-tier3 {{
    background: rgba(192, 132, 252, 0.09);
    border-left: 4px solid var(--md-secondary);
    border-radius: var(--radius-sm);
    padding: 0.9rem 1.1rem;
    margin: 0.6rem 0;
    color: var(--text-primary);
    font-size: 0.92rem;
    line-height: 1.5;
}}

.socrates-reflection-box {{
    background: rgba(248, 113, 113, 0.08);
    border: 1px solid var(--md-error);
    border-radius: var(--radius-md);
    padding: 1.1rem 1.3rem;
    margin: 0.8rem 0;
    color: var(--text-primary);
    line-height: 1.55;
    font-size: 0.94rem;
}}

.socrates-success-box {{
    background: rgba(52, 211, 153, 0.08);
    border: 1px solid var(--md-tertiary);
    border-radius: var(--radius-md);
    padding: 1.1rem 1.3rem;
    margin: 0.8rem 0;
    color: var(--text-primary);
    line-height: 1.55;
    font-size: 0.94rem;
}}

.socrates-chat-header {{
    font-family: 'Outfit', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--md-amber);
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 0.4rem;
}}

.socrates-chat-msg-user {{
    background: var(--surface-container-highest);
    border-radius: 12px 12px 2px 12px;
    padding: 8px 12px;
    margin: 4px 0 4px auto;
    max-width: 85%;
    font-size: 0.88rem;
    color: var(--text-primary);
}}

.socrates-chat-msg-bot {{
    background: var(--surface-container-low);
    border: 1px solid var(--border-outline-variant);
    border-radius: 12px 12px 12px 2px;
    padding: 9px 13px;
    margin: 4px auto 4px 0;
    max-width: 90%;
    font-size: 0.88rem;
    color: var(--text-primary);
    line-height: 1.45;
}}

/* Quiz Mode Selection Cards */
.quiz-mode-card {{
    background: var(--surface-container);
    border: 1px solid var(--border-outline-variant);
    border-radius: var(--radius-md);
    padding: 1.1rem 1.3rem;
    transition: all 0.2s ease-in-out;
    margin-bottom: 0.6rem;
}}

.quiz-mode-card-active {{
    background: var(--surface-container-high);
    border: 2px solid var(--md-amber) !important;
    box-shadow: 0 4px 16px rgba(251, 191, 36, 0.12);
}}

.quiz-mode-card-active-std {{
    background: var(--surface-container-high);
    border: 2px solid var(--md-primary) !important;
    box-shadow: 0 4px 16px var(--card-shadow);
}}

.quiz-mode-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.4rem;
}}

.quiz-mode-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 8px;
}}

.quiz-mode-badge {{
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 2px 8px;
    border-radius: 4px;
}}

.quiz-mode-badge-rec {{
    background: var(--md-amber-container);
    color: var(--md-on-amber-container);
    border: 1px solid var(--md-amber);
}}

.quiz-mode-badge-std {{
    background: var(--surface-container-highest);
    color: var(--text-secondary);
    border: 1px solid var(--border-outline-variant);
}}

.quiz-mode-desc {{
    font-size: 0.84rem;
    color: var(--text-secondary);
    line-height: 1.45;
    margin: 0;
}}


/* Hide unnecessary default Streamlit decoration and sidebar */
#MainMenu, footer {{
    visibility: hidden;
}}

header {{
    background: transparent !important;
}}
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
section[data-testid="stSidebar"] {{
    display: none !important;
}}
</style>
    """
    st.markdown(css, unsafe_allow_html=True)
