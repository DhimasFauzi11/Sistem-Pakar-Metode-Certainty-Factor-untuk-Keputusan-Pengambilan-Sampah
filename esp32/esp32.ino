/*
 * =============================================================
 * ESP32 IOT MONITORING - PEMILAH SAMPAH (FINAL VERSION)
 * Fitur: 
 * 1. Realtime Dashboard
 * 2. Dataset Logging
 * 3. Alarm Suhu Panas (DHT22 > 45 Derajat)
 * =============================================================
 */

#include <WiFi.h>
#include <Firebase_ESP_Client.h>
#include "DHT.h"

// Masukkan Token Helper
#include "addons/TokenHelper.h"
#include "addons/RTDBHelper.h"

// 1. KONFIGURASI WIFI (WAJIB DIISI)
const char* ssid = "AAA";          // nama WiFi
const char* password = "12345678";   // password WiFi

// 2. KONFIGURASI FIREBASE
#define DATABASE_URL "https://pemilah-sampah-cb971-default-rtdb.asia-southeast1.firebasedatabase.app/"
#define API_KEY "AIzaSyB-ruimuEUesMO6fnJFRbiRJhAH_g6vF08"

// 3. KONFIGURASI PIN
#define DHTPIN 4        
#define DHTTYPE DHT22   
#define PIN_MQ 34       

// KONFIGURASI ALARM BUZZER (SUHU)
#define PIN_BUZZER 13   // Wiring: Positif Buzzer ke D13, Negatif ke GND
#define BATAS_SUHU 45.0 // Buzzer nyala jika suhu di atas 45 derajat Celcius

const int trigOrg = 5;  
const int echoOrg = 18; 
const int trigAnorg = 19; 
const int echoAnorg = 21; 

const int TINGGI_TONG_CM = 30; // Tinggi maksimal tempat sampah (cm)

// OBJEK
DHT dht(DHTPIN, DHTTYPE);
FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;
bool signupOK = false;

// Variabel Timer
unsigned long previousMillis = 0;
const long intervalHistory = 3600000; // Simpan history setiap 1 jam

void setup() {
  Serial.begin(115200);
  
  // Setup Pin Sensor
  pinMode(trigOrg, OUTPUT);
  pinMode(echoOrg, INPUT);
  pinMode(trigAnorg, OUTPUT);
  pinMode(echoAnorg, INPUT);
  pinMode(PIN_MQ, INPUT);

  // Setup Pin Buzzer
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW); // Matikan buzzer saat awal start
  
  dht.begin();
  
  // Koneksi WiFi
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Menghubungkan ke WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(300);
  }
  Serial.println("\nTerhubung ke WiFi!");

  // SETUP FIREBASE
  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;
  
  if (Firebase.signUp(&config, &auth, "", "")){
    Serial.println(">> Firebase Connected!");
    signupOK = true;
  }
  else{
    Serial.printf("%s\n", config.signer.tokens.error.message.c_str());
  }

  config.token_status_callback = tokenStatusCallback; 
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
}

void loop() {
  // Cek koneksi WiFi
  if(WiFi.status() != WL_CONNECTED){
     WiFi.begin(ssid, password);
     return;
  }

  // 1. BACA SENSOR
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  
  // Validasi sensor DHT
  if (isnan(h) || isnan(t)) { 
    h = 0; t = 0; 
    Serial.println("Gagal baca DHT!"); 
  }

  // LOGIKA ALARM SUHU (BUZZER)
  // Jika suhu lebih dari 45 derajat, nyalakan buzzer
  if (t > BATAS_SUHU) {
    digitalWrite(PIN_BUZZER, HIGH);
    Serial.println(">> PERINGATAN! Suhu Panas Terdeteksi!");
  } else {
    digitalWrite(PIN_BUZZER, LOW);
  }

  // Baca Sensor Gas (Tetap dibaca untuk dikirim ke Firebase)
  int mqRaw = analogRead(PIN_MQ); 
  // Kirim Nilai sensor gas
  int gasPercent = map(mqRaw, 0, 4095, 0, 100); 

  // Hitung Organik
  long jarakOrg = ukurJarak(trigOrg, echoOrg);
  if (jarakOrg > TINGGI_TONG_CM) jarakOrg = TINGGI_TONG_CM;
  int persenOrg = ((TINGGI_TONG_CM - jarakOrg) * 100) / TINGGI_TONG_CM;
  if (persenOrg < 0) persenOrg = 0; if (persenOrg > 100) persenOrg = 100;

  // Hitung Anorganik
  long jarakAnorg = ukurJarak(trigAnorg, echoAnorg);
  if (jarakAnorg > TINGGI_TONG_CM) jarakAnorg = TINGGI_TONG_CM;
  int persenAnorg = ((TINGGI_TONG_CM - jarakAnorg) * 100) / TINGGI_TONG_CM;
  if (persenAnorg < 0) persenAnorg = 0; if (persenAnorg > 100) persenAnorg = 100;

  // Tampilkan di Serial Monitor
  Serial.printf("\nSuhu: %.1f C | Gas Raw: %d | Org: %d %% | Anorg: %d %%\n", t, mqRaw, persenOrg, persenAnorg);

  // 2. KIRIM KE FIREBASE
  if (Firebase.ready() && signupOK) {

    // A. UPDATE STATUS REALTIME (Dashboard)
    Firebase.RTDB.setFloat(&fbdo, "/monitoring/suhu", t);
    Firebase.RTDB.setFloat(&fbdo, "/monitoring/kelembapan", h);
    
    // Mengirim status gas (saya kirim raw & persen supaya lengkap)
    Firebase.RTDB.setInt(&fbdo, "/monitoring/gas_level", gasPercent);
    Firebase.RTDB.setInt(&fbdo, "/monitoring/gas_raw", mqRaw);
    
    Firebase.RTDB.setInt(&fbdo, "/monitoring/kapasitas_organik", persenOrg);
    Firebase.RTDB.setInt(&fbdo, "/monitoring/kapasitas_anorganik", persenAnorg);
    Firebase.RTDB.setTimestamp(&fbdo, "/monitoring/last_update");
    
    // B. SIMPAN RIWAYAT UNTUK DATASET (Logging)
    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= intervalHistory) {
        previousMillis = currentMillis;

        FirebaseJson json;
        json.set("suhu", t);
        json.set("kelembapan", h);
        json.set("gas_level", gasPercent);
        json.set("gas_raw", mqRaw);
        json.set("kapasitas_organik", persenOrg);
        json.set("kapasitas_anorganik", persenAnorg);
        
        // Timestamp Server
        json.set("timestamp", "{\".sv\": \"timestamp\"}");

        // Simpan ke folder 'riwayat_logs'
        if (Firebase.RTDB.pushJSON(&fbdo, "/riwayat_logs", &json)) {
            Serial.println(">> [SUCCESS] Log Riwayat tersimpan!");
        } else {
            Serial.println(">> [ERROR] Gagal simpan log: " + fbdo.errorReason());
        }
    }
  }

  delay(1000); // Delay loop
}

// Fungsi Ukur Jarak Ultrasonik
long ukurJarak(int trig, int echo) {
  digitalWrite(trig, LOW); delayMicroseconds(2);
  digitalWrite(trig, HIGH); delayMicroseconds(10);
  digitalWrite(trig, LOW);
  long duration = pulseIn(echo, HIGH);
  return duration * 0.034 / 2;
}
