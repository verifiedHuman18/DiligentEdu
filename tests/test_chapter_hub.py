"""Unit tests for Phases 1 to 4: Chapter Detail Hub & New Tab PDF Viewer."""

import os
import tempfile
import unittest

import streamlit as st

import backend
from backend.curriculum.service import get_chapter_pdf
from backend.storage.repository import QuizRepository
from frontend.screens.chapter_screen import render_chapter_screen
from frontend.state import (
    init_session_state,
    set_student_class_level,
)


class TestChapterHub(unittest.TestCase):
    """
    Verifies that Chapter Detail Hub integrates chapter metadata,
    mastery analytics, and chapter-filtered quiz history.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_chapter_hub.db")
        self.repo = QuizRepository(db_path=self.db_path)
        self.student_id = "student_hub_test"

        for k in list(st.session_state.keys()):
            del st.session_state[k]
        init_session_state()

        # Seed 2 attempts for Electricity (Class 10)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Electricity",
                "chapter_number": 11,
                "difficulty": "easy",
                "questions": [
                    {"question_id": f"q_elec1_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)},
        )
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Electricity",
                "chapter_number": 11,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"q_elec2_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 3 else "B" for i in range(1, 6)},
        )

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_chapter_hub_metadata_and_swat_data(self):
        """Phase 1: Validates that chapterId, chapterName, classLevel, pdfPath, and performance are accessible."""
        pdf_info = get_chapter_pdf(10, "Electricity")
        self.assertEqual(pdf_info["class_level"], 10)
        self.assertEqual(pdf_info["chapter_id"], "class10_science_electricity")
        self.assertEqual(pdf_info["chapter_name"], "Electricity")
        self.assertEqual(pdf_info["pdf_path"], "data/class10/jesc111.pdf")
        self.assertTrue(pdf_info["exists"])

        swat = backend.get_student_swat(self.student_id, class_level=10, db_path=self.db_path)
        ch_stats = swat["chapter_breakdown"]["Electricity"]
        self.assertEqual(ch_stats["attempts"], 2)
        self.assertEqual(ch_stats["status"], "average")
        self.assertEqual(ch_stats["score"], 50)  # average of 40 and 60

    def test_chapter_quiz_history_filtering(self):
        """Phase 4: Filters history specifically for Electricity."""
        history = self.repo.get_student_class_history(self.student_id, class_level=10)
        ch_history = [h for h in history if h.get("chapter") == "Electricity"]
        self.assertEqual(len(ch_history), 2)
        self.assertEqual(ch_history[0]["score"], 2)
        self.assertEqual(ch_history[1]["score"], 3)

    def test_render_chapter_hub_screen(self):
        """Phase 1-4: Screen executes cleanly."""
        set_student_class_level(10)
        st.session_state.active_chapter_detail = {
            "class_level": 10,
            "chapter_number": 11,
            "chapter": "Electricity",
            "filename": "jesc111.pdf",
            "pdf_path": "data/class10/jesc111.pdf",
        }
        try:
            render_chapter_screen(student_id=self.student_id)
        except Exception as e:
            self.fail(f"render_chapter_screen failed on hub view: {e}")


if __name__ == "__main__":
    unittest.main()
