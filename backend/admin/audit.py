"""Audit logging module for administrative operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("admin.audit")


def log_admin_action(
    action: str,
    admin_id: str,
    student_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Records an administrative audit log entry for security and accountability.
    
    Args:
        action: Identifier for the action (e.g. 'CREATE_STUDENT', 'DELETE_STUDENT', 'PROMOTE_STUDENT').
        admin_id: Identifier of the authenticated administrator performing the action.
        student_id: Optional identifier of the student affected.
        details: Additional context details (e.g. class_level, email, previous_class).
    
    Returns:
        Structured audit record dict.
    """
    ts = datetime.now(timezone.utc).isoformat()
    record = {
        "timestamp": ts,
        "action": action.upper(),
        "admin_id": admin_id,
        "student_id": student_id,
        "details": details or {},
    }
    logger.info(
        f"[AUDIT] action={record['action']} admin_id={admin_id} student_id={student_id} details={record['details']}"
    )
    return record
