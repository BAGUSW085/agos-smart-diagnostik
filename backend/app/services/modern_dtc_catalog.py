"""
Katalog Universal DTC Modern (Diesel Common-Rail, Turbo, VVT/VANOS, GDI, Hybrid/EV, CAN Bus)
& Evaluator Live Data Adaptif (Diesel & EV/Hybrid)
===========================================================================================
Melengkapi katalog OEM bensin NA (Suzuki JB420) agar bengkel multi-merek Asia, Eropa, dan China
mendapatkan analisa akurat, opsi perbaikan spesifik bahan bakar, serta guardrail keselamatan
tegangan tinggi (HV) dan batas kesesuaian jenis mesin (mencegah mobil EV/Diesel divonis busi/O2).
"""

from __future__ import annotations

import re
from typing import Any


def _dtc(
    code: str,
    title_id: str,
    system_category: str,
    applies_to: list[str],
    severity: str,
    root_causes: str,
    repair_options: list[dict[str, str]],
    repair_steps: list[str],
    standard_specs: list[dict[str, str]],
    requires_hv_safety: bool = False,
) -> dict[str, Any]:
    return {
        "code": code.upper(),
        "title_id": title_id,
        "system_category": system_category,
        "applies_to": applies_to,  # ["Diesel"], ["EV", "Hybrid"], ["Bensin", "Hybrid"], ["All"]
        "severity": severity,
        "root_causes": root_causes,
        "repair_options": repair_options,
        "repair_steps": repair_steps,
        "standard_specs": standard_specs,
        "requires_hv_safety": requires_hv_safety,
    }


def _opt(title: str, tag: str, priority: str, why: str, verify: str) -> dict[str, str]:
    return {
        "title": title,
        "tag": tag,
        "priority": priority,
        "why": why,
        "verify": verify,
    }


# ---------------------------------------------------------------------------
# 1. KATALOG 80+ DTC MODERN (DIESEL COMMON-RAIL, TURBO, VVT/VANOS, EV/HYBRID, CAN)
# ---------------------------------------------------------------------------

_RAW_MODERN_DTCS: list[dict[str, Any]] = [
    # ==================== DIESEL COMMON-RAIL & FUEL RAIL ====================
    _dtc(
        "P0087",
        "Tekanan Fuel Rail Common-Rail Terlalu Rendah (Fuel Rail Pressure Too Low)",
        "Bahan Bakar",
        ["Diesel"],
        "CRITICAL",
        "Filter solar tersumbat / kemasukan udara (masuk angin); SCV (Suction Control Valve) macet/aus; Kebocoran balik (backleak) injektor common-rail berlebih; Supply pump (high-pressure pump) lemah; Sensor tekanan rail (FRP) error.",
        [
            _opt(
                "Ganti Filter Solar, Bersihkan Water Sedimenter & Bleed Udara (Priming)",
                "Cek Pertama / Paling Sering",
                "UTAMA",
                "Solar kotor/bio-solar cepat menyumbat filter solar sehingga suplai ke supply pump tekor saat akselerasi.",
                "Pompa primer terasa keras dan tekanan rail stabil ≥ 30 MPa saat idle serta naik mulus saat digas.",
            ),
            _opt(
                "Bersihkan / Ganti SCV (Suction Control Valve) pada Supply Pump",
                "Penyebab Utama 2GD / 2KD / 4N15",
                "UTAMA",
                "Katup SCV yang macet atau aus gagal mengatur debit solar ke high-pressure rail.",
                "Hapus DTC, lakukan SCV / Supply Pump Learning dengan scanner, cek selisih Target vs Aktual Rail Pressure < 3 MPa.",
            ),
            _opt(
                "Uji Backleak (Kembali Solar) Injektor Common-Rail & Kalibrasi/Ganti Injektor Bocor",
                "Bocor Tekanan Internal",
                "SEKUNDER",
                "Satu injektor yang bocor balik menyebabkan tekanan seluruh common-rail drop saat beban berat.",
                "Volume tabung uji backleak seragam di semua silinder dan nilai kompensasi injektor dalam rentang -3.0 s/d +3.0 mm³/st.",
            ),
            _opt(
                "Periksa Pressure Limiter Valve (PLV), Sensor FRP & Pompa Tekanan Tinggi",
                "Cek Lanjutan",
                "OPSIONAL",
                "PLV yang bocor dini atau supply pump aus menyebabkan tekanan tidak pernah mencapai target.",
                "Tidak ada solar menetes dari jalur return PLV saat idle & tekanan cranking mencapai ≥ 25 MPa.",
            ),
        ],
        [
            "1. Periksa kondisi filter solar, water sedimenter, dan pastikan tidak ada selang solar retak / masuk angin.",
            "2. Baca Live Data Target vs Actual Fuel Rail Pressure saat idle (normal ~30–40 MPa) dan akselerasi (120–180 MPa).",
            "3. Periksa arus kontrol & kebersihan SCV (Suction Control Valve); lakukan kalibrasi ulang SCV bila diganti.",
            "4. Lakukan tes tabung backleak injektor untuk mendeteksi injektor yang bocor tekanan balik.",
            "5. Cek kebocoran katup Pressure Limiter Valve (PLV) di ujung common-rail & soket sensor FRP.",
        ],
        [
            {"parameter": "Fuel Rail Pressure (Cranking)", "normal_range": "25 – 35 MPa", "unit": "MPa"},
            {"parameter": "Fuel Rail Pressure (Idle)", "normal_range": "30 – 45 MPa", "unit": "MPa"},
            {"parameter": "Fuel Rail Pressure (Full Load)", "normal_range": "140 – 200 MPa", "unit": "MPa"},
            {"parameter": "Injector Feedback Compensation", "normal_range": "-3.0 s/d +3.0", "unit": "mm³/st"},
        ],
    ),
    _dtc(
        "P0088",
        "Tekanan Fuel Rail Terlalu Tinggi (Fuel Rail/System Pressure Too High)",
        "Bahan Bakar",
        ["Diesel", "Bensin"],
        "CRITICAL",
        "SCV / Fuel Pressure Regulator macet posisi terbuka penuh; Jalur return solar/BBM tersumbat atau terjepit; Sensor Fuel Rail Pressure (FRP) melenceng tinggi; Pompa HPFP (GDI/Diesel) bermasalah.",
        [
            _opt("Bersihkan / Ganti SCV atau Fuel Pressure Regulator (FPR)", "Penyebab Utama", "UTAMA", "Katup pengatur tekanan gagal membuang kelebihan tekanan rail.", "Actual Rail Pressure mengikuti Target Pressure tanpa lonjakan > +15 MPa."),
            _opt("Periksa Jalur Selang Return BBM/Solar dari Sumbatan / Terjepit", "Cek Mekanis", "SEKUNDER", "Jalur balik yang tersumbat membuat tekanan rail melonjak melebihi batas aman.", "Aliran return lancar ke tangki & tekanan idle normal."),
            _opt("Uji Tegangan & Ganti Sensor Fuel Rail Pressure (FRP)", "Sensor Error", "OPSIONAL", "Sensor FRP rusak memberi sinyal tegangan tinggi palsu ke ECU.", "Kunci kontak ON mesin mati menunjukkan tekanan mendekati 0 MPa (~0.5–1.0 V)."),
        ],
        [
            "1. Baca Live Data Fuel Rail Pressure saat kunci ON mesin mati (harus ~0 MPa).",
            "2. Periksa saluran pipa/selang return bahan bakar menuju tangki apakah tertekuk atau tersumbat.",
            "3. Periksa kerja katup SCV (Diesel) atau High-Pressure Fuel Regulator (GDI) dengan active test scanner.",
            "4. Cek soket & tegangan referensi 5V pada sensor FRP.",
        ],
        [
            {"parameter": "Fuel Rail Pressure (KOEO)", "normal_range": "0 – 1 MPa", "unit": "MPa"},
            {"parameter": "FRP Sensor Reference", "normal_range": "4.8 – 5.2 V", "unit": "Volt"},
        ],
    ),
    _dtc(
        "P0089",
        "Kinerja Regulator Tekanan Bahan Bakar / SCV Abnormal (Fuel Pressure Regulator 1 Performance)",
        "Bahan Bakar",
        ["Diesel", "Bensin"],
        "HIGH",
        "SCV (Suction Control Valve) aus/kotor oleh endapan bio-solar; Filter solar mampet; Kebocoran udara di jalur hisap solar; Regulator tekanan HPFP macet.",
        [
            _opt("Ganti SCV (Suction Control Valve) & Lakukan Supply Pump Learning", "Paling Terbukti", "UTAMA", "SCV sangat sensitif terhadap endapan parafin/air pada solar sehingga gerakan plunger tersendat.", "Idle halus tanpa pincang & nilai SCV current stabil."),
            _opt("Ganti Filter Solar & Kuras Tangki dari Endapan Air/Lumpur", "Pencegahan", "SEKUNDER", "Endapan kotoran akan kembali merusak SCV baru jika filter/tangki tidak dibersihkan.", "Solar keluar bersih tanpa air pada water sedimenter."),
        ],
        [
            "1. Periksa kondisi filter solar dan buang air dari water sedimenter.",
            "2. Monitor fluktuasi Fuel Rail Pressure saat idle (bila naik-turun tajam, SCV hampir pasti aus).",
            "3. Lepas & periksa plunger SCV dari goresan/kotoran; ganti dengan part OEM dan lakukan reset learning ECU.",
        ],
        [
            {"parameter": "Tahanan Coil SCV (20°C)", "normal_range": "1.8 – 3.5 Ohm", "unit": "Ohm"},
            {"parameter": "Fluktuasi Rail Idle", "normal_range": "< ±3 MPa", "unit": "MPa"},
        ],
    ),
    _dtc(
        "P0093",
        "Terdeteksi Kebocoran Besar Sistem Bahan Bakar Common-Rail (Fuel System Large Leak)",
        "Bahan Bakar",
        ["Diesel"],
        "CRITICAL",
        "Kebocoran eksternal pipa tekanan tinggi/selang solar; Injektor macet terbuka / bocor balik parah; Pressure Limiter Valve (PLV) membuka paksa; Filter solar kosong/masuk angin berat.",
        [
            _opt("Periksa Kebocoran Fisik Pipa High-Pressure, Rail & Selang Solar", "Keamanan Utama", "UTAMA", "Solar bertekanan tinggi sangat berbahaya — pastikan tidak ada rembesan di mur pipa rail/injektor.", "Seluruh sambungan kering & tidak ada tetesan saat mesin hidup."),
            _opt("Uji Backleak Injektor & Ganti Injektor / Seal Tembaga yang Bocor", "Penyebab Internal", "UTAMA", "Kebocoran internal injektor dibaca ECU sebagai 'Large Leak' karena tekanan rail langsung anjlok.", "Uji gelas ukur backleak normal & mesin tidak mati mendadak saat akselerasi."),
            _opt("Ganti Filter Solar & Periksa SCV / PLV", "Suplai Bahan Bakar", "SEKUNDER", "Filter solar mampet total juga dapat memicu P0093 akibat tekanan rail jatuh drastis.", "Tekanan rail mencapai target tanpa kode P0093 muncul kembali."),
        ],
        [
            "1. PERINGATAN: Jangan pernah meraba kebocoran pipa common-rail dengan tangan kosong saat mesin hidup!",
            "2. Inspeksi visual seluruh pipa besi rail, mur union injektor, dan filter solar.",
            "3. Lakukan uji backleak injektor common-rail untuk menemukan silinder yang bocor balik.",
            "4. Cek Pressure Limiter Valve (PLV) & ganti filter solar jika tersumbat.",
        ],
        [
            {"parameter": "Tekanan Rail Maksimum", "normal_range": "160 – 200 MPa", "unit": "MPa"},
            {"parameter": "Selisih Backleak Antar Silinder", "normal_range": "< 20%", "unit": "%"},
        ],
    ),
    _dtc(
        "P0299",
        "Tekanan Boost Turbo Terlalu Rendah (Turbocharger / Supercharger Underboost)",
        "Udara",
        ["Diesel", "Bensin"],
        "HIGH",
        "Selang intercooler / pipa intake turbo sobek atau klem lepas; Aktuator VNT / Wastegate macet berkerak karbon; Solenoid vakum VNT / Boost Control Valve rusak atau selang vakum bocor; Katup EGR macet terbuka; Filter udara tersumbat parah atau turbin turbo aus.",
        [
            _opt(
                "Periksa & Ganti Selang Intercooler / Pipa Intake Turbo yang Sobek atau Kendor",
                "Paling Sering & Murah",
                "UTAMA",
                "Selang karet intercooler bertekanan tinggi sering retak/sobek (ada bekas rembesan oli hitam) menyebabkan angin turbo bocor keluar.",
                "Tidak terdengar suara desis angin saat digas & Boost Pressure mencapai ≥ 180–220 kPa (absolut) saat akselerasi.",
            ),
            _opt(
                "Bersihkan / Perbaiki Aktuator VNT (Variable Nozzle Turbo) / Wastegate & Solenoid Vakum",
                "Khas 2GD / 4N15 / Turbo Bensin",
                "UTAMA",
                "Vane VNT yang berkerak jelaga atau solenoid boost control lemah membuat sudut turbin gagal membangun boost.",
                "Tuas aktuator VNT bergerak mulus penuh saat Active Test scanner tanpa tersendat.",
            ),
            _opt(
                "Bersihkan Katup EGR yang Macet Terbuka & Cek Sensor MAP / Boost Pressure",
                "Aliran Gas Buang",
                "SEKUNDER",
                "Katup EGR yang mengganjal terbuka membocorkan tekanan gas buang sebelum memutar turbin turbo.",
                "EGR menutup 0% saat beban penuh & bacaan sensor MAP saat kunci ON sama dengan tekanan atmosfer (~100 kPa).",
            ),
            _opt(
                "Periksa Sumbatan Katalis/DPF & Kerusakan Mekanis Cartridge Turbo",
                "Cek Lanjutan",
                "OPSIONAL",
                "Bilah kompresor aus/oblak atau knalpot DPF buntu menghambat putaran turbin turbo.",
                "As poros turbo tidak oblak berlebih & tidak ada oli banjir di dalam pipa intercooler.",
            ),
        ],
        [
            "1. Periksa fisik seluruh selang karet turbo-ke-intercooler-ke-intake (cari sobekan & bekas cipratan oli).",
            "2. Bandingkan Live Data Barometric Pressure (~100 kPa) vs MAP/Boost Pressure saat kunci ON & saat akselerasi.",
            "3. Periksa selang vakum kecil menuju solenoid turbo & gerakan tuas aktuator VNT / wastegate.",
            "4. Bersihkan sensor MAP/Boost dari kerak oli/jelaga EGR dan pastikan katup EGR tidak macet terbuka.",
            "5. Jika semua jalur kedap, periksa keausan poros cartridge turbo dan hambatan knalpot/DPF.",
        ],
        [
            {"parameter": "Boost / MAP (KOEO / Atmosfer)", "normal_range": "98 – 102 kPa", "unit": "kPa abs"},
            {"parameter": "Boost Pressure (Beban Penuh)", "normal_range": "180 – 250 kPa", "unit": "kPa abs"},
            {"parameter": "Relative Boost (Gauge)", "normal_range": "0.8 – 1.5 Bar", "unit": "Bar"},
        ],
    ),
    _dtc(
        "P0234",
        "Tekanan Boost Turbo Berlebih (Turbocharger Overboost Condition)",
        "Udara",
        ["Diesel", "Bensin"],
        "HIGH",
        "Mekanisme VNT / Wastegate macet pada posisi boost tinggi akibat kerak jelaga; Solenoid Boost Control / Vacuum Modulator rusak; Sensor Boost/MAP error; Remap ECU terlalu agresif.",
        [
            _opt("Bersihkan Kerak VNT / Wastegate Turbo & Pastikan Tuas Aktuator Bebas Macet", "Penyebab Utama", "UTAMA", "Jelaga karbon mengunci vane VNT sehingga tekanan turbo melampaui batas aman dan masuk Limp Mode.", "Boost pressure tidak melampaui target ECU saat akselerasi penuh."),
            _opt("Ganti Boost Control Solenoid / Cek Selang Vakum Wastegate", "Kontrol Aktuator", "SEKUNDER", "Solenoid yang macet atau selang wastegate lepas membuat wastegate gagal membuka.", "Active test solenoid merespons normal & tahanan coil sesuai spesifikasi."),
            _opt("Bersihkan / Ganti Sensor MAP / Boost Pressure", "Sensor", "OPSIONAL", "Sensor boost berkerak dapat mengirim sinyal tekanan berlebih palsu.", "Pembacaan tekanan atmosfer akurat ~100 kPa."),
        ],
        [
            "1. Lakukan uji gerak tuas VNT / wastegate (harus bergerak ringan tanpa tersangkut).",
            "2. Cek selang vakum/tekanan yang mengarah ke aktuator wastegate dan solenoid kontrol boost.",
            "3. Bersihkan sensor MAP/Boost & pantau Target vs Actual Boost di jalan.",
        ],
        [
            {"parameter": "Target vs Actual Boost", "normal_range": "Selisih < 20 kPa", "unit": "kPa"},
        ],
    ),
    _dtc(
        "P0401",
        "Aliran Gas Buang EGR Tidak Mencukupi (Exhaust Gas Recirculation Flow Insufficient)",
        "Emisi",
        ["Diesel", "Bensin"],
        "MEDIUM",
        "Katup EGR & saluran intake manifold mampet penuh kerak jelaga/oli; Motor/solenoid EGR Valve macet; EGR Cooler buntu; Sensor MAF/MAP kotor sehingga ECU membaca aliran EGR tidak berubah.",
        [
            _opt("Bersihkan Katup EGR, Pipa EGR & Intake Manifold dari Kerak Jelaga Karbon", "Paling Sering di Diesel", "UTAMA", "Gabungan jelaga knalpot dan uap oli PCV membentuk kerak tebal yang menyumbat saluran EGR pada 40.000+ km.", "Katup EGR membuka-menutup lancar & penurunan nilai MAF terdeteksi saat EGR diperintahkan aktif."),
            _opt("Periksa / Ganti Motor Katup EGR & Bersihkan Sensor MAF/MAP", "Aktuator & Sensor", "SEKUNDER", "Gear plastik/motor EGR yang aus gagal membuka katup sesuai perintah ECU.", "Posisi EGR Aktual mengikuti Target EGR (%) pada Live Data."),
        ],
        [
            "1. Lepas katup EGR dan periksa penumpukan kerak jelaga pada katup, pipa, dan intake manifold.",
            "2. Bersihkan kerak karbon secara menyeluruh (termasuk EGR cooler bila mampet).",
            "3. Lakukan Active Test EGR Valve dengan scanner sambil memantau posisi feedback sensor EGR dan nilai MAF.",
        ],
        [
            {"parameter": "EGR Valve Position (Idle Hangat)", "normal_range": "15 – 45 %", "unit": "%"},
            {"parameter": "EGR Valve Position (Full Load)", "normal_range": "0 % (Tertutup)", "unit": "%"},
        ],
    ),
    _dtc(
        "P0400",
        "Malfungsi Aliran Sistem EGR (Exhaust Gas Recirculation Flow Malfunction)",
        "Emisi",
        ["Diesel", "Bensin"],
        "MEDIUM",
        "Katup EGR macet terbuka/tertutup oleh kerak karbon; Solenoid vakum EGR bocor; Sensor posisi EGR atau MAF bermasalah.",
        [
            _opt("Bongkar & Bersihkan Katup EGR + Saluran Intake", "Utama", "UTAMA", "Kerak jelaga menghambat buka-tutup katup EGR.", "Pergerakan EGR lancar & idle stabil."),
            _opt("Ganti EGR Valve / Perbaiki Soket Kabel EGR", "Komponen", "SEKUNDER", "Motor penggerak atau sensor posisi internal EGR rusak.", "Tidak ada DTC EGR kembali setelah test drive."),
        ],
        ["1. Bersihkan katup & saluran EGR.", "2. Cek soket, tegangan suplai, & active test katup EGR."],
        [{"parameter": "Target vs Actual EGR", "normal_range": "Selisih < 5%", "unit": "%"}],
    ),
    _dtc(
        "P062D",
        "Malfungsi Sirkuit Driver Injektor Bahan Bakar (Fuel Injector Driver / EDU Circuit — Bank 1)",
        "Kelistrikan",
        ["Diesel"],
        "CRITICAL",
        "Modul EDU (Electronic Driver Unit) injektor rusak/kemasukan air; Kabel harness injektor konslet ke massa atau putus; Coil/piezo salah satu injektor short-circuit; Sekering/relay EDU bermasalah.",
        [
            _opt("Ukur Tahanan Seluruh Injektor & Periksa Kabel Harness Injektor dari Konslet", "Cek Pertama (Wajib!)", "UTAMA", "Satu injektor yang short atau kabel terkelupas dapat memutus kerja modul EDU (mesin mati total / pincang berat).", "Tahanan tiap injektor seragam (~0.5–1.5 Ohm solenoid / ~180–200 kOhm piezo) & tidak short ke ground."),
            _opt("Periksa Sekering, Relay, Ground & Ganti Modul EDU (Injector Driver)", "Khas Toyota 2KD / 2GD / Diesel", "UTAMA", "EDU menaikkan tegangan ~80–120V untuk membuka injektor diesel; modul EDU yang rusak membuat mesin tidak mau hidup.", "Suplai +12V & ground EDU normal; mesin hidup normal tanpa misfire."),
        ],
        [
            "1. PERINGATAN: Sirkuit injektor diesel bertegangan tinggi (~85–150V pulsa) — matikan kunci kontak sebelum melepas soket!",
            "2. Cek sekering & relay INJ/EDU serta massa bodi modul EDU.",
            "3. Ukur tahanan tiap injektor dan cek isolasi kabel harness terhadap massa mesin.",
            "4. Jika injektor & kabel normal, uji dengan modul EDU cadangan yang sehat.",
        ],
        [
            {"parameter": "Tahanan Injektor Solenoid Diesel", "normal_range": "0.5 – 2.0 Ohm", "unit": "Ohm"},
            {"parameter": "Isolasi Kabel ke Ground", "normal_range": "> 10 MOhm (OL)", "unit": "Ohm"},
        ],
    ),
    _dtc(
        "P1229",
        "Kelebihan Suplai Pompa Bahan Bakar (Fuel Pump System Overfeed — Toyota Diesel)",
        "Bahan Bakar",
        ["Diesel"],
        "HIGH",
        "SCV (Suction Control Valve) macet terbuka; Sirkuit kabel SCV short ke ground; Tekanan rail terlalu tinggi akibat sumbatan jalur return.",
        [
            _opt("Ganti SCV (Suction Control Valve) & Lakukan Reset Supply Pump Learning", "Penyebab Utama", "UTAMA", "SCV yang macet menyebabkan supply pump memompa debit berlebih ke common-rail.", "Tekanan rail stabil sesuai target di seluruh putaran mesin."),
            _opt("Periksa Kabel SCV dari Konslet ke Massa & Jalur Return Solar", "Kelistrikan & Pipa", "SEKUNDER", "Kabel SCV konslet membuat arus penuh terus mengalir membuka katup.", "Tahanan kabel baik & selang return lancar."),
        ],
        [
            "1. Cek kabel konektor SCV terhadap short-to-ground.",
            "2. Pantau Fuel Rail Pressure & SCV target current saat idle.",
            "3. Ganti SCV dan lakukan kalibrasi Supply Pump Initialization dengan scanner.",
        ],
        [{"parameter": "Tekanan Rail Idle", "normal_range": "30 – 45 MPa", "unit": "MPa"}],
    ),
    _dtc(
        "P1604",
        "Kesulitan Start Mesin (Startability Malfunction — Toyota)",
        "Bahan Bakar",
        ["Diesel", "Bensin"],
        "HIGH",
        "Tekanan bahan bakar/rail lambat naik saat cranking (filter solar/pompa/SCV/injektor bocor); Aki lemah / putaran starter terlalu lambat (< 200 RPM); Masuk angin di saluran solar; Sensor CKP/CMP atau busi/koil bermasalah.",
        [
            _opt("Cek Kecepatan Cranking Starter, Kondisi Aki & Filter Solar / Masuk Angin", "Cek Paling Cepat", "UTAMA", "Putaran cranking di bawah 200 RPM atau solar turun/masuk angin membuat mesin butuh starter panjang.", "Tegangan cranking ≥ 10.5V, RPM cranking ≥ 220 RPM, mesin langsung hidup < 2 detik."),
            _opt("Periksa Tekanan Fuel Rail saat Cranking, SCV & Tes Backleak Injektor", "Khusus Diesel Common-Rail", "UTAMA", "Jika tekanan rail saat cranking < 20 MPa, ECU menahan penyemprotan injektor.", "Tekanan rail mencapai ≥ 25 MPa dalam 1–2 detik starter."),
            _opt("Periksa Busi, Koil, Tekanan Fuel Pump & Throttle Body (Khusus Bensin)", "Khusus Bensin", "SEKUNDER", "Pada bensin 1TR-FE / NR-series, fuel pump lemah atau throttle kotor menyebabkan start panjang.", "Tekanan bensin ~3.0–3.5 bar stabil & mesin mudah hidup."),
        ],
        [
            "1. Cek tegangan aki saat starter (minimal 10.5V) dan kecepatan putaran starter (minimal 200 RPM).",
            "2. Baca Live Data tekanan rail (Diesel) atau ukur fuel pressure gauge (Bensin) saat cranking.",
            "3. Periksa filter solar/bensin, priming pump, dan kebocoran balik injektor.",
        ],
        [
            {"parameter": "Tegangan Aki saat Cranking", "normal_range": "≥ 10.5 V", "unit": "Volt"},
            {"parameter": "Kecepatan Cranking", "normal_range": "≥ 200 RPM", "unit": "RPM"},
        ],
    ),
    _dtc(
        "P2002",
        "Efisiensi Filter Partikulat Diesel di Bawah Ambang (DPF Efficiency Below Threshold)",
        "Emisi",
        ["Diesel"],
        "HIGH",
        "DPF tersumbat jelaga (soot) akibat sering jalan jarak pendek / solar kualitas rendah; Sensor Differential Pressure DPF atau selang karetnya retak/tersumbat; Proses regenerasi DPF gagal; Injektor bocor menghasilkan asap hitam berlebih.",
        [
            _opt("Lakukan Regenerasi Paksa (Forced DPF Regeneration) & Cek Sensor Tekanan DPF", "Tindakan Standar", "UTAMA", "Membakar timbunan jelaga di dalam DPF sesuai prosedur scanner setelah memastikan oli mesin tidak encer/over-level.", "DPF Differential Pressure < 2–3 kPa saat idle & lampu DPF padam."),
            _opt("Bongkar & Cuci (Cleaning) DPF + Ganti Oli Mesin Spesifikasi Low-SAPS (DL-1 / ACEA C3)", "Sumbatan Berat", "SEKUNDER", "Jika jelaga abu (ash) sudah penuh, forced regen tidak cukup dan DPF perlu dibersihkan fisik.", "Aliran gas buang lancar & tenaga kembali normal."),
        ],
        [
            "1. Cek level oli mesin (jangan lakukan forced regen bila oli naik tinggi tercampur solar!).",
            "2. Periksa selang karet menuju DPF Differential Pressure Sensor apakah sobek/mampet.",
            "3. Baca nilai PM Accumulation (%) & Differential Pressure, lalu jalankan DPF Regeneration di ruang terbuka.",
        ],
        [
            {"parameter": "DPF Diff Pressure (Idle)", "normal_range": "0.5 – 2.5 kPa", "unit": "kPa"},
            {"parameter": "Oli Mesin DPF", "normal_range": "Low-SAPS (ACEA C2/C3 / DL-1)", "unit": "Spec"},
        ],
    ),
    _dtc(
        "P0380",
        "Malfungsi Sirkuit Busi Pemanas Diesel (Glow Plug / Heater Circuit A)",
        "Kelistrikan",
        ["Diesel"],
        "MEDIUM",
        "Satu atau lebih busi pemanas (glow plug) putus; Relay glow plug rusak; Sekering utama glow plug putus; Kabel busbar glow plug berkarat/kendor.",
        [
            _opt("Ukur Tahanan Tiap Glow Plug & Ganti Glow Plug yang Putus", "Penyebab Utama", "UTAMA", "Glow plug yang putus membuat mesin diesel susah hidup di pagi hari / dingin dan memicu asap putih awal start.", "Tahanan tiap glow plug 0.5 – 2.0 Ohm."),
            _opt("Periksa Relay Glow Plug, Sekering & Konektor Busbar", "Kelistrikan", "SEKUNDER", "Relay glow plug rusak membuat tegangan +12V tidak sampai ke glow plug saat kunci ON.", "Tegangan +12V hadir di busbar glow plug selama 3–10 detik saat kunci ON mesin dingin."),
        ],
        [
            "1. Lepas rel penghubung (busbar) glow plug dan ukur tahanan tiap glow plug terhadap massa mesin.",
            "2. Cek sekering besar & relay glow plug saat kunci kontak diputar ON.",
        ],
        [{"parameter": "Tahanan Glow Plug", "normal_range": "0.5 – 2.0 Ohm", "unit": "Ohm"}],
    ),

    # ==================== VVT / VANOS / TIMING / GDI TURBO ====================
    _dtc(
        "P0011",
        "Posisi Camshaft Intake Terlalu Maju / Kinerja VVT-i / VANOS (Bank 1 Over-Advanced)",
        "Mekanis",
        ["Bensin", "Hybrid"],
        "HIGH",
        "Oli mesin kotor / berlumpur / viskositas salah; Solenoid OCV (Oil Control Valve) / VANOS macet atau saringan kasa tersumbat; Rantai timing melar / loncat gigi; VVT Camshaft Gear / Actuator aus.",
        [
            _opt("Ganti Oli Mesin + Bersihkan/Ganti Solenoid OCV (VVT-i / VANOS) & Filter Kasa Oli", "Paling Sering & Efektif", "UTAMA", "Lumpur oli menyumbat filter mikro OCV dan membuat plunger solenoid VVT/VANOS macet.", "Active test OCV membuat mesin langsung tersendat/mati & sudut Cam Actual mengikuti Target (< ±3°)."),
            _opt("Periksa Ketegangan Rantai Timing, Tensioner & Tanda Top Timing", "Cek Mekanis", "SEKUNDER", "Rantai keteng melar atau tensioner lemah menggeser sinkronisasi camshaft.", "Tanda top CKP & CMP lurus presisi."),
            _opt("Ganti Camshaft VVT Actuator / VANOS Gear & Cek Tekanan Oli", "Kerusakan Komponen", "OPSIONAL", "Pin pengunci di dalam gigi VVT aus (sering disertai bunyi kasar 'krak' 1 detik saat start pagi).", "Bunyi kasar hilang & sudut camshaft stabil."),
        ],
        [
            "1. Periksa level dan kebersihan oli mesin (pastikan tidak ada sludge dan sesuai SAE anjuran pabrikan).",
            "2. Lepas solenoid OCV / VANOS Intake, bersihkan filter kasa, dan uji klik solenoid dengan 12V.",
            "3. Pantau Live Data Camshaft Intake Target vs Actual Angle saat digas 2000–3000 RPM.",
            "4. Jika OCV sehat namun sudut tetap meleset, periksa rantai timing, tensioner, dan gear VVT.",
        ],
        [
            {"parameter": "Tahanan Solenoid OCV / VANOS", "normal_range": "6.5 – 12.0 Ohm", "unit": "Ohm"},
            {"parameter": "Selisih Sudut Cam Target vs Aktual", "normal_range": "< ±3.0 °", "unit": "Derajat"},
        ],
    ),
    _dtc(
        "P0012",
        "Posisi Camshaft Intake Terlalu Mundur / VVT-i / VANOS Lambat (Bank 1 Over-Retarded)",
        "Mekanis",
        ["Bensin", "Hybrid"],
        "HIGH",
        "Tekanan oli kurang / oli kental berlumpur; Solenoid OCV / VANOS Intake macet; Saringan oli OCV tersumbat; Rantai timing melar; Gear VVT-i / VANOS aus.",
        [
            _opt("Bersihkan/Ganti Solenoid OCV Intake, Saringan OCV & Ganti Oli Mesin Berkualitas", "Penyebab Utama", "UTAMA", "Tekanan oli tidak mampu mendorong gear VVT maju saat akselerasi.", "Sudut camshaft intake merespons cepat mengikuti target ECU."),
            _opt("Cek Tekanan Oli Mesin & Ketegangan Rantai Timing / Tensioner", "Cek Mekanis", "SEKUNDER", "Rantai keteng yang melar memundurkan posisi camshaft.", "Tekanan oli idle ≥ 1.0 Bar & tanda timing akurat."),
        ],
        [
            "1. Cek level & kualitas oli mesin serta bersihkan saringan kasa OCV.",
            "2. Uji kerja solenoid OCV Intake dan ukur tahanannya.",
            "3. Periksa posisi timing rantai/belt serta tekanan oli pelumas.",
        ],
        [{"parameter": "Tahanan OCV", "normal_range": "6.5 – 12.0 Ohm", "unit": "Ohm"}],
    ),
    _dtc(
        "P0014",
        "Posisi Camshaft Exhaust Terlalu Maju / Dual VVT-i / VANOS (Bank 1 B Over-Advanced)",
        "Mekanis",
        ["Bensin", "Hybrid"],
        "HIGH",
        "Solenoid OCV / VANOS sisi Exhaust (Bank 1 B) kotor/macet; Oli mesin berlumpur; Sensor posisi Camshaft Exhaust error; Gear VANOS/VVT Exhaust atau rantai timing bergeser.",
        [
            _opt("Bersihkan / Ganti Solenoid OCV / VANOS Exhaust & Ganti Oli Mesin", "Penyebab Utama", "UTAMA", "Sangat sering terjadi pada BMW N20/N46, Mercy M271/M274, Toyota Dual VVT-i (1TR-FE/2NR-VE), dan Hyundai/Kia.", "Sudut Exhaust Camshaft sinkron dengan target ECU & idle halus."),
            _opt("Periksa Sensor Camshaft Exhaust & Tanda Timing Rantai", "Cek Lanjutan", "SEKUNDER", "Sensor CMP Exhaust lemah atau timing rantai melar memicu kode P0014.", "Sinyal CMP bersih & timing chain kencang."),
        ],
        [
            "1. Cek kualitas oli mesin & lepas solenoid OCV/VANOS Exhaust untuk dibersihkan atau diganti.",
            "2. Tukar posisi solenoid Intake <-> Exhaust (bila tipe sama) untuk memastikan kerusakan berpindah kode ke P0011.",
            "3. Cek rantai timing & gear VVT Exhaust jika solenoid sudah sehat.",
        ],
        [{"parameter": "Tahanan Solenoid OCV/VANOS", "normal_range": "6.5 – 12.0 Ohm", "unit": "Ohm"}],
    ),
    _dtc(
        "P0015",
        "Posisi Camshaft Exhaust Terlalu Mundur / Dual VVT-i / VANOS (Bank 1 B Over-Retarded)",
        "Mekanis",
        ["Bensin", "Hybrid"],
        "HIGH",
        "Solenoid VANOS / OCV Exhaust (Bank 1 B) macet atau saringan oli tersumbat; Lumpur oli & tekanan oli kurang; Gear VANOS / VVT Exhaust aus; Rantai timing melar (khas BMW N20/N46, Mercy M271, Toyota Dual VVT-i).",
        [
            _opt(
                "Bersihkan / Ganti Solenoid VANOS / OCV Exhaust & Cek Filter Oli (Ganti Oli Sesuai Spec)",
                "Paling Sering (BMW / Mercy / Toyota Dual VVT)",
                "UTAMA",
                "Solenoid Exhaust yang macet oleh kerak oli adalah penyebab #1 P0015 dan pesan 'Drivetrain Malfunction' pada BMW.",
                "Tukar sementara solenoid Exhaust <-> Intake untuk verifikasi; sudut Camshaft Exhaust mengikuti target < ±3°.",
            ),
            _opt(
                "Periksa Tahanan & Sinyal Sensor Camshaft Exhaust (CMP B) + Kabel Konektor",
                "Sensor & Wiring",
                "SEKUNDER",
                "Remebesan oli ke soket sensor CMP atau sensor melemah saat panas menyebabkan pembacaan sudut melenceng.",
                "Konektor kering dari oli & sinyal CMP terbaca stabil di scanner.",
            ),
            _opt(
                "Periksa Rantai Timing, Guide Tensioner & Sprocket Cam Adjuster (VANOS / VVT Gear)",
                "Mekanis Berat",
                "OPSIONAL",
                "Pada BMW N20/N46 dan Mercy M271, guide rantai timing retak atau cam adjuster gear aus memicu P0015/P0017.",
                "Tanda top timing tepat & tidak ada bunyi ketukan rantai saat start dingin.",
            ),
        ],
        [
            "1. Periksa kondisi oli, filter oli (pastikan keranjang/insert tutup filter oli BMW tidak hilang!), dan level oli.",
            "2. Lepas solenoid VANOS/OCV sisi Exhaust, cek serpihan/sludge, bersihkan atau tukar uji dengan sisi Intake.",
            "3. Pantau Live Data Exhaust Camshaft Actual vs Target saat idle dan 2500 RPM.",
            "4. Cek kekencangan rantai timing & sprocket cam adjuster jika DTC tetap menetap.",
        ],
        [
            {"parameter": "Tahanan Solenoid VANOS/OCV", "normal_range": "6.5 – 12.0 Ohm", "unit": "Ohm"},
            {"parameter": "Selisih Sudut Cam Exhaust", "normal_range": "< ±3.0 °", "unit": "Derajat"},
        ],
    ),
    _dtc(
        "P0016",
        "Korelasi Posisi Crankshaft – Camshaft Intake Tidak Sinkron (CKP–CMP Bank 1 A)",
        "Mekanis",
        ["All"],
        "CRITICAL",
        "Rantai/sabuk timing melar atau loncat gigi; Tensioner rantai timing lemah; Sprocket VVT/Cam Adjuster rusak (pin pengunci patah); Sensor CKP/CMP atau reluctor ring bermasalah.",
        [
            _opt("Periksa Fisik Tanda Top Timing Rantai/Belt & Tensioner (Segera — Risiko Tabrakan Klep!)", "Prioritas Kritis", "UTAMA", "Timing yang loncat atau rantai melar melampaui toleransi ECU memicu P0016 dan berisiko membengkokkan klep.", "Seluruh tanda top CKP dan CMP lurus 100% dan rantai kencang."),
            _opt("Periksa Sprocket VVT / Cam Adjuster & Solenoid OCV", "Aktuator Timing", "SEKUNDER", "Pin pengunci gear VVT yang aus membuat posisi camshaft bergeser saat start.", "Tidak ada free-play berlebih pada gear VVT saat posisi terkunci."),
        ],
        [
            "1. JANGAN paksa memacu mesin pada RPM tinggi sebelum timing diperiksa!",
            "2. Cek riwayat pergantian oli & bunyi rantai berisik saat start dingin.",
            "3. Buka cover timing untuk verifikasi kelurusan tanda top CKP–CMP serta panjang tonjolan tensioner.",
            "4. Jika timing mekanis 100% tepat, periksa sinyal gelombang CKP vs CMP dengan osiloskop.",
        ],
        [{"parameter": "Sinkronisasi CKP–CMP", "normal_range": "0° Pergeseran Mekanis", "unit": "Derajat"}],
    ),
    _dtc(
        "P0017",
        "Korelasi Posisi Crankshaft – Camshaft Exhaust Tidak Sinkron (CKP–CMP Bank 1 B)",
        "Mekanis",
        ["All"],
        "CRITICAL",
        "Rantai timing melar/loncat pada sisi camshaft Exhaust; Sprocket Cam Adjuster Exhaust rusak (sangat khas Mercy M271/M274, Toyota Dual VVT-i, BMW); Solenoid OCV Exhaust macet total.",
        [
            _opt("Verifikasi Tanda Top Timing Rantai & Kondisi Sprocket Cam Adjuster Exhaust", "Prioritas Kritis", "UTAMA", "Ketidaksinkronan CKP–CMP Exhaust hampir selalu berasal dari rantai melar atau gigi cam adjuster aus.", "Tanda timing tepat & P0017 tidak muncul lagi saat start dingin."),
            _opt("Periksa Solenoid OCV Exhaust & Sensor CMP Exhaust", "Pendukung", "SEKUNDER", "Solenoid yang macet ekstrem kadang menggeser fase camshaft saat start.", "Sinyal CMP & kerja OCV normal."),
        ],
        [
            "1. Cek tanda top timing dan kondisi guide/tensioner rantai keteng.",
            "2. Cek penguncian sprocket camshaft Exhaust & kebersihan solenoid OCV Exhaust.",
        ],
        [{"parameter": "Sinkronisasi CKP–CMP Exhaust", "normal_range": "0° Pergeseran Mekanis", "unit": "Derajat"}],
    ),
    _dtc(
        "P0191",
        "Kinerja / Rentang Sensor Tekanan Fuel Rail Abnormal (Fuel Rail Pressure Sensor Range — GDI/Diesel)",
        "Bahan Bakar",
        ["Diesel", "Bensin"],
        "HIGH",
        "Sensor Fuel Rail Pressure (FRP) melenceng; High Pressure Fuel Pump (HPFP) lemah (khas Peugeot EP6 THP, BMW N20/B48, VW TSI, Chery TGDI, Diesel Common-Rail); Low-pressure fuel pump di tangki drop; Soket sensor FRP korosi.",
        [
            _opt("Cek Tekanan Pompa Tangki (Low Pressure) & Kinerja HPFP (High Pressure Pump)", "Penyebab Utama GDI/Diesel", "UTAMA", "Jika suplai pompa tangki lemah (< 3–4 bar) atau HPFP aus, tekanan rail gagal memenuhi target ECU.", "Low pressure 3.5–5 bar stabil & rail pressure mengikuti target."),
            _opt("Periksa Tegangan & Ganti Sensor Fuel Rail Pressure (FRP)", "Sensor Error", "SEKUNDER", "Sensor FRP yang bergeser membaca tekanan tinggi/rendah tidak wajar saat kunci ON.", "Pembacaan sensor saat kunci ON mesin mati sesuai tekanan sisa normal."),
        ],
        [
            "1. Cek tekanan pompa bensin/solar di tangki (low-pressure side) terlebih dahulu.",
            "2. Baca Live Data Target vs Actual Rail Pressure saat idle dan akselerasi.",
            "3. Periksa soket & tegangan referensi 5V sensor FRP.",
        ],
        [
            {"parameter": "Low-Pressure Pump (GDI)", "normal_range": "3.5 – 5.5 Bar", "unit": "Bar"},
            {"parameter": "High-Pressure Rail (GDI Idle)", "normal_range": "3.5 – 6.0 MPa", "unit": "MPa"},
        ],
    ),
    _dtc(
        "P2177",
        "Campuran Terlalu Kurus di Atas Idle (System Too Lean Off Idle — Bank 1)",
        "Bahan Bakar",
        ["Bensin", "Hybrid"],
        "HIGH",
        "Kebocoran vakum/angin setelah MAF (selang turbo/PCV membran sobek — sangat khas VW/Audi/BMW/Wuling Turbo); Sensor MAF kotor; Tekanan pompa bahan bakar/HPFP lemah saat beban; Injektor kotor.",
        [
            _opt("Uji Kebocoran Udara (Smoke Test), Cek Membran PCV & Selang Intake/Turbo", "Paling Sering Eropa & Turbo", "UTAMA", "Membran PCV sobek atau selang intake bocor memasukkan udara liar sehingga LTFT melambung > +15%.", "LTFT & STFT kembali turun ke kisaran -7% s/d +7%."),
            _opt("Bersihkan Sensor MAF & Periksa Tekanan Pompa Bahan Bakar saat Digas", "Suplai & Sensor", "SEKUNDER", "MAF kotor membaca udara lebih sedikit dari aktual, atau pompa bensin drop di putaran menengah.", "Nilai MAF idle normal (~2–4 g/s) & fuel pressure stabil saat beban."),
        ],
        [
            "1. Pantau STFT & LTFT saat idle vs 2500 RPM (jika memburuk saat digas, curigai suplai BBM/MAF; jika memburuk saat idle, curigai bocor vakum/PCV).",
            "2. Periksa kebocoran selang intake, katup PCV, dan selang intercooler.",
            "3. Bersihkan MAF dan ukur tekanan pompa bensin.",
        ],
        [{"parameter": "Total Fuel Trim (STFT+LTFT)", "normal_range": "-10% s/d +10%", "unit": "%"}],
    ),
    _dtc(
        "P2178",
        "Campuran Terlalu Kaya di Atas Idle (System Too Rich Off Idle — Bank 1)",
        "Bahan Bakar",
        ["Bensin", "Hybrid"],
        "HIGH",
        "Seal HPFP bocor (bensin masuk ke oli mesin — khas GDI/Turbo!); Injektor bocor; Katup EVAP Purge macet terbuka; Selang boost turbo bocor (udara terukur MAF keluar sebelum masuk silinder); Sensor O2/AFR melenceng.",
        [
            _opt("Periksa Kebocoran Selang Turbo/Intercooler, Katup EVAP Purge & Bau Bensin di Oli (HPFP)", "Khas GDI & Turbo", "UTAMA", "Pada mesin turbo/GDI, kebocoran pipa boost atau seal HPFP bocor membuat ECU menyemprot bensin berlebih (LTFT < -15%).", "Oli tidak bau bensin, jalur boost kedap, & LTFT kembali normal."),
            _opt("Uji Kebocoran Injektor & Pembacaan Sensor O2/AFR Bank 1 Sensor 1", "Injektor & Sensor", "SEKUNDER", "Injektor menetes atau sensor O2 rusak memicu campuran terlalu kaya.", "Fuel trim stabil dalam ±10%."),
        ],
        [
            "1. Cek dipstick oli mesin — bila level naik & berbau bensin tajam, periksa kebocoran seal HPFP!",
            "2. Periksa katup EVAP Purge (tidak boleh lolos tiupan saat tidak diberi tegangan).",
            "3. Cek kebocoran selang intercooler/turbo dan tes injektor.",
        ],
        [{"parameter": "Total Fuel Trim", "normal_range": "-10% s/d +10%", "unit": "%"}],
    ),
    _dtc(
        "P2279",
        "Terdeteksi Kebocoran Sistem Udara Intake (Intake Air System Leak)",
        "Udara",
        ["Bensin", "Diesel", "Hybrid"],
        "MEDIUM",
        "Selang intake/intercooler robek; Katup PCV / oil separator rusak; Paking throttle body atau intake manifold bocor; Tutup pengisian oli / dipstick tidak rapat (khas mesin Eropa!).",
        [
            _opt("Cek Selang Intake/Turbo, Tutup Oli, Dipstick & Membran PCV (Lakukan Smoke Test)", "Paling Cepat", "UTAMA", "Udara tak terukur masuk melewati kebocoran menyebabkan idle goyang dan campuran kurus.", "Tidak ada kebocoran asap & nilai vakum/MAF kembali normal."),
        ],
        [
            "1. Cek kerapatan tutup oli mesin, dipstick, dan semua klem pipa udara.",
            "2. Lakukan smoke test di jalur intake untuk menemukan retakan halus selang atau paking manifold.",
        ],
        [{"parameter": "MAP Idle (Bensin NA)", "normal_range": "26 – 35 kPa", "unit": "kPa"}],
    ),

    # ==================== HYBRID & EV (HIGH-VOLTAGE) ====================
    _dtc(
        "P0A80",
        "Penurunan Performa / Ganti Paket Baterai Tegangan Tinggi (Replace Hybrid / EV Battery Pack)",
        "Kelistrikan",
        ["EV", "Hybrid"],
        "CRITICAL",
        "Selisih tegangan antar blok/sel baterai HV melampaui batas (Cell Imbalance > 0.3V–1.2V); Satu atau lebih modul sel baterai lemah/drop; Busbar penghubung antar sel korosi; Kipas pendingin baterai HV tersumbat debu sehingga sel kepanasan.",
        [
            _opt(
                "WAJIB APD HV 1000V: Baca Tegangan Setiap Blok/Sel Baterai HV & Cek Delta Tegangan (Imbalance)",
                "Diagnosa Wajib Pertama",
                "UTAMA",
                "Kode P0A80 muncul karena blok sel tertentu drop jauh lebih cepat saat beban akselerasi dibanding sel lain.",
                "Teridentifikasi blok sel mana yang lemah (selisih tegangan antar blok sehat < 0.05–0.10 V).",
            ),
            _opt(
                "Bersihkan Kipas Pendingin Baterai HV, Filter Udara Baterai & Cek Korosi Busbar / Kabel Sensor Tegangan",
                "Cek Pendukung & Sering Terlewat",
                "SEKUNDER",
                "Debu pada filter kipas baterai Hybrid/EV menyebabkan overheat sel, dan korosi busbar tembaga memicu pembacaan tegangan drop palsu.",
                "Suhu semua sensor baterai merata (< 40°C) & seluruh sambungan busbar bersih tanpa oksidasi.",
            ),
            _opt(
                "Rekondisi / Ganti Modul Sel Lemah (Balancing) atau Ganti Paket Baterai HV",
                "Solusi Permanen",
                "UTAMA",
                "Penggantian modul sel yang rusak (atau 1 paket baterai HV) + cell balancing memulihkan kapasitas & menghilangkan P0A80.",
                "Delta tegangan sel saat beban penuh < 0.15 V dan lampu peringatan sistem Hybrid/EV padam.",
            ),
        ],
        [
            "1. PERINGATAN KESELAMATAN HV (200V–400V DC): Kenakan sarung tangan isolasi 1000V (Class 0), lepas perhiasan logam, & cabut Service Plug sebelum membuka penutup baterai HV!",
            "2. Baca Live Data BMS: Tegangan tiap blok/sel (Vmin vs Vmax), State of Charge (SoC), dan suhu baterai.",
            "3. Periksa filter & putaran kipas pendingin (atau sistem cairan pendingin) baterai HV.",
            "4. Inspeksi busbar penghubung sel dan konektor voltage-sensing BMS dari korosi hijau.",
            "5. Lakukan penggantian/balancing modul sel yang drop atau ganti assembly baterai HV sesuai hasil ukur.",
        ],
        [
            {"parameter": "Selisih Tegangan Sel (Delta V Normal)", "normal_range": "< 50 mV (0.05 V)", "unit": "mV"},
            {"parameter": "Batas Kritis Cell Imbalance", "normal_range": "> 200 – 300 mV", "unit": "mV"},
            {"parameter": "Tahanan Isolasi HV Minimal", "normal_range": "> 10 MOhm", "unit": "MOhm"},
        ],
        requires_hv_safety=True,
    ),
    _dtc(
        "P0AA6",
        "Kebocoran Isolasi Sistem Tegangan Tinggi (Hybrid/EV Battery Voltage System Isolation Fault)",
        "Kelistrikan",
        ["EV", "Hybrid"],
        "CRITICAL",
        "Kebocoran arus tegangan tinggi ke bodi/sasis (tahanan isolasi drop) akibat: Air/embun masuk ke baterai HV atau konektor oranye; Kompresor AC listrik (HV) bocor isolasi; Inverter / Motor traksi atau kabel HV lecet; Kebocoran elektrolit modul baterai.",
        [
            _opt(
                "STOP — BAHAYA SENGATAN LISTRIK: Uji Tahanan Isolasi (Megger 500V) per Cabang HV (Kompresor AC, Inverter, Baterai)",
                "Prosedur Wajib HV",
                "UTAMA",
                "Kompresor AC listrik HV yang kemasukan oli salah (non-POE / pakai oli PAG!) adalah penyebab PALING SERING P0AA6 di bengkel!",
                "Tahanan isolasi ke sasis > 10 MOhm pada semua cabang HV.",
            ),
            _opt(
                "Periksa Konektor Kabel Oranye HV, Area Genangan Air/Banjir & Oli Kompresor AC (Wajib POE/ND-11)",
                "Penyebab Lapangan #1",
                "UTAMA",
                "Pengisian oli kompresor AC bensin biasa (PAG yang bersifat konduktif) langsung merusak isolasi gulungan kompresor AC listrik Hybrid/EV.",
                "Konektor kering, kompresor AC terisolasi > 10 MOhm, kode P0AA6 hilang & mobil bisa masuk mode READY.",
            ),
        ],
        [
            "1. BAHAYA TEGANGAN TINGGI: Wajib pakai sarung tangan isolasi 1000V, cabut Service Plug, & tunggu 10 menit sebelum menyentuh kabel oranye!",
            "2. Cek riwayat servis AC — apakah pernah diisi oli kompresor biasa (PAG) bukan oli isolasi (POE / ND-11)?",
            "3. Lepas konektor kompresor AC HV, lalu cek apakah nilai Insulation Resistance kembali naik.",
            "4. Ukur tahanan isolasi (Insulation Tester 500V DC) pada baterai HV, kabel oranye, inverter, dan motor traksi.",
        ],
        [
            {"parameter": "Tahanan Isolasi HV Sehat", "normal_range": "> 10 – 500 MOhm", "unit": "MOhm"},
            {"parameter": "Ambang Bahaya Isolation Fault", "normal_range": "< 0.5 – 1.0 MOhm", "unit": "MOhm"},
        ],
        requires_hv_safety=True,
    ),
    _dtc(
        "P0A0F",
        "Mesin Bensin Gagal Hidup pada Sistem Hybrid (Engine Failed to Start)",
        "Bahan Bakar",
        ["Hybrid"],
        "CRITICAL",
        "Bahan bakar habis / pompa bensin lemah; Throttle body kotor/macet; Koil/busi/injektor bensin bermasalah; Aki kecil 12V soak sehingga sistem gagal inisialisasi; Sensor CKP/MAF error.",
        [
            _opt("Cek Bahan Bakar, Aki 12V Aux & Baca Sub-Kode DTC ECM Bensin", "Langkah Pertama", "UTAMA", "P0A0F adalah kode sekunder dari sistem Hybrid ketika mesin bensin gagal menyala saat diputar motor generator.", "Aki 12V ≥ 12.4V, bensin cukup, & mesin bensin langsung hidup saat mode READY."),
            _opt("Bersihkan Throttle Body, Cek Busi/Koil & Tekanan Pompa Bensin", "Sisi Mesin Bensin", "SEKUNDER", "Kerusakan pengapian atau suplai BBM bensin mencegah mesin menyala.", "Mesin bensin hidup halus tanpa mati mendadak."),
        ],
        [
            "1. Cek indikator tangki bensin & tegangan aki 12V tambahan (auxiliary battery).",
            "2. Scan modul Engine ECM (bukan hanya HV Control) untuk melihat kode pemicu asli (mis. P0300, P0335, P0171).",
            "3. Cek throttle body, tekanan fuel pump, dan busi/koil.",
        ],
        [{"parameter": "Aki 12V Aux (Standby)", "normal_range": "12.4 – 12.8 V", "unit": "Volt"}],
        requires_hv_safety=True,
    ),
    _dtc(
        "P0A93",
        "Kinerja Sistem Pendingin Inverter Hybrid/EV Abnormal (Inverter Cooling System Performance)",
        "Pendingin",
        ["EV", "Hybrid"],
        "CRITICAL",
        "Pompa air listrik pendingin inverter (Inverter Water Pump) mati/lemah; Cairan coolant inverter kurang/masuk angin; Radiator inverter tersumbat.",
        [
            _opt("Periksa Aliran Coolant di Reservoir Inverter & Ganti Pompa Coolant Inverter Listrik", "Paling Sering", "UTAMA", "Jika pompa coolant inverter mati, suhu IGBT inverter langsung melonjak > 70°C dan mobil membatasi tenaga.", "Terlihat pusaran aliran coolant di tabung reservoir saat kunci ON & suhu inverter < 55°C."),
            _opt("Kuras & Bleeding Udara Sistem Pendingin Inverter", "Perawatan", "SEKUNDER", "Kantong udara menghambat sirkulasi pendingin inverter.", "Level coolant stabil & tidak overheat."),
        ],
        [
            "1. Buka tutup reservoir coolant Inverter (SAAT DINGIN) lalu putar kunci ke IG-ON: amati apakah coolant berputar mengalir.",
            "2. Cek sekering/relay pompa air inverter dan dengarkan getaran motor pompa.",
            "3. Pantau suhu Inverter MG1/MG2 pada Live Data scanner.",
        ],
        [{"parameter": "Suhu Inverter Normal", "normal_range": "30 – 65 °C", "unit": "°C"}],
        requires_hv_safety=True,
    ),
    _dtc(
        "P0A94",
        "Kinerja Konverter DC/DC Tegangan Tinggi Abnormal (DC/DC Converter Performance)",
        "Kelistrikan",
        ["EV", "Hybrid"],
        "CRITICAL",
        "Inverter / DC-DC Converter rusak gagal mengisi aki 12V; Aki 12V soak/short internal; Sekering utama DC-DC putus; Overheat pendingin inverter.",
        [
            _opt("Ukur Tegangan Pengisian Aki 12V saat READY & Cek Kondisi Aki 12V", "Cek Pertama", "UTAMA", "Pada mobil EV/Hybrid tidak ada alternator konvensional — pengisian aki 12V dilakukan oleh DC/DC Converter.", "Saat mode READY tegangan di aki 12V terbaca 13.8 – 14.5 V."),
            _opt("Cek Sistem Pendingin Inverter, Sekering HV/DC-DC & Modul Inverter", "Tindakan Lanjut", "SEKUNDER", "Overheat atau kegagalan papan DC/DC mematikan pengisian 12V.", "Pengisian 12V stabil saat lampu & AC hidup."),
        ],
        [
            "1. Ukur tegangan aki 12V saat OFF dan saat mode READY (harus naik ke 13.8–14.5V).",
            "2. Periksa sekering jalur DC-DC & aliran coolant inverter.",
            "3. Pakai APD HV 1000V bila harus memeriksa konektor inverter.",
        ],
        [{"parameter": "Output DC/DC ke Aki 12V (READY)", "normal_range": "13.8 – 14.5 V", "unit": "Volt"}],
        requires_hv_safety=True,
    ),
    _dtc(
        "P0A7F",
        "Penurunan Kapasitas Baterai Hybrid / EV (Battery Pack Deterioration)",
        "Kelistrikan",
        ["EV", "Hybrid"],
        "HIGH",
        "Kapasitas baterai HV menurun (SoH rendah) karena usia pakai / panas berlebih; Cell imbalance mulai melebar.",
        [
            _opt("Periksa State of Health (SoH), Delta Tegangan Sel & Bersihkan Pendingin Baterai HV", "Analisa BMS", "UTAMA", "Memastikan apakah penurunan merata (penuaan alami) atau hanya beberapa blok sel yang lemah.", "Delta tegangan antar blok < 0.10 V & suhu baterai normal."),
        ],
        ["1. Scan BMS untuk melihat SoH (%) dan tegangan tiap blok sel.", "2. Bersihkan filter kipas/cooling baterai HV."],
        [{"parameter": "Delta Tegangan Sel", "normal_range": "< 50 mV", "unit": "mV"}],
        requires_hv_safety=True,
    ),
    _dtc(
        "P0AFA",
        "Tegangan Sistem Baterai Hybrid/EV Terlalu Rendah (Battery System Voltage Low)",
        "Kelistrikan",
        ["EV", "Hybrid"],
        "CRITICAL",
        "Baterai HV habis total (deep discharge); Sekering utama baterai HV / Service Plug belum terpasang rapat; Contactor/Relay utama (SMR) gagal menutup.",
        [
            _opt("Pastikan Service Plug Terkunci Penuh (2 Tahap Klik) & Cek Sekering HV + Aki 12V", "Cek Paling Cepat", "UTAMA", "Service plug yang kurang dikunci ke bawah memutus sirkuit baterai HV.", "Service plug terkunci rapat & tegangan HV terbaca di BMS."),
            _opt("Lakukan Pengisian Baterai HV (Charging) & Periksa Relay SMR (Main Contactor)", "Pemulihan", "SEKUNDER", "Baterai HV yang terlalu kosong tidak mampu menutup relay utama untuk masuk mode READY.", "Mobil berhasil masuk mode READY normal."),
        ],
        ["1. Cek aki 12V (harus > 12.2V agar relay SMR bisa aktif).", "2. Pastikan Service Plug terkunci penuh.", "3. Cek tegangan total HV pada scanner BMS."],
        [{"parameter": "Aki 12V Aux", "normal_range": "≥ 12.4 V", "unit": "Volt"}],
        requires_hv_safety=True,
    ),

    # ==================== TRANSMISI AT / CVT & CAN BUS ====================
    _dtc(
        "P0868",
        "Tekanan Oli Transmisi CVT Sekunder Terlalu Rendah (Transmission Fluid Pressure Low — CVT)",
        "Mekanis",
        ["All"],
        "CRITICAL",
        "Oli CVT kurang, kotor, atau salah spesifikasi; Filter oli CVT tersumbat; Valve body / solenoid tekanan CVT macet; Pompa oli CVT atau sabuk baja (steel belt) & pulley aus.",
        [
            _opt("Periksa Level, Warna & Ganti Oli CVT + Filter Kertas/Strainer CVT Sesuai Spec OEM", "Cek Pertama", "UTAMA", "Oli CVT kotor/kurang langsung menjatuhkan tekanan pulley sekunder dan menimbulkan gejala selip/ngeden.", "Level oli CVT tepat pada suhu kerja & tekanan sekunder sesuai target scanner."),
            _opt("Periksa / Bersihkan Valve Body, Solenoid Tekanan & Sensor Tekanan CVT", "Tindakan Menengah", "SEKUNDER", "Flow control valve macet atau solenoid lemah sangat sering terjadi pada CVT Honda/Nissan/Mitsubishi/Toyota.", "Tekanan sekunder idle ~0.5–0.8 MPa & naik mulus saat D/R."),
            _opt("Overhaul Mekanis Pompa Oli & Steel Belt / Pulley CVT", "Kerusakan Berat", "OPSIONAL", "Jika oli CVT penuh gram besi berkilau, belt & pulley sudah aus.", "Tidak ada selip atau bunyi mendengung saat uji jalan."),
        ],
        [
            "1. Cek level dan kebersihan oli CVT (periksa apakah ada serbuk logam halus di magnet karter).",
            "2. Baca Live Data Target vs Actual Secondary Line Pressure CVT.",
            "3. Ganti oli CVT asli + filter halus, lalu uji tekanan & lakukan kalibrasi CVT bila tersedia.",
        ],
        [{"parameter": "CVT Secondary Pressure (Idle)", "normal_range": "0.5 – 0.9 MPa", "unit": "MPa"}],
    ),
    _dtc(
        "P0700",
        "Permintaan Lampu Check Engine dari Modul Transmisi (TCM MIL Request)",
        "Kelistrikan",
        ["All"],
        "HIGH",
        "P0700 adalah kode pemberitahuan dari ECM bahwa ada kode kerusakan tersimpan di dalam modul Transmisi (TCM/AT/CVT/DCT/DSG).",
        [
            _opt("Scan Modul Transmisi (TCM / AT / CVT / DSG) untuk Membaca Kode Error Aslinya", "Wajib Dilakukan", "UTAMA", "P0700 bukan kerusakan tunggal — kode spesifik (solenoid, speed sensor, tekanan oli) ada di dalam modul TCM.", "Kode spesifik di TCM terbaca dan ditangani hingga tuntas."),
            _opt("Periksa Level & Kondisi Oli Transmisi serta Soket Harness Transmisi", "Cek Fisik", "SEKUNDER", "Soket transmisi kemasukan air/oli atau oli kurang sering memicu masuk mode darurat (limp mode).", "Soket kering bersih & perpindahan gigi kembali normal."),
        ],
        [
            "1. Gunakan scanner untuk masuk langsung ke modul TCM / Transmission (bukan hanya OBD Engine).",
            "2. Catat semua kode P07xx / P08xx / P09xx / P27xx di TCM dan tangani sumbernya.",
            "3. Periksa oli transmisi & konektor kabel transmisi.",
        ],
        [{"parameter": "Status Modul", "normal_range": "0 DTC di TCM", "unit": "DTC"}],
    ),
    _dtc(
        "U0100",
        "Hilang Komunikasi Jaringan CAN dengan ECM / PCM (Lost Communication with ECM)",
        "Kelistrikan",
        ["All"],
        "CRITICAL",
        "Aki lemah / terminal aki kendor; Sekering atau Main Relay EFI/ECM putus; Kabel jaringan CAN-High / CAN-Low putus atau konslet; Massa ground ECM korosi; Modul ECM mati/kemasukan air.",
        [
            _opt("Cek Tegangan Aki, Sekering Main EFI/ECM, Main Relay & Ground ECM", "Cek Paling Cepat", "UTAMA", "ECM yang tidak mendapat suplai +12V atau massa tidak dapat menjawab komunikasi CAN dari modul lain.", "Tegangan suplai +12V & massa ECM stabil; scanner dapat terhubung ke ECM."),
            _opt("Ukur Tahanan Jalur CAN Bus di Pin 6 & 14 OBD-II (Normal 60 Ohm)", "Diagnosa Jaringan CAN", "UTAMA", "Kabel CAN putus terbaca 120 Ohm/OL; konslet terbaca ~0 Ohm; normal persis ~60 Ohm (2 resistor 120 Ohm paralel).", "Tahanan Pin 6–14 = 58–62 Ohm (aki lepas) & tegangan CAN-H ~2.6V / CAN-L ~2.4V saat kunci ON."),
        ],
        [
            "1. Periksa tegangan aki, sekering EFI/ECM, dan bunyi klik Main Relay saat kunci ON.",
            "2. Matikan kontak & lepas aki: ukur tahanan antara Pin 6 (CAN-H) dan Pin 14 (CAN-L) di port OBD-II (normal 60 Ohm).",
            "3. Cek tegangan CAN-H (~2.5–2.7V) & CAN-L (~2.3–2.5V) saat kunci kontak ON.",
            "4. Periksa soket ECM dan kabel harness dari gigitan tikus atau korosi air.",
        ],
        [
            {"parameter": "Tahanan CAN-H ke CAN-L (OFF)", "normal_range": "58 – 62 Ohm", "unit": "Ohm"},
            {"parameter": "Tegangan CAN-High (ON)", "normal_range": "2.5 – 2.8 V", "unit": "Volt"},
            {"parameter": "Tegangan CAN-Low (ON)", "normal_range": "2.2 – 2.5 V", "unit": "Volt"},
        ],
    ),
    _dtc(
        "U0101",
        "Hilang Komunikasi Jaringan CAN dengan TCM / Transmisi (Lost Communication with TCM)",
        "Kelistrikan",
        ["All"],
        "HIGH",
        "Sekering/suplai daya TCM putus; Soket transmisi/TCM korosi atau kendor; Kabel CAN-H/CAN-L menuju TCM putus; Modul TCM / Mekatronik (DSG/CVT) rusak.",
        [
            _opt("Periksa Sekering TCM, Suplai +12V, Ground & Soket Konektor Transmisi", "Langkah Utama", "UTAMA", "Konektor transmisi di area bawah mesin rawan terkena air/oli sehingga memutus sinyal CAN.", "TCM kembali terdeteksi oleh scanner & indikator posisi gigi (P-R-N-D) tampil normal."),
            _opt("Ukur Kontinuitas Kabel CAN Bus (Pin 6 & 14) Menuju Modul TCM", "Cek Wiring", "SEKUNDER", "Kabel CAN putus di jalur harness transmisi memicu U0101.", "Tahanan CAN ~60 Ohm & tidak ada kabel putus."),
        ],
        ["1. Cek sekering & relay TCM.", "2. Inspeksi soket transmisi dari air/korosi.", "3. Ukur jalur CAN-H/CAN-L ke TCM."],
        [{"parameter": "Tahanan CAN Bus", "normal_range": "58 – 62 Ohm", "unit": "Ohm"}],
    ),
    _dtc(
        "U0121",
        "Hilang Komunikasi Jaringan CAN dengan Modul ABS / VSC",
        "Kelistrikan",
        ["All"],
        "HIGH",
        "Sekering ABS/VSC putus; Soket aktuator ABS korosi/kemasukan air; Kabel CAN menuju modul ABS putus; Modul elektronik ABS rusak.",
        [
            _opt("Cek Sekering ABS (Besar & Kecil), Ground & Konektor Modul Aktuator ABS", "Langkah Utama", "UTAMA", "Soket modul ABS di ruang mesin sering terkena rembesan minyak rem/air cuci mesin.", "Modul ABS merespons scanner & lampu ABS/VSC padam."),
        ],
        ["1. Periksa semua sekering ABS/VSC.", "2. Lepas & bersihkan soket modul ABS.", "3. Cek jalur CAN Bus ke modul ABS."],
        [{"parameter": "Tahanan CAN Bus", "normal_range": "58 – 62 Ohm", "unit": "Ohm"}],
    ),
    _dtc(
        "C1201",
        "Sistem Kontrol Mesin Bermasalah — Mode Pengaman ABS/VSC Aktif (Toyota Engine Control System)",
        "Kelistrikan",
        ["All"],
        "MEDIUM",
        "C1201 pada Toyota (Innova/Fortuner/Avanza/Camry) adalah kode pendamping di modul ABS/VSC yang otomatis menyala setiap kali ada kerusakan di Engine ECM (lampu Check Engine + VSC/TRC nyala bersamaan).",
        [
            _opt("Scan & Perbaiki Kode Kerusakan Utama di Modul Engine (ECM) Terlebih Dahulu", "Wajib Tahu (Khas Toyota)", "UTAMA", "Jangan ganti modul ABS! C1201 akan langsung hilang otomatis begitu kerusakan di Engine ECM diperbaiki dan di-reset.", "Engine ECM bebas DTC, lampu VSC/TRC & C1201 langsung padam."),
        ],
        ["1. Masuk ke modul Engine ECM dan baca kode Pxxxx yang aktif.", "2. Perbaiki masalah di mesin, lalu hapus DTC di ECM & ABS."],
        [{"parameter": "Status ECM", "normal_range": "0 DTC Aktif di Engine", "unit": "DTC"}],
    ),
]

# Tambahkan kode-kode pendamping umum (short aliases / siblings) agar total > 80 kode terpetakan
_SIBLING_DTCS: list[tuple[str, str, str, list[str], str]] = [
    ("P0090", "Sirkuit Kontrol Regulator Tekanan Bahan Bakar / SCV Terbuka (Fuel Pressure Regulator 1 Control)", "Bahan Bakar", ["Diesel", "Bensin"], "P0089"),
    ("P0100", "Malfungsi Sirkuit Sensor Aliran Udara (MAF Circuit Malfunction)", "Udara", ["All"], "P0299"),
    ("P0101", "Rentang / Kinerja Sensor MAF Abnormal (MAF Sensor Range/Performance — Cek Filter & Bocor Turbo)", "Udara", ["All"], "P2279"),
    ("P0190", "Malfungsi Sirkuit Sensor Tekanan Fuel Rail (FRP Sensor Circuit)", "Bahan Bakar", ["Diesel", "Bensin"], "P0191"),
    ("P0192", "Sinyal Sensor Tekanan Fuel Rail Terlalu Rendah (FRP Circuit Low)", "Bahan Bakar", ["Diesel", "Bensin"], "P0191"),
    ("P0193", "Sinyal Sensor Tekanan Fuel Rail Terlalu Tinggi (FRP Circuit High)", "Bahan Bakar", ["Diesel", "Bensin"], "P0191"),
    ("P0200", "Malfungsi Sirkuit Injektor Bahan Bakar (Injector Circuit Open/Short)", "Bahan Bakar", ["Diesel", "Bensin"], "P062D"),
    ("P0201", "Malfungsi Sirkuit Injektor Silinder 1 (Injector 1 Circuit)", "Bahan Bakar", ["Diesel", "Bensin"], "P062D"),
    ("P0202", "Malfungsi Sirkuit Injektor Silinder 2 (Injector 2 Circuit)", "Bahan Bakar", ["Diesel", "Bensin"], "P062D"),
    ("P0203", "Malfungsi Sirkuit Injektor Silinder 3 (Injector 3 Circuit)", "Bahan Bakar", ["Diesel", "Bensin"], "P062D"),
    ("P0204", "Malfungsi Sirkuit Injektor Silinder 4 (Injector 4 Circuit)", "Bahan Bakar", ["Diesel", "Bensin"], "P062D"),
    ("P0236", "Kinerja Sensor Tekanan Boost Turbo Abnormal (Turbo Boost Sensor A Range)", "Udara", ["Diesel", "Bensin"], "P0299"),
    ("P0237", "Sinyal Sensor Boost Turbo Terlalu Rendah (Turbo Boost Sensor A Low)", "Udara", ["Diesel", "Bensin"], "P0299"),
    ("P0238", "Sinyal Sensor Boost Turbo Terlalu Tinggi (Turbo Boost Sensor A High)", "Udara", ["Diesel", "Bensin"], "P0234"),
    ("P0243", "Malfungsi Sirkuit Solenoid Wastegate / VNT Turbo (Turbocharger Wastegate Solenoid A)", "Udara", ["Diesel", "Bensin"], "P0299"),
    ("P0251", "Malfungsi Kontrol Metering Pompa Injeksi / SCV (Injection Pump Fuel Metering A)", "Bahan Bakar", ["Diesel"], "P0089"),
    ("P0381", "Malfungsi Sirkuit Lampu Indikator Glow Plug (Diesel)", "Kelistrikan", ["Diesel"], "P0380"),
    ("P0402", "Aliran Gas Buang EGR Berlebih — Katup EGR Macet Terbuka (EGR Flow Excessive)", "Emisi", ["Diesel", "Bensin"], "P0401"),
    ("P0403", "Malfungsi Sirkuit Kontrol Katup EGR (EGR Control Circuit)", "Emisi", ["Diesel", "Bensin"], "P0400"),
    ("P0404", "Rentang / Kinerja Sirkuit Kontrol EGR Abnormal (Katup EGR Tersendat)", "Emisi", ["Diesel", "Bensin"], "P0401"),
    ("P0405", "Sinyal Sensor Posisi EGR A Terlalu Rendah (EGR Sensor A Low)", "Emisi", ["Diesel", "Bensin"], "P0400"),
    ("P0627", "Sirkuit Kontrol Pompa Bahan Bakar / SCV Terbuka (Fuel Pump A Control Open)", "Kelistrikan", ["Diesel", "Bensin"], "P0089"),
    ("P0628", "Sirkuit Kontrol Pompa Bahan Bakar Rendah / Konslet Massa (Fuel Pump Control Low)", "Kelistrikan", ["Diesel", "Bensin"], "P0089"),
    ("P0629", "Sirkuit Kontrol Pompa Bahan Bakar Tinggi (Fuel Pump Control High)", "Kelistrikan", ["Diesel", "Bensin"], "P0089"),
    ("P2263", "Kinerja Sistem Boost Turbocharger Abnormal (Turbo Boost System Performance)", "Udara", ["Diesel", "Bensin"], "P0299"),
    ("P2452", "Malfungsi Sirkuit Sensor Tekanan Diferensial DPF (DPF Pressure Sensor A)", "Emisi", ["Diesel"], "P2002"),
    ("P2453", "Rentang / Kinerja Sensor Tekanan Diferensial DPF Abnormal", "Emisi", ["Diesel"], "P2002"),
    ("P2463", "Penumpukan Jelaga DPF Berlebih (DPF Soot Accumulation)", "Emisi", ["Diesel"], "P2002"),
    ("P0010", "Malfungsi Sirkuit Aktuator Camshaft Intake / OCV / VANOS (Bank 1 A)", "Kelistrikan", ["Bensin", "Hybrid"], "P0011"),
    ("P0013", "Malfungsi Sirkuit Aktuator Camshaft Exhaust / OCV / VANOS (Bank 1 B)", "Kelistrikan", ["Bensin", "Hybrid"], "P0014"),
    ("P0018", "Korelasi CKP–CMP Bank 2 Sensor A Tidak Sinkron (Mesin V6/Boxer)", "Mekanis", ["Bensin", "Hybrid"], "P0016"),
    ("P0019", "Korelasi CKP–CMP Bank 2 Sensor B Tidak Sinkron (Mesin V6/Boxer)", "Mekanis", ["Bensin", "Hybrid"], "P0017"),
    ("P0174", "Campuran Terlalu Kurus Bank 2 (System Too Lean Bank 2)", "Bahan Bakar", ["Bensin", "Hybrid"], "P2177"),
    ("P0175", "Campuran Terlalu Kaya Bank 2 (System Too Rich Bank 2)", "Bahan Bakar", ["Bensin", "Hybrid"], "P2178"),
    ("P2187", "Campuran Terlalu Kurus saat Idle Bank 1 (Cek Kebocoran Vakum / PCV)", "Bahan Bakar", ["Bensin", "Hybrid"], "P2177"),
    ("P2188", "Campuran Terlalu Kaya saat Idle Bank 1 (Cek HPFP / Injektor / EVAP)", "Bahan Bakar", ["Bensin", "Hybrid"], "P2178"),
    ("P0A1F", "Malfungsi Modul Kontrol Energi Baterai HV (BECM / BMS Fault)", "Kelistrikan", ["EV", "Hybrid"], "P0A80"),
    ("P0C73", "Malfungsi Pompa Pendingin Elektronik Motor/Inverter EV/Hybrid", "Pendingin", ["EV", "Hybrid"], "P0A93"),
    ("P1A10", "Malfungsi Contactor / Sistem Penggerak Tegangan Tinggi EV/Hybrid", "Kelistrikan", ["EV", "Hybrid"], "P0AFA"),
    ("P1B00", "Malfungsi Sistem Manajemen Baterai HV (BMS Fault)", "Kelistrikan", ["EV", "Hybrid"], "P0A80"),
    ("P3000", "Malfungsi Sistem Baterai HV (Toyota Hybrid — Baca Sub-Kode BMS)", "Kelistrikan", ["EV", "Hybrid"], "P0A80"),
    ("U0001", "Malfungsi Jalur Komunikasi High-Speed CAN Bus", "Kelistrikan", ["All"], "U0100"),
    ("U0073", "Jaringan Komunikasi Modul CAN Bus Off (Cek Short Jalur CAN)", "Kelistrikan", ["All"], "U0100"),
    ("U0140", "Hilang Komunikasi CAN dengan Body Control Module (BCM / ETACS)", "Kelistrikan", ["All"], "U0100"),
    ("U0155", "Hilang Komunikasi CAN dengan Panel Instrumen / Speedometer (IPC)", "Kelistrikan", ["All"], "U0100"),
    ("P0715", "Malfungsi Sirkuit Sensor Kecepatan Input/Turbin Transmisi (AT/CVT)", "Kelistrikan", ["All"], "P0700"),
    ("P0717", "Tidak Ada Sinyal Sensor Kecepatan Input Transmisi (Input Speed Sensor)", "Kelistrikan", ["All"], "P0700"),
    ("P0720", "Malfungsi Sirkuit Sensor Kecepatan Output Transmisi (Output Speed Sensor)", "Kelistrikan", ["All"], "P0700"),
    ("P0741", "Kinerja Kopling Torque Converter Transmisi Otomatis (TCC Stuck Off)", "Mekanis", ["All"], "P0700"),
]


def _build_catalog() -> dict[str, dict[str, Any]]:
    by_code: dict[str, dict[str, Any]] = {}
    for item in _RAW_MODERN_DTCS:
        by_code[item["code"]] = item
    for code, title_id, sys_cat, applies_to, parent_code in _SIBLING_DTCS:
        parent = by_code.get(parent_code)
        if not parent:
            continue
        by_code[code.upper()] = {
            **parent,
            "code": code.upper(),
            "title_id": title_id,
            "system_category": sys_cat,
            "applies_to": applies_to,
        }
    return by_code


MODERN_DTC_CATALOG: dict[str, dict[str, Any]] = _build_catalog()


def lookup_modern_dtc(dtc_code: str, fuel_type: str = "Bensin") -> dict[str, Any] | None:
    """
    Mencari kode DTC pada katalog modern (Diesel Common-Rail, Turbo, VVT/VANOS, Hybrid/EV, CAN).
    Mengembalikan entri yang sesuai jenis bahan bakar kendaraan.
    """
    code = (dtc_code or "").strip().upper()
    if not code:
        return None
    entry = MODERN_DTC_CATALOG.get(code)
    if not entry:
        return None

    applies = entry.get("applies_to", ["All"])
    if "All" in applies:
        return entry
    f_clean = (fuel_type or "Bensin").strip()
    if f_clean in applies:
        return entry
    # Khusus P0087: hanya override untuk Diesel agar Bensin tetap memakai info GDI/fuel pump sesuai konteks
    if code == "P0087" and f_clean != "Diesel":
        return None
    # Untuk kode non-P0087 yang spesifik (mis. P0A80, P0299, P0015), tetap kembalikan bila kode persis dicari mekanik
    return entry


# ---------------------------------------------------------------------------
# 2. FILTER KESESUAIAN JENIS MESIN (MENCEGAH EV/DIESEL DIVONIS BUSI/SENSOR O2)
# ---------------------------------------------------------------------------

_EV_FORBIDDEN_KEYWORDS = (
    "sensor o2", "o2 sensor", "ho2s", "oksigen", "oxygen",
    "busi", "spark plug", "koil", "ignition coil", "pengapian",
    "injektor", "injector", "fuel pump", "pompa bensin", "tangki bensin",
    "bahan bakar", "bbm", "pertalite", "pertamax", "solar", "katalis",
    "catalytic", "egr", "throttle body", "karburator", "klep", "timing belt",
    "timing chain", "turbo", "knalpot", "exhaust", "misfire", "stft", "ltft",
)

_DIESEL_FORBIDDEN_KEYWORDS = (
    "busi", "spark plug", "koil pengapian", "ignition coil", "kabel busi",
    "pengapian (misfire)", "celah elektroda busi", "pertalite", "pertamax",
)


def is_text_compatible_with_fuel(text: str, fuel_type: str) -> bool:
    """
    Memastikan kasus historis / rekomendasi mesin bensin tidak pernah salah vonis
    pada mobil listrik murni (EV) atau menyarankan ganti busi/koil pada mesin Diesel.
    """
    f_low = (fuel_type or "Bensin").strip().lower()
    t_low = (text or "").lower()
    if f_low == "ev":
        return not any(kw in t_low for kw in _EV_FORBIDDEN_KEYWORDS)
    if f_low == "diesel":
        return not any(kw in t_low for kw in _DIESEL_FORBIDDEN_KEYWORDS)
    return True


def strip_unverified_jb420_pins_from_text(text: str) -> str:
    """Menghapus referensi nomor pin ECM Suzuki JB420 (E23-xx / C37-xx) dari teks opsi non-JB420."""
    if not text:
        return text
    cleaned = re.sub(
        r"\s*\((?:[ECGB]\d{2}-\d{1,2}(?:\s*,\s*[ECGB]\d{2}-\d{1,2})*)\)",
        "",
        text,
    )
    cleaned = re.sub(r"\b[EC]\d{2}-\d{1,2}\b", "Pin Soket Terkait", cleaned)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


# ---------------------------------------------------------------------------
# 3. EVALUATOR LIVE DATA ADAPTIF (DIESEL COMMON-RAIL & HYBRID/EV)
# ---------------------------------------------------------------------------

def evaluate_adaptive_live_data(
    fuel_type: str,
    rail_pressure_mpa: float | None = None,
    boost_kpa: float | None = None,
    inj_feedback_mm3: float | None = None,
    egr_pct: float | None = None,
    hv_soc_pct: float | None = None,
    hv_cell_delta_mv: float | None = None,
    hv_insulation_mohm: float | None = None,
    hv_temp_c: float | None = None,
) -> list[dict[str, str]]:
    """
    Menganalisa parameter Live Data khusus Diesel Common-Rail dan Hybrid/EV.
    Mengembalikan daftar temuan anomali siap tampil di hasil diagnosa.
    """
    findings: list[dict[str, str]] = []

    # --- DIESEL COMMON-RAIL ---
    if rail_pressure_mpa is not None:
        if rail_pressure_mpa < 22.0:
            findings.append({
                "parameter": "Fuel Rail Pressure",
                "value": f"{rail_pressure_mpa:.1f} MPa",
                "status": "CRITICAL",
                "note": "Tekanan Common-Rail TERLALU RENDAH (< 22 MPa) — Cek Filter Solar, Masuk Angin, SCV, atau Uji Backleak Injektor (risiko DTC P0087/P0093).",
            })
        elif rail_pressure_mpa > 195.0:
            findings.append({
                "parameter": "Fuel Rail Pressure",
                "value": f"{rail_pressure_mpa:.1f} MPa",
                "status": "HIGH",
                "note": "Tekanan Common-Rail TERLALU TINGGI (> 195 MPa) — Cek SCV macet terbuka, jalur return mampet, atau sensor FRP (risiko DTC P0088).",
            })
        else:
            findings.append({
                "parameter": "Fuel Rail Pressure",
                "value": f"{rail_pressure_mpa:.1f} MPa",
                "status": "NORMAL",
                "note": "Tekanan Fuel Rail Common-Rail berada dalam rentang kerja normal (25–190 MPa).",
            })

    if boost_kpa is not None:
        if boost_kpa < 95.0:
            findings.append({
                "parameter": "Boost Pressure Turbo",
                "value": f"{boost_kpa:.0f} kPa",
                "status": "HIGH",
                "note": "Tekanan boost di bawah atmosfer — cek filter udara mampet parah atau pembacaan sensor MAP/Boost error.",
            })
        elif boost_kpa > 260.0:
            findings.append({
                "parameter": "Boost Pressure Turbo",
                "value": f"{boost_kpa:.0f} kPa",
                "status": "HIGH",
                "note": "OVERBOOST (> 260 kPa abs) — VNT / Wastegate macet atau boost control solenoid bermasalah (risiko DTC P0234).",
            })
        else:
            findings.append({
                "parameter": "Boost Pressure Turbo",
                "value": f"{boost_kpa:.0f} kPa",
                "status": "NORMAL",
                "note": "Tekanan Boost Turbo dalam batas normal (98–105 kPa idle; 180–250 kPa beban penuh).",
            })

    if inj_feedback_mm3 is not None:
        if abs(inj_feedback_mm3) >= 3.0:
            findings.append({
                "parameter": "Koreksi Injektor (Feedback)",
                "value": f"{inj_feedback_mm3:+.2f} mm³/st",
                "status": "CRITICAL",
                "note": "Nilai kompensasi injektor melampaui batas ±3.0 mm³/st — Injektor silinder tersebut aus/mampet/bocor atau kompresi silinder lemah!",
            })
        elif abs(inj_feedback_mm3) >= 2.0:
            findings.append({
                "parameter": "Koreksi Injektor (Feedback)",
                "value": f"{inj_feedback_mm3:+.2f} mm³/st",
                "status": "MEDIUM",
                "note": "Koreksi injektor mulai melebar (±2.0–3.0 mm³/st) — Disarankan purging/kalibrasi injektor & cek filter solar.",
            })
        else:
            findings.append({
                "parameter": "Koreksi Injektor (Feedback)",
                "value": f"{inj_feedback_mm3:+.2f} mm³/st",
                "status": "NORMAL",
                "note": "Keseimbangan penyemprotan injektor sangat sehat (dalam ±2.0 mm³/st).",
            })

    if egr_pct is not None:
        if egr_pct > 85.0:
            findings.append({
                "parameter": "Posisi Katup EGR",
                "value": f"{egr_pct:.0f}%",
                "status": "MEDIUM",
                "note": "Bukaaan EGR sangat tinggi (> 85%) — Waspada katup macet terbuka jika terjadi saat akselerasi/beban penuh (asap hitam & tenaga drop).",
            })
        else:
            findings.append({
                "parameter": "Posisi Katup EGR",
                "value": f"{egr_pct:.0f}%",
                "status": "NORMAL",
                "note": "Posisi bukaan EGR terbaca normal.",
            })

    # --- HYBRID / EV (HIGH-VOLTAGE) ---
    if hv_insulation_mohm is not None:
        if hv_insulation_mohm < 1.0:
            findings.append({
                "parameter": "Tahanan Isolasi HV",
                "value": f"{hv_insulation_mohm:.2f} MOhm",
                "status": "CRITICAL",
                "note": "BAHAYA KEBOCORAN TEGANGAN TINGGI (< 1 MOhm)! Jangan sentuh komponen oranye tanpa sarung tangan 1000V — cek kompresor AC HV, konektor lembab, & inverter (DTC P0AA6).",
            })
        elif hv_insulation_mohm < 10.0:
            findings.append({
                "parameter": "Tahanan Isolasi HV",
                "value": f"{hv_insulation_mohm:.2f} MOhm",
                "status": "HIGH",
                "note": "Tahanan isolasi mulai menurun (< 10 MOhm) — Periksa kelembaban konektor HV & kualitas oli kompresor AC (wajib POE).",
            })
        else:
            findings.append({
                "parameter": "Tahanan Isolasi HV",
                "value": f"{hv_insulation_mohm:.1f} MOhm",
                "status": "NORMAL",
                "note": "Isolasi sistem tegangan tinggi aman (> 10 MOhm).",
            })

    if hv_cell_delta_mv is not None:
        if hv_cell_delta_mv >= 150.0:
            findings.append({
                "parameter": "Delta Tegangan Sel HV",
                "value": f"{hv_cell_delta_mv:.0f} mV",
                "status": "CRITICAL",
                "note": "CELL IMBALANCE BERAT (≥ 150 mV) — Ada modul/sel baterai HV yang lemah atau busbar korosi (pemicu DTC P0A80).",
            })
        elif hv_cell_delta_mv >= 60.0:
            findings.append({
                "parameter": "Delta Tegangan Sel HV",
                "value": f"{hv_cell_delta_mv:.0f} mV",
                "status": "MEDIUM",
                "note": "Selisih tegangan sel mulai melebar (60–150 mV) — Lakukan pemantauan beban & cell balancing.",
            })
        else:
            findings.append({
                "parameter": "Delta Tegangan Sel HV",
                "value": f"{hv_cell_delta_mv:.0f} mV",
                "status": "NORMAL",
                "note": "Keseimbangan sel baterai HV sangat baik (< 60 mV).",
            })

    if hv_soc_pct is not None:
        if hv_soc_pct < 15.0:
            findings.append({
                "parameter": "SoC Baterai HV",
                "value": f"{hv_soc_pct:.0f}%",
                "status": "HIGH",
                "note": "State of Charge (SoC) sangat rendah (< 15%) — Risiko gagal READY / gagal starter mesin Hybrid (P0AFA).",
            })
        else:
            findings.append({
                "parameter": "SoC Baterai HV",
                "value": f"{hv_soc_pct:.0f}%",
                "status": "NORMAL",
                "note": "Kapasitas muatan baterai HV memadai.",
            })

    if hv_temp_c is not None:
        if hv_temp_c >= 50.0:
            findings.append({
                "parameter": "Suhu Baterai / Inverter HV",
                "value": f"{hv_temp_c:.0f} °C",
                "status": "CRITICAL",
                "note": "OVERHEAT SISTEM HV (≥ 50°C) — Cek kipas/filter baterai HV & pompa cairan pendingin inverter (risiko P0A93)!",
            })
        else:
            findings.append({
                "parameter": "Suhu Baterai / Inverter HV",
                "value": f"{hv_temp_c:.0f} °C",
                "status": "NORMAL",
                "note": "Suhu sistem HV berada pada batas aman.",
            })

    return findings


def build_low_confidence_safe_advice(
    fuel_type: str,
    vehicle_label: str,
    dtc_raw: str = "",
    hv_safety_warning: str | None = None,
) -> dict[str, Any]:
    """
    Membangun saran pemeriksaan awal yang AMAN dan jujur bila skor kecocokan kasus < 25%
    dan kode DTC belum terdaftar di katalog (menghilangkan salah vonis acak!).
    """
    f_clean = (fuel_type or "Bensin").strip()
    dtc_txt = f" ({dtc_raw.upper()})" if dtc_raw else ""

    if f_clean == "EV":
        title = f"Kasus Baru EV / Kode Belum Terpetakan{dtc_txt} — Panduan Pemeriksaan Awal Aman"
        root = (
            f"Kode/gejala pada {vehicle_label} belum memiliki kecocokan kuat di database bengkel. "
            "Pada kendaraan listrik murni (EV), pemeriksaan awal wajib difokuskan pada Aki 12V Aux, "
            "komunikasi BMS/VCU, sistem pendingin baterai/inverter, serta keamanan tegangan tinggi (HV)."
        )
        options = [
            _opt("Cek Tegangan Aki 12V Aux, Sekering Utama & Status Mode READY di Scanner BMS/VCU", "Langkah Aman #1", "UTAMA", "80% gangguan EV gagal READY berawal dari aki 12V lemah atau modul BMS tidak merespons.", "Aki 12V ≥ 12.4V dan seluruh modul EV (BMS, VCU, MCU, OBC) terhubung tanpa error."),
            _opt("Periksa Live Data BMS: SoC (%), Delta Tegangan Sel (mV) & Tahanan Isolasi HV (MOhm)", "Analisa HV (Wajib APD)", "UTAMA", "Memastikan tidak ada cell imbalance atau kebocoran isolasi tegangan tinggi sebelum pembongkaran.", "Delta sel < 50 mV & Tahanan Isolasi > 10 MOhm."),
            _opt("Cek Aliran Coolant Inverter/Baterai & Simpan Kasus Baru Setelah Sembuh", "Pendinginan & Dokumentasi", "SEKUNDER", "Overheat inverter membatasi tenaga EV; menyimpan hasil perbaikan memperkaya AI bengkel.", "Suhu inverter < 55°C & kasus tercatat di Data Kasus."),
        ]
        steps = [
            "1. PERINGATAN HV: Kenakan sarung tangan isolasi 1000V jika menyentuh komponen/kabel oranye.",
            "2. Ukur tegangan aki 12V (sering menjadi pemicu EV tidak bisa masuk READY).",
            "3. Lakukan full-system scan (VCU, BMS, MCU, OBC, ABS) untuk membaca seluruh sub-kode DTC.",
            "4. Periksa Live Data SoC, selisih tegangan sel, suhu inverter, dan tahanan isolasi.",
            "5. Setelah perbaikan berhasil, klik 'Simpan Kasus' agar diagnosa ini langsung dikenali di masa depan.",
        ]
        specs = [
            {"parameter": "Aki 12V Aux EV", "normal_range": "12.4 – 12.8 V (OFF) / 13.8 – 14.5 V (READY)", "unit": "Volt"},
            {"parameter": "Tahanan Isolasi HV", "normal_range": "> 10 MOhm", "unit": "MOhm"},
            {"parameter": "Delta Tegangan Sel HV", "normal_range": "< 50 mV", "unit": "mV"},
        ]
    elif f_clean == "Diesel":
        title = f"Kasus Baru Diesel / Kode Belum Terpetakan{dtc_txt} — Panduan Pemeriksaan Awal Common-Rail"
        root = (
            f"Kode/gejala pada {vehicle_label} belum memiliki kecocokan kuat di database bengkel. "
            "Untuk mesin Diesel Common-Rail, lakukan pemeriksaan sistematis pada jalur suplai solar & tekanan rail, "
            "sistem boost turbo/intercooler, katup EGR, serta kelistrikan sensor tanpa menebak komponen."
        )
        options = [
            _opt("Cek Filter Solar, Water Sedimenter, Masuk Angin & Live Data Fuel Rail Pressure", "Langkah Utama Diesel", "UTAMA", "Masalah bahan bakar & tekanan rail adalah sumber utama tenaga drop/susah hidup pada diesel common-rail.", "Tekanan rail idle 30–45 MPa dan tidak ada gelembung udara di jalur solar."),
            _opt("Periksa Selang Intercooler/Turbo, Kerja VNT/Wastegate & Kebersihan Katup EGR", "Jalur Udara & Turbo", "UTAMA", "Kebocoran boost atau EGR macet menyebabkan mobil ngempos & asap hitam.", "Selang boost kedap & tekanan boost naik mulus saat digas."),
            _opt("Cek Koreksi Injektor (Feedback mm³/st), Soket Sensor & Simpan Kasus Baru", "Analisa Lanjut", "SEKUNDER", "Memastikan kondisi tiap injektor dan merekam temuan baru ke database bengkel.", "Koreksi injektor dalam ±3.0 mm³/st & DTC teratasi."),
        ]
        steps = [
            "1. Periksa kondisi filter solar, water sedimenter, dan pastikan tidak ada kebocoran/masuk angin.",
            "2. Baca Live Data Target vs Actual Fuel Rail Pressure, Boost Pressure, dan Injector Feedback.",
            "3. Inspeksi selang intercooler turbo dari sobekan dan periksa kebersihan katup EGR.",
            "4. Lakukan uji tegangan suplai (+5V / +12V) & massa pada soket sensor terkait kode DTC.",
            "5. Klik 'Simpan Kasus' setelah mobil sembuh agar langsung tersimpan di database bengkel.",
        ]
        specs = [
            {"parameter": "Fuel Rail Pressure (Idle)", "normal_range": "30 – 45 MPa", "unit": "MPa"},
            {"parameter": "Boost Pressure (Beban)", "normal_range": "180 – 250 kPa abs", "unit": "kPa"},
            {"parameter": "Injector Feedback", "normal_range": "-3.0 s/d +3.0 mm³/st", "unit": "mm³/st"},
        ]
    else:
        title = f"Kasus Baru / Kode Belum Terpetakan{dtc_txt} — Panduan Pemeriksaan Awal Sistematis"
        root = (
            f"Gejala atau kode DTC pada {vehicle_label} belum memiliki kecocokan kuat (< 25%) di database bengkel saat ini. "
            "Gunakan pendekatan verifikasi dasar (Tegangan Aki/Ground, Live Data Fuel Trim/Sensor, Tekanan BBM, dan Pengapian) agar tidak salah ganti komponen."
        )
        options = [
            _opt("Periksa Live Data Sensor Utama (STFT/LTFT, MAP/MAF, ECT, O2) & Tegangan Aki/Ground", "Langkah Pertama", "UTAMA", "Live data langsung membedakan apakah sumber masalah berasal dari udara, bahan bakar, pengapian, atau kelistrikan.", "Tegangan aki idle 13.8–14.4V & sensor terbaca masuk akal."),
            _opt("Periksa Fisik Konektor, Sekering, Kebocoran Vakum, Busi/Koil & Tekanan Fuel Pump", "Verifikasi Lapangan", "SEKUNDER", "Pengecekan fisik cepat menangkap 70% penyebab umum sebelum mengganti part mahal.", "Tekanan BBM ~3.0–3.5 Bar, tidak ada kebocoran vakum, percikan api kuat."),
            _opt("Impor Paket Manual Model Ini atau Simpan Kasus Baru Setelah Perbaikan Berhasil", "Pengembangan Database", "OPSIONAL", "Menambah paket manual atau menyimpan kasus membuat analisa berikutnya langsung akurat.", "Kasus tersimpan di tab Data Kasus."),
        ]
        steps = [
            "1. Catat seluruh kode DTC (termasuk pending DTC) dan Freeze Frame Data dari scanner.",
            "2. Periksa tegangan aki, sekering EFI, serta kondisi massa ground mesin & bodi.",
            "3. Pantau Live Data STFT, LTFT, MAP/MAF, ECT, dan O2 saat idle serta 2500 RPM.",
            "4. Cek fisik kebocoran selang vakum, busi/koil, serta tekanan pompa bahan bakar.",
            "5. Setelah sumber kerusakan ditemukan & sembuh, klik 'Simpan Kasus' agar AI bengkel langsung mempelajarinya.",
        ]
        specs = [
            {"parameter": "Tegangan Pengisian (Idle)", "normal_range": "13.8 – 14.4 V", "unit": "Volt"},
            {"parameter": "Total Fuel Trim Sehat", "normal_range": "-10% s/d +10%", "unit": "%"},
            {"parameter": "Tekanan Pompa Bensin (EFI)", "normal_range": "2.8 – 3.8 Bar", "unit": "Bar"},
        ]

    return {
        "title": title,
        "root_cause_summary": root,
        "proven_repair_action": options[0]["title"],
        "repair_options": options,
        "repair_steps": steps,
        "standard_specs": specs,
        "hv_safety_warning": hv_safety_warning,
    }
