#include <Wire.h>
#include <BH1750.h>
#include <Arduino.h>
#include "DHT.h"
#include "WiFi.h"
#include "FirebaseESP32.h"
#include <ArduinoJson.h>

// Cấu hình cảm biến và Wi-Fi0
#define DHTPIN 4
#define DHTTYPE DHT11
#define WIFI_SSID "LAPTOP"
#define WIFI_PASSWORD "20012002"

// Cấu hình Firebase
#define FIREBASE_HOST "https://iot-vuonrau-default-rtdb.firebaseio.com/"
#define FIREBASE_AUTH "sVND1E8RPBOhjj52fHnMok25BKHABxU3iF1EiHgS"

// Khởi tạo các đối tượng
DHT dht(DHTPIN, DHTTYPE);
BH1750 lightMeter;
FirebaseData firebaseData;
FirebaseConfig config;
FirebaseAuth auth;

// Biến lưu trữ dữ liệu
float value_l, real_value_l;
float value_r, real_value_r, real_value_m;
float rain, light, moisture;

// Biến thời gian và đường dẫn Firebase
unsigned long t1 = 0;
String path = "/";

void setup() {
Serial.begin(9600);

// Khởi tạo I2C và cảm biến ánh sáng
Wire.begin();
lightMeter.begin();
dht.begin();

// Kết nối Wi-Fi
WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
Serial.print("Connecting to Wi-Fi");
while (WiFi.status() != WL_CONNECTED) {
	Serial.print(".");
	delay(300);
}
Serial.println();
Serial.print("Connected with IP: ");
Serial.println(WiFi.localIP());

// Cấu hình Firebase
config.host = FIREBASE_HOST;
config.signer.tokens.legacy_token = FIREBASE_AUTH;

// Kết nối Firebase
Firebase.begin(&config, &auth);
Firebase.reconnectWiFi(true);

	Serial.println("Firebase initialized successfully.");
}

void loop() {
	// Đọc dữ liệu cảm biến ánh sáng
	float lux = lightMeter.readLightLevel();
	Serial.print("Light: ");
	Serial.print(lux);
	Serial.println(" lx");

	// Đọc dữ liệu nhiệt độ và độ ẩm từ DHT11
	float h = dht.readHumidity();
	float t = dht.readTemperature();
	Serial.print("Humidity: ");
	Serial.print(h);
	Serial.println(" %");
	Serial.print("Temperature: ");
	Serial.print(t);
	Serial.println(" *C");

	// Đọc dữ liệu từ cảm biến khác
	real_value_m = analogRead(19);
	moisture = 100 - (real_value_m / 4095) * 100;

	real_value_l = analogRead(35);
	light = 100 - (real_value_l / 4095) * 100;

	real_value_r = analogRead(32);
	rain = 100 - (real_value_r / 4095) * 100;

	Serial.print("Rain sensor: ");
	Serial.println(rain);
	Serial.print("Light sensor: ");
	Serial.println(light);
	Serial.print("Moisture sensor: ");
	Serial.println(moisture);

	// Gửi dữ liệu lên Firebase mỗi 500ms
	if (millis() - t1 > 500) {
	float light1 = round(light * 100) / 100;
	float rain1 = round(rain * 100) / 100;
	float moisture1 = round(moisture * 100) / 100;

	Firebase.setFloat(firebaseData, path + "/light", light1);
	Firebase.setFloat(firebaseData, path + "/Humidity", h);
	Firebase.setFloat(firebaseData, path + "/rain", rain1);
	Firebase.setFloat(firebaseData, path + "/Temperature", t);
	Firebase.setFloat(firebaseData, path + "/illu", lux);
	Firebase.setFloat(firebaseData, path + "/moisture", moisture1);



	t1 = millis();
	}
}
