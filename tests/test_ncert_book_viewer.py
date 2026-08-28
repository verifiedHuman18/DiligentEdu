"""Unit tests for the NCERT Book Viewer & Class-Scoped PDF Resolver."""

import os
import unittest

import streamlit as st

import backend
from backend.curriculum.service import get_chapter_pdf
from backend.exceptions import ChapterNotFoundError
from frontend.screens.chapter_screen import render_chapter_screen
from frontend.state import (
    init_session_state,
    set_student_class_level,
)


class TestNCERTBookViewer(unittest.TestCase):
    """
    Verifies that get_chapter_pdf resolves authoritative PDF files with strict class scoping,
    and render_chapter_screen renders the native browser PDF viewer cleanly.
    """

    def setUp(self):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        init_session_state()

    def test_class_10_electricity_pdf_resolution(self):
        """Class 10 Electricity resolves to data/class10_sci/jesc111.pdf and exists on disk."""
        pdf_info = get_chapter_pdf(10, "Electricity")
        self.assertEqual(pdf_info["class_level"], 10)
        self.assertEqual(pdf_info["chapter_number"], 11)
        self.assertEqual(pdf_info["chapter_name"], "Electricity")
        self.assertEqual(pdf_info["filename"], "jesc111.pdf")
        self.assertEqual(pdf_info["pdf_path"], "data/class10_sci/jesc111.pdf")
        self.assertTrue(pdf_info["exists"])
        self.assertTrue(os.path.isfile(pdf_info["pdf_path"]))

    def test_class_10_chapter_1_pdf_resolution(self):
        """Class 10 Chapter 1 resolves to data/class10_sci/jesc101.pdf and exists on disk."""
        pdf_info = get_chapter_pdf(10, 1)
        self.assertEqual(pdf_info["class_level"], 10)
        self.assertEqual(pdf_info["chapter_number"], 1)
        self.assertEqual(pdf_info["chapter_name"], "Chemical Reactions and Equations")
        self.assertEqual(pdf_info["filename"], "jesc101.pdf")
        self.assertTrue(pdf_info["exists"])

    def test_class_9_motion_pdf_resolution(self):
        """Class 9 Describing Motion resolves to data/class9_sci/iesc104.pdf and exists on disk."""
        pdf_info = get_chapter_pdf(9, "Describing Motion Around Us")
        self.assertEqual(pdf_info["class_level"], 9)
        self.assertEqual(pdf_info["chapter_number"], 4)
        self.assertEqual(pdf_info["chapter_name"], "Describing Motion Around Us")
        self.assertEqual(pdf_info["filename"], "iesc104.pdf")
        self.assertEqual(pdf_info["pdf_path"], "data/class9_sci/iesc104.pdf")
        self.assertTrue(pdf_info["exists"])
        self.assertTrue(os.path.isfile(pdf_info["pdf_path"]))

    def test_class_9_chapter_2_cell_pdf_resolution(self):
        """Class 9 Chapter 2 resolves to data/class9_sci/iesc102.pdf and exists on disk."""
        pdf_info = get_chapter_pdf(9, 2)
        self.assertEqual(pdf_info["class_level"], 9)
        self.assertEqual(pdf_info["chapter_number"], 2)
        self.assertEqual(pdf_info["chapter_name"], "Cell: The Building Block of Life")
        self.assertEqual(pdf_info["filename"], "iesc102.pdf")
        self.assertTrue(pdf_info["exists"])

    def test_cross_class_isolation_rejection(self):
        """Electricity is a Class 10 chapter and should not resolve under Class 9."""
        with self.assertRaises((ChapterNotFoundError, ValueError)):
            get_chapter_pdf(9, "Electricity")

    def test_backend_curriculum_contains_pdf_path(self):
        """get_ncert_curriculum returns chapter_id and pdf_path for all chapters."""
        c10 = backend.get_ncert_curriculum(10)
        self.assertEqual(len(c10), 13)
        for ch in c10:
            self.assertIn("pdf_path", ch)
            self.assertTrue(ch["pdf_path"].startswith("data/class10_sci/"))
            self.assertTrue(os.path.isfile(ch["pdf_path"]))

        c9 = backend.get_ncert_curriculum(9)
        self.assertEqual(len(c9), 13)
        for ch in c9:
            self.assertIn("pdf_path", ch)
            self.assertTrue(ch["pdf_path"].startswith("data/class9_sci/"))
            self.assertTrue(os.path.isfile(ch["pdf_path"]))

    def test_render_chapter_screen_with_pdf_viewer(self):
        """render_chapter_screen renders the native PDF document viewer cleanly."""
        set_student_class_level(10)
        st.session_state.active_chapter_detail = {
            "class_level": 10,
            "chapter_number": 11,
            "chapter": "Electricity",
            "filename": "jesc111.pdf",
            "pdf_path": "data/class10/jesc111.pdf",
        }
        try:
            render_chapter_screen(student_id="student_001")
        except Exception as e:
            self.fail(f"render_chapter_screen failed with embedded PDF viewer: {e}")


if __name__ == "__main__":
    unittest.main()
