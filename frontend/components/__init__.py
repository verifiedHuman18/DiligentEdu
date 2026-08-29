"""Components package exports."""

from frontend.components.cards import (
    get_status_badge_html,
    render_citation_box,
    render_metric_card,
)
from frontend.components.header import render_header
from frontend.components.navbar import render_navbar
from frontend.components.navigation import render_back_to_home
from frontend.components.scholarship_official_info import (
    get_canonical_portal_info,
    render_official_scholarship_info,
)
from frontend.components.theme_switcher import render_theme_switcher
from frontend.components.voice_assistant import (
    render_tts_player_component,
    render_voice_recorder_component,
)

__all__ = [
    "render_navbar",
    "render_header",
    "render_theme_switcher",
    "render_metric_card",
    "render_citation_box",
    "get_status_badge_html",
    "render_official_scholarship_info",
    "get_canonical_portal_info",
    "render_back_to_home",
    "render_voice_recorder_component",
    "render_tts_player_component",
]
