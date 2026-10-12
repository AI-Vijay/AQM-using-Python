
#include <WiFi.h>
#include <DHT.h>

// ==================================================
// 1. WI-FI CREDENTIALS
// ==================================================

const char* ssid = "Darkstar";
const char* password = "YOUR_HOTSPOT_PASSWORD";

// ==================================================
// 2. SENSOR CONFIGURATION
// ==================================================

#define DHT_PIN 4
#define DHT_TYPE DHT11
#define MQ135_PIN 34

DHT dht(DHT_PIN, DHT_TYPE);

// ==================================================
// 3. REST API SERVER
// ==================================================

WiFiServer server(80);

// ==================================================
// 4. SENSOR DATA
// ==================================================

float temperature = 0.0;
float humidity = 0.0;

int rawGas = 0;

// This is an estimated project-specific index,
// NOT an official AQI measurement.
int estimatedAQI = 0;

String airQuality = "Starting";
bool dhtValid = false;

// Set this from your observed baseline readings.
int cleanAirBaseline = 3350;

// ==================================================
// 5. AQI-STYLE ESTIMATE
// ==================================================

int calculateAQI(int gasValue) {
  int difference = gasValue - cleanAirBaseline;

  if (difference <= 0) {
    return 25;
  }

  int value = map(difference, 0, 500, 25, 500);
  return constrain(value, 25, 500);
}

String getAirQuality(int value) {
  if (value <= 50)  return "Good";
  if (value <= 100) return "Moderate";
  if (value <= 150) return "Sensitive";
  if (value <= 200) return "Unhealthy";
  if (value <= 300) return "Very Unhealthy";
  return "Hazardous";
}

// ==================================================
// 6. READ SENSORS
// ==================================================

void readSensors() {
  float newHumidity = dht.readHumidity();
  float newTemperature = dht.readTemperature();

  if (!isnan(newHumidity) && !isnan(newTemperature)) {
    humidity = newHumidity;
    temperature = newTemperature;
    dhtValid = true;
  } else {
    dhtValid = false;
    Serial.println("Warning: DHT11 reading failed");
  }

  // Average several ADC samples to reduce random noise.
  long total = 0;

  for (int i = 0; i < 10; i++) {
    total += analogRead(MQ135_PIN);
    delay(5);
  }

  rawGas = total / 10;

  estimatedAQI = calculateAQI(rawGas);
  airQuality = getAirQuality(estimatedAQI);

  Serial.println("\n---------- SENSOR DATA ----------");

  if (dhtValid) {
    Serial.printf("Temperature: %.1f C\n", temperature);
    Serial.printf("Humidity: %.1f %%\n", humidity);
  } else {
    Serial.println("Temperature/Humidity: unavailable");
  }

  Serial.printf("Raw MQ-135: %d\n", rawGas);
  Serial.printf("Estimated index: %d\n", estimatedAQI);
  Serial.printf("Category: %s\n", airQuality.c_str());

  Serial.println("---------------------------------");
}

// ==================================================
// 7. SEND JSON RESPONSE
// ==================================================

void sendJSON(WiFiClient &client) {
  String json = "{";

  json += "\"temperature\":";
  json += dhtValid ? String(temperature, 1) : "null";

  json += ",\"humidity\":";
  json += dhtValid ? String(humidity, 1) : "null";

  json += ",\"raw_gas\":";
  json += String(rawGas);

  json += ",\"aqi\":";
  json += String(estimatedAQI);

  json += ",\"air_quality\":\"";
  json += airQuality;
  json += "\"";

  json += ",\"aqi_type\":\"estimated_mq135_index\"";
  json += "}";

  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: application/json");
  client.println("Cache-Control: no-store");
  client.println("Access-Control-Allow-Origin: *");
  client.println("Connection: close");
  client.println();
  client.println(json);
}

// ==================================================
// 8. HANDLE HTTP REQUEST
// ==================================================

void handleRequests() {
  WiFiClient client = server.available();

  if (!client) {
    return;
  }

  client.setTimeout(1000);

  unsigned long start = millis();

  while (client.connected() &&
         !client.available() &&
         millis() - start < 1500) {
    delay(1);
  }

  if (!client.available()) {
    client.stop();
    return;
  }

  String request = client.readStringUntil('\n');
  request.trim();

  Serial.print("HTTP request: ");
  Serial.println(request);

  if (request.startsWith("GET /api/data ")) {
    sendJSON(client);
  } else if (request.startsWith("GET / ")) {
    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: text/plain");
    client.println("Connection: close");
    client.println();
    client.println("ESP32 Air Quality Monitoring REST API");
    client.println("Endpoint: /api/data");
  } else {
    client.println("HTTP/1.1 404 Not Found");
    client.println("Content-Type: application/json");
    client.println("Connection: close");
    client.println();
    client.println("{\"error\":\"Endpoint not found\"}");
  }

  client.stop();
}

// ==================================================
// 9. SETUP
// ==================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\nESP32 Air Quality Monitor");

  dht.begin();
  analogReadResolution(12);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  Serial.print("Connecting to hotspot");

  int attempts = 0;

  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("Wi-Fi connected!");
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());

    server.begin();

    Serial.println("REST API started");
    Serial.print("JSON URL: http://");
    Serial.print(WiFi.localIP());
    Serial.println("/api/data");
  } else {
    Serial.println("Wi-Fi connection failed.");
    Serial.println("Check hotspot name, password and 2.4 GHz support.");
  }

  readSensors();
}

// ==================================================
// 10. MAIN LOOP
// ==================================================

void loop() {
  handleRequests();

  // Reconnect if the hotspot temporarily disconnects.
  static unsigned long lastReconnectAttempt = 0;

  if (WiFi.status() != WL_CONNECTED &&
      millis() - lastReconnectAttempt >= 5000) {
    lastReconnectAttempt = millis();
    Serial.println("Wi-Fi disconnected; reconnecting...");
    WiFi.reconnect();
  }

  // Refresh sensor values every 2 seconds.
  static unsigned long lastSensorRead = 0;

  if (millis() - lastSensorRead >= 2000) {
    lastSensorRead = millis();
    readSensors();
  }

  delay(1);
}
