# PROGRES — APK Android Offline AGOS Smart Diagnostik

> Aturan: kerjakan tugas pertama yang belum dicentang `[ ]`. Setelah selesai, ubah jadi `[x]`,
> isi kolom catatan, lalu commit. Spesifikasi lengkap ada di `PROMPT_APK_OFFLINE.md`.

**Status terakhir:** SELURUH FASE (Fase 1 s/d Fase 9) SELESAI 100%. File `AGOS-Smart-Diagnostik-Offline.apk` berhasil dibangun dan dirilis.
**Model AI terakhir yang bekerja:** Gemini 4 Argon (High)
**Tanggal update terakhir:** 2026-11-16

---

## Fase 1 — Persiapan
- [x] 1.1 Commit perubahan yang masih tertunda di `main` (`backend/app/db/seed_historical_cases.py` sudah ditambah K013–K018, plus `PROMPT_APK_OFFLINE.md` dan file ini).
- [x] 1.2 Buat branch `git checkout -b apk-offline`.
- [x] 1.3 Buat folder `android_offline/` sesuai struktur di Bagian 4 prompt master.
- [x] 1.4 Salin `backend/app/static/index.html` → `android_offline/www/index.html` (salin, bukan pindah). Salin juga `icon-192.png` dan `icon-512.png`.

## Fase 2 — Ekspor Data
- [x] 2.1 Tulis `android_offline/tools/export_data.py` (koneksi SQLite mode baca saja: `file:...?mode=ro`).
- [x] 2.2 Hasilkan `www/data/historical_cases.json`, `dtc_codes.json`, `wiring_diagrams.json`, `sensor_specs.json`, `repair_manuals.json`, `jb420_catalog.json` serta `www/js/embedded-data.js`.
- [x] 2.3 Catat ukuran tiap file JSON. Jika `repair_manuals.json` > 5 MB, buang kolom yang tidak dipakai UI.
  - `historical_cases.json`: 14.83 KB (17 kasus: K001–K018)
  - `dtc_codes.json`: 416.51 KB (208 kode DTC)
  - `wiring_diagrams.json`: 41.82 KB (11 diagram)
  - `sensor_specs.json`: 6.15 KB (9 sensor)
  - `repair_manuals.json`: 2,726.87 KB (~2.66 MB, 1.381 entri manual Vol 1 & Vol 2)
  - `jb420_catalog.json`: 893.39 KB (207 entri)

## Fase 3 — Port Mesin Diagnosa
- [x] 3.1 `www/js/engine.js`: tokenizer, stopword, sinonim, parsing DTC, keluarga DTC.
- [x] 3.2 Skor teks, skor live, skor total, kategori, ranking, `system_summaries`.
- [x] 3.3 Pembuatan `direct_manual_advice` (port logika `ManualRepairAdvice` dari Python).
- [x] 3.4 `tools/verify_engine.py` + hasil verifikasi semua kasus lolos ±0.5% (selisih aktual 0.00% s/d 0.10% untuk seluruh 17 kasus K001–K018).

## Fase 4 — Port Pencarian Manual / DTC
- [x] 4.1 `www/js/manual-search.js` meniru respons `/manuals/ask-assistant` (`synthesized_guidance`, `detected_dtc_codes`, `matched_wiring_diagrams`).
  Sumber yang di-port: `backend/app/services/manual_wiring_service.py` → `ask_rag_assistant()`, `retrieve_repair_manuals()`, `search_sensor_specs()`, `search_wiring_diagrams()`, `lookup_dtc_codes()`.
- [x] 4.2 Uji 10 kueri ("P0122", "P0480 kipas", "MAF", "O2 heater P0037", "pinout C37", "TCM E92", "ECT suhu", "P0300 misfire", "C1021 ABS", "B1133 BCM") — seluruh 10 kueri LULUS 100%.

## Fase 5 — Lapisan Offline API
- [x] 5.1 `www/js/data-store.js`: muat JSON bawaan + simpan kasus tambahan/terhapus di `localStorage` (bawaan tidak diubah).
- [x] 5.2 `www/js/offline-api.js`: fungsi `offlineFetch()` untuk 6 endpoint (lihat tabel Bagian 3).
- [x] 5.3 Ganti semua `fetch(\`${API_BASE}...\`)` dan `fetch('/health')` di `www/index.html`.

## Fase 6 — Hilangkan Ketergantungan Internet
- [x] 6.1 Tailwind CDN → build lokal `www/css/app.css` (35 KB).
- [x] 6.2 Font Awesome lokal (`www/css/fontawesome.min.css` + `www/webfonts/fa-solid-900.woff2`, `fa-regular-400.woff2`, `fa-brands-400.woff2`).
- [x] 6.3 Font stack sistem lokal yang bersih dan cepat tanpa Google Fonts CDN.
- [x] 6.4 Hapus/sembunyikan QR `api.qrserver.com`, link `bore.pub`, tombol Pasang App, service worker.
- [x] 6.5 Ganti `window.print()` dengan bagikan/simpan hasil (`navigator.share` / unduh `.txt`).

## Fase 7 — Rapikan Tampilan HP (Bagian 6 prompt master)
- [x] 7.1 Viewport (`viewport-fit=cover`), safe-area, anti scroll samping.
- [x] 7.2 Tabel → kartu bertumpuk di layar < 640px (5 tabel menggunakan `.agos-mobile-cards` & `data-label`).
- [x] 7.3 Bottom nav, target sentuh 44px, ukuran font `16px` pada input.
- [x] 7.4 SVG simulator (`.agos-svg-scroll-wrap`) dan modal layar penuh di HP.
- [x] 7.5 Tombol Back Android (`handleAndroidBackAction`).
- [x] 7.6 Uji lebar 360/393/412px di semua tab, catat hasilnya (LULUS 0 scroll samping di semua tab).

## Fase 8 — Capacitor & Build
- [x] 8.1 `package.json`, `capacitor.config.json`, `tailwind.config.js`, `src/input.css`.
- [x] 8.2 `.github/workflows/build_apk_offline.yml`.
- [x] 8.3 Build sukses di GitHub Actions (Run ID `43872674412` SUKSES, APK dirilis di `v1.2.0-offline` & diunduh ke `AGOS-Smart-Diagnostik-Offline.apk`).

## Fase 9 — Uji Akhir & Serah Terima
- [x] 9.1 Semua poin lokal Definition of Done (Bagian 9 prompt master) lolos (`git diff main -- backend` kosong).
- [x] 9.2 Tulis `android_offline/CARA_INSTAL_APK.md` (bahasa sederhana untuk pengguna).

---

## Catatan Kerja
| Tanggal | Model AI | Tugas | Catatan |
|---|---|---|---|
| 2026-11-16 | Claude Opus 5.5 | Prompt master | Membuat `PROMPT_APK_OFFLINE.md` dan file progres ini. Belum ada kode APK. |
| 2026-11-16 | Gemini 4 Argon | Fase 1 s/d 8.2 & 9.2 | Menyelesaikan cabang `apk-offline`, ekspor data SQLite read-only, port `engine.js` & `manual-search.js` (verifikasi 17 kasus & 10 kueri LULUS 100%), bundel CSS/FontAwesome offline, perapian tabel->kartu HP 360/393/412px, dan workflow GitHub Actions (`v1.2.0-offline`). |
| 2026-11-16 | Gemini 4 Hydrogen | Evaluasi UI v1.2.1 (Perbaikan HP & Horizontal) | Memperbaiki pill "Pilih Komponen" agar horizontal rapi (tidak bertumpuk vertikal huruf per huruf), mengubah seluruh SVG simulasi (`man-workflow-loop-svg`, `man-component-anatomy-svg`, `man-engine-bay-svg`, `sim-wiring-svg`) agar muat penuh 100% tanpa geser samping, merapikan layout horizontal seluruh 4 tab, serta menambahkan tombol & bridge native Android (`AgosNative.setOrientation` di `MainActivity.java`) agar APK mendukung orientasi Horizontal (Landscape) & Vertikal (`v1.2.1-offline`). |

## Catatan Masalah
- (kosong — tidak ada kendala)
