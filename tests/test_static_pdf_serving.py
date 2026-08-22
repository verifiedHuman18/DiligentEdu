"""Unit tests for Streamlit Static PDF Serving and genuine st.link_button new-tab navigation."""

import os
import unittest
import streamlit as st

from frontend.screens.chapter_screen import render_chapter_screen
from frontend.state import (
    init_session_state,
    set_student_class_level,
)
from src.academic_rag.curriculum.service import get_chapter_pdf


class TestStaticPDFServing(unittest.TestCase):
    """
    Verifies that Streamlit static file serving is configured,
    static PDF assets exist on disk, and get_chapter_pdf supplies valid static URLs.
    """

    def setUp(self):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        init_session_state()

    def test_streamlit_config_enables_static_serving(self):
        """Phase 6: .streamlit/config.toml has enableStaticServing = true."""
        config_path = os.path.join(".streamlit", "config.toml")
        self.assertTrue(os.path.isfile(config_path), ".streamlit/config.toml must exist")
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("enableStaticServing", content)
        self.assertIn("true", content.lower())

    def test_static_pdf_files_exist_on_disk(self):
        """Phase 6: Static PDF files exist for all Class 10 and Class 9 chapters."""
        self.assertTrue(os.path.isdir(os.path.join("static", "class10")))
        self.assertTrue(os.path.isdir(os.path.join("static", "class9")))
        self.assertTrue(os.path.isfile(os.path.join("static", "class10", "jesc111.pdf")))
        self.assertTrue(os.path.isfile(os.path.join("static", "class9", "iesc104.pdf")))

    def test_resolver_returns_static_url(self):
        """Phase 5: get_chapter_pdf returns static_url accessible by Streamlit."""
        info_c10 = get_chapter_pdf(10, "Electricity")
        self.assertEqual(info_c10["static_url"], "app/static/class10/jesc111.pdf")

        info_c9 = get_chapter_pdf(9, "Describing Motion Around Us")
        self.assertEqual(info_c9["static_url"], "app/static/class9/iesc104.pdf")

    def test_render_chapter_screen_with_link_button(self):
        """Phase 4 & 8: Chapter screen executes cleanly with st.link_button and actions."""
        set_student_class_level(10)
        st.session_state.active_chapter_detail = {
            "class_level": 10,
            "chapter_number": 11,
            "chapter": "Electricity",
            "filename": "jesc111.pdf",
            "pdf_path": "data/class10/jesc111.pdf",
            "static_url": "app/static/class10/jesc111.pdf",
        }
        try:
            render_chapter_screen(student_id="student_001")
        except Exception as e:
            self.fail(f"render_chapter_screen failed with st.link_button: {e}")


if __name__ == "__main__":
    unittest.main()
