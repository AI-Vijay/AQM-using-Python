#include "arduino_secrets.h"
#include "thingProperties.h"
#include "DHT.h"

// DHT11 Sensor
#define DHTPIN 4
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

// MQ-135 Sensor
#define MQ135_PIN 34

// Sensor reading interval
unsigned long previousMillis = 0;
const unsigned long interval = 2000;

void setup() {
  Serial.begin(9600);
  delay(1500);

  // Initialize DHT11
  dht.begin();

  // Initialize Arduino IoT Cloud properties
  initProperties();

  // Connect to Arduino IoT Cloud
  ArduinoCloud.begin(ArduinoIoTPreferredConnection);

  // Enable Cloud debugging
  setDebugMessageLevel(2);
  ArduinoCloud.printDebugInfo();

  // ESP32 ADC resolution: 12-bit (0-4095)
  analogReadResolution(12);

  Serial.println("ESP32 Air Quality Monitoring Started");
}

void loop() {
  // Keep the Cloud connection updated
  ArduinoCloud.update();

  unsigned long currentMillis = millis();

  // Read sensors every 2 seconds
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;

    // Read DHT11 values
    float hm = dht.readHumidity();
    float temp = dht.readTemperature();

    // Check if DHT11 readings are valid
    if (!isnan(hm) && !isnan(temp)) {

      // Update Arduino IoT Cloud variables
      Humidity = hm;
      temperature = temp;

      Serial.print("Humidity: ");
      Serial.print(hm);
      Serial.println(" %");

      Serial.print("Temperature: ");
      Serial.print(temp);
      Serial.println(" °C");

    } else {
      Serial.println("Error: Failed to read DHT11 sensor!");
    }

    // Read MQ-135 analog value
    int airQualityValue = analogRead(MQ135_PIN);

    // Update Arduino IoT Cloud variable
    air_quality = airQualityValue;

    Serial.print("MQ-135 Raw Value: ");
    Serial.println(airQualityValue);

    // Update message variable
    message = "Temperature = " + String(temperature) +
              " C, Humidity = " + String(Humidity) +
              " %, Air Quality = " + String(air_quality);

    Serial.println("-------------------------");
  }
}

/*
  Arduino IoT Cloud callbacks
  Keep these if they are generated in thingProperties.h
*/

void onMessageChange() {
  // Add code here if needed
}

void onHumidityChange() {
  // Add code here if needed
}

void onTemperatureChange() {
  // Add code here if needed
}

void onAirQualityChange() {
  // Add code here if needed
}