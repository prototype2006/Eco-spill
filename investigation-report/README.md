# EcoSpillGuard — Investigation Report

## Overview
This folder contains the Python report generator for the EcoSpillGuard oil-spill monitoring prototype.

The report retrieves the latest sensor record from the local backend and generates a PDF investigation report.

## Current Data Flow
Ultrasonic Sensor -> ESP32 -> Local Backend -> Python Report Generator -> PDF

## Files
- ecospillguard_live_report.py: Generates the investigation report PDF.
- requirements.txt: Python package dependencies.

## Prerequisites
- Python 3
- EcoSpillGuard backend running locally at http://127.0.0.1:8000
- Backend endpoint /latest returning the latest reading as JSON

## Setup
From this folder, install dependencies:

    python -m pip install -r requirements.txt

## Generate the Report
Start the backend first. Then run:

    python ecospillguard_live_report.py

The generated PDF is saved in the output path configured in the Python script.

## Current Hardware Fields
- Ultrasonic distance in centimetres
- Backend receipt timestamp
- Sensor/RTC timestamp
- Status and LED state
- GPS status, latitude and longitude when available
- Water percentage only when supplied by the backend

Unavailable measurements must remain unavailable; they must not be invented.

## Known Limitations
- RTC timestamp requires hardware verification and correction.
- GPS coordinates are unavailable until a valid GPS fix is received.
- Ultrasonic distance alone does not confirm an oil spill.
- Camera evidence and image-model confidence are not currently provided by this report endpoint.
- Firebase incident details and AI recommendations are planned for later integration.

## Planned Integration
The frontend may later supply additional incident details from Firebase. Historical spill-case retrieval and evidence-grounded recommendations will be integrated in a later phase.

## Safety and Review
This is a prototype report. All incident conclusions and proposed actions require verification by the Master/Chief Engineer. It is not a substitute for approved vessel emergency procedures.
