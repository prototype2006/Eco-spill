# EcoSpill 🌊
### AI-Powered Oil Spill Monitoring and Detection System for Ships

EcoSpill is an AI-assisted oil spill monitoring system designed to detect potential oil leakage, capture visual evidence, record incident timestamps and geographical coordinates, and support automated incident report generation.

The project combines embedded hardware, sensor-based monitoring, camera-based image acquisition, artificial intelligence, and software-based reporting to help improve the monitoring and documentation of potential oil spill incidents around ships.

## 📌 Table of Contents

- [Overview](#-overview)
- [Problem Statement](#-problem-statement)
- [Objectives](#-objectives)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Hardware Components](#-hardware-components)
- [Software and Technologies](#-software-and-technologies)
- [System Workflow](#-system-workflow)
- [AI and Image Analysis](#-ai-and-image-analysis)
- [Automated Incident Reporting](#-automated-incident-reporting)
- [Installation and Setup](#-installation-and-setup)
- [Project Structure](#-project-structure)
- [Testing and Validation](#-testing-and-validation)
- [Limitations](#-limitations)
- [Future Enhancements](#-future-enhancements)
- [Research and References](#-research-and-references)
- [Contributors](#-contributors)
- [License](#-license)

## 🌍 Overview

Oil spills in marine environments can cause severe ecological damage, affect marine biodiversity, and create significant operational and regulatory challenges for the shipping industry.

Early detection and reliable incident documentation are essential for effective response and investigation. However, relying exclusively on manual observation can delay detection and make it difficult to collect consistent evidence.

EcoSpill proposes an integrated monitoring approach using:

- **Embedded sensing:** Monitors changes in a designated onboard monitoring area.
- **Camera-based observation:** Captures images of the surrounding water surface for visual inspection.
- **Location and time recording:** Associates incident evidence with geographical coordinates and timestamps.
- **AI-assisted analysis:** Supports the classification and analysis of captured images for potential oil spill indicators.
- **Automated reporting:** Organizes incident information and supporting evidence into a structured report.

The system is being developed as an academic prototype to demonstrate how embedded systems and AI can support marine environmental monitoring.

## 🎯 Problem Statement

Conventional oil spill monitoring may depend on manual inspection, separate sensing devices, and incident reports assembled from multiple sources. These approaches can make timely detection, evidence collection, and incident documentation more difficult.

EcoSpill aims to integrate sensing, visual evidence collection, incident metadata, and AI-assisted reporting into a unified prototype.

The system is intended to support human operators rather than replace professional environmental assessment or established maritime safety procedures.

## 🎯 Objectives

1. Design an embedded monitoring system using an ESP32-based controller.
2. Detect relevant changes in the monitored area using an appropriate sensor.
3. Capture images of the water surface using an ESP32-CAM.
4. Record incident timestamps using a real-time clock module.
5. Obtain geographical coordinates using a GPS module.
6. Explore AI-based image analysis for identifying potential oil spill evidence.
7. Develop a software interface for reviewing incident data and supporting report generation.
8. Evaluate the prototype under controlled testing conditions.

## ✨ Key Features

| Feature | Description |
|---|---|
| Sensor monitoring | Detects configured changes in the monitored area. |
| Image acquisition | Captures visual evidence using a camera module. |
| Timestamp recording | Associates evidence with a date and time. |
| GPS integration | Records available geographical coordinates. |
| AI-assisted image analysis | Analyzes images for potential oil spill indicators when the model is integrated. |
| Incident evidence management | Organizes images and associated metadata. |
| Report generation | Supports structured incident report creation using available evidence. |
| Web-based interface | Provides a potential interface for monitoring, reviewing evidence, and generating reports. |

*Feature status depends on the current implementation. Proposed or partially integrated components must be validated before being described as operational.*

## 🏗️ System Architecture

EcoSpill is organized into five logical layers.

### 1. Sensing Layer

The sensing layer monitors the designated area using the selected sensor. Changes that meet configured conditions can trigger further investigation or evidence collection.

### 2. Embedded Processing Layer

The ESP32 acts as the primary microcontroller for sensor interfacing, event handling, and communication with supported peripherals.

The ESP32-CAM provides image acquisition capabilities for visual monitoring.

### 3. Location and Time Layer

- **GPS module (NEO-6M):** Supplies geographical coordinates when satellite reception is available.
- **RTC module (DS3231):** Provides a local time reference for recording events.

The system must define how timestamps and coordinates are associated with each captured image.

### 4. AI Analysis Layer

Captured images can be processed by an image classification or computer vision model to identify visual patterns associated with possible oil contamination.

Model performance depends on the quality, diversity, and relevance of the training and evaluation data.

### 5. Application and Reporting Layer

The software layer can organize incident records, display supporting images and metadata, present AI analysis results, and generate structured reports for human review.

### Architecture Flow

```text
       Marine Environment
               |
       +-------+--------+
       |                |
  Sensor Module     ESP32-CAM
       |                |
       +-------+--------+
               |
        ESP32 Controller
               |
       +-------+--------+
       |                |
   GPS Module         RTC
       |                |
       +-------+--------+
               |
       Incident Evidence
       and Metadata
               |
       AI Image Analysis
               |
       Software Interface
               |
       Incident Report
```

This diagram represents the intended system flow. Actual data paths depend on the implemented communication interfaces, firmware, and software integration.

## 🔩 Hardware Components

The following components are part of the proposed prototype design.

| Component | Purpose |
|---|---|
| ESP32 DevKit V1 | Main microcontroller for sensor interfacing and system control. |
| ESP32-CAM AI Thinker | Captures images for visual monitoring and AI analysis. |
| TCRT5000 / selected optical sensor | Experimental sensing of reflectance changes in the monitored area. |
| NEO-6M GPS module | Obtains geographical coordinates. |
| DS3231 RTC module | Maintains date and time information. |
| MicroSD card and compatible interface, if required | Stores captured images, logs, or incident records locally. |
| LEDs and suitable resistors | Provide basic status indications. |
| Breadboard, jumper wires, and power supply | Support prototype assembly and testing. |

**Hardware note:** The TCRT5000 is a reflective infrared sensor, not a dedicated oil spill detector. Its suitability depends on the geometry, surface conditions, lighting, and experimental setup. Its output should not be treated as proof of an oil spill without validation.

The ESP32 and ESP32-CAM also have different pin assignments, power requirements, and resource constraints. Their interconnections must be verified against the selected board documentation before assembly.

## 💻 Software and Technologies

The following technologies describe the intended software stack. Only the technologies actually used in the repository should be treated as implemented dependencies.

| Technology | Intended role |
|---|---|
| C/C++ and Arduino framework | Embedded firmware development. |
| Python | AI processing, data handling, and report generation. |
| Streamlit | Potential web interface for the prototype. |
| Computer vision libraries | Image preprocessing and analysis. |
| Machine learning / deep learning framework | Training or running the image analysis model. |
| Groq API | Optional integration for generating report narratives from structured incident information. |
| Git and GitHub | Version control and collaborative development. |

Groq-based report generation, where implemented, should be treated as a reporting aid rather than the mechanism responsible for validating sensor readings or proving that a spill occurred.

## ⚙️ System Workflow

The intended end-to-end workflow is as follows:

1. **Monitor:** The embedded controller reads the configured sensor input.
2. **Detect a trigger:** The firmware identifies a sensor change that meets predefined conditions.
3. **Capture evidence:** The camera captures an image of the relevant area.
4. **Record metadata:** The system associates the image with the available timestamp and GPS coordinates.
5. **Process the evidence:** The software prepares the captured image for analysis.
6. **Analyze the image:** An integrated AI model evaluates the image for possible oil spill indicators.
7. **Review the incident:** The application presents the image, metadata, and analysis results.
8. **Generate a report:** The application compiles available information into a structured incident report.
9. **Store the record:** The evidence and associated metadata are retained according to the configured storage mechanism.

These steps describe the target workflow. In particular, sensor triggering, camera synchronization, AI inference, and report generation must be verified through integration tests.

## 🤖 AI and Image Analysis

The AI component is intended to assist with identifying visual patterns that may indicate oil contamination on a water surface.

A typical image analysis pipeline consists of:

1. Image collection.
2. Dataset inspection and labeling.
3. Image preprocessing and normalization.
4. Model training or integration of a pretrained model.
5. Validation using images not used during training.
6. Inference on captured images.
7. Presentation of the prediction and relevant confidence information.

### Model Evaluation

Useful evaluation metrics include:

- **Precision:** The proportion of predicted spill-positive cases that are actually positive.
- **Recall:** The proportion of actual spill-positive cases correctly identified.
- **F1-score:** The harmonic mean of precision and recall.
- **Confusion matrix:** The distribution of correct and incorrect predictions across classes.

For a safety-relevant monitoring application, false negatives and false positives both matter. Performance should be assessed under different lighting conditions, water-surface appearances, camera angles, and environmental conditions.

A model prediction is not definitive evidence of contamination. Human review and independent verification remain important.

## 📄 Automated Incident Reporting

EcoSpill aims to organize incident evidence into a structured report that may contain:

- Incident identification number.
- Date and time of the observation.
- GPS coordinates, if available.
- Captured image or supporting evidence.
- Sensor readings and trigger information.
- AI-generated classification and confidence, if available.
- Incident description and observations.
- Recommended verification or follow-up actions.
- Report generation timestamp.

An optional language-model integration using the Groq API may help convert validated incident data into readable report text.

The reporting layer should distinguish between measured values, model predictions, and generated descriptions. Missing coordinates, unavailable images, and uncertain classifications must not be silently replaced with fabricated information.

## 🚀 Installation and Setup

### Prerequisites

- Python 3.10 or a version supported by the project's dependencies.
- Git.
- A compatible code editor.
- Arduino IDE or another supported ESP32 development environment.
- The required hardware components for physical testing.
- API credentials only for external services that the implementation actually uses.

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
```

Replace the placeholder repository URL with the actual GitHub repository address.

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

If the repository contains a `requirements.txt` file:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The dependency file should contain only packages required by the actual implementation.

### 4. Configure Environment Variables

If the application uses the Groq API or other external services, configure the required credentials through environment variables or Streamlit secrets.

Example environment variable:

```text
GROQ_API_KEY=your_api_key_here
```

Do not commit real API keys, passwords, or other secrets to GitHub.

### 5. Run the Application

For a Streamlit application with an entry point named `app.py`:

```bash
streamlit run app.py
```

Replace `app.py` with the actual application entry point if the repository uses a different filename.

### 6. Upload the Firmware

1. Open the ESP32 firmware project in the supported development environment.
2. Select the correct ESP32 board and serial port.
3. Configure the sensor and peripheral pin assignments.
4. Verify the power supply and wiring.
5. Compile and upload the firmware.
6. Test the sensor, camera, GPS, and RTC individually before testing the complete system.

The commands above are a setup template. A successful installation depends on the repository containing the referenced application files and dependency definitions.

## 📁 Project Structure

A recommended repository organization is:

```text
EcoSpill/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── firmware/
│   ├── esp32_controller/
│   └── esp32_cam/
├── ai/
│   ├── preprocessing.py
│   ├── inference.py
│   └── model/
├── data/
│   ├── sample_images/
│   └── README.md
├── reports/
├── src/
│   ├── incident_manager.py
│   ├── metadata_handler.py
│   └── report_generator.py
├── tests/
└── docs/
    ├── architecture.md
    └── hardware_setup.md
```

This is a suggested structure, not a claim about the files currently present in the repository. Keep only the directories and files that are relevant to the actual implementation.

## 🧪 Testing and Validation

The prototype should be evaluated in stages.

| Test | Purpose |
|---|---|
| Sensor calibration | Determine whether the selected sensor reliably detects the intended changes. |
| Camera validation | Verify image quality, capture timing, and storage. |
| GPS validation | Check coordinate availability and accuracy under suitable reception conditions. |
| RTC validation | Verify timestamp accuracy and behavior after power interruptions. |
| AI evaluation | Measure classification performance on independent test images. |
| Integration testing | Verify that sensor events, images, metadata, and incident records are associated correctly. |
| Report validation | Check the completeness and consistency of generated reports. |
| Environmental testing | Evaluate performance under different lighting and surface conditions. |

Testing should include normal conditions, negative cases, sensor noise, unavailable GPS data, failed image capture, and other realistic edge cases.

Quantitative performance claims should be added only after the relevant experiments have been conducted and documented.

## ⚠️ Limitations

- Reflectance changes alone cannot reliably establish that oil contamination has occurred.
- Camera-based detection can be affected by lighting, reflections, waves, weather, and image quality.
- GPS performance depends on satellite reception and environmental conditions.
- An RTC requires appropriate configuration and may need initial time synchronization.
- Embedded hardware may have limited processing, memory, and storage resources.
- AI model performance depends on representative training data and rigorous evaluation.
- External API integrations require network connectivity and may have usage limits.
- Generated reports require verification before being used for operational, legal, or regulatory decisions.

EcoSpill is an academic prototype and should not be considered a certified maritime safety system or a replacement for established spill detection and response procedures.

## 🔮 Future Enhancements

Potential future improvements include:

- Training and validating a more robust oil spill image classification model.
- Evaluating object detection or image segmentation for localizing suspected contamination.
- Improving sensor calibration and investigating more suitable oil detection technologies.
- Adding reliable wireless communication between embedded hardware and the application.
- Implementing a persistent incident database and searchable incident history.
- Adding an interactive map for displaying recorded incident coordinates.
- Supporting downloadable PDF incident reports.
- Adding authentication, access control, and secure evidence storage.
- Implementing offline buffering and reliable data synchronization.
- Evaluating the prototype under controlled and real-world marine conditions.
- Integrating alerts and event notifications after validating detection reliability.

## 📚 Research and References


Relevant reference categories include:

- ESP32 and ESP32-CAM technical documentation.
- DS3231 RTC and NEO-6M GPS documentation.
- Optical sensing and reflectance-based measurement studies.
- Research on computer vision for marine oil spill detection.
- Machine learning evaluation methods and dataset documentation.
- Maritime oil pollution monitoring and incident response guidance.
- Documentation for the software frameworks and external APIs used.

[1] Espressif Systems, “ESP32 Series Datasheet and Technical Documentation.” [Online]. Available: https://www.espressif.com/en/support/documents/technical-documents

[2] Espressif Systems, “ESP32 Camera Driver.” GitHub repository. [Online]. Available: https://github.com/espressif/esp32-camera

[3] Analog Devices, “DS3231: Extremely Accurate I²C-Integrated RTC/TCXO/Crystal.” [Online]. Available: https://www.analog.com/en/products/ds3231.html

[4] u-blox, “NEO-6 Series: Versatile u-blox 6 GPS Modules.” [Online]. Available: https://www.u-blox.com/en/product/neo-6-series

[5] Vishay Semiconductors, “TCRT5000, TCRT5000L: Reflective Optical Sensor with Transistor Output.” [Online]. Available: https://www.vishay.com/docs/83760/tcrt5000.pdf

[6] “A Two-Stage Oil Spill Detection Method Based on an Improved Superpixel Module and DeepLab V3+ Using SAR Images,” IEEE Geoscience and Remote Sensing Letters, vol. 22, article 4000505, Nov. 2024. doi: 10.1109/LGRS.2024.3508020.

[7] “A Survey on Oil Spill Detection using SAR images in Machine Learning,” in Proc. Parul International Conference on Engineering and Technology (PICET), 2024. doi: 10.1109/PICET60765.2024.10716148.

[8] Espressif Systems, “Arduino-ESP32 Documentation.” [Online]. Available: https://docs.espressif.com/projects/arduino-esp32/en/latest/

[9] Groq, “Groq API Reference.” [Online]. Available: https://console.groq.com/docs/api-reference

[10] Streamlit, “Streamlit Documentation.” [Online]. Available: https://docs.streamlit.io/

## 👥 Contributors

EcoSpill is developed as an academic project involving embedded systems, hardware design, software development, AI integration, and technical documentation.

Add the project contributors and their verified GitHub profiles here.

| Contributor | Responsibility |
|---|---|
| Crystal D'souza | System architecture, hardware design, component selection, and integration planning. |
| Blossom Fernandes | Machine learning development, dataset preparation, AI image analysis, hardware development, and component integration. |

## 📜 License

---

**EcoSpill: Integrating embedded sensing, AI-assisted visual analysis, and structured incident documentation for marine environmental monitoring.**
