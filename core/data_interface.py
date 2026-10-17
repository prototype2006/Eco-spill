
import requests

SENSOR_URL = "http://192.168.0.100:8000/latest"


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
