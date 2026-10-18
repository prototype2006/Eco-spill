
import csv
import json
import os
import time
import urllib.request
import urllib.error
import serial

# ============================================================
# SETTINGS
# ============================================================

PORT = "COM5"
BAUD_RATE = 115200

# Local CSV backup
CSV_FILE = "ecospill_data.csv"

# Your local EcoSpillGuard backend
SERVER_URL = "http://127.0.0.1:8000/data"

HEADERS = [
    "Time",
    "Distance_cm",
    "Status",
    "LED",
    "Latitude",
    "Longitude",
    "GPS"
]


# ============================================================
# SEND ONE READING TO THE SERVER
# ============================================================

def send_to_server(row):
    # Convert the ESP32 CSV columns into JSON fields.
    timestamp, distance, status, led, latitude, longitude, gps = row

    # INVALID is a measurement state, not proof of a spill.
    if distance.strip().upper() == "INVALID":
        distance_value = None
    else:
        try:
            distance_value = float(distance)
        except ValueError:
            distance_value = None

    # Convert coordinates only when they contain numeric values.
    try:
        latitude_value = float(latitude)
    except ValueError:
        latitude_value = None

    try:
        longitude_value = float(longitude)
    except ValueError:
        longitude_value = None

    # The backend expects ALERT_ON or NORMAL.
    # Do not create an incident from an invalid measurement.
    status_value = status.strip().upper()

    if distance_value is None or status_value == "UNKNOWN":
        status_value = "INVALID"
    elif status_value == "ALERT":
        status_value = "ALERT_ON"
    elif status_value != "NORMAL":
        status_value = "INVALID"

    payload = {
        "timestamp": timestamp,
        "distance_cm": distance_value,
        "water_percent": None,  # Not calculated by the current ESP32 sketch
        "status": status_value,
        "led": led,
        "latitude": latitude_value,
        "longitude": longitude_value,
        "gps_status": gps
    }

    request = urllib.request.Request(
        SERVER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            if response.status == 200:
                print("SERVER OK:", status_value, distance_value)
            else:
                print("SERVER returned HTTP", response.status)

    except (urllib.error.URLError, TimeoutError, OSError) as error:
        print("SERVER ERROR:", error)
        print("Is ecospill_server.py running on port 8000?")


# ============================================================
# MAIN SERIAL LOGGER
# ============================================================

def main():
    print("Connecting to EcoSpillGuard on", PORT)
    print("Website backend:", SERVER_URL)

    try:
        with serial.Serial(PORT, BAUD_RATE, timeout=2) as esp32:
            # Allow ESP32 serial output to settle after connection.
            time.sleep(2)

            print("Connected to ESP32!")
            print("Saving CSV and forwarding readings to server.")
            print("Press Ctrl+C to stop.")

            with open(
                CSV_FILE,
                "a",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                # Check actual file size, not the append-mode cursor.
                if os.path.getsize(CSV_FILE) == 0:
                    writer.writerow(HEADERS)
                    file.flush()

                while True:
                    line = esp32.readline().decode(
                        "utf-8", errors="replace"
                    ).strip()

                    if not line:
                        continue

                    # Ignore startup messages, CSV header and diagnostics.
                    if line.startswith("Time,Distance_cm"):
                        continue

                    row = next(csv.reader([line]))

                    # Only accept actual seven-column ESP32 data rows.
                    if len(row) != len(HEADERS):
                        print("Skipping non-data line:", line)
                        continue

                    # Save the original reading to the CSV backup.
                    writer.writerow(row)
                    file.flush()

                    print("ESP32:", line)

                    # Forward the reading to the backend.
                    send_to_server(row)

    except serial.SerialException as error:
        print("Serial connection error:", error)
        print("Check COM5 and close Arduino Serial Monitor.")

    except KeyboardInterrupt:
        print("\nLogging stopped.")

    finally:
        print("CSV logger finished.")


if __name__ == "__main__":
    main()
