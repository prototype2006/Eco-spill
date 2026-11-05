
"""Server-side Firebase identity and company-role checks."""

from typing import Any

from firebase_admin import auth, db


ALLOWED_ROLES = {"company_admin", "captain", "engineer", "crew"}


class AuthorizationError(Exception):
    """Raised when a request has no valid identity or permission."""


def verify_user_token(id_token: str) -> dict[str, Any]:
    """Verify a Firebase ID token and load its registered access record."""
    if not id_token or not id_token.strip():
        raise AuthorizationError("Missing Firebase ID token.")

    try:
        decoded = auth.verify_id_token(id_token.strip(), check_revoked=True)
    except Exception as exc:
        raise AuthorizationError("Invalid or expired Firebase ID token.") from exc

    uid = decoded.get("uid")
    if not uid:
        raise AuthorizationError("Token does not contain a user ID.")

    access = db.reference(f"/user_access/{uid}").get()

    if not isinstance(access, dict):
        raise AuthorizationError("User has no registered company access.")

    if access.get("firebase_uid") != uid:
        raise AuthorizationError("User access record does not match the token.")

    if access.get("status") != "active":
        raise AuthorizationError("User account is not active.")

    role = access.get("role")
    if role not in ALLOWED_ROLES:
        raise AuthorizationError("User has an invalid role.")

    company_id = access.get("company_id")
    if not isinstance(company_id, str) or not company_id.strip():
        raise AuthorizationError("User has no assigned company.")

    company = db.reference(f"/companies/{company_id}").get()
    if not isinstance(company, dict) or company.get("status") != "active":
        raise AuthorizationError("Company is missing or inactive.")

    return {
        "uid": uid,
        "email": decoded.get("email"),
        "company_id": company_id,
        "role": role,
        "vessel_ids": access.get("vessel_ids", []),
    }


def require_role(
    principal: dict[str, Any],
    allowed_roles: set[str],
) -> None:
    """Reject operations not permitted for the authenticated role."""
    if principal.get("role") not in allowed_roles:
        raise AuthorizationError("Your role cannot perform this operation.")


def require_company(
    principal: dict[str, Any],
    requested_company_id: str,
) -> None:
    """Prevent a user from operating on another company's records."""
    if principal.get("company_id") != requested_company_id:
        raise AuthorizationError("Access to this company is not permitted.")
