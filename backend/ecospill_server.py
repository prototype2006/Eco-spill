
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
import json
import csv
import os
import uuid

# ---------------- SETTINGS ----------------
HOST = "0.0.0.0"
PORT = 8000
MAX_READINGS_PER_ALERT = 3

READINGS_FILE = "ecospill_alert_readings_v2.csv"
INCIDENTS_FILE = "ecospill_incidents.csv"

# ---------------- INCIDENT STATE ----------------
current_incident_id = None
incident_start_time = None
saved_readings = 0

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
        "status"
    ]
)

create_csv_if_missing(
    INCIDENTS_FILE,
    [
        "incident_id",
        "start_time",
        "end_time",
        "status",
        "readings_saved"
    ]
)


# ---------------- INCIDENT HELPERS ----------------
def start_incident():
    global current_incident_id, incident_start_time, saved_readings

    # A short unique ID for this prototype incident
    current_incident_id = (
        "ESG-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        + "-" + uuid.uuid4().hex[:4].upper()
    )

    incident_start_time = datetime.now().isoformat(timespec="seconds")
    saved_readings = 0

    with open(INCIDENTS_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            current_incident_id,
            incident_start_time,
            "",
            "OPEN",
            0
        ])

    print(f"\nNEW INCIDENT: {current_incident_id}")
    print("Incident status: OPEN")


def save_alert_reading(data):
    global saved_readings

    if saved_readings >= MAX_READINGS_PER_ALERT:
        print("Reading limit reached; not saving another alert reading.")
        return

    received_at = datetime.now().isoformat(timespec="seconds")

    with open(READINGS_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            current_incident_id,
            received_at,
            data.get("timestamp", "Not provided"),
            data.get("distance_cm", "Not provided"),
            data.get("water_percent", "Not provided"),
            "ALERT_ON"
        ])

    saved_readings += 1
    print(
        f"Saved reading {saved_readings}/{MAX_READINGS_PER_ALERT} "
        f"for {current_incident_id}"
    )


def close_incident():
    global current_incident_id, incident_start_time, saved_readings

    if current_incident_id is None:
        return

    incident_id = current_incident_id
    end_time = datetime.now().isoformat(timespec="seconds")
    count = saved_readings

    # Update the summary row belonging to this incident.
    rows = []

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

    print(f"\nINCIDENT CLOSED: {incident_id}")
    print(f"Alert readings saved: {count}")
    print("System is ready for the next incident.")

    current_incident_id = None
    incident_start_time = None
    saved_readings = 0


# ---------------- HTTP RECEIVER ----------------
class EcoSpillHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global current_incident_id

        if self.path != "/data":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_data = self.rfile.read(length)
            data = json.loads(raw_data.decode("utf-8"))

            status = str(data.get("status", "")).upper()

            if status == "ALERT_ON":
                # Start a new incident only if none is open.
                if current_incident_id is None:
                    start_incident()

                save_alert_reading(data)

            elif status == "NORMAL":
                # A normal reading closes the current incident.
                if current_incident_id is not None:
                    close_incident()
                else:
                    print("NORMAL reading received; no incident is open.")

            else:
                print("Unknown status received:", status)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"received"}')

        except (ValueError, UnicodeDecodeError, csv.Error) as error:
            print("Invalid incoming data:", error)
            self.send_error(400, "Invalid data")

    def log_message(self, format, *args):
        pass


# ---------------- START SERVER ----------------
server = HTTPServer((HOST, PORT), EcoSpillHandler)

print("===== EcoSpillGuard Edge Server =====")
print(f"Listening on port {PORT}")
print(f"Alert readings: {os.path.abspath(READINGS_FILE)}")
print(f"Incident summaries: {os.path.abspath(INCIDENTS_FILE)}")
print("Waiting for ESP32 data...")
print("Press Ctrl+C to stop.")

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped.")
    server.server_close()
