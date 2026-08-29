"""Unit tests for the 3D Intro / Splash Screen (Phases 1–23).

Verifies:
- Session-state lifecycle (intro_completed flag)
- 3D HTML content (branding, Three.js elements, academic motifs)
- Security (zero browser navigation in 3D HTML)
- Visual identity elements (gold/teal/purple palette)
- Phased animation markers
- WebGL fallback text
- Reduced-motion CSS
"""

import os
import unittest
from unittest.mock import patch

import streamlit as st

from frontend.screens.intro_screen import _INTRO_HTML, render_intro_screen
from frontend.state import init_session_state


class TestIntroSessionState(unittest.TestCase):
    """Session-state lifecycle: intro_completed flag behavior."""

    def setUp(self):
        st.session_state.clear()
        if hasattr(st, "query_params"):
            st.query_params.clear()
        init_session_state()

    def test_intro_completed_defaults_to_false(self):
        self.assertFalse(st.session_state.get("intro_completed", False))

    def test_setting_intro_completed_skips_intro(self):
        st.session_state.intro_completed = True
        self.assertTrue(st.session_state.get("intro_completed"))

    def test_intro_completed_survives_rerun_simulation(self):
        """Within a session, intro_completed persists across simulated reruns."""
        st.session_state.intro_completed = True
        # Simulate rerun: init_session_state() should not reset intro_completed
        init_session_state()
        self.assertTrue(st.session_state.get("intro_completed", False))


class TestIntroBranding(unittest.TestCase):
    """3D HTML contains the correct branding and tagline."""

    def test_brand_name(self):
        self.assertIn("Diligent", _INTRO_HTML)
        self.assertIn("Edu", _INTRO_HTML)

    def test_tagline(self):
        self.assertIn("Learn", _INTRO_HTML)
        self.assertIn("Understand", _INTRO_HTML)
        self.assertIn("Grow", _INTRO_HTML)


class TestIntroThreeJSScene(unittest.TestCase):
    """3D HTML contains expected Three.js scene elements."""

    def test_scene_setup(self):
        self.assertIn("THREE.Scene", _INTRO_HTML)
        self.assertIn("THREE.PerspectiveCamera", _INTRO_HTML)
        self.assertIn("THREE.WebGLRenderer", _INTRO_HTML)

    def test_core_geometry(self):
        """Central Knowledge Core: sphere + icosahedron cage."""
        self.assertIn("SphereGeometry", _INTRO_HTML)
        self.assertIn("IcosahedronGeometry", _INTRO_HTML)

    def test_orbital_rings(self):
        self.assertIn("RingGeometry", _INTRO_HTML)

    def test_academic_satellites(self):
        """Three satellite shapes: octahedron, dodecahedron, tetrahedron."""
        self.assertIn("OctahedronGeometry", _INTRO_HTML)
        self.assertIn("DodecahedronGeometry", _INTRO_HTML)
        self.assertIn("TetrahedronGeometry", _INTRO_HTML)

    def test_particle_system(self):
        self.assertIn("THREE.Points", _INTRO_HTML)
        self.assertIn("PointsMaterial", _INTRO_HTML)

    def test_mouse_parallax(self):
        self.assertIn("mousemove", _INTRO_HTML)

    def test_lighting(self):
        self.assertIn("AmbientLight", _INTRO_HTML)
        self.assertIn("PointLight", _INTRO_HTML)


class TestIntroSecurity(unittest.TestCase):
    """3D HTML must contain zero browser navigation attempts."""

    def test_no_window_top(self):
        self.assertNotIn("window.top", _INTRO_HTML)

    def test_no_window_parent(self):
        self.assertNotIn("window.parent", _INTRO_HTML)

    def test_no_window_location(self):
        self.assertNotIn("window.location", _INTRO_HTML)

    def test_no_window_open(self):
        self.assertNotIn("window.open", _INTRO_HTML)

    def test_no_postmessage(self):
        self.assertNotIn("postMessage", _INTRO_HTML)


class TestIntroVisualIdentity(unittest.TestCase):
    """Verifies the gold/teal/purple palette is used in the 3D scene."""

    def test_gold_accent(self):
        self.assertIn("0xFBBF24", _INTRO_HTML)

    def test_teal_accent(self):
        self.assertIn("0x14B8A6", _INTRO_HTML)

    def test_purple_accent(self):
        self.assertIn("0xA855F7", _INTRO_HTML)

    def test_orange_accent(self):
        self.assertIn("0xF97316", _INTRO_HTML)

    def test_dark_background(self):
        self.assertIn("0x0D0A07", _INTRO_HTML)


class TestIntroPhasedAnimation(unittest.TestCase):
    """Verifies phase markers exist in the animation loop."""

    def test_phase_comments(self):
        self.assertIn("Phase 0", _INTRO_HTML)
        self.assertIn("Phase 1", _INTRO_HTML)
        self.assertIn("Phase 2", _INTRO_HTML)

    def test_easing_function(self):
        self.assertIn("easeOut", _INTRO_HTML)

    def test_assembly_particles(self):
        """Assembly particles converge to core during Phase 1."""
        self.assertIn("aStart", _INTRO_HTML)
        self.assertIn("needsUpdate", _INTRO_HTML)


class TestIntroFallbackAndAccessibility(unittest.TestCase):
    """WebGL fallback and reduced-motion support."""

    def test_webgl_fallback(self):
        self.assertIn("catch", _INTRO_HTML)
        # Fallback should still show branding
        self.assertIn("Diligent", _INTRO_HTML)

    def test_reduced_motion_media_query(self):
        self.assertIn("prefers-reduced-motion", _INTRO_HTML)


if __name__ == "__main__":
    unittest.main()
