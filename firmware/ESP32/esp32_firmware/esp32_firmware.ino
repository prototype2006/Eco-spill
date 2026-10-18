
#include <Wire.h>
#include <RTClib.h>
#include <TinyGPSPlus.h>

// -------- HARDWARE OBJECTS --------
RTC_DS3231 rtc;
TinyGPSPlus gps;

// -------- PIN CONNECTIONS --------
#define TRIG_PIN 5
#define ECHO_PIN 18
#define LED_PIN 23

// GPS TX -> ESP32 GPIO 16
// GPS RX -> ESP32 GPIO 17
#define GPS_RX_PIN 16
#define GPS_TX_PIN 17

// -------- SETTINGS --------
const float SOUND_SPEED = 0.0343;
const unsigned long ECHO_TIMEOUT_US = 30000;
const float ALERT_DISTANCE_CM = 22.0;

// IMPORTANT:
// Set true for the FIRST upload to correct the RTC.
// After a successful upload, change to false and upload again.
const bool SET_RTC_FROM_COMPILE_TIME = true;

unsigned long lastEchoDuration = 0;
unsigned long lastGpsByteMillis = 0;

String invalidReason = "VALID";
bool rtcAvailable = false;

// -------- ULTRASONIC READING --------
float readDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  lastEchoDuration =
      pulseIn(ECHO_PIN, HIGH, ECHO_TIMEOUT_US);

  // No echo received before timeout.
  if (lastEchoDuration == 0) {
    invalidReason = "NO_ECHO_TIMEOUT";
    return -1.0;
  }

  float distance =
      lastEchoDuration * SOUND_SPEED / 2.0;

  // Keep original validation limits.
  if (distance <= 20.0) {
    invalidReason = "TOO_CLOSE";
    return -1.0;
  }

  if (distance > 400.0) {
    invalidReason = "TOO_FAR";
    return -1.0;
  }

  invalidReason = "VALID";
  return distance;
}

// -------- RTC TIMESTAMP --------
String getTimestamp() {
  if (!rtcAvailable) {
    return "RTC_ERROR";
  }

  DateTime now = rtc.now();
  char timestamp[20];

  snprintf(
    timestamp, sizeof(timestamp),
    "%04d-%02d-%02d %02d:%02d:%02d",
    now.year(), now.month(), now.day(),
    now.hour(), now.minute(), now.second()
  );

  return String(timestamp);
}

// -------- GPS READING --------
void readGPS() {
  while (Serial2.available() > 0) {
    char incoming = Serial2.read();

    gps.encode(incoming);
    lastGpsByteMillis = millis();
  }
}

String getGPSStatus() {
  // No GPS bytes received recently.
  if (lastGpsByteMillis == 0 ||
      millis() - lastGpsByteMillis > 3000) {
    return "NO_DATA";
  }

  // Data is arriving, but no valid position yet.
  if (!gps.location.isValid() ||
      gps.location.age() >= 10000) {
    return "NO_FIX";
  }

  return "FIX";
}

// -------- CSV OUTPUT --------
void printLog(float distance) {
  bool validDistance = distance >= 0;

  String status;
  String ledStatus;

  // Invalid readings must not trigger the LED.
  if (!validDistance) {
    status = "INVALID";
    digitalWrite(LED_PIN, LOW);
    ledStatus = "OFF";
  }
  else if (distance > ALERT_DISTANCE_CM) {
    status = "ALERT";
    digitalWrite(LED_PIN, HIGH);
    ledStatus = "ON";
  }
  else {
    status = "NORMAL";
    digitalWrite(LED_PIN, LOW);
    ledStatus = "OFF";
  }

  String latitude = "null";
  String longitude = "null";

  if (gps.location.isValid() &&
      gps.location.age() < 10000) {
    latitude = String(gps.location.lat(), 6);
    longitude = String(gps.location.lng(), 6);
  }

  // Keep exactly seven CSV columns.
  Serial.print(getTimestamp());
  Serial.print(",");

  if (validDistance) {
    Serial.print(distance, 2);
  } else {
    Serial.print("INVALID");
  }

  Serial.print(",");
  Serial.print(status);
  Serial.print(",");
  Serial.print(ledStatus);
  Serial.print(",");
  Serial.print(latitude);
  Serial.print(",");
  Serial.print(longitude);
  Serial.print(",");
  Serial.println(getGPSStatus());

  // Diagnostic output for invalid distance readings.
  if (!validDistance) {
    Serial.print("DEBUG,");
    Serial.print(invalidReason);
    Serial.print(",echo_us=");
    Serial.println(lastEchoDuration);
  }
}

// -------- SETUP --------
void setup() {
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);

  digitalWrite(TRIG_PIN, LOW);
  digitalWrite(LED_PIN, LOW);

  // RTC I2C: SDA = GPIO 21, SCL = GPIO 22.
  Wire.begin(21, 22);
  rtcAvailable = rtc.begin();

  if (rtcAvailable && SET_RTC_FROM_COMPILE_TIME) {
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }

  // GPS UART: RX = GPIO 16, TX = GPIO 17.
  Serial2.begin(
    9600, SERIAL_8N1,
    GPS_RX_PIN, GPS_TX_PIN
  );

  Serial.println("EcoSpillGuard started");
  Serial.println(
    "Time,Distance_cm,Status,LED,Latitude,Longitude,GPS"
  );

  if (!rtcAvailable) {
    Serial.println("WARNING: RTC not detected");
  }
}

// -------- MAIN LOOP --------
void loop() {
  // Process GPS messages.
  readGPS();

  // Read tank-level distance.
  float distance = readDistance();

  // Log timestamp, distance, alert and GPS status.
  printLog(distance);

  delay(1000);
}
