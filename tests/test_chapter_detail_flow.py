"""Unit tests for Phases 5 to 8: Interactive Curriculum Cards & Dedicated Chapter Detail Screen."""

import unittest

import streamlit as st

from backend.curriculum.service import curriculum_service
from frontend.screens.chapter_screen import render_chapter_screen
from frontend.state import (
    init_session_state,
    set_student_class_level,
)


class TestChapterDetailFlow(unittest.TestCase):
    """
    Verifies that chapters resolve strictly with composite (class_level, chapter) keys,
    map to authoritative NCERT PDF filenames, and render detail pages without errors.
    """

    def setUp(self):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        init_session_state()

    def test_class_10_chapter_source_resolution(self):
        """Phase 8: Class 10 Electricity resolves to Ch 11 and jesc111.pdf."""
        ch_num, ch_title = curriculum_service.resolve_chapter(10, "Electricity")
        self.assertEqual(ch_num, 11)
        self.assertEqual(ch_title, "Electricity")

        # Verify PDF mapping
        c10_map = curriculum_service.get_mapping()["class10"]
        matched_file = None
        for fname, info in c10_map.items():
            if info["chapter_number"] == 11:
                matched_file = fname
                break
        self.assertEqual(matched_file, "jesc111.pdf")

    def test_class_9_chapter_source_resolution(self):
        """Phase 8: Class 9 Describing Motion resolves to Ch 4 and iesc104.pdf."""
        ch_num, ch_title = curriculum_service.resolve_chapter(9, "Describing Motion Around Us")
        self.assertEqual(ch_num, 4)
        self.assertEqual(ch_title, "Describing Motion Around Us")

        # Verify PDF mapping
        c9_map = curriculum_service.get_mapping()["class9"]
        matched_file = None
        for fname, info in c9_map.items():
            if info["chapter_number"] == 4:
                matched_file = fname
                break
        self.assertEqual(matched_file, "iesc104.pdf")

    def test_render_chapter_screen_class_10(self):
        """Phase 7: render_chapter_screen executes cleanly for Class 10 chapter."""
        set_student_class_level(10)
        st.session_state.active_chapter_detail = {
            "class_level": 10,
            "chapter_number": 11,
            "chapter": "Electricity",
            "filename": "jesc111.pdf",
        }
        try:
            render_chapter_screen(student_id="student_001")
        except Exception as e:
            self.fail(f"render_chapter_screen failed for Class 10: {e}")

    def test_render_chapter_screen_class_9(self):
        """Phase 7: render_chapter_screen executes cleanly for Class 9 chapter."""
        set_student_class_level(9)
        st.session_state.active_chapter_detail = {
            "class_level": 9,
            "chapter_number": 4,
            "chapter": "Describing Motion Around Us",
            "filename": "iesc104.pdf",
        }
        try:
            render_chapter_screen(student_id="student_001")
        except Exception as e:
            self.fail(f"render_chapter_screen failed for Class 9: {e}")


if __name__ == "__main__":
    unittest.main()
