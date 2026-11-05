
"""Data builder for EcoSpill vessel records. No Firebase writes occur here."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


VALID_VESSEL_STATUSES = {"active", "inactive", "maintenance"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_vessel(
    *,
    company_id: str,
    name: str,
    registered_by_uid: str,
    imo_number: str | None = None,
    call_sign: str | None = None,
    vessel_type: str | None = None,
    flag_state: str | None = None,
    device_id: str | None = None,
    status: str = "active",
) -> dict[str, Any]:
    """Build a vessel record associated with one shipping company."""

    clean_company_id = company_id.strip()
    clean_name = name.strip()
    clean_uid = registered_by_uid.strip()

    if not clean_company_id:
        raise ValueError("company_id is required.")
    if not clean_name:
        raise ValueError("Vessel name is required.")
    if not clean_uid:
        raise ValueError("registered_by_uid is required.")
    if status not in VALID_VESSEL_STATUSES:
        raise ValueError(
            f"status must be one of: "
            f"{', '.join(sorted(VALID_VESSEL_STATUSES))}."
        )

    now = utc_now()

    return {
        "vessel_id": f"VS-{uuid4().hex[:10].upper()}",
        "company_id": clean_company_id,
        "name": clean_name,
        "imo_number": imo_number.strip() if imo_number else None,
        "call_sign": call_sign.strip() if call_sign else None,
        "vessel_type": vessel_type.strip() if vessel_type else None,
        "flag_state": flag_state.strip() if flag_state else None,
        "device_id": device_id.strip() if device_id else None,
        "status": status,
        "created_by_uid": clean_uid,
        "created_at": now,
        "updated_at": now,
    }
