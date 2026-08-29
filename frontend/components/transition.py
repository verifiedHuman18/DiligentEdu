"""Unified Page Transition Controller, Branded Loading States, and Error Boundaries for DiligentEdu (Phases 1-24)."""

import textwrap
import time
from typing import Callable, Dict, Optional

import streamlit as st

MODULE_TRANSITION_MESSAGES: Dict[str, str] = {
    "home": "Loading your curriculum workspace...",
    "quiz": "Preparing your quiz...",
    "tutor": "Opening Tutor...",
    "swat": "Loading your performance analytics...",
    "scholarships": "Finding relevant scholarships...",
    "knowledge_graph": "Building your topic concept map...",
    "chapter": "Opening NCERT Chapter...",
    "study_material": "Opening Study Materials...",
    "study_twin": "Connecting with Study Twins...",
    "settings": "Opening Settings & Configuration...",
    "teacher": "Opening Educator Portal...",
    "admin_home": "Opening Administrator Portal...",
    "login": "Preparing login portal...",
}


class TransitionController:
    """Centralized controller for application navigation transitions and loading lifecycle (Phases 3-7)."""

    @staticmethod
    def start_transition(target_screen: str, message: Optional[str] = None) -> None:
        """Starts a transition toward the target screen with an appropriate contextual message."""
        st.session_state.is_transitioning = True
        st.session_state.transition_target = target_screen
        st.session_state.transition_start_time = time.time()
        st.session_state.transition_message = message or MODULE_TRANSITION_MESSAGES.get(
            target_screen, "Loading Workspace..."
        )

    @staticmethod
    def is_transitioning() -> bool:
        """Returns True if a navigation transition is currently active."""
        if not st.session_state.get("is_transitioning", False):
            return False
        # Failsafe: auto-expire transition if running for more than 8 seconds (Phase 17)
        start_time = st.session_state.get("transition_start_time", 0)
        if start_time and (time.time() - start_time > 8.0):
            TransitionController.finish_transition()
            return False
        return True

    @staticmethod
    def get_transition_message() -> str:
        """Retrieves the current transition message."""
        return st.session_state.get("transition_message", "Loading Workspace...")

    @staticmethod
    def finish_transition() -> None:
        """Marks the active transition as finished."""
        st.session_state.is_transitioning = False
        st.session_state.transition_target = None
        st.session_state.transition_message = None
        st.session_state.transition_start_time = None


# Module-level convenience functions
start_transition = TransitionController.start_transition
is_transitioning = TransitionController.is_transitioning
get_transition_message = TransitionController.get_transition_message
finish_transition = TransitionController.finish_transition


def render_global_transition_layer() -> None:
    """
    Renders the global transition overlay at the top of the Application Shell (Phases 7, 8, 9, 10).
    Uses Material Design 3 surfaces and typography with smooth fade-out to prevent black flashes.
    """
    if not is_transitioning():
        return

    msg = get_transition_message()

    html = textwrap.dedent(f"""\
    <style>
    @keyframes transition-fade-out {{
        0% {{ opacity: 1; visibility: visible; }}
        75% {{ opacity: 1; visibility: visible; }}
        100% {{ opacity: 0; visibility: hidden; pointer-events: none; }}
    }}
    .global-transition-overlay {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        width: 100vw;
        height: 100vh;
        background-color: var(--bg-app, #191310);
        z-index: 99999;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        pointer-events: all;
        animation: transition-fade-out 0.8s cubic-bezier(0.4, 0, 0.2, 1) forwards;
    }}
    .global-transition-spinner {{
        width: 44px;
        height: 44px;
        border: 3.5px solid var(--surface-container-highest, #45372e);
        border-top-color: var(--md-amber, #fbbf24);
        border-radius: 50%;
        animation: global-spin 0.85s linear infinite;
        margin-bottom: 22px;
    }}
    @keyframes global-spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    .global-transition-brand {{
        font-family: 'Outfit', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        color: var(--text-primary, #faf0e6);
        margin-bottom: 24px;
        letter-spacing: -0.03em;
    }}
    .global-transition-accent {{
        color: var(--md-amber, #fbbf24);
    }}
    .global-transition-title {{
        font-family: 'Outfit', sans-serif;
        font-size: 1.15rem;
        font-weight: 600;
        color: var(--text-primary, #faf0e6);
        margin-bottom: 6px;
        letter-spacing: -0.01em;
    }}
    .global-transition-sub {{
        font-size: 0.85rem;
        color: var(--text-muted, #a89587);
        font-family: 'Inter', sans-serif;
    }}
    </style>
    <div class="global-transition-overlay" id="global-transition-overlay">
        <div class="global-transition-brand">
            Diligent<span class="global-transition-accent">Edu</span>
        </div>
        <div class="global-transition-spinner"></div>
        <div class="global-transition-title">{msg}</div>
        <div class="global-transition-sub">Preparing your interactive learning workspace...</div>
    </div>
    """)
    st.markdown(html, unsafe_allow_html=True)


def render_screen_loader(
    title: str = "DiligentEdu",
    subtitle: str = "Loading Workspace...",
    message: Optional[str] = None,
) -> None:
    """
    Renders an in-page section loader for asynchronous component operations.
    """
    sub_text = message or subtitle
    html = textwrap.dedent(f"""\
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 380px; width: 100%; padding: 40px 20px; text-align: center;">
        <div style="margin-bottom: 24px;">
            <span class="brand-corner" style="font-size: 2.2rem;">Diligent<span class="brand-corner-accent">Edu</span></span>
        </div>
        <div style="width: 44px; height: 44px; border: 3.5px solid var(--surface-container-highest); border-top-color: var(--md-amber); border-radius: 50%; animation: spin 0.85s linear infinite; margin-bottom: 22px;"></div>
        <div style="font-family: 'Outfit', sans-serif; font-size: 1.15rem; font-weight: 600; color: var(--text-primary); margin-bottom: 6px; letter-spacing: -0.01em;">
            {sub_text}
        </div>
        <div style="font-size: 0.85rem; color: var(--text-muted); font-family: 'Inter', sans-serif;">
            Preparing your interactive learning environment...
        </div>
    </div>
    <style>
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """)
    st.markdown(html, unsafe_allow_html=True)


def render_skeleton_card(height_px: int = 180, count: int = 1) -> None:
    """
    Renders animated shimmer skeleton placeholder cards to prevent layout shifts during async data loading.
    """
    skeletons_html = ""
    for _ in range(count):
        skeletons_html += f"""
        <div style="width: 100%; height: {height_px}px; background: linear-gradient(90deg, var(--surface-container-low) 25%, var(--surface-container-high) 50%, var(--surface-container-low) 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 14px; border: 1px solid var(--border-outline-variant); margin-bottom: 16px;"></div>
        """

    html = textwrap.dedent(f"""\
    <style>
    @keyframes shimmer {{
        0% {{ background-position: 200% 0; }}
        100% {{ background-position: -200% 0; }}
    }}
    </style>
    {skeletons_html}
    """)
    st.markdown(html, unsafe_allow_html=True)


def render_error_boundary(
    title: str = "Unable to load this section",
    message: str = "A temporary connection issue occurred. Please check your network or try again.",
    retry_label: str = "Retry",
    on_retry: Optional[Callable[[], None]] = None,
    key_suffix: str = "default",
) -> None:
    """
    Renders a clean, centered error boundary card with optional retry action to prevent broken half-screens.
    """
    card_html = textwrap.dedent(f"""\
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 320px; padding: 32px 24px; background: var(--surface-container); border: 1px solid var(--border-outline-variant); border-radius: 16px; text-align: center; margin: 20px 0;">
        <div style="width: 52px; height: 52px; border-radius: 50%; background: var(--md-error-container); display: flex; align-items: center; justify-content: center; margin-bottom: 18px; color: var(--md-error);">
            <span class="material-symbols-outlined" style="font-size: 1.8rem;">warning</span>
        </div>
        <div style="font-family: 'Outfit', sans-serif; font-size: 1.25rem; font-weight: 700; color: var(--text-primary); margin-bottom: 8px;">
            {title}
        </div>
        <div style="font-size: 0.9rem; color: var(--text-secondary); max-width: 480px; line-height: 1.5; margin-bottom: 24px;">
            {message}
        </div>
    </div>
    """)
    st.markdown(card_html, unsafe_allow_html=True)

    if on_retry or retry_label:
        col_pad1, col_btn, col_pad2 = st.columns([1.5, 1, 1.5])
        with col_btn:
            if st.button(
                retry_label, key=f"retry_btn_{key_suffix}", type="primary", use_container_width=True
            ):
                if on_retry:
                    on_retry()
                st.rerun()
