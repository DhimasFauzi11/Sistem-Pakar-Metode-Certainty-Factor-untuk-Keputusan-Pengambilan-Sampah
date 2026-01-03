# Smart Waste Management System (Parakan Ceuri Tourism Area) ♻️🤖

![Project Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![IoT](https://img.shields.io/badge/IoT-ESP32-yellow)
![Method](https://img.shields.io/badge/Architecture-Dual%20Output-orange)

> **Sistem Tong Sampah Cerdas Terintegrasi:** Menampilkan pemantauan *real-time* dengan keputusan prioritas (Sistem Pakar) dan prediksi masa depan (Machine Learning) dalam satu Dashboard monitoring.

---

## 📋 Daftar Isi
- [Latar Belakang](#-latar-belakang)
- [Arsitektur Dual-Output](#-arsitektur-dual-output)

---

## 📖 Latar Belakang
Pengelolaan sampah di kawasan wisata budaya **Parakan Ceuri** memiliki dinamika tinggi. Petugas kebersihan sering mengalami dilema: *mengangkut sampah yang belum penuh* (pemborosan) atau *terlambat mengangkut saat acara ramai* (polusi bau).

Sistem ini hadir untuk memberikan dua sudut pandang sekaligus kepada pengelola:
1.  **WHAT TO DO NOW:** Apa yang harus dilakukan sekarang? (Ditangani oleh **Sistem Pakar**).
2.  **WHAT TO EXPECT:** Apa yang akan terjadi nanti? (Ditangani oleh **Machine Learning**).

---

## 🏗 Arsitektur Dual-Output

Sistem memproses data sensor menjadi dua output terpisah yang independen di Dashboard:

```mermaid
graph TD
    A[Hardware: Tong Sampah] -->|Pilahan Otomatis| B(IoT Sensors: Ultrasonic, Gas, Sorter)
    
    %% Jalur 1: Real-time Decision
    B -->|Data Real-time + Konteks| C{Sistem Pakar Hybrid}
    C -->|Output 1| D[Status Prioritas: AMAN/WASPADA/KRITIS]
    
    %% Jalur 2: Future Prediction
    B -->|Data Historis| E(Machine Learning Model)
    E -->|Output 2| F[Forecasting: Penuh dalam X Hari]
    
    %% Muara
    D --> G[DASHBOARD MONITORING]
    F --> G
