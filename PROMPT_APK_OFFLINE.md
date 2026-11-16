# PROMPT MASTER — Konversi Web AGOS Smart Diagnostik → APK Android Offline

> **Untuk AI apa pun (Claude, Gemini, GPT, Copilot, dll.) yang membaca file ini:**
> Dokumen ini adalah instruksi utama sekaligus serah terima (handoff). Sebelum mengubah apa pun,
> baca file ini sampai selesai, lalu baca `PROGRES_APK_OFFLINE.md`. Kerjakan tugas pertama
> yang belum dicentang. Jangan memulai ulang dari nol dan jangan menanyakan ulang hal yang sudah
> diputuskan di sini.

---

## 0. CARA MEMAKAI (untuk pengguna)

Tempelkan kalimat ini ke model AI mana pun:

```
Baca file "c:\project bengkel masa depan ai antigravity\PROMPT_APK_OFFLINE.md"
dan "PROGRES_APK_OFFLINE.md" di folder yang sama. Ikuti seluruh aturannya,
lalu lanjutkan tugas berikutnya yang belum selesai. Setelah setiap tugas selesai,
perbarui PROGRES_APK_OFFLINE.md.
```

---

## 1. TUJUAN

Membuat **APK Android yang berjalan 100% offline** (tanpa server, tanpa internet) dari web
diagnostik yang sudah ada, dengan:

1. **Fitur sama** dengan web: Diagnosa Cepat (pencarian kasus berbobot), Data Kasus (lihat, tambah,
   hapus, uji), Manual & Wiring (simulator komponen + cari DTC/manual), Tool Diagnostik
   (kalkulator Fuel Trim, MAP, Voltage Drop, lookup DTC).
2. **Tampilan HP rapi**: tidak ada scroll ke samping, tidak ada teks/tombol keluar layar,
   tabel tetap terbaca, tombol mudah disentuh jari.
3. **Web lama tetap utuh** sebagai cadangan, supaya pengguna bisa kembali ke Opsi A (Render/online)
   kapan saja.

---

## 2. ATURAN WAJIB (JANGAN DILANGGAR)

| # | Aturan |
|---|---|
| R1 | **DILARANG mengubah, memindahkan, atau menghapus** isi folder `backend/`, `frontend/`, `manual repair suzuki vitara/`, file `.db`, `Dockerfile`, `render.yaml`, `railway.json`. Folder-folder ini **hanya boleh dibaca**. |
| R2 | Semua pekerjaan APK dibuat di folder baru: **`android_offline/`** di root proyek. |
| R3 | Kerjakan di git branch **`apk-offline`**. Branch `main` = versi web (cadangan). Jika branch belum ada: `git checkout -b apk-offline`. |
| R4 | Jangan menulis ulang aplikasi dari nol. **Salin** `backend/app/static/index.html` lalu modifikasi salinannya. Pertahankan tampilan, warna, teks, dan alur yang sudah ada. |
| R5 | Rumus diagnosa harus **identik** dengan Python (lihat Bagian 5). Hasil skor JS vs Python untuk input yang sama boleh beda maksimal ±0.5%. |
| R6 | Setelah setiap tugas selesai: centang di `PROGRES_APK_OFFLINE.md`, tulis catatan singkat, lalu `git add` + `git commit` dengan pesan jelas. Ini penting agar model AI berikutnya bisa melanjutkan. |
| R7 | Jika sebuah langkah gagal, tulis error-nya di bagian "Catatan Masalah" pada file progres sebelum berhenti. Jangan diam-diam melewatinya. |
| R8 | Jangan push ke GitHub kecuali pengguna memintanya. |

---

## 3. KONDISI PROYEK SAAT INI (fakta, sudah dicek)

- **Root proyek:** `c:\project bengkel masa depan ai antigravity`
- **OS:** Windows, shell PowerShell.
- **Tool terpasang:** Python 3.12 dan Git. **Belum ada** Node.js, Java/JDK, Android SDK, maupun Flutter.
  Karena itu APK dibangun di **GitHub Actions** (lihat Bagian 7). Membangun di lokal opsional.
- **Repo GitHub:** `https://github.com/BAGUSW085/agos-smart-diagnostik` (branch `main` sudah ter-push).
- **Web UI:** satu file `backend/app/static/index.html` (±4.631 baris, Tailwind + JavaScript murni).
  - `const API_BASE = '/api/v1';` ada di baris ±1516.
  - Pemanggilan server yang harus diganti versi offline:

    | Baris (±) | Panggilan | Fungsi JS |
    |---|---|---|
    | 2220 | `POST /diagnostics/search-case` | `executeSearch()` |
    | 3360 | `GET /diagnostics/cases` | `loadAllCases()` |
    | 3537 | `POST /diagnostics/cases` | `submitNewCase()` |
    | 3425 | `DELETE /diagnostics/cases/{id}` | `deleteCase()` |
    | 1904 & 4592 | `POST /manuals/ask-assistant` | `quickLookupDtc()`, `searchManualRAG()` |
    | 4621 | `GET /health` | status header |

  - Ketergantungan internet yang harus dihilangkan:
    - baris 16: `<script src="https://cdn.tailwindcss.com">` → tidak jalan offline
    - baris 18: Font Awesome dari cdnjs
    - baris 45: Google Fonts "Plus Jakarta Sans"
    - baris 1487 & 2111: gambar QR dari `api.qrserver.com`
    - baris 1492 & 2098: link `bore.pub` (tunnel lama)
    - baris 1754: `window.print()` (tidak berfungsi di WebView Android)
    - registrasi service worker `/sw.js` (tidak dibutuhkan di APK)
- **Mesin diagnosa (sumber kebenaran rumus):** `backend/app/services/diagnostic_service.py`,
  class `WeightedDiagnosticEngine` (mulai baris ±655) termasuk pembuatan `ManualRepairAdvice`.
- **Pencari manual "AI" (RAG):** `backend/app/services/manual_wiring_service.py` → `ask_rag_assistant()`.
  Ini **bukan** model AI online. Isinya pencarian kata kunci + skor relevansi atas data manual lokal
  (1.381 potongan manual ±2,4 MB, 208 DTC, katalog JB420 ±1 MB, pinout, spesifikasi sensor).
  Fitur ini **wajib ikut di APK dan berjalan penuh offline** dengan cara di-port ke JavaScript. Dilarang menggantinya dengan panggilan API AI online.
- **Database:** `backend/bengkel_masa_depan.db` (SQLite). Jumlah baris per tabel:
  `historical_cases` 13, `dtc_codes` 208, `repair_manuals` 1381, `wiring_diagrams` 11, `sensor_specs` 9.
- **Katalog DTC:** `backend/app/jb420_extracted_catalog.json` (189 DTC + 51 bab).
- **Data kasus:** `backend/app/db/seed_historical_cases.py` sudah dilengkapi K013–K018 agar
  sama dengan isi database.
- **Folder `frontend/` (Flutter)** adalah prototipe lama yang memanggil server; **tidak dipakai** untuk APK ini.
- **Workflow lama** `.github/workflows/build_apk.yml` gagal di tahap "Set up job" karena
  menulis `uses: actions/subosito/flutter-action@v2` (nama action salah). Workflow ini milik
  Flutter dan **tidak dipakai lagi**. Jangan dihapus; cukup buat workflow baru (Bagian 7).

---

## 4. ARSITEKTUR YANG SUDAH DIPUTUSKAN

**Capacitor (WebView) + JavaScript offline.** Alasannya: UI web sudah lengkap, jadi cukup dibungkus
tanpa menulis ulang tampilan, dan seluruh logika Python di-port ke JavaScript.

```
android_offline/
├── package.json                 # @capacitor/core, @capacitor/cli, @capacitor/android, tailwindcss
├── capacitor.config.json        # appId: com.agos.smartdiagnostik, appName: AGOS Diagnostik, webDir: www
├── tailwind.config.js           # salin konfigurasi warna brand/accent dari index.html baris 20-42
├── src/input.css                # @tailwind base; @tailwind components; @tailwind utilities; + CSS custom dari <style>
├── tools/
│   ├── export_data.py           # SQLite + JSON katalog -> www/data/*.json (hanya MEMBACA db)
│   └── verify_engine.py         # bandingkan hasil Python vs JS untuk semua kasus
├── www/                         # folder yang dibungkus jadi APK
│   ├── index.html               # salinan index.html yang sudah dimodifikasi
│   ├── css/app.css              # hasil build Tailwind (tanpa CDN)
│   ├── css/fontawesome.min.css + webfonts/   # Font Awesome lokal
│   ├── fonts/                   # Plus Jakarta Sans lokal (atau fallback font sistem)
│   ├── js/data-store.js         # baca JSON + simpan kasus baru di localStorage/IndexedDB
│   ├── js/engine.js             # port WeightedDiagnosticEngine (Python -> JS)
│   ├── js/manual-search.js      # port pencarian manual/DTC (ask-assistant)
│   ├── js/offline-api.js        # pengganti fetch(API_BASE...) dengan struktur respons identik
│   └── data/                    # historical_cases.json, dtc_codes.json, wiring.json, sensor_specs.json, manual_chunks.json, jb420_catalog.json
└── android/                     # dibuat otomatis oleh `npx cap add android` (di CI)
```

**Prinsip penggantian API:** jangan bongkar fungsi UI. Buat `offlineFetch(path, options)` di
`offline-api.js` yang mengembalikan objek mirip `Response` (`ok`, `status`, `json()`), lalu ganti
setiap `fetch(\`${API_BASE}...\`)` menjadi `offlineFetch(...)`. Dengan begitu `renderResults()`,
`renderCasesTable()`, dan fungsi lain tetap jalan tanpa diubah.

---

## 5. SPESIFIKASI RUMUS (wajib sama dengan Python)

Baca langsung `diagnostic_service.py` sebagai acuan utama. Ringkasan:

- **Skor teks** (0–1) = `(0.10·Merk + 0.15·Model + 0.20·Keluhan + 0.20·Gejala + 0.20·DTC) / 0.85`, maksimal 1.
  - Merk: 1 jika sama/saling mengandung (huruf kecil).
  - Model, Keluhan, Gejala: irisan token / jumlah token terbanyak. Keluhan & Gejala memakai
    `preprocess_symptom_tokens` (hapus non-alfanumerik, buang stopword Indonesia, petakan sinonim
    bengkel seperti brebet→mbrebet). Salin daftar `INDONESIAN_STOPWORDS` dan `AUTOMOTIVE_SYNONYM_MAP` apa adanya.
  - DTC: kedua kosong = 1; salah satu kosong = 0; sama persis +1, satu keluarga `_DTC_SUBSYSTEM_FAMILIES` +0.60,
    dibagi jumlah kode terbanyak. Jika pengguna isi DTC tapi skor DTC = 0, skor teks ×0.30.
  - Parsing DTC mengikuti `split_dtc_codes` + `_extract_all_request_dtcs` (format `P0037-00` → `P0037`, termasuk `KLS-xx`).
- **Skor live data** (hanya parameter yang terisi di kedua sisi):
  STFT bobot 0.20 tol 5 · LTFT 0.15 tol 5 · RPM 0.10 tol 300 · MAP 0.15 tol 10 · MAF 0.10 tol 2 · ECT 0.15 tol 10 ·
  O2 0.15 tol 0.15 (rata-rata rentang, mis. `"0,15–0,85 V"`). Rumus per parameter `max(0, 1 − |selisih|/tol)`,
  lalu dibagi total bobot yang aktif. Jika tidak ada yang aktif → `null`.
- **Skor total** = `0.85·teks + 0.15·live` (jika live `null`, ikuti persis perilaku Python).
- **Kategori:** ≥80% Sangat mirip · ≥60% Mirip · ≥40% Cukup mirip · <40% Kurang mirip.
- **Struktur respons** `search-case` harus sama dengan `WeightedCaseSearchResponse`:
  `top_headline, top_case_code, top_diagnosis, top_score_percent, top_category_label,
  system_filter_applied, ranked_matches[], system_summaries[], direct_manual_advice{...}`.
  Field `direct_manual_advice` mengikuti `ManualRepairAdvice` (cause_summary, cause_items,
  repair_options, step_by_step_repair, sensor_standards, wiring_pinout, relearn_reset_steps, dll.).
- **Verifikasi:** `tools/verify_engine.py` menjalankan engine Python (impor dari `backend/app`, hanya membaca)
  dan engine JS (via data JSON yang sama) untuk tiap kasus di database sebagai input, lalu mencetak
  tabel perbandingan. Semua harus lolos toleransi ±0.5%. Jika Node belum ada di lokal, jalankan
  verifikasi ini di GitHub Actions.

---

## 6. STANDAR TAMPILAN HP (anti-amburadul)

Terapkan semua poin ini pada `www/index.html` dan `src/input.css`:

1. **Viewport & area aman:** `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`.
   Gunakan `padding: env(safe-area-inset-*)` untuk header dan bottom nav. Status bar tidak boleh menimpa header.
2. **Tidak ada scroll horizontal:** `html, body { overflow-x: hidden; max-width: 100vw; }`. Setiap elemen
   lebar (tabel, SVG, `<pre>`) dibungkus `overflow-x-auto` atau diubah jadi kartu.
3. **Tabel → kartu di layar < 640px:** tabel `table-ranked-cases`, `table-all-cases`, `table-system-summaries`,
   `table-sensor-standards`, `table-wiring-pinouts` tampil sebagai daftar kartu bertumpuk di HP
   (label kecil di atas nilai). Di tablet ke atas tetap tabel.
4. **Navigasi:** bottom navigation bar tetap di bawah (4 tab: Diagnosa, Data Kasus, Manual & Wiring, Tool),
   tinggi ±64px + safe-area, ikon + label pendek. Konten utama diberi `padding-bottom` agar tidak tertutup.
5. **Target sentuh:** tombol/chip minimal 44×44px, jarak antar tombol minimal 8px.
6. **Font:** input/select/textarea `font-size: 16px` (mencegah auto-zoom). Teks isi minimal 13px, label minimal 11px.
   Judul panjang memakai `break-words`, bukan meluber.
7. **Grid responsif:** form diagnosa 1 kolom di HP, 2 kolom di tablet. Grid live data 2 kolom di HP.
8. **SVG simulator** (`sim-wiring-svg`, `man-workflow-loop-svg`, `man-component-anatomy-svg`, `man-engine-bay-svg`):
   `width:100%; height:auto;` dengan `viewBox` tetap. Jika teks SVG terlalu kecil di HP, bungkus dengan
   container `overflow-x-auto` dan `min-width` ±560px agar bisa digeser, bukan menyusut tak terbaca.
9. **Modal** (simpan kasus, pasang app): penuh layar di HP (`inset-0`, scroll di dalam modal), tombol aksi menempel di bawah.
10. **Fitur online di APK:** sembunyikan tombol "Pasang App / Bagikan", QR, dan link bore.pub. Ganti status
    "Engine Online" menjadi **"Mode Offline"**. Ganti "Cetak Lembar" dengan **bagikan/simpan teks hasil**
    (Capacitor Share atau unduh file `.txt`).
11. **Tombol Back Android:** tutup modal yang terbuka dulu; jika tidak ada modal, kembali ke tab Diagnosa;
    jika sudah di Diagnosa, konfirmasi keluar aplikasi.
12. **Uji tampilan** di lebar **360px, 393px, dan 412px** (Chrome DevTools mode perangkat). Lulus bila tidak ada
    scroll samping dan tidak ada elemen terpotong di semua tab.

---

## 7. BUILD APK (GitHub Actions, karena lokal belum ada SDK)

Buat file baru `.github/workflows/build_apk_offline.yml`:

- Trigger: `workflow_dispatch` dan `push` ke branch `apk-offline`.
- Langkah: `actions/checkout@v4` → `actions/setup-node@v4` (node 20) → `actions/setup-java@v4`
  (temurin 17) → `android-actions/setup-android@v3` → di folder `android_offline/`:
  `npm ci` (atau `npm install`) → build Tailwind ke `www/css/app.css` → `npx cap add android`
  (jika folder `android/` belum ada) → `npx cap sync android` → `cd android && ./gradlew assembleDebug`.
- Upload artifact `android_offline/android/app/build/outputs/apk/debug/app-debug.apk`
  dengan nama `agos-diagnostik-offline-apk`.
- APK debug cukup untuk dipasang manual di HP (aktifkan "Instal dari sumber tidak dikenal").

---

## 8. URUTAN KERJA (ringkas — rincian dan checklist ada di PROGRES_APK_OFFLINE.md)

1. Persiapan: branch `apk-offline`, folder `android_offline/`, salin `index.html`.
2. Ekspor data ke JSON (`tools/export_data.py`).
3. Port engine diagnosa ke `engine.js` + verifikasi vs Python.
4. Port pencarian manual/DTC ke `manual-search.js`.
5. `data-store.js` + `offline-api.js`, ganti semua `fetch` di `www/index.html`.
6. Hilangkan semua ketergantungan internet (Tailwind build, Font Awesome lokal, font lokal, QR, bore.pub, print, service worker).
7. Rapikan tampilan HP sesuai Bagian 6.
8. Konfigurasi Capacitor + workflow GitHub Actions.
9. Uji akhir (Bagian 9) dan tulis panduan instal untuk pengguna.

---

## 9. KRITERIA SELESAI (Definition of Done)

- [ ] Mode pesawat aktif → aplikasi terbuka, semua 4 tab berfungsi, tidak ada error di console.
- [ ] `grep -E "https?://" android_offline/www` hanya menemukan link yang memang opsional (mis. WhatsApp share), tidak ada CDN.
- [ ] Hasil Diagnosa Cepat untuk 8 contoh kasus (tombol "Uji Coba Cepat") sama dengan versi web (±0.5%).
- [ ] Tambah kasus baru → tutup aplikasi → buka lagi → kasus masih ada.
- [ ] Hapus kasus berfungsi dan tidak menghapus data bawaan secara permanen dari file JSON.
- [ ] Tampilan lolos uji 360/393/412px tanpa scroll samping.
- [ ] APK berhasil dibangun di GitHub Actions dan terpasang di HP Android.
- [ ] Folder `backend/` dan branch `main` tidak berubah (`git diff main -- backend` kosong).

---

## 10. CARA KEMBALI KE VERSI WEB (Opsi A)

Pengguna cukup menjalankan `git checkout main`, lalu `run_backend_windows.bat` (lokal) atau melanjutkan
deploy Render. Tidak ada yang hilang karena semua pekerjaan APK berada di branch dan folder terpisah.
