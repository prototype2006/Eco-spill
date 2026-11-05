import json
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
from core.data_interface import get_sensor_incidents
from modules.incident_management import sync_sensor_incident
from modules.report_generator import generate_incident_pdf
from modules.recommendation_engine import recommend
from modules.incident_management import (
    get_all_incidents,
    save_incident,
)
def show_incident_history():
    """Display searchable, filterable incident history."""

    st.title("Incident History")
    st.caption("Review previously recorded EcoSpillGuard incidents.")
    
    if st.button("Sync sensor incidents", type="primary"):
        with st.spinner("Fetching sensor incident history..."):
            result = get_sensor_incidents()

            if not result["connected"]:
                st.error(
                    "Could not fetch sensor incidents: "
                    + str(result["error"])
                )
            else:
                sensor_incidents = result["incidents"]
                synced = 0
                errors = []

                for sensor_incident in sensor_incidents:
                    try:
                        sync_sensor_incident(sensor_incident)
                        synced += 1
                    except Exception as exc:
                        errors.append(
                            f"{sensor_incident.get('incident_id', 'Unknown ID')}: "
                            f"{exc}"
                        )

                if synced:
                    st.success(f"Synced {synced} sensor incident(s) to Firebase.")

                if not sensor_incidents:
                    st.info("The sensor server returned no incidents.")

                for error in errors:
                    st.error(error)

                if not errors:
                    st.rerun()

    try:
        incidents = get_all_incidents()
    except Exception as exc:
        st.error(f"Could not load incidents: {exc}")
        st.info(
            "Check your Firebase login, database URL, "
            "and Realtime Database security rules."
        )
        return

    if not incidents:
        local_file = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "incidents.json"
        )

        st.info("No incidents found in Firebase yet.")

        if local_file.exists():
            if st.button("Migrate local incidents to Firebase"):
                try:
                    local_incidents = json.loads(
                        local_file.read_text(encoding="utf-8")
                    )

                    if not isinstance(local_incidents, list):
                        st.error("Local incident data must be a JSON list.")
                        st.stop()

                    migrated = 0

                    for incident in local_incidents:
                        if not isinstance(incident, dict):
                            continue

                        if not incident.get("incident_id"):
                            continue

                        save_incident(incident)
                        migrated += 1

                    st.success(
                        f"Successfully migrated {migrated} incident(s) "
                        "to Firebase."
                    )
                    st.rerun()

                except Exception as exc:
                    st.error(f"Migration failed: {exc}")

        else:
            st.warning("No local incidents.json file was found.")

        return

    # Prepare display values
    rows = []

    for item in incidents:
        vessel = item.get("vessel", {})
        details = item.get("incident", {})

        rows.append({
            "Incident ID": item.get("incident_id", "Unknown"),
            "Vessel": vessel.get("name") or "Not provided",
            "Description": details.get("description") or "Not provided",
            "Status": (details.get("status") or "suspected").title(),
            "Created At": item.get("created_at", "Not available"),
        })

    # Summary metrics
    total = len(rows)
    suspected = sum(row["Status"] == "Suspected" for row in rows)
    confirmed = sum(row["Status"] == "Confirmed" for row in rows)
    dismissed = sum(row["Status"] == "Dismissed" for row in rows)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total incidents", total)
    col2.metric("Suspected", suspected)
    col3.metric("Confirmed", confirmed)
    col4.metric("Dismissed", dismissed)

    st.divider()

    # Search and filters
    search = st.text_input(
        "Search incidents",
        placeholder="Search by incident ID, vessel, or description",
    )

    status_filter = st.selectbox(
        "Filter by status",
        ["All", "Suspected", "Confirmed", "Dismissed"],
    )

    filtered = rows

    if search.strip():
        query = search.strip().lower()
        filtered = [
            row for row in filtered
            if query in row["Incident ID"].lower()
            or query in row["Vessel"].lower()
            or query in row["Description"].lower()
        ]

    if status_filter != "All":
        filtered = [
            row for row in filtered
            if row["Status"] == status_filter
        ]

    st.subheader(f"Records ({len(filtered)})")

    if filtered:
        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No incidents match your search and filters.")

    # Incident details
    st.divider()
    st.subheader("Incident Details")

    incident_ids = [row["Incident ID"] for row in filtered]

    if not incident_ids:
        st.caption("No incident is available to inspect.")
        return

    selected_id = st.selectbox(
        "Select an incident",
        incident_ids,
    )

    selected = next(
        item for item in incidents
        if item.get("incident_id") == selected_id
    )

    vessel = selected.get("vessel", {})
    incident = selected.get("incident", {})
    location = selected.get("location", {})
    crew = selected.get("crew_investigation", {})
    ml = selected.get("ml_analysis", {})

    # Read-only recommendation generation: does not write to Firebase.
    recommendation_result = None
    recommendation_error = None
    try:
        recommendation_result = recommend(
            cause=crew.get("cause_category", ""),
            oil_type=incident.get("oil_type", ""),
            incident_description=incident.get("description", ""),
            top_k=3,
        )
    except (FileNotFoundError, ValueError, OSError) as exc:
        recommendation_error = str(exc)

    report_incident = dict(selected)
    report_incident["ml_analysis"] = dict(ml or {})
    if recommendation_result is not None:
        report_incident["ml_analysis"]["recommendation_engine"] = recommendation_result


    
    with st.expander("Location and Sensor Readings"):
        latitude = location.get("latitude")
        longitude = location.get("longitude")

        st.write(
            "**Latitude:**",
            latitude if latitude is not None else "Not available",
        )
        st.write(
            "**Longitude:**",
            longitude if longitude is not None else "Not available",
        )

        readings = selected.get("sensor_readings", [])

        if readings:
            st.dataframe(
                [
                    {
                        "Received At": reading.get(
                            "received_at", "Not available"
                        ),
                        "Sensor Timestamp": reading.get(
                            "sensor_timestamp", "Not available"
                        ),
                        "Distance (cm)": reading.get("distance_cm"),
                        "Water (%)": (
                            reading.get("water_percent") or "Not available"
                        ),
                        "Status": reading.get("status", "Unknown"),
                    }
                    for reading in readings
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No sensor readings are linked to this incident yet.")

    with st.expander("Crew Investigation & Aftermath Report", expanded=True):
        st.caption(
        "Complete this report after the crew has assessed the incident. "
        "Save a draft while the investigation is ongoing, or submit it "
        "for review when ready."
    )

        existing_crew = selected.get("crew_investigation") or {}
        existing_tasks = existing_crew.get("task_log") or []

        # Keep the editor usable even when no tasks have been recorded.
        task_rows = existing_tasks or [{
            "task": "",
            "responsible_person": "",
            "role": "",
            "start_time": "",
            "completion_time": "",
            "status": "Pending",
            "outcome": "",
        }]

        with st.form(f"crew_investigation_form_{selected_id}"):
            st.markdown("#### 1. Incident details")

            st.text_input(
                "Incident ID",
                value=selected_id,
                disabled=True,
            )

            st.text_input(
                "Vessel",
                value=(vessel.get("name") or "Not provided"),
                disabled=True,
            )

            st.text_input(
                "Incident description",
                value=(incident.get("description") or "Not provided"),
                disabled=True,
            )

            st.markdown("#### 2. Immediate response")

            discovery_options = [
                "Sensor alert",
                "Visual observation",
                "Crew report",
                "External notification",
                "Other",
            ]

            old_discovery = existing_crew.get("discovery_method")
            discovery_index = (
                discovery_options.index(old_discovery)
                if old_discovery in discovery_options else 0
            )

            discovery_method = st.selectbox(
                "How was the incident discovered?",
                discovery_options,
                index=discovery_index,
            )

            severity_options = [
                "Unknown",
                "Low",
                "Moderate",
                "High",
                "Critical",
            ]

            old_severity = existing_crew.get("severity", "Unknown")
            severity_index = (
                severity_options.index(old_severity)
                if old_severity in severity_options else 0
            )

            severity = st.selectbox(
                "Assessed severity",
                severity_options,
                index=severity_index,
            )

            source_identified = st.selectbox(
                "Has the source been identified?",
                ["Unconfirmed", "Yes", "No", "Under investigation"],
                index=[
                    "Unconfirmed",
                    "Yes",
                    "No",
                    "Under investigation",
                ].index(
                    existing_crew.get(
                        "source_identified", "Unconfirmed"
                    )
                )
                if existing_crew.get(
                    "source_identified", "Unconfirmed"
                ) in [
                    "Unconfirmed",
                    "Yes",
                    "No",
                    "Under investigation",
                ] else 0,
            )

            response_time = st.text_input(
                "Response time",
                value=existing_crew.get("response_time", ""),
                placeholder="e.g. 10 minutes after detection",
            )

            initial_actions = st.text_area(
                "Initial actions taken",
                value=existing_crew.get("initial_actions", ""),
                placeholder=(
                    "Describe containment, isolation, notifications "
                    "and other immediate actions."
                ),
            )

            st.markdown("#### 3. Task and responsibility log")
            st.caption(
                "Add rows for tasks performed, responsible crew members, "
                "timings and outcomes."
            )

            task_df = st.data_editor(
                pd.DataFrame(task_rows),
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key=f"crew_tasks_{selected_id}",
                column_config={
                    "task": st.column_config.TextColumn("Task"),
                    "responsible_person": st.column_config.TextColumn(
                        "Responsible person"
                    ),
                    "role": st.column_config.TextColumn(
                        "Role / designation"
                    ),
                    "start_time": st.column_config.TextColumn(
                        "Start time"
                    ),
                    "completion_time": st.column_config.TextColumn(
                        "Completion time"
                    ),
                    "status": st.column_config.SelectboxColumn(
                        "Task status",
                        options=[
                            "Pending",
                            "In progress",
                            "Completed",
                            "Blocked",
                        ],
                    ),
                    "outcome": st.column_config.TextColumn(
                        "Outcome / remarks"
                    ),
                },
            )

            st.markdown("#### 4. Aftermath and final outcome")

            containment_options = [
                "Unknown",
                "Not contained",
                "Partially contained",
                "Contained",
            ]

            old_containment = existing_crew.get(
                "containment_status", "Unknown"
            )
            containment_index = (
                containment_options.index(old_containment)
                if old_containment in containment_options else 0
            )

            containment_status = st.selectbox(
                "Containment status",
                containment_options,
                index=containment_index,
            )

            environmental_impact = st.text_area(
                "Observed environmental impact",
                value=existing_crew.get("environmental_impact", ""),
                placeholder=(
                    "Record observed impact. Distinguish observations "
                    "from unverified estimates."
                ),
            )

            injuries = st.text_area(
                "Injuries or personnel safety concerns",
                value=existing_crew.get("injuries", ""),
            )

            cleanup_recovery = st.text_area(
                "Cleanup and recovery measures",
                value=existing_crew.get("cleanup_recovery", ""),
            )

            remaining_hazards = st.text_area(
                "Remaining hazards",
                value=existing_crew.get("remaining_hazards", ""),
            )

            follow_up_tasks = st.text_area(
                "Follow-up actions required",
                value=existing_crew.get("follow_up_tasks", ""),
            )

            st.markdown("#### 5. Evidence and captain's review")

            evidence_text = st.text_area(
                "Evidence references",
                value="\n".join(
                    str(item)
                    for item in (selected.get("evidence") or [])
                ),
                placeholder=(
                    "Enter one item per line: sensor logs, photo references, "
                    "GPS records, crew statements or authority notifications."
                ),
            )

            captain_name = st.text_input(
                "Captain / authorized officer",
                value=existing_crew.get("captain_name", ""),
            )

            captain_notes = st.text_area(
                "Captain's notes and review comments",
                value=existing_crew.get("captain_notes", ""),
            )

            current_report_status = existing_crew.get(
                "report_status", "Draft"
            )

            report_status_options = [
                "Draft",
                "Submitted for review",
            ]

            # A previously reviewed record should not silently lose its
            # review state just because the form was reopened.
            if current_report_status == "Reviewed":
                st.info(
                    "This investigation is marked Reviewed. "
                    "Saving a new draft or submission will change its status."
                )

            report_status = st.selectbox(
                "Investigation status",
                report_status_options,
                index=(
                    1 if current_report_status == "Submitted for review"
                    else 0
                ),
            )

            save_draft = st.form_submit_button(
                "Save Draft",
                use_container_width=True,
            )

            submit_review = st.form_submit_button(
                "Submit for Review",
                type="primary",
                use_container_width=True,
            )

        if save_draft or submit_review:
            # Keep only task rows containing meaningful information.
            task_log = []
            for task in task_df.to_dict(orient="records"):
                cleaned_task = {
                    key: (
                        str(value).strip()
                        if value is not None and not pd.isna(value)
                        else ""
                    )
                    for key, value in task.items()
                }

                if any(
                    cleaned_task.get(key)
                    for key in [
                        "task",
                        "responsible_person",
                        "role",
                        "start_time",
                        "completion_time",
                        "outcome",
                    ]
                ):
                    task_log.append(cleaned_task)

            new_status = (
                "Submitted for review"
                if submit_review
                else "Draft"
            )

            # Preserve legacy crew fields while adding the new form fields.
            updated_crew = {
                **existing_crew,
                "discovery_method": discovery_method,
                "severity": severity,
                "source_identified": source_identified,
                "response_time": response_time.strip(),
                "initial_actions": initial_actions.strip(),
                "task_log": task_log,
                "containment_status": containment_status,
                "environmental_impact": environmental_impact.strip(),
                "injuries": injuries.strip(),
                "cleanup_recovery": cleanup_recovery.strip(),
                "remaining_hazards": remaining_hazards.strip(),
                "follow_up_tasks": follow_up_tasks.strip(),
                "captain_name": captain_name.strip(),
                "captain_notes": captain_notes.strip(),
                "report_status": new_status,
                "last_saved_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }

            # Save on the existing incident object. Do not construct a new
            # partial incident, because save_incident uses a full-record PUT.
            selected["crew_investigation"] = updated_crew
            updated_crew["evidence_references"] = [
                line.strip()
                for line in evidence_text.splitlines()
                if line.strip()
            ]

            report_metadata = selected.get("report") or {}
            report_metadata["status"] = new_status
            report_metadata["last_updated_at"] = datetime.now(
                timezone.utc
            ).isoformat()
            selected["report"] = report_metadata

            try:
                save_incident(selected)
                st.success(
                    "Investigation saved to Firebase."
                    if save_draft
                    else "Investigation submitted for review and saved to Firebase."
                )
                st.rerun()
            except Exception as exc:
                st.error(f"Could not save the investigation: {exc}")
    with st.expander("Historical Case Recommendations"):
        st.caption(
            "Historical-case retrieval using text matching. This is not a trained "
            "machine-learning model and does not confirm an oil spill."
        )
        if recommendation_error:
            st.warning("Recommendations could not be loaded. " + recommendation_error)
        elif recommendation_result and recommendation_result["recommendations"]:
            st.write(
                f"Method: {recommendation_result['method']} · "
                f"Matched cases: {recommendation_result['matched_case_count']}"
            )
            for index, item in enumerate(recommendation_result["recommendations"], start=1):
                st.markdown(f"**{index}. {item['incident_name']}**")
                st.write(
                    f"**Case ID:** {item['case_id']} | "
                    f"**Cause:** {item['cause_category']} | "
                    f"**Match score:** {item['match_score']}"
                )
                st.write("**Measures taken:**", item["measures_taken"] or "Not available")
                st.write("**Preventive measures:**", item["preventive_measures"] or "Not available")
                st.write("**Source:**", item["source"] or "Not available")
                st.caption(item["review_note"])
                st.divider()
            st.warning(recommendation_result["disclaimer"])
        elif recommendation_result:
            st.info(
                "No historical cases matched the available incident details. "
                "Add a cause category, oil type, or a more descriptive incident description."
            )

    with st.expander("Existing AI Analysis Data"):
        st.json(ml)

    with st.expander("Evidence and Report"):
        st.write("**Evidence**")
        st.json(selected.get("evidence", []))
        st.write("**Report metadata**")
        st.json(selected.get("report", {}))
    st.divider()
    st.subheader("Generate EcoSpill Incident Report")

    pdf_bytes = generate_incident_pdf(report_incident)

    st.download_button(
        label="Download Incident Report (PDF)",
        data=pdf_bytes,
        file_name=f"EcoSpill_Report_{selected.get('incident_id', 'incident')}.pdf",
        mime="application/pdf",
        key=f"download_report_{selected.get('incident_id', 'incident')}",
        use_container_width=True,
    )