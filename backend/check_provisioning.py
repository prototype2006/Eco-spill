
import os
import firebase_admin
from firebase_admin import db

UID = "OZVJeFTA2PMcHVTeJ1M97m730GF3"

if not firebase_admin._apps:
    firebase_admin.initialize_app(
        options={"databaseURL": os.environ["FIREBASE_DATABASE_URL"]}
    )

access = db.reference(f"/user_access/{UID}").get()

if not isinstance(access, dict):
    raise SystemExit("FAIL: Administrator access record is missing.")

company_id = access.get("company_id")
company = db.reference(f"/companies/{company_id}").get()

if not isinstance(company, dict):
    raise SystemExit("FAIL: Company record is missing.")

checks = {
    "UID matches": access.get("firebase_uid") == UID,
    "Role is company_admin": access.get("role") == "company_admin",
    "Account is active": access.get("status") == "active",
    "Company ID matches": company.get("company_id") == company_id,
    "Company is active": company.get("status") == "active",
}

print(f"Company: {company.get('name')}")
print(f"Company ID: {company_id}")

for label, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'}: {label}")

if not all(checks.values()):
    raise SystemExit("Verification failed. Do not continue.")
