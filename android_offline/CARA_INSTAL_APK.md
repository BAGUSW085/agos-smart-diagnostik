# Cara Mengambil & Memasang APK Offline AGOS Smart Diagnostik di HP Android

Aplikasi **AGOS Smart Diagnostik (Mode Offline v1.2.1)** sudah dikonversi agar berjalan **100% tanpa internet dan tanpa server**, sementara seluruh data web lama Anda tetap tersimpan utuh di branch `main`.

### Pembaruan Tampilan HP (v1.2.1):
- **Tombol Pilih Komponen Horizontal:** Seluruh tombol sensor (`MAF + IAT`, `O2`, `ECT`, `MAP`, `CKP`, `Throttle`, `Koil`) tersusun rapi ke samping dan tidak bertumpuk vertikal huruf per huruf.
- **Gambar Simulasi Tampil Penuh (Full-View):** Diagram Alur Kerja, Anatomi Sensor, Peta Lokasi Mesin, dan Skema Wiring otomatis menyesuaikan lebar layar HP sehingga terlihat utuh 100% tanpa perlu menggeser layar.
- **Dukungan Layar Horizontal (Landscape):** Tekan tombol **Horizontal / Vertikal** di pojok kanan atas aplikasi (atau miringkan HP Anda bila rotasi otomatis aktif) untuk memakai tampilan layar lebar agar teks panjang tidak memanjang ke bawah.

---

## Langkah 1 — Mengunduh File `.apk` Langsung (GitHub Releases / Actions)
1. File siap pasang tersedia di folder proyek Anda sebagai **`AGOS-Smart-Diagnostik-Offline.apk`**, atau dapat diunduh langsung dari menu **Releases** / **Actions** di GitHub:
   👉 **[https://github.com/BAGUSW085/agos-smart-diagnostik/releases](https://github.com/BAGUSW085/agos-smart-diagnostik/releases)**
2. Untuk build otomatis via Actions, buka **[https://github.com/BAGUSW085/agos-smart-diagnostik/actions](https://github.com/BAGUSW085/agos-smart-diagnostik/actions)**, klik workflow **"Build Android APK Offline - AGOS Smart Diagnostik"** paling atas, tunggu centang hijau ✅, lalu unduh **`AGOS-Smart-Diagnostik-Offline.apk`**.

## Langkah 2 — Memasang APK di HP Android
1. Kirim file **`AGOS-Smart-Diagnostik-Offline.apk`** ke HP Android Anda (lewat WhatsApp, kabel USB, atau Google Drive).
2. Ketuk file **`AGOS-Smart-Diagnostik-Offline.apk`** di HP Anda (jika sebelumnya sudah menginstal v1.2.0, cukup timpa / pilih **Update / Perbarui**).
3. Jika muncul peringatan keamanan *"Instal aplikasi yang tidak dikenal"*, ketuk **Setelan (Settings)** $\rightarrow$ aktifkan **"Izinkan dari sumber ini"**.
4. Ketuk **Instal (Install)** $\rightarrow$ **Buka (Open)**.

---

## Cara Kembali ke Versi Web / Cloud (Cadangan Opsi A)
Jika suatu saat Anda berubah pikiran dan ingin memakai versi Web / Cloud kembali, cukup jalankan:
```bash
git checkout main
```
Seluruh file `backend/`, database `bengkel_masa_depan.db`, dan data kasus Anda (`K001` s/d `K018`) **100% utuh dan tidak berubah sedikit pun**.
