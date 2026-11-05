
"""Firebase-backed company and user-access helpers.

These functions use the signed-in user's Firebase ID token.
They do not grant roles or bypass Firebase security rules.
"""

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import requests
import streamlit as st


TIMEOUT_SECONDS = 15


def _database_url() -> str:
    try:
        url = st.secrets["firebase"]["database_url"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(
            "Firebase database_url is missing from Streamlit secrets."
        ) from exc

    return str(url).rstrip("/")


def _firebase_token(token: str | None = None) -> str:
    resolved = token or st.session_state.get("firebase_token")

    if not resolved:
        raise PermissionError(
            "Please sign in to EcoSpill before accessing company data."
        )

    return str(resolved)


def _request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
) -> Any:
    """Make an authenticated Firebase REST request."""
    url = f"{_database_url()}/{path.strip('/')}.json"
    params = {"auth": _firebase_token(token)}

    try:
        response = requests.request(
            method,
            url,
            params=params,
            json=payload,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            "Firebase request failed. Check database rules and connectivity."
        ) from exc

    if not response.content:
        return None

    return response.json()


def get_company(
    company_id: str,
    *,
    token: str | None = None,
) -> dict[str, Any] | None:
    """Read a company record. Access must be allowed by Firebase Rules."""
    key = quote(company_id.strip(), safe="")
    if not key:
        raise ValueError("company_id is required.")

    result = _request("GET", f"companies/{key}", token=token)
    return result if isinstance(result, dict) else None


def get_user_access(
    firebase_uid: str,
    *,
    token: str | None = None,
) -> dict[str, Any] | None:
    """Read a user-access mapping. This does not itself authorize the user."""
    key = quote(firebase_uid.strip(), safe="")
    if not key:
        raise ValueError("firebase_uid is required.")

    result = _request("GET", f"user_access/{key}", token=token)
    return result if isinstance(result, dict) else None


def list_company_vessels(
    company_id: str,
    *,
    token: str | None = None,
) -> list[dict[str, Any]]:
    """List vessel records belonging to a company.

    The caller must separately verify that the signed-in user is permitted
    to access this company. Firebase Rules must also enforce access.
    """
    if not company_id.strip():
        raise ValueError("company_id is required.")

    result = _request("GET", "vessels", token=token)
    if not isinstance(result, dict):
        return []

    vessels = []
    for vessel_id, vessel in result.items():
        if not isinstance(vessel, dict):
            continue
        if vessel.get("company_id") == company_id:
            item = dict(vessel)
            item.setdefault("vessel_id", vessel_id)
            vessels.append(item)

    return vessels
