
"""Trusted, local-only bootstrap for a company's first administrator.

Run manually from the project root. Never expose this script as an API route.
"""

import argparse
import os

import firebase_admin
from firebase_admin import auth, db

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.company_schema import create_company
from models.user_schema import create_user_access


def initialize_firebase() -> None:
    """Initialize Firebase Admin without duplicating an existing app."""
    if not firebase_admin._apps:
        database_url = os.environ.get("FIREBASE_DATABASE_URL")
        if not database_url:
            raise RuntimeError(
                "Set FIREBASE_DATABASE_URL before running this script."
            )

        firebase_admin.initialize_app(
            options={"databaseURL": database_url}
        )


def provision_company_admin(
    firebase_uid: str,
    company_name: str,
    contact_email: str | None = None,
) -> str:
    """Create a company and grant its first administrator access."""
    if not firebase_uid.strip():
        raise ValueError("Firebase UID cannot be empty.")

    if not company_name.strip():
        raise ValueError("Company name cannot be empty.")

    # Confirm the target is a real Firebase Authentication account.
    firebase_user = auth.get_user(firebase_uid)

    # Do not overwrite an existing user's membership or role.
    access_ref = db.reference(f"/user_access/{firebase_uid}")
    if access_ref.get() is not None:
        raise ValueError(
            "This user already has an access record. "
            "No changes were made."
        )

    if contact_email is None:
        contact_email = firebase_user.email

    company = create_company(
        name=company_name.strip(),
        registered_by_uid=firebase_uid,
        contact_email=contact_email,
    )

    company_id = company.get("company_id") or company.get("id")
    if not company_id:
        raise ValueError(
            "Company schema did not return a company ID. "
            "Check models/company_schema.py."
        )

    company_ref = db.reference(f"/companies/{company_id}")

    if company_ref.get() is not None:
        raise ValueError(
            f"Company ID {company_id} already exists. No changes made."
        )

    access = create_user_access(
        firebase_uid=firebase_uid,
        company_id=company_id,
        role="company_admin",
        email=contact_email,
        vessel_ids=[],
        status="active",
        created_by_uid=firebase_uid,
    )

    # Write the company first, then its administrator access record.
        # Write both records in one atomic multi-location update.
    db.reference("/").update({
        f"companies/{company_id}": company,
        f"user_access/{firebase_uid}": access,
    })

    return company_id


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Provision a company's first administrator."
    )
    parser.add_argument("--uid", required=True, help="Existing Firebase Auth UID")
    parser.add_argument("--name", required=True, help="Shipping company name")
    parser.add_argument("--email", help="Optional company contact email")
    args = parser.parse_args()

    initialize_firebase()

    company_id = provision_company_admin(
        firebase_uid=args.uid,
        company_name=args.name,
        contact_email=args.email,
    )

    print("Company and first administrator created successfully.")
    print(f"Company ID: {company_id}")


if __name__ == "__main__":
    main()

