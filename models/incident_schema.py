from datetime import datetime, timezone
from uuid import uuid4
from typing import Any


def create_incident(
    vessel_name: str,
    description: str,
    vessel_domain: str | None = None,
    vessel_id: str | None = None,
    vessel_type: str | None = None,
    oil_type: str | None = None,
    tank_id: str | None = None,
    status: str = "suspected",
    sensor_readings: list | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    evidence: list | None = None,
    crew_investigation: dict | None = None,
    ml_analysis: dict | None = None,
) -> dict[str, Any]:
    """Create a standardized EcoSpillGuard incident record."""

    allowed_statuses = {"suspected", "confirmed", "dismissed"}

    if status not in allowed_statuses:
        raise ValueError(
            f"Status must be one of: {', '.join(sorted(allowed_statuses))}"
        )

    now = datetime.now(timezone.utc).isoformat()

    return {
        "incident_id": f"ESG-{uuid4().hex[:10].upper()}",
        "created_at": now,
        "updated_at": now,
        "vessel": {
            "name": vessel_name,
            "domain": vessel_domain,
            "vessel_id": vessel_id,
            "vessel_type": vessel_type,
        },
        "incident": {
            "description": description,
            "status": status,
            "detection_time": None,
            "oil_type": oil_type,
            "tank_id": tank_id,
            "estimated_quantity": None,
        },
        "location": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "sensor_readings": sensor_readings or [],
        "evidence": evidence or [],
        "crew_investigation": crew_investigation or {
            "cause_category": None,
            "cause_confirmation": "unconfirmed",
            "chief_engineer_comments": None,
            "actions_taken": [],
            "crew_acknowledgement": None,
            "follow_up_observations": None,
        },
        "ml_analysis": ml_analysis or {
            "matched_historical_cases": [],
            "recommendations": [],
            "model_version": None,
        },
        "report": {
            "status": "not_generated",
            "pdf_url": None,
        },
    }