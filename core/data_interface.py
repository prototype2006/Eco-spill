
import requests

SENSOR_URL = "http://172.26.105.66:8000/latest"

import os
import requests

SENSOR_BASE_URL = os.getenv(
    "ECOSPILL_SENSOR_BASE_URL",
    "http://172.26.105.66:8000",
).rstrip("/")


def get_sensor_incidents():
    """Fetch historical incidents from Blossom's hardware server."""
    try:
        response = requests.get(
            f"{SENSOR_BASE_URL}/incidents",
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()

        if not isinstance(payload, dict):
            raise ValueError("Unexpected incident-history response.")

        incidents = payload.get("incidents", [])
        if not isinstance(incidents, list):
            raise ValueError("Incident history must be a list.")

        return {
            "connected": payload.get("status") == "ok",
            "incidents": [
                item for item in incidents
                if isinstance(item, dict) and item.get("incident_id")
            ],
            "error": None,
        }

    except (requests.RequestException, ValueError) as exc:
        return {
            "connected": False,
            "incidents": [],
            "error": str(exc),
        }


def get_latest_reading():
    """Fetch the latest sensor reading from Blossom's server."""

    try:
        response = requests.get(
            SENSOR_URL,
            timeout=3,
        )
        response.raise_for_status()

        payload = response.json()

        if not isinstance(payload, dict):
            return {
                "connected": True,
                "reading": None,
                "error": "Unexpected response format.",
            }

        reading = payload.get("reading")

        if not isinstance(reading, dict):
            return {
                "connected": True,
                "reading": None,
                "error": "No valid reading object was returned.",
            }

        return {
            "connected": payload.get("status") == "ok",
            "reading": reading,
            "error": None,
        }

    except requests.RequestException:
        return {
            "connected": False,
            "reading": None,
            "error": (
                "Sensor server unavailable. Check that Blossom's "
                "server is running and accessible on the local network."
            ),
        }

    except ValueError:
        return {
            "connected": False,
            "reading": None,
            "error": "The sensor server returned invalid JSON.",
        }
