"""Data builders for EcoSpill user access mappings.

A role here is only data; trusted server-side code must enforce permissions.
"""
from datetime import datetime, timezone
from typing import Any

ALLOWED_ROLES = {"company_admin", "captain", "engineer", "crew"}
ALLOWED_USER_STATUSES = {"active", "invited", "disabled"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_user_access(
    *,
    firebase_uid: str,
    company_id: str,
    role: str,
    email: str | None = None,
    vessel_ids: list[str] | None = None,
    status: str = "active",
    created_by_uid: str | None = None,
) -> dict[str, Any]:
    """Build a user_access/{firebase_uid} mapping."""
    uid = firebase_uid.strip()
    company = company_id.strip()
    if not uid:
        raise ValueError("firebase_uid is required.")
    if not company:
        raise ValueError("company_id is required.")
    if role not in ALLOWED_ROLES:
        raise ValueError(f"role must be one of: {', '.join(sorted(ALLOWED_ROLES))}.")
    if status not in ALLOWED_USER_STATUSES:
        raise ValueError(
            f"status must be one of: {', '.join(sorted(ALLOWED_USER_STATUSES))}."
        )

    now = utc_now()
    clean_vessel_ids = sorted({v.strip() for v in (vessel_ids or []) if v.strip()})
    return {
        "firebase_uid": uid,
        "company_id": company,
        "role": role,
        "email": email.strip().lower() if email else None,
        "vessel_ids": clean_vessel_ids,
        "status": status,
        "created_by_uid": created_by_uid.strip() if created_by_uid else None,
        "created_at": now,
        "updated_at": now,
    }
