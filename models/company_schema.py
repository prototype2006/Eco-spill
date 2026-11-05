"""Data builders for EcoSpill company records. No Firebase writes occur here."""
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_company(
    name: str,
    *,
    registered_by_uid: str,
    contact_email: str | None = None,
    status: str = "active",
) -> dict[str, Any]:
    """Build a company record with a generated ID."""
    clean_name = name.strip()
    clean_uid = registered_by_uid.strip()
    if not clean_name:
        raise ValueError("Company name is required.")
    if not clean_uid:
        raise ValueError("registered_by_uid is required.")
    if status not in {"active", "suspended"}:
        raise ValueError("status must be 'active' or 'suspended'.")

    now = utc_now()
    company_id = f"CO-{uuid4().hex[:10].upper()}"
    return {
        "company_id": company_id,
        "name": clean_name,
        "contact_email": contact_email.strip() if contact_email else None,
        "status": status,
        "registered_by_uid": clean_uid,
        "created_at": now,
        "updated_at": now,
    }
