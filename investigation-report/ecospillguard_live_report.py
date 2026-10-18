"""
EcoSpillGuard — 8-page Live Hardware Investigation Report
=========================================================
Fetches the latest real reading from the local backend and generates an
8-page PDF. Missing values are explicitly marked unavailable; no readings,
incident facts, crew actions, causes, or GPS coordinates are invented.

Run from the backend folder:
    python ecospillguard_live_report.py

Backend endpoint:
    http://127.0.0.1:8000/latest

Firebase incident details can be integrated later.
"""

from datetime import datetime
from pathlib import Path
import json
import sys
import urllib.error
import urllib.request
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)

API_URL = "http://127.0.0.1:8000/latest"
OUTPUT_PDF = Path(__file__).resolve().parent / "EcoSpillGuard_Investigation_Report.pdf"

NAVY = colors.HexColor("#12304A")
BLUE = colors.HexColor("#1E6A8D")
PALE_BLUE = colors.HexColor("#EAF3F8")
LIGHT_GREY = colors.HexColor("#F3F5F7")
MID_GREY = colors.HexColor("#5D6872")
BORDER = colors.HexColor("#CCD5DC")
WARNING_BG = colors.HexColor("#FFF3D6")
WARNING_TEXT = colors.HexColor("#805500")
GREEN_BG = colors.HexColor("#E5F5EA")
GREEN_TEXT = colors.HexColor("#21663A")


def fetch_live_reading():
    """Fetch the latest reading from the running local backend."""
    request = urllib.request.Request(
        API_URL,
        headers={"Accept": "application/json", "User-Agent": "EcoSpillGuard-Report/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Cannot reach {API_URL}. Start ecospill_server.py first. Details: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("The backend response was not valid JSON.") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected backend response: expected a JSON object.")
    reading = payload.get("reading", payload)
    if not isinstance(reading, dict):
        raise RuntimeError("Unexpected backend response: 'reading' is not an object.")
    return reading


def display(value, missing="Unavailable"):
    if value is None or value == "":
        return missing
    return str(value)


def make_styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(
        name="CoverTitle", parent=s["Title"], fontName="Helvetica-Bold",
        fontSize=25, leading=30, textColor=NAVY, alignment=TA_CENTER,
        spaceAfter=7 * mm,
    ))
    s.add(ParagraphStyle(
        name="CoverSub", parent=s["Normal"], fontSize=12, leading=17,
        textColor=MID_GREY, alignment=TA_CENTER, spaceAfter=6 * mm,
    ))
    s.add(ParagraphStyle(
        name="SectionTitle", parent=s["Heading1"], fontName="Helvetica-Bold",
        fontSize=16, leading=20, textColor=NAVY, spaceAfter=4 * mm,
    ))
    s.add(ParagraphStyle(
        name="SubTitle", parent=s["Heading2"], fontName="Helvetica-Bold",
        fontSize=11, leading=14, textColor=BLUE, spaceBefore=3 * mm,
        spaceAfter=2 * mm, keepWithNext=True,
    ))
    s.add(ParagraphStyle(
        name="Body9", parent=s["BodyText"], fontSize=9, leading=13,
        spaceAfter=2.5 * mm,
    ))
    s.add(ParagraphStyle(
        name="BodySmall", parent=s["BodyText"], fontSize=8, leading=11,
        textColor=MID_GREY, spaceAfter=2 * mm,
    ))
    s.add(ParagraphStyle(
        name="Warning", parent=s["BodyText"], fontName="Helvetica-Bold",
        fontSize=9, leading=13, textColor=WARNING_TEXT, spaceAfter=2.5 * mm,
    ))
    s.add(ParagraphStyle(
        name="Cell", parent=s["BodyText"], fontSize=7.7, leading=10,
        wordWrap="CJK",
    ))
    s.add(ParagraphStyle(
        name="CellHeader", parent=s["BodyText"], fontName="Helvetica-Bold",
        fontSize=7.7, leading=10, textColor=colors.white, wordWrap="CJK",
    ))
    s.add(ParagraphStyle(
        name="Raw", parent=s["Code"], fontName="Courier",
        fontSize=8, leading=11, wordWrap="CJK",
    ))
    s.add(ParagraphStyle(
        name="Callout", parent=s["BodyText"], fontName="Helvetica-Bold",
        fontSize=10, leading=15, textColor=NAVY, backColor=PALE_BLUE,
        borderPadding=8, spaceBefore=2 * mm, spaceAfter=3 * mm,
    ))
    return s


def P(value, style):
    """Escape all dynamic text before inserting it into a ReportLab paragraph."""
    return Paragraph(escape(str(value)), style)


def bullet(text, styles):
    return Paragraph("• " + escape(str(text)), styles["Body9"], bulletText=None)


def table(rows, widths, styles, header=True):
    converted = []
    for i, row in enumerate(rows):
        sty = styles["CellHeader"] if header and i == 0 else styles["Cell"]
        converted.append([
            item if isinstance(item, Paragraph) else P(item, sty)
            for item in row
        ])
    t = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        cmds += [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ]
    else:
        cmds += [
            ("BACKGROUND", (0, 0), (0, -1), PALE_BLUE),
            ("ROWBACKGROUNDS", (1, 0), (-1, -1), [colors.white, LIGHT_GREY]),
        ]
    t.setStyle(TableStyle(cmds))
    return t


def info_table(items, styles, key_width=47 * mm):
    return table([[k, v] for k, v in items], [key_width, 120 * mm], styles, header=False)


def rtc_note(timestamp):
    if not timestamp:
        return "No sensor timestamp was returned by the backend."
    if str(timestamp).startswith("2000-01-01"):
        return ("The timestamp begins with 2000-01-01 and may be a default/unset RTC value. "
                "Set and verify the RTC before treating this as the incident time.")
    return "Timestamp was returned by the backend; verify it against the RTC and local time."


def gps_note(gps_status, lat, lon):
    if lat is None or lon is None:
        return f"GPS coordinates are unavailable. Backend GPS status: {display(gps_status)}."
    return (f"Coordinates returned: latitude {lat}, longitude {lon}. "
            f"Backend GPS status: {display(gps_status)}. Verify the fix.")


def draw_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 12 * mm, w, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(18 * mm, h - 7.5 * mm, "ECOSPILLGUARD")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(w - 18 * mm, h - 7.5 * mm, "Oil Spill Investigation Report")
    canvas.setStrokeColor(BORDER)
    canvas.line(18 * mm, 14 * mm, w - 18 * mm, 14 * mm)
    canvas.setFillColor(MID_GREY)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(18 * mm, 9 * mm, "PROTOTYPE — MASTER / CHIEF ENGINEER MUST VERIFY")
    canvas.drawRightString(w - 18 * mm, 9 * mm, f"Page {doc.page} of 8")
    canvas.restoreState()


def build_report(reading):
    generated = datetime.now().astimezone()
    s = make_styles()
    received = reading.get("received_at")
    sensor_time = reading.get("timestamp")
    distance = reading.get("distance_cm")
    status = reading.get("status")
    led = reading.get("led")
    water = reading.get("water_percent")
    lat = reading.get("latitude")
    lon = reading.get("longitude")
    gps = reading.get("gps_status")

    warnings = []
    if distance is None:
        warnings.append("Ultrasonic distance is missing.")
    if sensor_time is None or str(sensor_time).startswith("2000-01-01"):
        warnings.append("RTC timestamp may be unset/default; verify the RTC.")
    if lat is None or lon is None:
        warnings.append(f"GPS coordinates unavailable (status: {display(gps)}).")
    if water is None:
        warnings.append("Water percentage was not supplied by the backend.")

    story = []

    # PAGE 1 — COVER AND EXECUTIVE SUMMARY
    story += [
        Spacer(1, 18 * mm),
        P("ECOSPILLGUARD", s["CoverTitle"]),
        P("Oil Spill Monitoring and Investigation Report", s["CoverSub"]),
        Spacer(1, 8 * mm),
        P("DRAFT — AI-GENERATED — MASTER / CHIEF ENGINEER MUST VERIFY", s["Warning"]),
        Spacer(1, 4 * mm),
        P("Purpose", s["SubTitle"]),
        P("This report presents the latest hardware reading received by the EcoSpillGuard local backend, "
          "records data-quality limitations, and provides a structured place for authorized personnel to "
          "review an incident. It does not by itself confirm an oil spill or leak.", s["Body9"]),
        info_table([
            ("Report generated", generated.isoformat(timespec="seconds")),
            ("Backend received at", display(received)),
            ("Sensor timestamp", display(sensor_time)),
            ("Data source", API_URL),
            ("Current sensor status", display(status)),
        ], s),
        Spacer(1, 7 * mm),
        P("Live reading at a glance", s["SubTitle"]),
        table([
            ["Measurement", "Current returned value"],
            ["Ultrasonic distance", f"{display(distance)} cm"],
            ["Status", display(status)],
            ["Red LED", display(led)],
            ["GPS status", display(gps)],
            ["Water percentage", display(water)],
        ], [65 * mm, 102 * mm], s),
        Spacer(1, 6 * mm),
        P("Important: a distance measurement alone is not proof of a leak. "
          "Interpret it against the tank's known reference level and the project's validated threshold logic.",
          s["Callout"]),
        PageBreak(),
    ]

    # PAGE 2 — INCIDENT DETAILS
    story += [
        P("1. Incident Details", s["SectionTitle"]),
        P("The following values are populated from the live hardware endpoint. Fields that the backend "
          "does not provide are marked unavailable and must not be guessed.", s["Body9"]),
        info_table([
            ("Incident ID", "Not provided by current hardware endpoint"),
            ("Vessel / tank identifier", "Not provided by current hardware endpoint"),
            ("Backend receipt time", display(received)),
            ("Sensor / RTC timestamp", display(sensor_time)),
            ("Ultrasonic distance (cm)", display(distance)),
            ("Water percentage", display(water)),
            ("Sensor status", display(status)),
            ("LED state", display(led)),
            ("GPS status", display(gps)),
            ("Latitude", display(lat)),
            ("Longitude", display(lon)),
        ], s),
        P("Environmental and operating conditions", s["SubTitle"]),
        P("Water conditions, vessel speed, tank identity, oil type, tank capacity, weather, and operating "
          "conditions are not included in the current /latest response. These details should be entered by "
          "authorized personnel or supplied by the future frontend/Firebase integration.", s["Body9"]),
        P("Incident classification", s["SubTitle"]),
        P("Current classification: not confirmed from this reading alone. The backend status is "
          + display(status) + ", but a normal status is not a substitute for the project's complete "
          "leak-detection logic or a physical inspection.", s["Body9"]),
        PageBreak(),
    ]

    # PAGE 3 — HARDWARE AND DATA FLOW
    story += [
        P("2. Hardware and Data Flow", s["SectionTitle"]),
        P("Prototype data path", s["SubTitle"]),
        table([
            ["Stage", "Role in the prototype", "Current report status"],
            ["Ultrasonic sensor", "Measures distance to the tank surface/reference.", display(distance) + " cm returned"],
            ["ESP32 controller", "Reads the sensor and sends a structured reading to the backend.", "Backend reading received"],
            ["Status / LED logic", "Reports status and LED state based on the implemented logic.", f"{display(status)} / {display(led)}"],
            ["RTC module", "Provides the sensor timestamp.", display(sensor_time)],
            ["GPS module", "Provides latitude and longitude when a valid fix is available.", display(gps)],
            ["Local backend", "Makes the latest reading available at /latest.", "Responding successfully"],
            ["PDF generator", "Fetches the latest record and includes it in this report.", "Generated from live response"],
        ], [30 * mm, 82 * mm, 55 * mm], s),
        P("Interpretation of the ultrasonic measurement", s["SubTitle"]),
        P("The sensor reports distance, not directly the volume or percentage of oil. Converting distance to "
          "a tank level requires the sensor mounting position, tank geometry, reference measurement, and a "
          "validated conversion rule. No conversion is performed here because those details are not present "
          "in the backend response.", s["Body9"]),
        P("Camera evidence", s["SubTitle"]),
        P("No camera image or camera metadata is supplied by this endpoint. Therefore, this report does not "
          "claim that a camera image was captured or reviewed.", s["Body9"]),
        PageBreak(),
    ]

    # PAGE 4 — LIVE READING AND QUALITY
    story += [
        P("3. Live Sensor Reading and Data Quality", s["SectionTitle"]),
        P("Raw field review", s["SubTitle"]),
        table([
            ["Field", "Returned value", "Quality / interpretation"],
            ["received_at", display(received), "Backend receipt time; not the RTC time."],
            ["timestamp", display(sensor_time), rtc_note(sensor_time)],
            ["distance_cm", display(distance), "Ultrasonic distance as reported."],
            ["water_percent", display(water), "Unavailable; do not substitute zero."],
            ["status", display(status), "Status string supplied by backend."],
            ["led", display(led), "LED state supplied by backend."],
            ["latitude", display(lat), "Unavailable if no GPS coordinate is returned."],
            ["longitude", display(lon), "Unavailable if no GPS coordinate is returned."],
            ["gps_status", display(gps), gps_note(gps, lat, lon)],
        ], [31 * mm, 37 * mm, 99 * mm], s),
        P("Data-quality flags", s["SubTitle"]),
    ]
    if warnings:
        for warning in warnings:
            story.append(bullet(warning, s))
    else:
        story.append(P("No missing values were detected among the fields checked by this report.", s["Body9"]))
    story += [
        P("The backend receipt time shows when the backend received the record. It should not be substituted "
          "for an incorrect RTC timestamp without clearly labelling it as receipt time.", s["Body9"]),
        PageBreak(),
    ]

    # PAGE 5 — DETECTION AND ALERT LOGIC
    story += [
        P("4. Detection and Alert Interpretation", s["SectionTitle"]),
        P("Current state", s["SubTitle"]),
        P(f"The latest returned status is {display(status)} and the returned LED state is {display(led)}. "
          "This report records those fields as supplied; it does not independently activate the LED or buzzer.", s["Body9"]),
        P("What is needed to assess an unexpected level drop", s["SubTitle"]),
        table([
            ["Required input", "Why it matters", "Current availability"],
            ["Known normal/baseline distance", "Allows current distance to be compared with a reference.", "Not supplied in /latest"],
            ["Previous readings and timestamps", "Shows whether the level is changing unexpectedly over time.", "Not included in this response"],
            ["Tank dimensions and sensor position", "Needed to interpret distance as level/volume.", "Not supplied"],
            ["Validated alert threshold", "Defines when the prototype should flag an anomaly.", "Not included in this response"],
            ["Human inspection", "Checks whether an alert corresponds to a real-world condition.", "Must be recorded by crew"],
        ], [47 * mm, 77 * mm, 43 * mm], s),
        P("Do not label this reading as a confirmed spill", s["SubTitle"]),
        P("A single distance value and a NORMAL status do not establish that a leak has or has not occurred. "
          "The system should compare a sequence of readings with the tank baseline and the configured rules, "
          "then request human verification when an anomaly is detected.", s["Body9"]),
        P("Alert actions", s["SubTitle"]),
        P("If the prototype's implemented threshold logic activates a red LED or buzzer, the actual event, "
          "time, and crew response should be recorded from the system or entered by an authorized user. "
          "This PDF does not fabricate any alert or action history.", s["Body9"]),
        PageBreak(),
    ]

    # PAGE 6 — ROOT CAUSE, ACTIONS, AND EVIDENCE
    story += [
        P("5. Root Cause, Measures Taken, and Evidence", s["SectionTitle"]),
        P("Root cause", s["SubTitle"]),
        P("Not provided. The AI/report generator must not state a cause as a confirmed fact. In the final "
          "workflow, crew should select a cause category; AI may suggest contributing factors from available "
          "evidence, clearly marked as suggestions requiring verification by the Chief Engineer.", s["Body9"]),
        info_table([
            ("Crew-selected cause category", "Not provided by current endpoint"),
            ("AI-suggested contributing factors", "Not generated from this sensor record alone"),
            ("Verification status", "Pending authorized human review"),
        ], s),
        P("Measures taken — timeline", s["SubTitle"]),
        table([
            ["Time", "Action / observation", "Recorded by / source"],
            ["Not provided", "No crew action history is included in the live reading.", "Not provided"],
            ["Not provided", "No valve operation or physical response is asserted by this report.", "Not provided"],
            ["Not provided", "No camera evidence is attached to the current backend response.", "Not provided"],
        ], [32 * mm, 92 * mm, 43 * mm], s),
        P("Evidence register", s["SubTitle"]),
        table([
            ["Evidence item", "Availability in current endpoint"],
            ["Live sensor JSON", "Available; reproduced on page 7"],
            ["CCTV / ESP32-CAM frame", "Not supplied"],
            ["Camera ID and capture time", "Not supplied"],
            ["ML confidence score", "Not supplied by this endpoint"],
            ["Crew confirmation", "Not supplied"],
        ], [63 * mm, 104 * mm], s),
        P("All incident actions, evidence timestamps, and camera identifiers should be added only when they "
          "are actually captured or supplied by an authorized source.", s["BodySmall"]),
        PageBreak(),
    ]

    # PAGE 7 — FUTURE MEASURES AND VERIFICATION
    story += [
        P("6. Verification and Future Preventive Measures", s["SectionTitle"]),
        P("Immediate prototype checks", s["SubTitle"]),
        bullet("Compare the ultrasonic distance with a known physical measurement.", s),
        bullet("Confirm the sensor is mounted securely and its measuring direction is correct.", s),
        bullet("Set the RTC and verify that its timestamp matches local time.", s),
        bullet("Test the GPS module in a suitable location and wait for a valid fix before relying on coordinates.", s),
        bullet("Confirm that LED/buzzer state reported by the backend matches the physical outputs.", s),
        bullet("Record several readings under known safe conditions to establish a baseline before testing anomaly logic.", s),
        P("Longer-term report improvements", s["SubTitle"]),
        P("The final application can supply additional incident details from Firebase, including vessel/tank "
          "metadata, crew-selected cause category, action timeline, and evidence references. These fields are "
          "intentionally not connected in this version.", s["Body9"]),
        P("Case-based recommendations", s["SubTitle"]),
        P("A future recommendation section can retrieve relevant past spill cases from the case library and "
          "cite each case ID. Recommendations should be based on retrieved case records, not presented as "
          "verified facts about this current reading.", s["Body9"]),
        P("Operational caution", s["SubTitle"]),
        P("This student prototype is for demonstration and evaluation. Follow approved vessel procedures and "
          "human review; do not rely on this PDF as the sole basis for safety-critical decisions.", s["Body9"]),
        PageBreak(),
    ]

    # PAGE 8 — APPENDIX AND SIGN-OFF
    raw = json.dumps(reading, indent=2, ensure_ascii=False, default=str)
    story += [
        P("7. Appendix — Original Live Backend Record", s["SectionTitle"]),
        P("The following JSON is the reading object returned by the backend during PDF generation.", s["Body9"]),
        P(escape(raw).replace("\n", "<br/>").replace(" ", "&nbsp;"), s["Raw"]),
        Spacer(1, 4 * mm),
        P("8. Review and Sign-off", s["SectionTitle"]),
        info_table([
            ("Report generated at", generated.isoformat(timespec="seconds")),
            ("Backend URL", API_URL),
            ("Backend received at", display(received)),
            ("RTC note", rtc_note(sensor_time)),
            ("GPS note", gps_note(gps, lat, lon)),
            ("Report status", "Draft — review required"),
        ], s),
        Spacer(1, 5 * mm),
        P("Review checklist", s["SubTitle"]),
        bullet("Verify the sensor reading against the physical prototype.", s),
        bullet("Verify/fix RTC timestamp and GPS fix.", s),
        bullet("Confirm whether an alert occurred; enter actual crew actions and evidence.", s),
        bullet("Master / Chief Engineer to review all incident interpretations.", s),
        Spacer(1, 4 * mm),
        P("Reviewed by: __________________________________________", s["Body9"]),
        P("Role: Master / Chief Engineer", s["Body9"]),
        P("Signature: ____________________________________________", s["Body9"]),
        P("Date and time of review: _______________________________", s["Body9"]),
        Spacer(1, 3 * mm),
        P("Report limitation: generated from the live backend reading only. Additional incident data, "
          "Firebase fields, images, and historical case recommendations are not connected in this version.", s["BodySmall"]),
    ]

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF), pagesize=A4,
        rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=19 * mm, bottomMargin=19 * mm,
        title="EcoSpillGuard 8-page Live Hardware Investigation Report",
        author="EcoSpillGuard",
    )
    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)


def main():
    print(f"Fetching live hardware data from {API_URL} ...")
    try:
        reading = fetch_live_reading()
        print("LIVE READING RECEIVED:")
        for key in (
            "received_at", "timestamp", "distance_cm", "water_percent", "status",
            "led", "latitude", "longitude", "gps_status",
        ):
            print(f"  {key}: {display(reading.get(key))}")
        build_report(reading)
        print(f"\nPDF CREATED: {OUTPUT_PDF}")
        print(f"File size: {OUTPUT_PDF.stat().st_size / 1024:.1f} KB")
        print("The report includes eight planned sections/pages and uses the live backend reading.")
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
