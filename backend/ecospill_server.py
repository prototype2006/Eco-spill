
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from datetime import datetime
import json
import csv
import os
import threading

# Allow other devices on the same Wi-Fi to connect
HOST = "0.0.0.0"
PORT = 8000

# Files for storing readings and incidents
READINGS_FILE = "ecospill_live_readings.csv"
INCIDENTS_FILE = "ecospill_incidents.csv"
ALERT_READINGS_FILE = "ecospill_alert_readings_v2.csv"

# Store the latest reading in memory
latest_reading = {
    "received_at": None,
    "timestamp": None,
    "distance_cm": None,
    "water_percent": None,
    "status": "WAITING",
    "led": "LED_OFF",
    "latitude": None,
    "longitude": None,
    "gps_status": "NO_FIX"
}

# Basic incident tracking
active_incident = False
incident_id = None
incident_counter = 0
data_lock = threading.Lock()


def ensure_csv_file(filename, headers):
    """Create a CSV file with headers if it does not exist."""
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        with open(filename, "w", newline="", encoding="utf-8") as file:
            csv.writer(file).writerow(headers)


ensure_csv_file(
    READINGS_FILE,
    ["received_at", "timestamp", "distance_cm", "water_percent",
     "status", "led", "latitude", "longitude", "gps_status"]
)

ensure_csv_file(
    INCIDENTS_FILE,
    ["incident_id", "started_at", "ended_at", "last_status"]
)

ensure_csv_file(
    ALERT_READINGS_FILE,
    ["incident_id", "received_at", "timestamp",
     "distance_cm", "latitude", "longitude", "status"]
)


def save_reading(reading):
    """Save each received sensor reading to the CSV file."""
    with open(READINGS_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            reading.get("received_at"),
            reading.get("timestamp"),
            reading.get("distance_cm"),
            reading.get("water_percent"),
            reading.get("status"),
            reading.get("led"),
            reading.get("latitude"),
            reading.get("longitude"),
            reading.get("gps_status")
        ])


def process_reading(data):
    """Validate and store a reading sent by the Python logger."""
    global latest_reading, active_incident
    global incident_id, incident_counter

    distance = data.get("distance_cm")

    # Convert valid numeric distances into numbers.
    try:
        distance = float(distance) if distance is not None else None
    except (TypeError, ValueError):
        distance = None

    # Don't treat invalid or missing distance as a real measurement.
    if distance is not None and not (20 < distance <= 400):
        distance = None

    status = str(data.get("status", "INVALID")).upper()
    if status in ("ALERT", "ALERT_ON"):
        status = "ALERT_ON"
    elif status == "NORMAL" and distance is not None:
        status = "NORMAL"
    elif distance is None:
        status = "INVALID"

    received = datetime.now().astimezone().isoformat(timespec="seconds")

    reading = {
        "received_at": received,
        "timestamp": data.get("timestamp"),
        "distance_cm": distance,
        "water_percent": data.get("water_percent"),
        "status": status,
        "led": data.get("led", "LED_OFF"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "gps_status": data.get("gps_status", "NO_FIX")
    }

    with data_lock:
        latest_reading = reading.copy()

        if status == "ALERT_ON" and distance is not None:
            if not active_incident:
                incident_counter += 1
                incident_id = (
                    "SPILL-" + datetime.now().strftime("%Y%m%d-%H%M%S")
                )
                active_incident = True

                with open(INCIDENTS_FILE, "a", newline="", encoding="utf-8") as file:
                    csv.writer(file).writerow([
                        incident_id, received, "", "ALERT_ON"
                    ])

            with open(ALERT_READINGS_FILE, "a", newline="", encoding="utf-8") as file:
                csv.writer(file).writerow([
                    incident_id, received, reading["timestamp"],
                    distance, reading["latitude"], reading["longitude"], status
                ])

        elif status == "NORMAL" and active_incident:
            with open(INCIDENTS_FILE, "a", newline="", encoding="utf-8") as file:
                csv.writer(file).writerow([
                    incident_id, received, received, "NORMAL"
                ])
            active_incident = False
            incident_id = None

        save_reading(reading)

    return reading


# This is the webpage that refreshes automatically.
DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EcoSpillGuard Live Monitor</title>
<style>
body {
    margin: 0;
    padding: 24px;
    background: #101820;
    color: #f3f6f9;
    font-family: Arial, sans-serif;
}
h1 { color: #55dfb2; }
.subtitle { color: #b9c5d0; }
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-top: 24px;
}
.card {
    background: #1c2935;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #344653;
}
.label { color: #b9c5d0; font-size: 14px; }
.value { font-size: 25px; font-weight: bold; margin-top: 12px; }
#status { color: #ffd166; }
#led { color: #ff6464; }
.small { color: #b9c5d0; font-size: 13px; margin-top: 24px; }
</style>
</head>
<body>
<h1>EcoSpillGuard</h1>
<div class="subtitle">Live tank monitoring and incident status</div>

<div class="grid">
    <div class="card">
        <div class="label">Tank sensor distance</div>
        <div class="value" id="distance">Waiting...</div>
    </div>
    <div class="card">
        <div class="label">Detection status</div>
        <div class="value" id="status">WAITING</div>
    </div>
    <div class="card">
        <div class="label">LED indicator</div>
        <div class="value" id="led">LED_OFF</div>
    </div>
    <div class="card">
        <div class="label">GPS coordinates</div>
        <div class="value" id="gps" style="font-size:18px">Waiting...</div>
    </div>
    <div class="card">
        <div class="label">GPS fix</div>
        <div class="value" id="gpsStatus">NO_FIX</div>
    </div>
    <div class="card">
        <div class="label">ESP32 timestamp</div>
        <div class="value" id="timestamp" style="font-size:17px">Waiting...</div>
    </div>
</div>

<div class="small">
    Auto-refreshes every 2 seconds. Last server update:
    <span id="received">Waiting...</span>
    <br><span id="connection">Connecting to server...</span>
</div>

<script>
async function updateDashboard() {
    try {
        const response = await fetch('/latest?t=' + Date.now(), {
            cache: 'no-store'
        });
        if (!response.ok) throw new Error('HTTP ' + response.status);

        const result = await response.json();
        const d = result.reading || {};

        document.getElementById('distance').textContent =
            d.distance_cm == null ? 'No valid reading' :
            Number(d.distance_cm).toFixed(2) + ' cm';

        document.getElementById('status').textContent =
            d.status || 'WAITING';

        document.getElementById('led').textContent =
            d.led || 'LED_OFF';

        document.getElementById('gps').textContent =
            d.latitude == null || d.longitude == null ? 'No coordinates' :
            Number(d.latitude).toFixed(6) + ', ' +
            Number(d.longitude).toFixed(6);

        document.getElementById('gpsStatus').textContent =
            d.gps_status || 'NO_FIX';

        document.getElementById('timestamp').textContent =
            d.timestamp || 'Not available';

        document.getElementById('received').textContent =
            d.received_at || 'No data received';

        document.getElementById('connection').textContent =
            'Connected • Updated ' + new Date().toLocaleTimeString();

    } catch (error) {
        document.getElementById('connection').textContent =
            'Server connection failed: ' + error.message;
    }
}

updateDashboard();
setInterval(updateDashboard, 2000);
</script>
</body>
</html>
"""


class EcoSpillHandler(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            body = DASHBOARD_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif path == "/health":
            self.send_json({"status": "ok"})

        
        elif path == "/latest":
            with data_lock:
                reading = latest_reading.copy()

                # Include the current incident ID in the response.
                reading["incident_id"] = (
                    incident_id if active_incident else None
                )

            self.send_json({
                "status": "ok",
                "reading": reading
            })


        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path

        if path != "/data":
            self.send_json({"error": "Not found"}, 404)
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0:
                self.send_json({"error": "Empty request body"}, 400)
                return

            data = json.loads(self.rfile.read(length).decode("utf-8"))
            reading = process_reading(data)
            self.send_json({"status": "ok", "reading": reading})

        except (ValueError, json.JSONDecodeError) as error:
            self.send_json({"error": "Invalid JSON", "detail": str(error)}, 400)

        except Exception as error:
            print("Request error:", error)
            self.send_json({"error": "Server error"}, 500)

    def log_message(self, format_string, *args):
        print("[SERVER]", format_string % args)


if __name__ == "__main__":
    print(f"EcoSpillGuard server starting on port {PORT}...")
    print("Dashboard: http://127.0.0.1:8000/")
    print("Health:    http://127.0.0.1:8000/health")
    print("Latest:    http://127.0.0.1:8000/latest")
    print("For teammates, use your laptop's Wi-Fi IP with port 8000.")

    server = ThreadingHTTPServer((HOST, PORT), EcoSpillHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping EcoSpillGuard server...")
    finally:
        server.server_close()
