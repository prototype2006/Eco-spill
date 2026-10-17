
import csv
import serial
import time

# ESP32 serial connection
PORT = "COM5"
BAUD_RATE = 115200

# CSV file created in the current working folder
CSV_FILE = "ecospill_data.csv"

# Columns produced by the EcoSpillGuard ESP32 sketch
HEADERS = [
    "Time",
    "Distance_cm",
    "Status",
    "LED",
    "Latitude",
    "Longitude",
    "GPS"
]

print("Connecting to EcoSpillGuard on", PORT)

try:
    # Open the ESP32 serial connection
    with serial.Serial(PORT, BAUD_RATE, timeout=2) as esp32:

        # Allow the serial connection to settle
        time.sleep(2)

        print("Connected! Saving sensor readings to CSV.")
        print("Press Ctrl+C to stop logging.")

        # Create/open the CSV file
        with open(
            CSV_FILE,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            # Add column headings only if the file is empty
            if file.tell() == 0:
                writer.writerow(HEADERS)
                file.flush()

            while True:
                # Read one line sent by the ESP32
                line = esp32.readline().decode(
                    "utf-8", errors="replace"
                ).strip()

                if not line:
                    continue

                # Ignore startup messages and the ESP32 header
                if line.startswith("Time,Distance_cm"):
                    continue

                # Split the CSV row received over serial
                row = next(csv.reader([line]))

                # Accept only the seven expected columns
                if len(row) != len(HEADERS):
                    print("Skipping non-data line:", line)
                    continue

                # Save the sensor reading
                writer.writerow(row)
                file.flush()

                print("Saved:", line)

except serial.SerialException as error:
    print("Serial connection error:", error)
    print("Check COM5 and close Arduino Serial Monitor.")

except KeyboardInterrupt:
    print("\nLogging stopped.")

finally:
    print("CSV logger finished.")
