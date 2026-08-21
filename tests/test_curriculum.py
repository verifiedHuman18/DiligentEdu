"""Unit tests for CurriculumService."""

import unittest

from src.academic_rag.curriculum.service import curriculum_service
from src.academic_rag.exceptions import ChapterNotFoundError, CurriculumError


class TestCurriculumService(unittest.TestCase):
    """Tests chapter resolution, listing, and curriculum navigation."""

    def test_get_chapters_class10(self):
        chapters = curriculum_service.get_chapters_for_grade(10)
        self.assertEqual(len(chapters), 13)
        self.assertEqual(chapters[0].chapter_number, 1)
        self.assertEqual(chapters[0].chapter_title, "Chemical Reactions and Equations")
        self.assertEqual(chapters[10].chapter_number, 11)
        self.assertEqual(chapters[10].chapter_title, "Electricity")

    def test_get_chapters_class9(self):
        chapters = curriculum_service.get_chapters_for_grade(9)
        self.assertEqual(len(chapters), 13)
        self.assertEqual(chapters[0].chapter_number, 1)
        self.assertTrue("Exploration" in chapters[0].chapter_title)

    def test_resolve_chapter_by_number(self):
        num, title = curriculum_service.resolve_chapter(10, 11)
        self.assertEqual(num, 11)
        self.assertEqual(title, "Electricity")

        num, title = curriculum_service.resolve_chapter(10, "11")
        self.assertEqual(num, 11)
        self.assertEqual(title, "Electricity")

    def test_resolve_chapter_by_string(self):
        num, title = curriculum_service.resolve_chapter(10, "electricity")
        self.assertEqual(num, 11)
        self.assertEqual(title, "Electricity")

        num, title = curriculum_service.resolve_chapter(10, "Ch 9: Light")
        self.assertEqual(num, 9)
        self.assertEqual(title, "Light – Reflection and Refraction")

    def test_resolve_invalid_chapter(self):
        with self.assertRaises(ChapterNotFoundError):
            curriculum_service.resolve_chapter(10, "NonExistentChapterXYZ")

    def test_resolve_invalid_grade(self):
        with self.assertRaises(CurriculumError):
            curriculum_service.resolve_chapter(12, 1)

    def test_get_next_chapter(self):
        next_num, next_title, has_more = curriculum_service.get_next_chapter(10, 11)
        self.assertEqual(next_num, 12)
        self.assertEqual(next_title, "Magnetic Effects of Electric Current")
        self.assertTrue(has_more)

        # Final chapter
        last_num, last_title, has_more = curriculum_service.get_next_chapter(10, 13)
        self.assertEqual(last_num, 13)
        self.assertEqual(last_title, "Our Environment")
        self.assertFalse(has_more)


if __name__ == "__main__":
    unittest.main()
