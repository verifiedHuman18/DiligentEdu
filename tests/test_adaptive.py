"""Unit tests for Adaptive Quiz Engine."""

import unittest

from backend.quiz.adaptive import get_next_quiz_config


class TestAdaptiveEngine(unittest.TestCase):
    """Tests deterministic adaptive progression rules."""

    def test_remedial_under_40(self):
        res = {
            "class_level": 10,
            "chapter": "Electricity",
            "percentage": 35,
            "difficulty": "medium",
        }
        cfg = get_next_quiz_config(res)
        self.assertEqual(cfg["difficulty"], "easy")
        self.assertEqual(cfg["chapter"], "Electricity")
        self.assertEqual(cfg["action"], "remedial_reinforcement")

    def test_practice_40_to_69(self):
        res = {"class_level": 10, "chapter": "Electricity", "percentage": 60, "difficulty": "easy"}
        cfg = get_next_quiz_config(res)
        self.assertEqual(cfg["difficulty"], "medium")
        self.assertEqual(cfg["chapter"], "Electricity")
        self.assertEqual(cfg["action"], "conceptual_practice")

    def test_step_up_from_easy(self):
        res = {"class_level": 10, "chapter": "Electricity", "percentage": 80, "difficulty": "easy"}
        cfg = get_next_quiz_config(res)
        self.assertEqual(cfg["difficulty"], "medium")
        self.assertEqual(cfg["action"], "step_up_difficulty")

    def test_step_up_from_medium(self):
        res = {
            "class_level": 10,
            "chapter": "Electricity",
            "percentage": 80,
            "difficulty": "medium",
        }
        cfg = get_next_quiz_config(res)
        self.assertEqual(cfg["difficulty"], "hard")
        self.assertEqual(cfg["action"], "step_up_difficulty")

    def test_advance_chapter_from_hard(self):
        res = {"class_level": 10, "chapter": "Electricity", "percentage": 85, "difficulty": "hard"}
        cfg = get_next_quiz_config(res)
        self.assertEqual(cfg["difficulty"], "medium")
        self.assertEqual(cfg["chapter"], "Magnetic Effects of Electric Current")
        self.assertEqual(cfg["action"], "advance_chapter")

    def test_syllabus_mastery(self):
        res = {
            "class_level": 10,
            "chapter": "Our Environment",
            "percentage": 95,
            "difficulty": "hard",
        }
        cfg = get_next_quiz_config(res)
        self.assertEqual(cfg["action"], "syllabus_mastery")


if __name__ == "__main__":
    unittest.main()
