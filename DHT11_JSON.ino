#include <DHT.h>
#include <ArduinoJson.h>

#define DHTPIN 2       // DHT11 data pin
#define DHTTYPE DHT11  // DHT11 sensor type

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  dht.begin();
  delay(2000);  // Allow the sensor to stabilize
}

void loop() {
  // Read temperature and humidity
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  // Check if any reads failed
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println(F("{\"error\": \"Failed to read from DHT sensor!\"}"));
    return;
  }

  // Create JSON document
  StaticJsonDocument<200> doc;
  
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;
  doc["timestamp"] = millis();

  // Serialize JSON to Serial
  serializeJson(doc, Serial);
  Serial.println();

  // Wait a bit before next reading
  delay(2000);
}
