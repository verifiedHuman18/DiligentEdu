"""Regression and Boundary tests for Student Promotion Architecture (Phases 6, 7, 15, 19)."""

import unittest
from unittest.mock import MagicMock, patch

from backend.admin.service import AdminService
from backend.exceptions import PermissionDeniedError, StudentNotFoundError


class MockUser:
    def __init__(self, id, email, name, role, class_level, subject="Science"):
        self.id = id
        self.email = email
        self.name = name
        self.role = role
        self.class_level = class_level
        self.subject = subject
        self.createdAt = "2026-08-29T00:00:00Z"


class TestPromotionRegression(unittest.TestCase):
    """Tests the promotion workflow, permission boundaries, and handoff between Class 9 and Class 10 admins."""

    def setUp(self):
        self.service = AdminService()
        self.mock_db = MagicMock()
        self.service._db = self.mock_db
        self.mock_db.is_connected.return_value = True

        self.admin_9 = MockUser("admin_9_id", "admin9@school.edu", "Admin Nine", "admin", 9)
        self.admin_10 = MockUser("admin_10_id", "admin10@school.edu", "Admin Ten", "admin", 10)
        self.student_aarav = MockUser("aarav_id", "aarav@school.edu", "Aarav", "student", 9)

    @patch("backend.analytics.teacher.promote_student_in_db")
    def test_class_9_admin_promote_class_9_student(self, mock_promote_db):
        """Class 9 admin successfully promotes Class 9 student to Class 10."""
        self.mock_db.user.find_unique.side_effect = [
            self.admin_9,        # get_admin_scope
            self.student_aarav,  # lookup student
        ]

        res = self.service.promote_student("admin_9_id", "aarav_id")

        self.assertTrue(res["success"])
        self.assertEqual(res["previous_class"], 9)
        self.assertEqual(res["new_class"], 10)
        mock_promote_db.assert_called_once_with("aarav_id", 10)

    def test_class_10_admin_cannot_promote_student(self):
        """Class 10 admin is denied promotion privileges (only Class 9 admin can promote)."""
        self.mock_db.user.find_unique.return_value = self.admin_10

        with self.assertRaises(PermissionDeniedError):
            self.service.promote_student("admin_10_id", "aarav_id")

    def test_promote_already_promoted_student_denied(self):
        """Attempting to promote a student who is already in Class 10 is denied."""
        student_senior = MockUser("senior_id", "senior@school.edu", "Senior Student", "student", 10)
        self.mock_db.user.find_unique.side_effect = [
            self.admin_9,
            student_senior,
        ]

        with self.assertRaises(PermissionDeniedError):
            self.service.promote_student("admin_9_id", "senior_id")

    @patch("backend.admin.service.quiz_repository")
    def test_post_promotion_scope_boundary_handoff(self, mock_repo):
        """
        After promotion:
        1. Class 9 admin can NO LONGER delete the promoted student.
        2. Class 10 admin CAN manage and delete the student.
        """
        # Step 1: Student is promoted to Class 10
        promoted_aarav = MockUser("aarav_id", "aarav@school.edu", "Aarav", "student", 10)

        # Step 2: Class 9 Admin tries to delete Aarav -> DENIED
        self.mock_db.user.find_unique.side_effect = [
            self.admin_9,     # scope = 9
            promoted_aarav,   # Aarav is now class 10
        ]
        with self.assertRaises(PermissionDeniedError):
            self.service.delete_student("admin_9_id", "aarav_id")

        # Step 3: Class 10 Admin tries to delete Aarav -> SUCCESS
        self.mock_db.user.find_unique.side_effect = [
            self.admin_10,    # scope = 10
            promoted_aarav,   # Aarav is class 10
        ]
        res = self.service.delete_student("admin_10_id", "aarav_id")
        self.assertTrue(res["success"])
        mock_repo.delete_student_cascade.assert_called_once_with("aarav_id")


if __name__ == "__main__":
    unittest.main()
