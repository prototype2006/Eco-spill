
import json
import urllib.request
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

SERVER_URL = "http://127.0.0.1:8000/latest"


def get_latest_reading():
    """Fetch the latest sensor reading from the backend."""
    try:
        with urllib.request.urlopen(SERVER_URL, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data.get("reading", {})
    except Exception as error:
        print("Could not fetch sensor data:", error)
        return None


def ask(prompt):
    """Collect information from the crew."""
    answer = input(prompt).strip()
    return answer if answer else "Not provided"


def create_pdf(report):
    """Create a PDF containing the four required report sections."""
    filename = "EcoSpillGuard_Incident_Report.pdf"
    pdf = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    content = []

    def add_heading(text):
        content.append(Paragraph(text, styles["Heading2"]))
        content.append(Spacer(1, 8))

    def add_line(label, value):
        # Escape special characters before putting data into PDF paragraphs.
        from xml.sax.saxutils import escape
        content.append(
            Paragraph(f"<b>{escape(str(label))}:</b> "
                      f"{escape(str(value))}", styles["BodyText"])
        )
        content.append(Spacer(1, 5))

    content.append(Paragraph(
        "ECOSPILLGUARD INCIDENT REPORT",
        styles["Title"]
    ))
    content.append(Paragraph(
        "<b>DRAFT — AI-GENERATED — MASTER MUST VERIFY</b>",
        styles["BodyText"]
    ))
    content.append(Spacer(1, 16))

    add_heading("1. Incident Details")
    add_line("Report generated", report["generated_at"])
    add_line("Vessel", report["vessel"])
    add_line("Tank ID", report["tank_id"])
    add_line("Crew-reported oil type", report["oil_type"])
    add_line("Estimated quantity", report["quantity"])
    add_line("Sensor timestamp", report["sensor_timestamp"])
    add_line("Distance reading", report["distance"])
    add_line("Sensor status", report["status"])
    add_line("GPS coordinates", report["gps"])
    add_line("GPS fix", report["gps_status"])

    add_heading("2. Suspected Root Cause")
    add_line("Cause selected by crew", report["crew_cause"])
    add_line(
        "AI-suggested contributing factors",
        "Not generated yet. Verify all possible factors with the Chief Engineer."
    )
    add_line(
        "Verification",
        "The cause is unconfirmed. Do not treat a sensor alert as proof of an oil spill."
    )

    add_heading("3. Measures Taken and Evidence")
    add_line("Actions reported by crew", report["actions"])
    add_line(
        "Camera evidence",
        "Not attached or verified by this report generator."
    )
    add_line(
        "Evidence note",
        "Record actual timestamps, camera ID and model confidence only when available."
    )

    add_heading("4. Future Preventive Measures")
    add_line(
        "Recommendations",
        "Pending review against verified historical spill cases."
    )
    add_line(
        "Historical case references",
        "No case IDs attached. A verified case library must be connected before citing cases."
    )

    pdf.build(content)
    print(f"\nPDF created: {filename}")


def main():
    reading = get_latest_reading()

    if reading is None:
        print("Start ecospill_server.py and try again.")
        return

    print("\n===== INCIDENT REPORT DETAILS =====")
    print("Latest sensor status:", reading.get("status"))
    print("Latest distance:", reading.get("distance_cm"), "cm")

    # Crew-entered information; blanks are recorded as Not provided.
    report = {
        "generated_at": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "vessel": ask("Vessel name: "),
        "tank_id": ask("Tank ID: "),
        "oil_type": ask("Oil type (if known): "),
        "quantity": ask("Estimated quantity and unit (if known): "),
        "crew_cause": ask("Suspected cause selected by crew: "),
        "actions": ask("Actions actually taken by crew: "),
        "sensor_timestamp": reading.get("timestamp") or "Unavailable",
        "distance": (
            str(reading["distance_cm"]) + " cm"
            if reading.get("distance_cm") is not None
            else "No valid reading"
        ),
        "status": reading.get("status", "Unknown"),
        "gps": (
            f'{reading["latitude"]}, {reading["longitude"]}'
            if reading.get("latitude") is not None
            and reading.get("longitude") is not None
            else "Unavailable"
        ),
        "gps_status": reading.get("gps_status", "Unknown"),
    }

    create_pdf(report)


if __name__ == "__main__":
    main()
