"""Firebase-backed incident storage for EcoSpill.

Keeps the existing public function names so dashboard callers can continue
using save_incident(), get_all_incidents(), and related functions.

The Streamlit login should store the Firebase ID token in
st.session_state["firebase_token"].
"""

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import requests
import streamlit as st

REQUEST_TIMEOUT_SECONDS = 15
ALLOWED_STATUSES = {"suspected", "confirmed", "dismissed"}


def _database_url() -> str:
    """Return the configured Firebase Realtime Database URL."""
    try:
        url = st.secrets["firebase"]["database_url"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(
            "Firebase database_url is missing. Add it under [firebase] "
            "in .streamlit/secrets.toml."
        ) from exc
    return str(url).rstrip("/")


def _get_token(token: str | None = None) -> str:
    """Get the caller's Firebase ID token."""
    resolved_token = token or st.session_state.get("firebase_token")
    if not resolved_token:
        raise PermissionError(
            "No Firebase login token found. Log in through the EcoSpill "
            "dashboard before accessing incidents."
        )
    return str(resolved_token)


def _incident_url(incident_id: str | None = None) -> str:
    """Build a Realtime Database REST URL."""
    base_url = f"{_database_url()}/incidents"
    if incident_id is None:
        return f"{base_url}.json"
    return f"{base_url}/{quote(str(incident_id), safe='')}.json"


def _request(
    method: str,
    url: str,
    token: str | None = None,
    **kwargs: Any,
) -> Any:
    """Make an authenticated Firebase REST request with readable errors."""
    id_token = _get_token(token)
    params = dict(kwargs.pop("params", {}) or {})
    params["auth"] = id_token

    try:
        response = requests.request(
            method,
            url,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
            **kwargs,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not reach Firebase Realtime Database: {exc}"
        ) from exc

    if not response.ok:
        try:
            payload = response.json()
            detail = str(payload.get("error", payload)) if isinstance(payload, dict) else str(payload)
        except ValueError:
            detail = response.text[:300]

        if response.status_code in (401, 403):
            raise PermissionError(
                "Firebase denied access. Check that you are logged in, "
                "the ID token is current, the database URL is correct, "
                "and the Realtime Database rules include your Firebase UID. "
                f"Details: {detail}"
            )
        raise RuntimeError(
            f"Firebase request failed ({response.status_code}): {detail}"
        )

    if not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return response.text


def save_incident(
    incident: dict[str, Any],
    token: str | None = None,
) -> dict[str, Any]:
    """Save a new incident or replace an existing incident with the same ID."""
    incident_id = incident.get("incident_id")
    if not incident_id:
        raise ValueError("Incident must have an incident_id.")

    updated = dict(incident)
    updated["updated_at"] = datetime.now(timezone.utc).isoformat()
    _request("PUT", _incident_url(str(incident_id)), token=token, json=updated)
    return updated


def get_all_incidents(token: str | None = None) -> list[dict[str, Any]]:
    """Return all incidents, newest first."""
    data = _request("GET", _incident_url(), token=token)
    if data is None:
        return []
    if not isinstance(data, dict):
        raise RuntimeError(
            "Firebase incidents data must be an object keyed by incident ID."
        )

    incidents: list[dict[str, Any]] = []
    for key, value in data.items():
        if isinstance(value, dict):
            incident = dict(value)
            incident.setdefault("incident_id", key)
            incidents.append(incident)

    return sorted(
        incidents,
        key=lambda item: item.get("created_at") or "",
        reverse=True,
    )


def get_incident_by_id(
    incident_id: str,
    token: str | None = None,
) -> dict[str, Any] | None:
    """Find an incident by its unique ID."""
    data = _request("GET", _incident_url(incident_id), token=token)
    if data is None:
        return None
    if not isinstance(data, dict):
        raise RuntimeError(f"Invalid Firebase record for incident {incident_id}.")

    incident = dict(data)
    incident.setdefault("incident_id", incident_id)
    return incident



def sync_sensor_incident(
    sensor_incident: dict[str, Any],
    token: str | None = None,
) -> dict[str, Any]:
    """Merge sensor history into Firebase without erasing crew data."""
    incident_id = sensor_incident.get("incident_id")
    if not incident_id:
        raise ValueError("Sensor incident is missing its incident_id.")

    existing = get_incident_by_id(str(incident_id), token=token)

    if existing is None:
        existing = {
            "incident_id": str(incident_id),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "incident": {"status": "suspected"},
            "crew_investigation": {},
            "ml_analysis": {},
            "report": {},
        }

    merged = dict(existing)
    merged["incident_id"] = str(incident_id)

    # Refresh hardware fields only. Preserve crew notes, vessel,
    # model analysis, report information, and other app-owned fields.
    merged["edge_status"] = sensor_incident.get("status")
    merged["start_time"] = sensor_incident.get("start_time")
    merged["end_time"] = sensor_incident.get("end_time")
    merged["readings_saved"] = sensor_incident.get("readings_saved", 0)
    merged["sensor_readings"] = sensor_incident.get("sensor_readings", [])

    # Update location only when the hardware has actual coordinates.
    location = sensor_incident.get("location")
    if isinstance(location, dict) and (
        location.get("latitude") is not None
        and location.get("longitude") is not None
    ):
        merged["location"] = location

    # Keep existing incident metadata and never label a sensor alert
    # as a confirmed spill automatically.
    merged.setdefault("incident", {})
    if not isinstance(merged["incident"], dict):
        merged["incident"] = {"status": "suspected"}

    merged["incident"].setdefault("status", "suspected")
    merged["incident"].setdefault(
        "detected_at",
        sensor_incident.get("start_time"),
    )

    return save_incident(merged, token=token)


def update_incident_status(
    incident_id: str,
    status: str,
    token: str | None = None,
) -> dict[str, Any]:
    """Update an incident's status."""
    if status not in ALLOWED_STATUSES:
        raise ValueError(
            f"Status must be one of: {', '.join(sorted(ALLOWED_STATUSES))}"
        )

    incident = get_incident_by_id(incident_id, token=token)
    if incident is None:
        raise KeyError(f"Incident not found: {incident_id}")

    incident.setdefault("incident", {})["status"] = status
    return save_incident(incident, token=token)


def delete_incident(
    incident_id: str,
    token: str | None = None,
) -> bool:
    """Delete an incident by ID. Returns True if it existed."""
    existing = get_incident_by_id(incident_id, token=token)
    if existing is None:
        return False

    _request("DELETE", _incident_url(incident_id), token=token)
    return True
