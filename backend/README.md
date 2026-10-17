# EcoSpillGuard — Backend

EcoSpillGuard is a prototype for detecting potential oil-tank level anomalies and recording incident information.

## Files

- `ecospill_logger.py` — Reads serial data from the ESP32 and saves readings to a CSV file.
- `ecospill_server.py` — Receives JSON readings through an HTTP POST endpoint and records incident information.
- `requirements.txt` — Lists the Python dependencies.

## Requirements

- Python 3
- ESP32 connected to the computer via USB for serial logging
- Arduino Serial Monitor closed while the Python logger uses the same COM port

## Setup

Open a terminal in the `backend` folder.

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run the serial logger

```bash
python ec