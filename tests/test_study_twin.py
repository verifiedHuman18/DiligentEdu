"""Comprehensive Unit and Integration Tests for Study Twin Academic Matching (Phases 1-32)."""

import os
import tempfile
import unittest

from backend.analytics.study_twin import (
    build_study_twin_profile,
    calculate_twin_similarity,
    find_study_twin,
)
from backend.storage.database import init_database
from backend.storage.repository import (
    QuizRepository,
    get_saved_study_twin_match,
)


class TestStudyTwin(unittest.TestCase):
    """Test suite for Study Twin matching engine, boundaries, privacy, and dynamic state updates."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        init_database(self.db_path)
        self.repo = QuizRepository(db_path=self.db_path)

        # Seed sample students
        # Student Alice (Class 10 Math): Weak in Real Numbers & Polynomials
        self._record_mock_quiz(
            student_id="student_alice",
            class_level=10,
            subject="Mathematics",
            chapter="Real Numbers",
            score=1,
            total=5,  # 20% (Weak)
        )
        self._record_mock_quiz(
            student_id="student_alice",
            class_level=10,
            subject="Mathematics",
            chapter="Polynomials",
            score=2,
            total=5,  # 40% (Weak)
        )

        # Student Bob (Class 10 Math): Also weak in Real Numbers & Polynomials (Ideal Twin for Alice)
        self._record_mock_quiz(
            student_id="student_bob",
            class_level=10,
            subject="Mathematics",
            chapter="Real Numbers",
            score=2,
            total=5,  # 40% (Weak)
        )
        self._record_mock_quiz(
            student_id="student_bob",
            class_level=10,
            subject="Mathematics",
            chapter="Polynomials",
            score=1,
            total=5,  # 20% (Weak)
        )

        # Student Charlie (Class 10 Math): Strong in Real Numbers (100%), Weak in Triangles
        self._record_mock_quiz(
            student_id="student_charlie",
            class_level=10,
            subject="Mathematics",
            chapter="Real Numbers",
            score=5,
            total=5,  # 100% (Strong)
        )
        self._record_mock_quiz(
            student_id="student_charlie",
            class_level=10,
            subject="Mathematics",
            chapter="Triangles",
            score=1,
            total=5,  # 20% (Weak)
        )

        # Student Dave (Class 9 Math): Different Class Level (Boundary Test)
        self._record_mock_quiz(
            student_id="student_dave",
            class_level=9,
            subject="Mathematics",
            chapter="Introduction to Linear Polynomials",
            score=1,
            total=5,
        )

        # Student Eve (Class 10 Science): Different Subject (Boundary Test)
        self._record_mock_quiz(
            student_id="student_eve",
            class_level=10,
            subject="Science",
            chapter="Chemical Reactions and Equations",
            score=1,
            total=5,
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _record_mock_quiz(
        self,
        student_id: str,
        class_level: int,
        subject: str,
        chapter: str,
        score: int,
        total: int,
    ):
        """Helper to seed quiz records."""
        quiz_data = {
            "class_level": class_level,
            "subject": subject,
            "chapter": chapter,
            "chapter_number": 1,
            "difficulty": "medium",
            "questions": [
                {
                    "question_id": f"q_{i}",
                    "question": f"Sample question {i}",
                    "correct_answer": "A",
                    "options": {"A": "1", "B": "2"},
                }
                for i in range(1, total + 1)
            ],
        }
        answers = {f"q_choice_{i}": "A" if i <= score else "B" for i in range(1, total + 1)}
        self.repo.record_attempt(student_id, quiz_data, answers)

    def test_phase_2_matching_boundary_hard_filters(self):
        """Verify strict class and subject isolation: Class 10 Math cannot match Class 9 Math or Class 10 Science."""
        profile_alice = build_study_twin_profile(
            "student_alice", class_level=10, subject="Mathematics", db_path=self.db_path
        )
        profile_dave = build_study_twin_profile(
            "student_dave", class_level=9, subject="Mathematics", db_path=self.db_path
        )
        profile_eve = build_study_twin_profile(
            "student_eve", class_level=10, subject="Science", db_path=self.db_path
        )

        # Alice vs Dave (Different Class)
        score_diff_class, _, _ = calculate_twin_similarity(profile_alice, profile_dave)
        self.assertEqual(score_diff_class, 0.0)

        # Alice vs Eve (Different Subject)
        score_diff_subject, _, _ = calculate_twin_similarity(profile_alice, profile_eve)
        self.assertEqual(score_diff_subject, 0.0)

    def test_phase_5_to_11_similarity_scoring_prioritizes_aligned_weaknesses(self):
        """Verify Alice matches Bob with higher similarity than Charlie due to aligned weak topics & Action Plan."""
        profile_alice = build_study_twin_profile(
            "student_alice", class_level=10, subject="Mathematics", db_path=self.db_path
        )
        profile_bob = build_study_twin_profile(
            "student_bob", class_level=10, subject="Mathematics", db_path=self.db_path
        )
        profile_charlie = build_study_twin_profile(
            "student_charlie", class_level=10, subject="Mathematics", db_path=self.db_path
        )

        score_alice_bob, comps_bob, shared_bob = calculate_twin_similarity(
            profile_alice, profile_bob
        )
        score_alice_charlie, comps_charlie, shared_charlie = calculate_twin_similarity(
            profile_alice, profile_charlie
        )

        # Alice and Bob both have Real Numbers & Polynomials weak
        self.assertIn("Real Numbers", shared_bob["shared_weak"])
        self.assertIn("Polynomials", shared_bob["shared_weak"])
        self.assertGreater(score_alice_bob, score_alice_charlie)
        self.assertGreater(score_alice_bob, 70.0)

    def test_phase_13_insufficient_data_handling(self):
        """Verify brand new student with 0 quizzes receives insufficient_data status without synthetic scores."""
        match = find_study_twin(
            "brand_new_student", class_level=10, subject="Mathematics", db_path=self.db_path
        )
        self.assertEqual(match.status, "insufficient_data")
        self.assertEqual(match.similarity_score, 0.0)
        self.assertIn("practice quizzes", match.explanation.lower())

    def test_phase_14_end_to_end_matching_service(self):
        """Verify find_study_twin finds Bob for Alice, returns deterministic explanation, and caches result."""
        match = find_study_twin(
            "student_alice",
            class_level=10,
            subject="Mathematics",
            db_path=self.db_path,
            force_refresh=True,
        )
        self.assertEqual(match.status, "active")
        self.assertEqual(match.twin_student_id, "student_bob")
        self.assertGreater(match.similarity_score, 70.0)
        self.assertIn("Real Numbers", match.explanation)

        # Verify caching in SQLite
        cached = get_saved_study_twin_match(
            "student_alice", class_level=10, subject="Mathematics", db_path=self.db_path
        )
        self.assertIsNotNone(cached)
        self.assertEqual(cached["twin_student_id"], "student_bob")

    def test_phase_18_privacy_by_design(self):
        """Verify match dictionary does not expose emails, personal names, phone numbers, or private quiz history."""
        match = find_study_twin(
            "student_alice", class_level=10, subject="Mathematics", db_path=self.db_path
        )
        data = match.to_dict()

        # Sensitive field absence check
        self.assertNotIn("email", data)
        self.assertNotIn("phone", data)
        self.assertNotIn("real_name", data)
        self.assertNotIn("quiz_history", data)
        self.assertNotIn("raw_answers", data)
        self.assertNotIn("uploaded_documents", data)

    def test_phase_23_31_dynamic_recalculation_on_performance_change(self):
        """Verify that when Alice masters Real Numbers, her profile updates and twin similarity adapts."""
        # Alice masters Real Numbers (takes 3 consecutive 100% quizzes)
        for _ in range(3):
            self._record_mock_quiz(
                student_id="student_alice",
                class_level=10,
                subject="Mathematics",
                chapter="Real Numbers",
                score=5,
                total=5,
            )

        # Re-build profile
        updated_profile = build_study_twin_profile(
            "student_alice", class_level=10, subject="Mathematics", db_path=self.db_path
        )
        self.assertIn("Real Numbers", updated_profile.strong_topics)
        self.assertNotIn("Real Numbers", updated_profile.weak_topics)

        # Alice now also attempts Triangles and fails (Weak in Triangles)
        self._record_mock_quiz(
            student_id="student_alice",
            class_level=10,
            subject="Mathematics",
            chapter="Triangles",
            score=1,
            total=5,
        )

        # Now Charlie is also Strong in Real Numbers and Weak in Triangles!
        match_after = find_study_twin(
            "student_alice",
            class_level=10,
            subject="Mathematics",
            db_path=self.db_path,
            force_refresh=True,
        )
        self.assertEqual(match_after.status, "active")
        self.assertEqual(match_after.twin_student_id, "student_charlie")
        self.assertIn("Triangles", match_after.shared_weak_topics)


if __name__ == "__main__":
    unittest.main()
