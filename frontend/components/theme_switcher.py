"""Theme Switcher Component (Dark / Light)."""

import streamlit as st

from frontend.styles import inject_custom_css


def render_theme_switcher(location: str = "sidebar") -> str:
    """
    Renders a theme selector widget for Dark / Light mode.

    Args:
        location: 'sidebar' or 'inline'

    Returns:
        The selected theme name ('Dark' or 'Light').
    """
    theme_options = ["Dark", "Light"]
    current_theme = st.session_state.get("theme", "Dark")
    if current_theme not in theme_options:
        current_theme = "Dark"
        st.session_state.theme = "Dark"

    current_idx = theme_options.index(current_theme)

    if location == "sidebar":
        st.markdown("#### Theme")
        selected_theme = st.selectbox(
            "Interface Mode",
            theme_options,
            index=current_idx,
            key="theme_switcher_select",
            help="Switch between Dark and Light mode",
        )
    else:
        selected_theme = st.selectbox(
            "Theme",
            theme_options,
            index=current_idx,
            key="theme_switcher_inline",
            label_visibility="collapsed",
        )

    if selected_theme != st.session_state.get("theme"):
        st.session_state.theme = selected_theme
        inject_custom_css(selected_theme)
        st.rerun()

    return selected_theme
