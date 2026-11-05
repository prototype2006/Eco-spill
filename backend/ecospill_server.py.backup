"""
EcoSpill edge server with CSV logging and Firebase Realtime Database sync.

Required environment variables:
  GOOGLE_APPLICATION_CREDENTIALS = path to Firebase service-account JSON
  FIREBASE_DATABASE_URL = Firebase Realtime Database URL

Keep the service-account JSON outside the Git repository. Do not commit it.
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone
import csv
import json
import os
import uuid

import firebase_admin
from firebase_admin import credentials, db

# ---------------- SETTINGS ----------------
HOST = "0.0.0.0"
PORT = 8000
MAX_READINGS_PER_ALERT = 3

READINGS_FILE = "ecospill_alert_readings_v2.csv"
INCIDENTS_FILE = "ecospill_incidents.csv"

DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL", "").strip()
SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()

# ---------------- INCIDENT STATE ----------------
current_incident_id = None
incident_start_time = None
saved_readings = 0
current_sensor_readings = []
latest_sensor_reading = None
# ---------------- TIME / FIREBASE ----------------
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def initialize_firebase() -> None:
    """Initialize Firebase Admin using a private service-account file."""
    if not DATABASE_URL:
        raise RuntimeError(
            "FIREBASE_DATABASE_URL is not set. Set it to your Realtime "
            "Database URL before starting this server."
        )
    if not SERVICE_ACCOUNT_PATH:
        raise RuntimeError(
            "GOOGLE_APPLICATION_CREDENTIALS is not set. Point it to your "
            "Firebase service-account JSON file stored outside the repo."
        )
    if not os.path.isfile(SERVICE_ACCOUNT_PATH):
        raise RuntimeError(
            "Service-account JSON file was not found at the configured path."
        )

    if not firebase_admin._apps:
        credential = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(
            credential,
            {"databaseURL": DATABASE_URL},
        )


def incident_ref(incident_id: str):
    return db.reference(f"/incidents/{incident_id}")


# ---------------- CREATE CSV FILES ----------------
def create_csv_if_missing(filename, headers):
    if not os.path.exists(filename):
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)


create_csv_if_missing(
    READINGS_FILE,
    [
        "incident_id",
        "received_at",
        "sensor_timestamp",
        "distance_cm",
        "water_percent",
        "status",
    ],
)

create_csv_if_missing(
    INCIDENTS_FILE,
    [
        "incident_id",
        "start_time",
        "end_time",
        "status",
        "readings_saved",
    ],
)


# ---------------- INCIDENT HELPERS ----------------
def start_incident(self):
    """Create one local incident and its shared Firebase record."""
    global current_incident_id, latest_sensor_reading 
    
    global saved_readings, current_sensor_readings

    current_incident_id = (
        "ESG-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        + "-" + uuid.uuid4().hex[:4].upper()
    )
    incident_start_time = utc_now()
    saved_readings = 0
    current_sensor_readings = []

    # Preserve the existing CSV incident summary.
    with open(INCIDENTS_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [current_incident_id, incident_start_time, "", "OPEN", 0]
        )

    # Create the record in the structure expected by the Streamlit app.
    incident_record = {
        "incident_id": current_incident_id,
        "created_at": incident_start_time,
        "updated_at": incident_start_time,
        "vessel": {
            "name": "Not provided",
            "domain": None,
            "vessel_id": None,
            "vessel_type": None,
        },
        "incident": {
            "description": "Sensor alert triggered; investigation required.",
            "status": "suspected",
            "detection_time": incident_start_time,
            "oil_type": None,
            "tank_id": None,
            "estimated_quantity": None,
        },
        "location": {
            "latitude": None,
            "longitude": None,
        },
        "sensor_readings": [],
        "evidence": [],
        "crew_investigation": {
            "cause_category": None,
            "cause_confirmation": "unconfirmed",
            "chief_engineer_comments": None,
            "actions_taken": [],
            "crew_acknowledgement": None,
            "follow_up_observations": None,
        },
        "ml_analysis": {
            "matched_historical_cases": [],
            "recommendations": [],
            "model_version": None,
        },
        "report": {
            "status": "not_generated",
            "pdf_url": None,
        },
        "edge_status": "OPEN",
        "readings_saved": 0,
    }

    incident_ref(current_incident_id).set(incident_record)

    print(f"\nNEW INCIDENT: {current_incident_id}")
    print("Incident status: suspected (awaiting investigation)")


def save_alert_reading(data):
    """Save up to three alert readings to CSV and the matching Firebase record."""
    global saved_readings, current_sensor_readings

    if current_incident_id is None:
        raise RuntimeError("Cannot save a reading without an open incident.")

    if saved_readings >= MAX_READINGS_PER_ALERT:
        print("Reading limit reached; not saving another alert reading.")
        return

    received_at = utc_now()
    sensor_timestamp = data.get("timestamp")
    distance_cm = data.get("distance_cm")
    water_percent = data.get("water_percent")

    row = {
        "incident_id": current_incident_id,
        "received_at": received_at,
        "sensor_timestamp": (
            sensor_timestamp if sensor_timestamp is not None else ""
        ),
        "distance_cm": distance_cm if distance_cm is not None else "",
        "water_percent": water_percent if water_percent is not None else "",
        "status": "ALERT_ON",
    }

    # CSV stays as the local audit/log record.
    with open(READINGS_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "incident_id",
                "received_at",
                "sensor_timestamp",
                "distance_cm",
                "water_percent",
                "status",
            ],
        )
        writer.writerow(row)

    current_sensor_readings.append(row)
    saved_readings += 1

    # Keep the same readings attached to the incident in Firebase.
    incident_ref(current_incident_id).update(
        {
            "sensor_readings": current_sensor_readings,
            "readings_saved": saved_readings,
            "updated_at": utc_now(),
        }
    )

    print(
        f"Saved reading {saved_readings}/{MAX_READINGS_PER_ALERT} "
        f"for {current_incident_id}"
    )


def close_incident():
    """Close the edge alert without automatically confirming an oil spill."""
    global current_incident_id, incident_start_time
    global saved_readings, current_sensor_readings

    if current_incident_id is None:
        return

    incident_id = current_incident_id
    end_time = utc_now()
    count = saved_readings

    with open(INCIDENTS_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        rows = list(reader)

    for row in rows:
        if row["incident_id"] == incident_id:
            row["end_time"] = end_time
            row["status"] = "CLOSED"
            row["readings_saved"] = count

    with open(INCIDENTS_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    incident_ref(incident_id).update(
        {
            "edge_status": "CLOSED",
            "edge_end_time": end_time,
            "readings_saved": count,
            "updated_at": utc_now(),
        }
    )

    print(f"\nINCIDENT CLOSED: {incident_id}")
    print(f"Alert readings saved: {count}")
    print("Investigation status remains 'suspected' until reviewed.")

    current_incident_id = None
    incident_start_time = None
    saved_readings = 0
    current_sensor_readings = []


# ---------------- HTTP RECEIVER ----------------
class EcoSpillHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global current_incident_id

        if self.path != "/data":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                self.send_error(400, "Empty request body")
                return

            raw_data = self.rfile.read(length)
            data = json.loads(raw_data.decode("utf-8"))
            if not isinstance(data, dict):
                self.send_error(400, "JSON body must be an object")
                return
                        # Keep the latest sensor reading for dashboard polling.
            latest_sensor_reading = dict(data)
            latest_sensor_reading.setdefault(
                "received_at", utc_now()
            )

            status = str(data.get("status", "")).upper()
            firebase_sync = "ok"

            if status == "ALERT_ON":
                if current_incident_id is None:
                    start_incident()
                save_alert_reading(data)

            elif status == "NORMAL":
                if current_incident_id is not None:
                    close_incident()
                else:
                    print("NORMAL reading received; no incident is open.")

            else:
                print("Unknown status received:", status)

            response = json.dumps(
                {"status": "received", "firebase_sync": firebase_sync}
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        except (ValueError, UnicodeDecodeError, csv.Error) as error:
            print("Invalid incoming data:", error)
            self.send_error(400, "Invalid data")
        except Exception as error:
            # Return an explicit error so the logger can report failed sync.
            print("Failed to process sensor data:", error)
            body = json.dumps(
                {"status": "error", "message": "Sensor data processing failed"}
            ).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
       
    def do_GET(self):
        if self.path == "/health":
            payload = json.dumps(
                {
                    "status": "ok",
                    "incident_open": current_incident_id is not None,
                    "incident_id": current_incident_id,
                    "readings_saved": saved_readings,
                    "max_readings_per_alert": MAX_READINGS_PER_ALERT,
                }
            ).encode("utf-8")

        elif self.path == "/latest":
            if latest_sensor_reading is None:
                payload = json.dumps(
                    {
                        "status": "unavailable",
                        "reading": None,
                    }
                ).encode("utf-8")
            else:
                payload = json.dumps(
                    {
                        "status": "ok",
                        "reading": latest_sensor_reading,
                    }
                ).encode("utf-8")

        else:
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        pass


    def log_message(self, format, *args):
        pass
        if self.path == "/latest":
            if latest_sensor_reading is None:
                payload = json.dumps({
                    "status": "unavailable",
                    "reading": None,
                }).encode("utf-8")
            else:
                payload = json.dumps({
                    "status": "ok",
                    "reading": latest_sensor_reading,
                }).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

# ---------------- START SERVER ----------------
if __name__ == "__main__":
    try:
        initialize_firebase()
    except Exception as error:
        raise SystemExit(
            "Firebase initialization failed. CSV logging has not started. "
            f"Check your environment configuration. Details: {error}"
        ) from error

    server = ThreadingHTTPServer((HOST, PORT), EcoSpillHandler)

    print("===== EcoSpill Edge Server =====")
    print(f"Listening on port {PORT}")
    print(f"Alert readings CSV: {os.path.abspath(READINGS_FILE)}")
    print(f"Incident summaries CSV: {os.path.abspath(INCIDENTS_FILE)}")
    print(f"Firebase database: {DATABASE_URL}")
    print("Waiting for ESP32 data...")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()
