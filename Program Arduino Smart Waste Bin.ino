
#include <Wire.h> 
#include <LiquidCrystal_I2C.h>
#include <Servo.h>
#include <RTClib.h> // Library yang Anda pakai tadi

// --- OBJEK ---
LiquidCrystal_I2C lcd(0x27, 16, 2); // Jika layar gelap, ganti 0x3F
RTC_DS3231 rtc;                     // SAMA PERSIS dengan kode tes Anda
Servo servoPemilah;

// Variabel Hari (Opsional, untuk tampilan nanti)
char namaHari[7][12] = {"Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"};

// Status RTC
bool rtcSehat = false;

// --- PIN SENSOR ---
const int pinSensorLogam     = 3;
const int pinSensorKapasitif = 2;
const int pinSensorIR        = 4;
const int pinServo           = 9;

// --- SETTING SERVO ---
const int SUDUT_STANDBY   = 60; 
const int SUDUT_ORGANIK   = 0;   
const int SUDUT_ANORGANIK = 180; 

const int THRESHOLD_MINIMAL = 5; 

void setup() {
  Serial.begin(9600);
  
  // 1. MULAI JALUR I2C SECARA MANUAL (PENTING!)
  Wire.begin(); 
  delay(100); // Beri nafas sebentar untuk listrik stabil

  // 2. INISIALISASI RTC DULUAN (Prioritas)
  if (!rtc.begin()) {
    Serial.println("RTC Gagal! Cek Kabel.");
    rtcSehat = false;
  } else {
    Serial.println("RTC OK! Siap digunakan.");
    rtcSehat = true;
    
    // Cek jika baterai habis/baru pasang
    if (rtc.lostPower()) {
      Serial.println("RTC lost power, setting time...");
      rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    }
  }

  // 3. BARU INISIALISASI LCD
  lcd.init();
  lcd.backlight();
  
  // Tampilkan Status RTC di Layar
  if (rtcSehat) {
    lcd.setCursor(0,0); lcd.print("RTC: OK");
  } else {
    lcd.setCursor(0,0); lcd.print("RTC: ERROR");
  }
  lcd.setCursor(0,1); lcd.print("SYSTEM START...");
  delay(1500);
  lcd.clear();

  // 4. SETUP SENSOR & SERVO
  pinMode(pinSensorLogam, INPUT_PULLUP);
  pinMode(pinSensorKapasitif, INPUT);
  pinMode(pinSensorIR, INPUT);
  
  servoPemilah.attach(pinServo);
  servoPemilah.write(SUDUT_STANDBY);

  // Tampilan Intro
  lcd.setCursor(0,0); lcd.print("SISTEM PEMILAH");
  lcd.setCursor(0,1); lcd.print("SIAP KERJA...");
  delay(1500);
  lcd.clear();
}

void loop() {
  // 1. CEK TRIGGER (IR SENSOR)
  bool adaBenda = (digitalRead(pinSensorIR) == LOW); 

  if (adaBenda) {
    // --- MODE PEMILAHAN ---
    delay(400); 

    // A. CEK LOGAM
    if (digitalRead(pinSensorLogam) == LOW) {
      Serial.println("Terdeteksi: LOGAM");
      tampilLCD("DETEKSI: LOGAM", "JENIS: ANORGANIK");
      buangKeKiri();
    } 
    // B. CEK KAPASITIF
    else {
      tampilLCD("CEK KANDUNGAN...", "SAMPLING...");
      
      bool isOrganik = false; 
      int skor = 0;

      for(int i=0; i<60; i++) {
        if(digitalRead(pinSensorKapasitif) == HIGH) skor++;
        if (skor >= THRESHOLD_MINIMAL) {
          isOrganik = true;
          break; 
        }
        delay(2);
      }
      
      if (isOrganik) {
        Serial.println("Terdeteksi: ORGANIK");
        tampilLCD("HASIL: ORGANIK", "SAMPAH BASAH");
        buangKeKanan();
      } else {
        Serial.println("Terdeteksi: PLASTIK/KERING");
        tampilLCD("HASIL: ANORGANIK", "PLASTIK/KERING");
        buangKeKiri();
      }
    }
  } 
  else {
    // --- MODE STANDBY (TAMPILKAN JAM) ---
    tampilkanJam();
  }
}

// --- FUNGSI TAMPILAN JAM ---
void tampilkanJam() {
  lcd.setCursor(0,0); 
  lcd.print("SIAP MEMILAH... ");
  
  lcd.setCursor(0,1);
  
  if (rtcSehat) {
    DateTime now = rtc.now();
    
    // Format Jam:Menit:Detik
    printDuaDigit(now.hour());
    lcd.print(":");
    printDuaDigit(now.minute());
    lcd.print(":");
    printDuaDigit(now.second());
    
    // Tampilkan Hari (Singkat) di sebelahnya
    // Mengambil 3 huruf pertama dari nama hari
    lcd.print(" ");
    lcd.print(namaHari[now.dayOfTheWeek()]); 
  } 
  else {
    lcd.print("--:--:-- (ERR)  ");
  }
}

void printDuaDigit(int number) {
  if (number < 10) lcd.print("0");
  lcd.print(number);
}

// --- FUNGSI GERAK & LCD ---
void tampilLCD(String baris1, String baris2) {
  lcd.clear();
  lcd.setCursor(0,0); lcd.print(baris1);
  lcd.setCursor(0,1); lcd.print(baris2);
}

void buangKeKanan() { // ORGANIK
  servoPemilah.write(SUDUT_ORGANIK);
  delay(2500); 
  servoPemilah.write(SUDUT_STANDBY);
  delay(1000);
  lcd.clear();
}

void buangKeKiri() { // ANORGANIK
  servoPemilah.write(SUDUT_ANORGANIK);
  delay(2500);
  servoPemilah.write(SUDUT_STANDBY);
  delay(1000);
  lcd.clear();
}