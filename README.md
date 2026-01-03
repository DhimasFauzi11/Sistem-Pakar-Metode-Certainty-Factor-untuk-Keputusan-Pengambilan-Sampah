# Smart Waste Management System (Parakan Ceuri Tourism Area) ♻️🤖

![Project Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![IoT](https://img.shields.io/badge/IoT-ESP32-yellow)
![Method](https://img.shields.io/badge/Method-Hybrid%20Fuzzy%20CF-red)

> **Sistem Manajemen Sampah Cerdas Terintegrasi:** Menggabungkan pemilahan otomatis, prediksi *Machine Learning*, dan pengambilan keputusan berbasis *Sistem Pakar Hybrid* untuk optimalisasi kebersihan kawasan wisata.

---

## 📋 Daftar Isi
- [Latar Belakang](#-latar-belakang)
- [Fitur Utama](#-fitur-utama)
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Logika Sistem Pakar (The Brain)](#-logika-sistem-pakar-the-brain)
- [Instalasi & Penggunaan](#-instalasi--penggunaan)
- [Struktur Folder](#-struktur-folder)
- [Tim Pengembang](#-tim-pengembang)

---

## 📖 Latar Belakang
Pengelolaan sampah di kawasan wisata budaya **Parakan Ceuri** menghadapi tantangan fluktuasi pengunjung yang dinamis. Jadwal pengangkutan konvensional seringkali tidak efektif (terlambat saat *peak season* atau boros operasional saat sepi).

Proyek ini bertujuan mengubah manajemen sampah dari **Reaktif-Statis** menjadi **Prediktif-Dinamis** dengan mengintegrasikan:
1.  **Hardware:** Pemilahan sampah otomatis di tempat.
2.  **Machine Learning:** Memprediksi kapan tong akan penuh.
3.  **Expert System:** Menentukan prioritas pengangkutan berdasarkan urgensi fisik dan lingkungan.

---

## 🚀 Fitur Utama

### 1. Auto-Sorting (IoT)
* Menggunakan sensor untuk mendeteksi dan memisahkan sampah **Organik** dan **Non-Organik** secara otomatis.
* Mengurangi beban kerja pemilahan manual di TPA.

### 2. Fill-Level Forecasting (Machine Learning)
* Menggunakan algoritma regresi untuk memprediksi waktu kepenuhan tong (*Time-to-Full*).
* Memberikan data antisipasi untuk perencanaan rute truk.

### 3. Smart Decision System (Expert System) 🧠
* **Hybrid Method:** Menggabungkan **Fuzzy Logic** (menangani ketidakpastian sensor) dan **Certainty Factor** (bobot kepercayaan pakar).
* **Context Aware:** Mempertimbangkan faktor lingkungan seperti *Event*, *Lokasi (VIP)*, dan *Suhu*.
* **Fail-Safe:** Fitur *Hard Rule* untuk mencegah luapan fisik.

---

## 🏗 Arsitektur Sistem

Sistem bekerja dengan alur data sebagai berikut:

```mermaid
graph TD
    A[Sampah Masuk] -->|Sensor| B(Auto-Sorting Hardware)
    B -->|Output: Jenis Sampah| D[Central Processing Unit]
    C[Sensor Ultrasonic & Gas] -->|Output: Kepenuhan & Bau| D
    E[Machine Learning] -->|Output: Prediksi Laju| D
    F[Data Lingkungan] -->|Input: Event & Lokasi| D
    
    D -->|Data Fusion| G{Sistem Pakar Hybrid}
    G -->|Keputusan| H[Status Prioritas]
    
    H --> I[Dashboard Admin / Armada Truk]
