"""Unit tests for Admin Scoped Student Management & Authorization (Phases 2-5, 10-14, 18)."""

import unittest
from unittest.mock import MagicMock, patch

from backend.admin.service import AdminService
from backend.exceptions import (
    PermissionDeniedError,
    StudentNotFoundError,
    StudentValidationError,
)


class MockUser:
    def __init__(self, id, email, name, role, class_level, subject="Science"):
        self.id = id
        self.email = email
        self.name = name
        self.role = role
        self.class_level = class_level
        self.subject = subject
        self.createdAt = "2026-08-29T00:00:00Z"


class TestAdminScope(unittest.TestCase):
    """Tests admin scope resolution, authorization, scoped creation, deletion, and validation."""

    def setUp(self):
        self.service = AdminService()
        self.mock_db = MagicMock()
        self.service._db = self.mock_db
        self.mock_db.is_connected.return_value = True

        # Pre-seed mock users
        self.admin_9 = MockUser("admin_9_id", "admin9@school.edu", "Admin Nine", "admin", 9)
        self.admin_10 = MockUser("admin_10_id", "admin10@school.edu", "Admin Ten", "admin", 10)
        self.teacher = MockUser("teacher_id", "teacher@school.edu", "Teacher One", "teacher", None)
        self.student_9 = MockUser("s_9_id", "student9@school.edu", "Aarav 9", "student", 9)
        self.student_10 = MockUser("s_10_id", "student10@school.edu", "Bhavya 10", "student", 10)

    def test_get_admin_scope_class_9(self):
        """Class 9 admin scope resolves with class_scope=9."""
        self.mock_db.user.find_unique.return_value = self.admin_9
        scope = self.service.get_admin_scope("admin_9_id")

        self.assertEqual(scope["role"], "admin")
        self.assertEqual(scope["class_scope"], 9)
        self.assertEqual(scope["admin_id"], "admin_9_id")

    def test_get_admin_scope_class_10(self):
        """Class 10 admin scope resolves with class_scope=10."""
        self.mock_db.user.find_unique.return_value = self.admin_10
        scope = self.service.get_admin_scope("admin_10_id")

        self.assertEqual(scope["role"], "admin")
        self.assertEqual(scope["class_scope"], 10)
        self.assertEqual(scope["admin_id"], "admin_10_id")

    def test_non_admin_rejected(self):
        """Non-admin user (e.g. teacher or student) is denied admin scope."""
        self.mock_db.user.find_unique.return_value = self.teacher
        with self.assertRaises(PermissionDeniedError):
            self.service.get_admin_scope("teacher_id")

    def test_invalid_class_scope_rejected(self):
        """Admin with invalid class_level (e.g. 11 or None) is denied."""
        invalid_admin = MockUser("admin_inv", "inv@school.edu", "Inv Admin", "admin", 11)
        self.mock_db.user.find_unique.return_value = invalid_admin
        with self.assertRaises(PermissionDeniedError):
            self.service.get_admin_scope("admin_inv")

    def test_get_students_for_admin_scoped_query(self):
        """Listing students queries only students matching admin's class scope."""
        self.mock_db.user.find_unique.return_value = self.admin_9
        self.mock_db.user.find_many.return_value = [self.student_9]

        students = self.service.get_students_for_admin("admin_9_id")

        self.assertEqual(len(students), 1)
        self.assertEqual(students[0]["id"], "s_9_id")
        self.assertEqual(students[0]["class_level"], 9)
        self.mock_db.user.find_many.assert_called_once_with(
            where={"role": "student", "class_level": 9},
            order={"name": "asc"},
        )

    def test_create_student_class_9_admin(self):
        """Class 9 admin creates student -> student.class_level is strictly 9 and subject is None."""
        self.mock_db.user.find_unique.return_value = self.admin_9
        self.mock_db.user.find_first.return_value = None  # No duplicate
        created_mock = MockUser("new_s_1", "new1@school.edu", "New Student", "student", 9, subject=None)
        self.mock_db.user.create.return_value = created_mock

        res = self.service.create_student("admin_9_id", {"name": "New Student", "email": "new1@school.edu", "password": "MySecretPassword123"})

        self.assertEqual(res["class_level"], 9)
        self.mock_db.user.create.assert_called_once_with(
            data={
                "id": unittest.mock.ANY,
                "name": "New Student",
                "email": "new1@school.edu",
                "role": "student",
                "class_level": 9,
                "subject": None,
            }
        )

    def test_create_student_ignores_client_supplied_class_override(self):
        """Even if client attempts to pass class_level=10 to Class 9 admin, backend forces class=9."""
        self.mock_db.user.find_unique.return_value = self.admin_9
        self.mock_db.user.find_first.return_value = None
        created_mock = MockUser("new_s_2", "new2@school.edu", "Hacker Student", "student", 9)
        self.mock_db.user.create.return_value = created_mock

        res = self.service.create_student(
            "admin_9_id",
            {"name": "Hacker Student", "email": "new2@school.edu", "class_level": 10},
        )

        self.assertEqual(res["class_level"], 9)
        create_args = self.mock_db.user.create.call_args[1]["data"]
        self.assertEqual(create_args["class_level"], 9)

    def test_create_student_validation_missing_fields(self):
        """Missing student name or email raises StudentValidationError."""
        self.mock_db.user.find_unique.return_value = self.admin_9

        with self.assertRaises(StudentValidationError):
            self.service.create_student("admin_9_id", {"name": "", "email": "aarav@school.edu"})

        with self.assertRaises(StudentValidationError):
            self.service.create_student("admin_9_id", {"name": "Aarav", "email": ""})

    def test_create_student_duplicate_email_rejected(self):
        """Duplicate email/roll number raises StudentValidationError."""
        self.mock_db.user.find_unique.return_value = self.admin_9
        self.mock_db.user.find_first.return_value = self.student_9  # Existing student

        with self.assertRaises(StudentValidationError):
            self.service.create_student("admin_9_id", {"name": "Duplicate", "email": "student9@school.edu"})

    @patch("backend.admin.service.quiz_repository")
    def test_delete_student_class_9_admin_success(self, mock_repo):
        """Class 9 admin can delete a Class 9 student."""
        self.mock_db.user.find_unique.side_effect = [
            self.admin_9,    # get_admin_scope
            self.student_9,  # lookup student
        ]

        res = self.service.delete_student("admin_9_id", "s_9_id")

        self.assertTrue(res["success"])
        mock_repo.delete_student_cascade.assert_called_once_with("s_9_id")

    @patch("backend.admin.service.quiz_repository")
    def test_cross_class_deletion_denied(self, mock_repo):
        """Class 9 admin cannot delete a Class 10 student (raises PermissionDeniedError)."""
        self.mock_db.user.find_unique.side_effect = [
            self.admin_9,     # get_admin_scope (scope=9)
            self.student_10,  # lookup student (class=10)
        ]

        with self.assertRaises(PermissionDeniedError):
            self.service.delete_student("admin_9_id", "s_10_id")

        mock_repo.delete_student_cascade.assert_not_called()

    def test_delete_nonexistent_student_raises_not_found(self):
        """Deleting a non-existent student ID raises StudentNotFoundError."""
        self.mock_db.user.find_unique.side_effect = [
            self.admin_9,
            None,
        ]

        with self.assertRaises(StudentNotFoundError):
            self.service.delete_student("admin_9_id", "unknown_id")


if __name__ == "__main__":
    unittest.main()
