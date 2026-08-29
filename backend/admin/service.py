"""Admin Service for Scoped Student Management (Phases 1-17).

Enforces backend authorization invariants, scope isolation, input validation,
cascading data cleanup, promotion preservation, and audit logging.
"""

import logging
import uuid
from typing import Any, Dict, List

from backend.admin.audit import log_admin_action
from backend.exceptions import (
    PermissionDeniedError,
    StudentNotFoundError,
    StudentValidationError,
)
from backend.storage.repository import get_prisma_client, quiz_repository

logger = logging.getLogger(__name__)


class AdminService:
    """Provides authorization-enforced administrative capabilities for class admins."""

    def __init__(self):
        self._db = None

    @property
    def db(self):
        if self._db is None:
            self._db = get_prisma_client()
        return self._db

    def _ensure_connected(self):
        if not self.db.is_connected():
            try:
                self.db.connect()
            except Exception as e:
                logger.warning(f"Prisma reconnect failed in AdminService: {e}")

    def get_admin_scope(self, admin_id: str) -> Dict[str, Any]:
        """
        Resolves and validates the authenticated administrator's scope from the database.

        Raises:
            PermissionDeniedError: If the user is not an admin or lacks a valid class scope (9 or 10).
        """
        if not admin_id or not str(admin_id).strip():
            raise PermissionDeniedError("Admin identity is required for authorization.")

        self._ensure_connected()
        clean_admin_id = str(admin_id).strip()

        try:
            admin_user = self.db.user.find_unique(where={"id": clean_admin_id})
        except Exception as e:
            logger.error(f"Failed to fetch admin user {clean_admin_id}: {e}")
            raise PermissionDeniedError("Could not verify administrator credentials.")

        if not admin_user or admin_user.role != "admin":
            raise PermissionDeniedError("User does not have administrator privileges.")

        class_scope = admin_user.class_level
        if class_scope not in (9, 10):
            raise PermissionDeniedError(
                f"Administrator '{clean_admin_id}' has invalid class scope ({class_scope}). Must be Class 9 or Class 10."
            )

        return {
            "admin_id": admin_user.id,
            "name": admin_user.name or "Admin",
            "email": admin_user.email,
            "role": "admin",
            "class_scope": int(class_scope),
        }

    def get_students_for_admin(self, admin_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all students within the administrator's scoped class level.
        The database query is strictly filtered server-side by the admin's class scope.
        """
        scope = self.get_admin_scope(admin_id)
        self._ensure_connected()

        try:
            students = self.db.user.find_many(
                where={"role": "student", "class_level": scope["class_scope"]},
                order={"name": "asc"},
            )
            return [
                {
                    "id": s.id,
                    "name": s.name if s.name else (s.email.split("@")[0] if s.email else "Student"),
                    "email": s.email,
                    "class_level": s.class_level,
                    "subject": s.subject or "Science",
                    "createdAt": s.createdAt.isoformat()
                    if hasattr(s.createdAt, "isoformat")
                    else str(s.createdAt),
                }
                for s in students
            ]
        except Exception as e:
            logger.error(f"Failed to fetch scoped students for admin {admin_id}: {e}")
            return []

    def create_student(self, admin_id: str, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new student strictly within the administrator's class scope.
        The student's class level is derived solely from the authenticated admin's scope.

        Raises:
            PermissionDeniedError: If caller lacks admin scope.
            StudentValidationError: If required fields are missing or email/identifier already exists.
        """
        scope = self.get_admin_scope(admin_id)
        self._ensure_connected()

        name = str(student_data.get("name", "")).strip()
        email_or_roll = str(
            student_data.get("email", "") or student_data.get("roll_number", "")
        ).strip()

        if not name:
            raise StudentValidationError("Student name is required.")
        if not email_or_roll:
            raise StudentValidationError("Student email or roll number is required.")

        # Normalize email address if raw roll number was entered
        email = email_or_roll if "@" in email_or_roll else f"{email_or_roll.lower()}@school.edu"
        raw_password = str(student_data.get("password", "")).strip()
        password = raw_password if raw_password else "Student@123"

        # 1. Provision user in Firebase Auth if available to obtain real Firebase UID
        student_id = str(student_data.get("id", "")).strip()
        if not student_id:
            try:
                from backend.auth.firebase_auth import create_or_get_firebase_user

                student_id = create_or_get_firebase_user(
                    email=email, password=password, display_name=name
                )
            except Exception as fb_err:
                logger.warning(f"Firebase user creation fallback to local UUID: {fb_err}")
                student_id = f"student_{uuid.uuid4().hex[:8]}"

        # Validate uniqueness against database
        try:
            existing = self.db.user.find_first(where={"OR": [{"email": email}, {"id": student_id}]})
            if existing:
                raise StudentValidationError(f"A student with email/roll '{email}' already exists.")
        except StudentValidationError:
            raise
        except Exception as e:
            logger.error(f"Error checking student uniqueness: {e}")
            raise StudentValidationError("Failed to validate student uniqueness.")

        # Enforce server-side class scope invariant (ignores any client-supplied class)
        target_class = scope["class_scope"]

        try:
            created = self.db.user.create(
                data={
                    "id": student_id,
                    "name": name,
                    "email": email,
                    "role": "student",
                    "class_level": target_class,
                    "subject": None,
                }
            )

            log_admin_action(
                action="CREATE_STUDENT",
                admin_id=admin_id,
                student_id=created.id,
                details={
                    "name": name,
                    "email": email,
                    "class_level": target_class,
                    "subject": None,
                },
            )

            return {
                "id": created.id,
                "name": created.name,
                "email": created.email,
                "class_level": created.class_level,
                "role": created.role,
                "subject": created.subject,
            }
        except Exception as e:
            logger.error(f"Failed to create student: {e}")
            raise StudentValidationError(f"Failed to create student in database: {e}")

    def delete_student(self, admin_id: str, student_id: str) -> Dict[str, Any]:
        """
        Deletes a student and cascades all associated records after verifying class scope.

        Raises:
            PermissionDeniedError: If caller is not authorized or if student's class != admin's class scope.
            StudentNotFoundError: If the target student does not exist.
        """
        scope = self.get_admin_scope(admin_id)
        self._ensure_connected()

        clean_student_id = str(student_id).strip()
        if not clean_student_id:
            raise StudentValidationError("Student ID is required for deletion.")

        try:
            student = self.db.user.find_unique(where={"id": clean_student_id})
        except Exception as e:
            logger.error(f"Failed to find student {clean_student_id}: {e}")
            raise StudentNotFoundError(f"Could not locate student '{clean_student_id}'.")

        if not student:
            raise StudentNotFoundError(f"Student '{clean_student_id}' does not exist.")

        if student.role != "student":
            raise PermissionDeniedError("Target user is not a student.")

        # Backend Authorization Invariant: Current class check
        if student.class_level != scope["class_scope"]:
            log_admin_action(
                action="DELETE_STUDENT_DENIED",
                admin_id=admin_id,
                student_id=clean_student_id,
                details={
                    "admin_scope": scope["class_scope"],
                    "student_class": student.class_level,
                    "reason": "cross_class_scope_violation",
                },
            )
            raise PermissionDeniedError(
                f"Permission denied: Class {scope['class_scope']} administrator cannot delete a Class {student.class_level} student."
            )

        # Cascading deletion
        quiz_repository.delete_student_cascade(clean_student_id)

        log_admin_action(
            action="DELETE_STUDENT",
            admin_id=admin_id,
            student_id=clean_student_id,
            details={
                "name": student.name,
                "email": student.email,
                "class_level": student.class_level,
            },
        )

        return {
            "success": True,
            "student_id": clean_student_id,
            "deleted_student": {
                "name": student.name,
                "email": student.email,
                "class_level": student.class_level,
            },
        }

    def promote_student(self, admin_id: str, student_id: str) -> Dict[str, Any]:
        """
        Promotes a Class 9 student to Class 10, preserving the existing promotion logic
        while enforcing Class 9 admin authorization.

        Raises:
            PermissionDeniedError: If caller is not a Class 9 admin or target student is not Class 9.
            StudentNotFoundError: If the target student does not exist.
        """
        scope = self.get_admin_scope(admin_id)

        if scope["class_scope"] != 9:
            raise PermissionDeniedError(
                "Only Class 9 administrators can promote students to Class 10."
            )

        self._ensure_connected()
        clean_student_id = str(student_id).strip()

        try:
            student = self.db.user.find_unique(where={"id": clean_student_id})
        except Exception as e:
            logger.error(f"Failed to find student for promotion {clean_student_id}: {e}")
            raise StudentNotFoundError(f"Could not locate student '{clean_student_id}'.")

        if not student:
            raise StudentNotFoundError(f"Student '{clean_student_id}' does not exist.")

        if student.class_level != 9:
            raise PermissionDeniedError(
                f"Cannot promote student: current class is Class {student.class_level}, not Class 9."
            )

        # Execute existing promotion logic
        from backend.analytics.teacher import promote_student_in_db

        promote_student_in_db(clean_student_id, 10)

        log_admin_action(
            action="PROMOTE_STUDENT",
            admin_id=admin_id,
            student_id=clean_student_id,
            details={"name": student.name, "from_class": 9, "to_class": 10},
        )

        return {
            "success": True,
            "student_id": clean_student_id,
            "previous_class": 9,
            "new_class": 10,
        }


# Singleton service instance
admin_service = AdminService()
