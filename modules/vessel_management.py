
"""Authorized vessel registration and retrieval for EcoSpill."""

import os

import firebase_admin
from firebase_admin import db

from models.vessel_schema import create_vessel
from backend.authorization import require_role, verify_user_token


def _initialize_firebase():
    """Initialize Firebase Admin once per Python process."""
    if not firebase_admin._apps:
        database_url = os.environ.get("FIREBASE_DATABASE_URL")

        if not database_url:
            raise RuntimeError(
                "FIREBASE_DATABASE_URL is not configured."
            )

        firebase_admin.initialize_app(
            options={"databaseURL": database_url}
        )


def register_vessel(
    *,
    id_token: str,
    name: str,
    imo_number: str | None = None,
    call_sign: str | None = None,
    vessel_type: str | None = None,
    flag_state: str | None = None,
    device_id: str | None = None,
) -> dict:
    """Register a vessel for the authenticated company administrator."""

    _initialize_firebase()

    principal = verify_user_token(id_token)
    require_role(principal, {"company_admin"})

    company_id = principal["company_id"]
    uid = principal["uid"]

    vessel = create_vessel(
        company_id=company_id,
        name=name,
        registered_by_uid=uid,
        imo_number=imo_number,
        call_sign=call_sign,
        vessel_type=vessel_type,
        flag_state=flag_state,
        device_id=device_id,
    )

    vessel_id = vessel["vessel_id"]
    vessel_ref = db.reference(f"/vessels/{vessel_id}")

    # Create the record only if the generated ID is unused.
    result = vessel_ref.transaction(
        lambda current: vessel if current is None else current
    )

    if result != vessel:
        raise RuntimeError(
            "Vessel ID collision detected. Please try registering again."
        )

    return vessel


def list_company_vessels(*, id_token: str) -> list[dict]:
    """List vessels belonging only to the authenticated user's company."""

    _initialize_firebase()

    principal = verify_user_token(id_token)
    company_id = principal["company_id"]

    # Filter server-side to avoid requiring a Firebase database index.
    all_vessels = db.reference("/vessels").get()

    if not isinstance(all_vessels, dict):
        return []

    company_vessels = [
        vessel
        for vessel in all_vessels.values()
        if (
            isinstance(vessel, dict)
            and vessel.get("company_id") == company_id
        )
    ]

    return sorted(
        company_vessels,
        key=lambda vessel: vessel.get("name", "").lower(),
    )
