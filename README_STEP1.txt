EcoSpill Step 1: schema helpers

Copy company_schema.py and user_schema.py into your project's models/ directory.

Example:

from models.company_schema import create_company
from models.user_schema import create_user_access

company = create_company(
    "Example Shipping Co.",
    registered_by_uid="FIREBASE_UID_FROM_AUTH",
    contact_email="admin@example.com",
)

admin_access = create_user_access(
    firebase_uid="FIREBASE_UID_FROM_AUTH",
    company_id=company["company_id"],
    role="company_admin",
    email="admin@example.com",
    created_by_uid="FIREBASE_UID_FROM_AUTH",
)

Important:
- These helpers only build dictionaries. They do not write to Firebase.
- Do not let public signup choose company_admin and write that role directly.
- A trusted onboarding/admin flow must create the company and first admin mapping.
- Server-side authorization and staged Firebase rules are still required.
- Never put service-account JSON or passwords in this folder or commit them.
