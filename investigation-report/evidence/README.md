# Camera evidence files for the investigation PDF

Place an actual ESP32-CAM image in this folder before generating the investigation PDF.

Supported file types:
- JPEG: `.jpg` or `.jpeg`
- PNG: `.png`
- BMP: `.bmp`

The report generator embeds the most recently modified supported image it can read. The file modification time is used only to select an image; it is **not** described as the image capture time.

## Optional image metadata

For an image named `capture_001.jpg`, an optional sidecar file can be named `capture_001.json`.

Example structure (replace values only with information actually recorded):

```json
{
  "camera_id": "ESP32-CAM-01",
  "captured_at": null,
  "incident_id": null,
  "latitude": null,
  "longitude": null,
  "classification": null,
  "confidence": null
}
```

Leave unknown fields as `null`. Do not enter estimated coordinates, timestamps, image classifications, or confidence values.

## Workflow

1. Obtain an actual image file from the ESP32-CAM or its SD card.
2. Copy the image into this folder.
3. Add a matching JSON sidecar only when reliable metadata is available.
4. Run `ecospillguard_live_report.py`.
5. Check the PDF to confirm the correct image and metadata were embedded.

The image file itself is kept out of Git by this folder's `.gitignore`. Do not commit private or sensitive incident imagery to the public repository.

If this folder contains no readable image, the report explicitly displays that no camera image is attached.
