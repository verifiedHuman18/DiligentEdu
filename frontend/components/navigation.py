"""Shared Navigation Components across DiligentEdu screens (Phases 1-19).

Provides a single, standardized "Back to Home" navigation button:
- Single implementation
- Single styling & layout contract
- State-preserving navigation back to the Home screen
"""

from typing import Optional

import streamlit as st

from frontend.state import navigate_to


def render_back_to_home(screen_name: Optional[str] = None) -> bool:
    """Renders the standardized, compact "Back to Home" button at the top of a screen.

    Parameters:
        screen_name: Optional screen identifier used to generate a unique button key.

    Returns:
        True if the button was clicked and navigation was triggered, False otherwise.
    """
    current_screen = st.session_state.get("current_screen", "screen")
    key_ident = f"btn_back_to_home_{screen_name or current_screen}"

    # Render standardized compact secondary button with arrow icon
    if st.button(
        "Back to Home",
        icon=":material/arrow_back:",
        type="secondary",
        key=key_ident,
        help="Return to Home Dashboard",
    ):
        navigate_to("home")
        st.rerun()
        return True

    st.write("")
    return False
