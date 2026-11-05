
from io import BytesIO
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


def _display(value):
    """Display missing values honestly instead of inventing data."""
    if value is None or value == "":
        return "Not available"
    return str(value)


def _section(title, styles):
    return Paragraph(title, styles["SectionHeading"])


def generate_incident_pdf(incident):
    """Generate an EcoSpill investigation report as PDF bytes."""
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.7 * cm,
        leftMargin=1.7 * cm,
        topMargin=1.7 * cm,
        bottomMargin=1.7 * cm,
        title=f"EcoSpill Incident Report - "
              f"{incident.get('incident_id', 'Unknown')}",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontSize=21,
        leading=26,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#087E8B"),
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#087E8B"),
        spaceBefore=12,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="SmallText",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
    ))

    story = []

    def add_table(rows, widths=None):
        safe_rows = [
            [
                Paragraph(
                    _display(cell).replace("&", "&amp;")
                    .replace("<", "&lt;").replace(">", "&gt;"),
                    styles["SmallText"],
                )
                for cell in row
            ]
            for row in rows
        ]

        table = Table(
            safe_rows,
            colWidths=widths,
            repeatRows=1 if len(rows) > 1 else 0,
            hAlign="LEFT",
        )
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0),
             colors.HexColor("#DCEFF0")),
            ("TEXTCOLOR", (0, 0), (-1, 0),
             colors.HexColor("#12343B")),
            ("GRID", (0, 0), (-1, -1), 0.4,
             colors.HexColor("#CBD5D8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(table)
        story.append(Spacer(1, 8))

    vessel = incident.get("vessel") or {}
    details = incident.get("incident") or {}
    location = incident.get("location") or {}
    crew = incident.get("crew_investigation") or {}
    ml = incident.get("ml_analysis") or {}
    report = incident.get("report") or {}
    readings = incident.get("sensor_readings") or []
    evidence = incident.get("evidence") or []

    incident_id = incident.get("incident_id", "Unknown")

    story.append(Paragraph("EcoSpill", styles["ReportTitle"]))
    story.append(Paragraph(
        "Marine Incident Investigation Report",
        styles["Heading2"],
    ))
    story.append(Paragraph(
        f"Incident ID: {_display(incident_id)}",
        styles["BodyText"],
    ))
    story.append(Paragraph(
        "Generated: " + datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M UTC"
        ),
        styles["SmallText"],
    ))
    story.append(Spacer(1, 12))

    story.append(_section("1. Executive Summary", styles))
    story.append(Paragraph(
        "This report records the available incident, sensor, crew, "
        "and AI-analysis information. A sensor alert alone does not "
        "confirm an oil spill. Missing information is marked as "
        "'Not available'.",
        styles["BodyText"],
    ))

    story.append(_section("2. Vessel Information", styles))
    add_table([
        ["Field", "Value"],
        ["Vessel name", vessel.get("name")],
        ["Vessel ID", vessel.get("vessel_id")],
        ["Vessel type", vessel.get("vessel_type")],
        ["Domain", vessel.get("domain")],
    ], [5 * cm, 11 * cm])

    story.append(_section("3. Incident Details", styles))
    add_table([
        ["Field", "Value"],
        ["Status", details.get("status", incident.get("status"))],
        ["Description", details.get("description", incident.get("description"))],
        ["Detection time", details.get("detection_time", incident.get("created_at"))],
        ["Last updated", incident.get("updated_at")],
        ["Oil type", details.get("oil_type")],
        ["Estimated quantity", details.get("estimated_quantity")],
        ["Tank ID", details.get("tank_id")],
        ["Edge status", incident.get("edge_status")],
        ["Edge end time", incident.get("edge_end_time")],
    ], [5 * cm, 11 * cm])

    story.append(_section("4. Location", styles))
    add_table([
        ["Field", "Value"],
        ["Latitude", location.get("latitude")],
        ["Longitude", location.get("longitude")],
    ], [5 * cm, 11 * cm])

    story.append(_section("5. Sensor Readings", styles))
    if readings:
        rows = [[
            "Received at", "Sensor timestamp", "Distance (cm)",
            "Water (%)", "Status"
        ]]
        for reading in readings:
            rows.append([
                reading.get("received_at"),
                reading.get("sensor_timestamp"),
                reading.get("distance_cm"),
                reading.get("water_percent"),
                reading.get("status"),
            ])
        add_table(rows, [3.4 * cm, 4.0 * cm, 2.4 * cm, 2.3 * cm, 2.9 * cm])
    else:
        story.append(Paragraph(
            "No sensor readings are linked to this incident.",
            styles["BodyText"],
        ))

        story.append(_section("6. Crew Investigation and Aftermath", styles))

    crew_rows = [["Field", "Recorded information"]]

    for key, label in [
        ("report_status", "Investigation status"),
        ("discovery_method", "Discovery method"),
        ("severity", "Assessed severity"),
        ("source_identified", "Source identification"),
        ("response_time", "Response time"),
        ("initial_actions", "Initial actions"),
        ("containment_status", "Containment status"),
        ("environmental_impact", "Observed environmental impact"),
        ("injuries", "Injuries / safety concerns"),
        ("cleanup_recovery", "Cleanup and recovery"),
        ("remaining_hazards", "Remaining hazards"),
        ("follow_up_tasks", "Follow-up actions"),
        ("captain_name", "Captain / authorized officer"),
        ("captain_notes", "Captain's notes"),
        ("cause_category", "Cause category"),
        ("cause_confirmation", "Cause confirmation"),
        ("chief_engineer_comments", "Chief engineer comments"),
        ("actions_taken", "Previously recorded actions"),
        ("crew_acknowledgement", "Crew acknowledgement"),
        ("follow_up_observations", "Previously recorded observations"),
    ]:
        crew_rows.append([label, crew.get(key)])

    add_table(crew_rows, [5 * cm, 11 * cm])

    task_log = crew.get("task_log") or []

    story.append(_section("6.1 Task and Responsibility Log", styles))

    if task_log:
        task_rows = [[
            "Task",
            "Responsible person",
            "Role",
            "Start",
            "Completion",
            "Status",
            "Outcome",
        ]]

        for task in task_log:
            task_rows.append([
                task.get("task"),
                task.get("responsible_person"),
                task.get("role"),
                task.get("start_time"),
                task.get("completion_time"),
                task.get("status"),
                task.get("outcome"),
            ])

        add_table(
            task_rows,
            [
                2.8 * cm,
                2.5 * cm,
                2.0 * cm,
                2.1 * cm,
                2.1 * cm,
                1.7 * cm,
                2.5 * cm,
            ],
        )
    else:
        story.append(Paragraph(
            "No task and responsibility entries have been recorded.",
            styles["BodyText"],
        ))

    story.append(_section("7. Historical Case Analysis and Recommendations", styles))
    story.append(Paragraph(
        "Results use historical-case retrieval with text matching, not a trained "
        "machine-learning model. Similarity does not establish the current incident's "
        "cause. Qualified vessel crew must verify all suggestions before action.",
        styles["BodyText"],
    ))
    story.append(Spacer(1, 5))

    retrieval = ml.get("recommendation_engine") or {}
    if retrieval:
        story.append(Paragraph(
            f"<b>Method:</b> {_display(retrieval.get('method'))}",
            styles["BodyText"],
        ))
        story.append(Paragraph(
            f"<b>Matched cases:</b> {_display(retrieval.get('matched_case_count'))}",
            styles["BodyText"],
        ))
        recommendations = retrieval.get("recommendations") or []
        if recommendations:
            for index, item in enumerate(recommendations, start=1):
                story.append(Paragraph(
                    f"<b>{index}. {_display(item.get('incident_name'))}</b>",
                    styles["Heading3"],
                ))
                add_table([
                    ["Field", "Historical case details"],
                    ["Case ID", item.get("case_id")],
                    ["Cause category", item.get("cause_category")],
                    ["Oil type", item.get("oil_type")],
                    ["Historical spill quantity", item.get("spill_quantity")],
                    ["Measures taken", item.get("measures_taken")],
                    ["Preventive measures", item.get("preventive_measures")],
                    ["Source", item.get("source")],
                    ["Match score (ranking only)", item.get("match_score")],
                ], [5 * cm, 11 * cm])
                story.append(Paragraph(_display(item.get("review_note")), styles["SmallText"]))
        else:
            story.append(Paragraph(
                "No relevant historical cases matched the available incident details.",
                styles["BodyText"],
            ))
        story.append(Spacer(1, 5))
        story.append(Paragraph(_display(retrieval.get("disclaimer")), styles["SmallText"]))
    else:
        for label, key in [
            ("Previously recorded matched historical cases", "matched_historical_cases"),
            ("Previously recorded recommendations", "recommendations"),
            ("Model version", "model_version"),
        ]:
            story.append(Paragraph(
                f"<b>{label}:</b> {_display(ml.get(key))}",
                styles["BodyText"],
            ))
            story.append(Spacer(1, 4))

    story.append(_section("8. Evidence", styles))
    if evidence:
        for index, item in enumerate(evidence, start=1):
            story.append(Paragraph(
                f"Evidence {index}: {_display(item)}",
                styles["BodyText"],
            ))
    else:
        story.append(Paragraph(
            "No evidence has been attached to this incident.",
            styles["BodyText"],
        ))

    story.append(_section("9. Report Metadata", styles))
    add_table([
        ["Field", "Value"],
        ["Report status", report.get("status")],
        ["PDF URL", report.get("pdf_url")],
    ], [5 * cm, 11 * cm])

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "End of report. Verify all findings before using this document "
        "for operational, regulatory, or environmental decisions.",
        styles["SmallText"],
    ))

    def add_page_number(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(
            1.7 * cm, 1.0 * cm, "EcoSpill | Incident Report"
        )
        canvas.drawRightString(
            A4[0] - 1.7 * cm, 1.0 * cm,
            f"Page {document.page}",
        )
        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    return buffer.getvalue()
