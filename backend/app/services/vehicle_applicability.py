"""
Vehicle Applicability, Multi-Model Generation Resolver, Global Engine Code Catalog
(Asia, Eropa, China) & Custom Manual Pack Registry
====================================================================================
Menyelesaikan tiga kebutuhan kritis bengkel multi-merek modern:
1. Katalog Lengkap Generasi, Rentang Tahun & Kode Mesin mobil Asia (Jepang & Korea),
   Eropa (Jerman, Prancis, Inggris, Swedia), dan China (Wuling, Chery, DFSK, MG, BYD,
   GWM, BAIC, Jetour) lengkap dengan normalisasi alias lapangan (mis. 1TR-VE <-> 1TR-FE,
   2GD <-> 2GD-FTV, 2KD <-> 2KD-FTV).
2. Guardrail Keamanan Wiring: membedakan secara tegas apakah diagnosa memakai Manual OEM
   yang benar-benar terverifikasi untuk model+tahun tersebut, atau masih memakai standar
   Universal OBD-II (SAE J2012) agar mekanik tidak salah baca pinout ECM lintas merek/tahun.
3. Manajemen Paket Manual Kustom (`custom_manual_packs.json`): memungkinkan penambahan
   buku manual model baru kapan saja tanpa mengubah kode sumber backend/aplikasi.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# 1. HELPER DEFINISI VARIAN MESIN & NORMALISASI ALIAS
# ---------------------------------------------------------------------------


def _ev(
    code: str,
    cc: str,
    fuel: str,
    desc: str,
    aliases: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "cc": cc,
        "fuel": fuel,
        "desc": desc,
        "aliases": aliases or [],
    }


def _gen(
    generation_id: str,
    region: str,
    origin_country: str,
    brand: str,
    model: str,
    model_aliases: list[str],
    generation_label: str,
    engine_variants: list[dict[str, Any]],
    year_start: int,
    year_end: int,
    wiring_platform: str,
    notes: str,
) -> dict[str, Any]:
    codes = [v["code"] for v in engine_variants]
    ccs = list(dict.fromkeys(v["cc"] for v in engine_variants if v.get("cc")))
    fuels = list(dict.fromkeys(v["fuel"] for v in engine_variants if v.get("fuel")))
    all_aliases: list[str] = []
    for v in engine_variants:
        for al in v.get("aliases", []):
            if al not in all_aliases:
                all_aliases.append(al)
    return {
        "generation_id": generation_id,
        "region": region,  # "Asia" | "Eropa" | "China"
        "origin_country": origin_country,
        "brand": brand,
        "model": model,
        "model_aliases": model_aliases,
        "generation_label": generation_label,
        "engine_codes": codes,
        "engine_aliases": all_aliases,
        "engine_variants": engine_variants,
        "engine_cc": " / ".join(ccs),
        "fuel_types": fuels,
        "year_start": year_start,
        "year_end": year_end,
        "wiring_platform": wiring_platform,
        "notes": notes,
    }


def _norm_code(raw: str) -> str:
    """Normalisasi kode mesin (hapus spasi, strip, titik; huruf kecil)."""
    return re.sub(r"[^a-z0-9]", "", (raw or "").strip().lower())


# ---------------------------------------------------------------------------
# 2. KATALOG LENGKAP GENERASI & KODE MESIN (ASIA · EROPA · CHINA)
# ---------------------------------------------------------------------------

VEHICLE_GENERATION_CATALOG: list[dict[str, Any]] = [
    # =========================================================================
    # REGION: ASIA — JEPANG
    # =========================================================================
    # --- SUZUKI ---
    _gen(
        "suzuki_jb420", "Asia", "Jepang", "Suzuki", "Grand Vitara",
        ["grand vitara", "vitara", "jb420", "escudo 2.0", "vitara 2.4"],
        "Grand Vitara Gen 2 (JB420 / JB424)",
        [
            _ev("J20A", "2.0L", "Bensin", "2.0L DOHC 16V MPI (Manual OEM Terpasang)", ["J20"]),
            _ev("J24B", "2.4L", "Bensin", "2.4L DOHC VVT (Grand Vitara 2.4)", ["J24"]),
        ],
        2006, 2018, "suzuki_jb420_j20a",
        "Manual OEM Suzuki Grand Vitara JB420 Vol 1 & Vol 2 (ECM C37/E23, TCM E92/E93, BCM G30-G32).",
    ),
    _gen(
        "suzuki_grand_vitara_hybrid", "Asia", "Jepang", "Suzuki", "Grand Vitara",
        ["grand vitara", "grand vitara hybrid", "vitara hybrid"],
        "Grand Vitara Smart Hybrid (K15C)",
        [_ev("K15C", "1.5L", "Hybrid", "1.5L DualJet Smart Hybrid SHVS", ["K15C Hybrid"])],
        2023, 2027, "suzuki_k15c_shvs",
        "Grand Vitara generasi baru bermesin K15C DualJet dengan sistem mild-hybrid ISG.",
    ),
    _gen(
        "suzuki_ertiga_gen1", "Asia", "Jepang", "Suzuki", "Ertiga",
        ["ertiga", "ertiga lama", "ertiga dreza", "new ertiga", "ertiga diesel"],
        "Ertiga Gen 1 (ZE / ZF — Model Lama)",
        [
            _ev("K14B", "1.4L", "Bensin", "1.4L DOHC VVT Bensin (1.373 cc)", ["K14"]),
            _ev("D13A", "1.3L", "Diesel", "1.3L DDiS Diesel Hybrid SHVS", ["D13A SHVS", "DDiS"]),
        ],
        2012, 2018, "suzuki_k14b_platform",
        "Ertiga generasi pertama bermesin K14B / D13A. Berbeda pinout & ECU dengan Ertiga Gen 2 K15B.",
    ),
    _gen(
        "suzuki_ertiga_gen2", "Asia", "Jepang", "Suzuki", "Ertiga",
        ["ertiga", "all new ertiga", "ertiga hybrid", "ertiga baru"],
        "All New Ertiga Gen 2 (K15B / Smart Hybrid)",
        [_ev("K15B", "1.5L", "Bensin", "1.5L DOHC VVT (HEARTECT / Hybrid SHVS)", ["K15", "K15B Hybrid"])],
        2018, 2027, "suzuki_k15b_platform",
        "Ertiga generasi ke-2 bermesin K15B (platform HEARTECT, berbagi skema mesin dengan Suzuki XL7).",
    ),
    _gen(
        "suzuki_xl7", "Asia", "Jepang", "Suzuki", "XL7",
        ["xl7", "xl 7", "xl-7", "xl7 hybrid"],
        "Suzuki XL7 / XL7 Hybrid (HEARTECT K15B)",
        [_ev("K15B", "1.5L", "Bensin", "1.5L DOHC VVT / Smart Hybrid ISG", ["K15", "K15B Hybrid"])],
        2020, 2027, "suzuki_k15b_platform",
        "Berbagi mesin dan mayoritas wiring harness ECM K15B dengan All New Ertiga Gen 2 (2018+).",
    ),
    _gen(
        "suzuki_apv", "Asia", "Jepang", "Suzuki", "APV",
        ["apv", "apv arena", "apv luxury", "mega carry"],
        "Suzuki APV / Arena / Mega Carry (G15A)",
        [_ev("G15A", "1.5L", "Bensin", "1.5L SOHC 16V MPI non-VVT", ["G15"])],
        2005, 2026, "suzuki_g15a_platform",
        "Platform mesin G15A 1.5L non-VVT niaga & MPV.",
    ),
    _gen(
        "suzuki_new_carry", "Asia", "Jepang", "Suzuki", "Carry",
        ["carry", "new carry", "carry pickup", "carry pick up", "futura"],
        "Suzuki New Carry Pick Up (K15B-C)",
        [
            _ev("K15B-C", "1.5L", "Bensin", "1.5L DOHC Komersial (New Carry 2019+)", ["K15BC"]),
            _ev("G15A", "1.5L", "Bensin", "1.5L Carry Futura Injection (2005-2019)"),
        ],
        2005, 2027, "suzuki_carry_platform",
        "Carry Futura lama memakai G15A; New Carry 2019+ memakai mesin K15B-C.",
    ),
    _gen(
        "suzuki_swift_sx4_baleno", "Asia", "Jepang", "Suzuki", "Swift / SX4 / Baleno",
        ["swift", "sx4", "s-cross", "scross", "baleno", "baleno hatchback", "aerio", "neo baleno"],
        "Suzuki Swift / SX4 / S-Cross / Baleno",
        [
            _ev("M15A", "1.5L", "Bensin", "1.5L DOHC VVT (Swift lama, SX4, S-Cross, Neo Baleno)", ["M15"]),
            _ev("K14B", "1.4L", "Bensin", "1.4L DOHC VVT (All New Swift, Baleno 2017-2021)"),
            _ev("K15B", "1.5L", "Bensin", "1.5L DOHC VVT (New Baleno 2022+)"),
            _ev("M16A", "1.6L", "Bensin", "1.6L DOHC VVT (Swift Sport)"),
        ],
        2005, 2027, "suzuki_compact_platform",
        "Keluarga hatchback & crossover Suzuki (M15A generasi awal, K14B pertengahan, K15B terbaru).",
    ),
    _gen(
        "suzuki_ignis_wagonr_spresso", "Asia", "Jepang", "Suzuki", "Ignis / Karimun / S-Presso",
        ["ignis", "karimun", "wagon r", "karimun wagon r", "s-presso", "spresso", "splash"],
        "Suzuki Ignis / Karimun Wagon R / S-Presso / Splash",
        [
            _ev("K12M", "1.2L", "Bensin", "1.2L 4-Silinder (Ignis & Splash)", ["K12"]),
            _ev("K10B", "1.0L", "Bensin", "1.0L 3-Silinder (Karimun Wagon R / S-Presso lama)", ["K10"]),
            _ev("K10C", "1.0L", "Bensin", "1.0L DualJet (S-Presso 2023+)", ["K10C DualJet"]),
        ],
        2010, 2027, "suzuki_citycar_platform",
        "City car Suzuki 1.0L–1.2L (transmisi MT & AGS).",
    ),
    _gen(
        "suzuki_jimny_jb74", "Asia", "Jepang", "Suzuki", "Jimny",
        ["jimny", "jimny jb74", "jimny 5 pintu", "jimny 3 pintu"],
        "Suzuki Jimny Gen 4 (JB74)",
        [_ev("K15B", "1.5L", "Bensin", "1.5L DOHC VVT 4WD Longitudinal", ["K15"])],
        2019, 2027, "suzuki_jb74_k15b",
        "Jimny 4x4 generasi terbaru bermesin K15B longitudinal.",
    ),

    # --- TOYOTA ---
    _gen(
        "toyota_innova_gen1", "Asia", "Jepang", "Toyota", "Innova",
        ["innova", "kijang innova", "innova lama", "innova bensin", "innova diesel", "innova barong"],
        "Kijang Innova Gen 1 (1TR-FE Bensin / 2KD-FTV Diesel)",
        [
            _ev("1TR-FE", "2.0L", "Bensin", "2.0L VVT-i Bensin Innova Gen 1 (sering disebut 1TR-VE)", ["1TR-VE", "1TRVE", "1TR", "1TRFE"]),
            _ev("2KD-FTV", "2.5L", "Diesel", "2.5L D-4D Common-Rail Turbo Diesel Innova Gen 1", ["2KD", "2KDFTV"]),
            _ev("2TR-FE", "2.7L", "Bensin", "2.7L VVT-i Bensin (Innova 2.7 V)", ["2TR-VE", "2TR", "2TRFE"]),
        ],
        2004, 2015, "toyota_innova_imv1",
        "Platform IMV generasi pertama (Euro 2/3). Kode resmi 2.0 bensin adalah 1TR-FE (di bengkel sering dicari sebagai 1TR-VE).",
    ),
    _gen(
        "toyota_innova_reborn", "Asia", "Jepang", "Toyota", "Innova",
        ["innova", "innova reborn", "reborn", "kijang innova reborn", "reborn diesel", "reborn bensin", "venturer"],
        "Kijang Innova Reborn Gen 2 (1TR-FE Dual VVT-i / 2GD-FTV Diesel)",
        [
            _ev("1TR-FE", "2.0L", "Bensin", "2.0L Dual VVT-i Bensin Innova Reborn (sering disebut 1TR-VE)", ["1TR-VE", "1TRVE", "1TR", "1TRFE"]),
            _ev("2GD-FTV", "2.4L", "Diesel", "2.4L VNT Intercooler Common-Rail Diesel (Reborn 2GD)", ["2GD", "2GDFTV"]),
            _ev("1GD-FTV", "2.8L", "Diesel", "2.8L VNT Common-Rail Diesel", ["1GD", "1GDFTV"]),
        ],
        2016, 2026, "toyota_innova_imv2",
        "Innova Reborn bensin 2.0L memakai 1TR-FE Dual VVT-i; varian diesel 2.4L memakai 2GD-FTV bertekanan common-rail tinggi & CAN Bus.",
    ),
    _gen(
        "toyota_innova_zenix", "Asia", "Jepang", "Toyota", "Innova Zenix",
        ["innova zenix", "zenix", "kijang innova zenix", "zenix hybrid"],
        "All New Kijang Innova Zenix (TNGA FWD M20A)",
        [
            _ev("M20A-FKS", "2.0L", "Bensin", "2.0L Dynamic Force Bensin TNGA (Non-Hybrid)", ["M20A"]),
            _ev("M20A-FXS", "2.0L", "Hybrid", "2.0L Dynamic Force Hybrid Gen-5", ["M20A Hybrid"]),
        ],
        2022, 2027, "toyota_tnga_zenix",
        "Platform TNGA-C FWD dengan CVT / e-CVT Hybrid, sangat berbeda total dari Innova Reborn RWD.",
    ),
    _gen(
        "toyota_fortuner_gen1", "Asia", "Jepang", "Toyota", "Fortuner",
        ["fortuner", "fortuner vnt", "fortuner lama", "fortuner trd"],
        "Toyota Fortuner Gen 1 (2KD-FTV / 2TR-FE)",
        [
            _ev("2KD-FTV", "2.5L", "Diesel", "2.5L D-4D / VNT Turbo Diesel", ["2KD"]),
            _ev("2TR-FE", "2.7L", "Bensin", "2.7L VVT-i Bensin", ["2TR", "2TR-VE"]),
        ],
        2005, 2015, "toyota_imv1_fortuner",
        "Fortuner generasi pertama berbasis platform IMV 1 (berbagi mesin dengan Innova Gen 1 & Hilux).",
    ),
    _gen(
        "toyota_fortuner_gen2", "Asia", "Jepang", "Toyota", "Fortuner",
        ["fortuner", "fortuner vrz", "fortuner srz", "fortuner gr", "all new fortuner"],
        "All New Fortuner VRZ / SRZ / GR Gen 2 (2GD / 1GD / 2TR)",
        [
            _ev("2GD-FTV", "2.4L", "Diesel", "2.4L VNT Intercooler Diesel (VRZ / G)", ["2GD"]),
            _ev("1GD-FTV", "2.8L", "Diesel", "2.8L VNT Intercooler Diesel (GR Sport 2.8)", ["1GD"]),
            _ev("2TR-FE", "2.7L", "Bensin", "2.7L Dual VVT-i Bensin (SRZ)", ["2TR", "2TR-VE"]),
        ],
        2016, 2027, "toyota_imv2_fortuner",
        "Fortuner Gen 2 VRZ 2.4 (2GD-FTV) & GR 2.8 (1GD-FTV).",
    ),
    _gen(
        "toyota_hilux_hiace", "Asia", "Jepang", "Toyota", "Hilux / HiAce",
        ["hilux", "hilux revo", "hilux vigo", "hilux rangga", "hiace", "hiace premio", "hiace commuter"],
        "Toyota Hilux / Hilux Rangga / HiAce",
        [
            _ev("2GD-FTV", "2.4L", "Diesel", "2.4L Diesel (Hilux Revo / Rangga Diesel)", ["2GD"]),
            _ev("1GD-FTV", "2.8L", "Diesel", "2.8L Diesel (HiAce Premio / Hilux GR)", ["1GD"]),
            _ev("2KD-FTV", "2.5L", "Diesel", "2.5L Diesel (Hilux Vigo / HiAce Commuter lama)", ["2KD"]),
            _ev("1KD-FTV", "3.0L", "Diesel", "3.0L Diesel (HiAce Commuter / Hilux 3.0)", ["1KD"]),
            _ev("1TR-FE", "2.0L", "Bensin", "2.0L Bensin (Hilux Single Cab / Rangga Bensin)", ["1TR-VE", "1TR"]),
        ],
        2005, 2027, "toyota_commercial_imv",
        "Keluarga niaga & double cabin Toyota IMV (berbagi keluarga mesin TR, KD, GD).",
    ),
    _gen(
        "toyota_avanza_gen1_2_kv", "Asia", "Jepang", "Toyota", "Avanza",
        ["avanza", "veloz", "avanza vvti", "all new avanza", "avanza lama"],
        "Avanza / Veloz Gen 1 & Gen 2 Awal (K3-VE / 3SZ-VE)",
        [
            _ev("K3-VE", "1.3L", "Bensin", "1.3L VVT-i RWD (2004-2015)", ["K3VE"]),
            _ev("3SZ-VE", "1.5L", "Bensin", "1.5L VVT-i RWD (Avanza S / Veloz 2006-2015)", ["3SZVE"]),
        ],
        2004, 2015, "toyota_daihatsu_k3ve",
        "Mesin VVT-i generasi K3-VE (1.3) & 3SZ-VE (1.5) RWD, berbagi arsitektur dengan Daihatsu Xenia.",
    ),
    _gen(
        "toyota_avanza_gen2_nr", "Asia", "Jepang", "Toyota", "Avanza",
        ["avanza", "grand new avanza", "veloz", "grand veloz"],
        "Grand New Avanza / Veloz (Dual VVT-i RWD)",
        [
            _ev("1NR-VE", "1.3L", "Bensin", "1.3L Dual VVT-i RWD", ["1NRVE", "1NR"]),
            _ev("2NR-VE", "1.5L", "Bensin", "1.5L Dual VVT-i RWD", ["2NRVE", "2NR"]),
        ],
        2015, 2021, "toyota_nr_rwd",
        "Mesin Dual VVT-i 1NR-VE / 2NR-VE penggerak belakang (RWD).",
    ),
    _gen(
        "toyota_avanza_gen3_fwd", "Asia", "Jepang", "Toyota", "Avanza",
        ["avanza", "all new avanza", "veloz", "all new veloz", "avanza fwd"],
        "All New Avanza / Veloz Gen 3 (DNGA FWD D-CVT)",
        [
            _ev("1NR-VE", "1.3L", "Bensin", "1.3L Dual VVT-i FWD (Avanza E)", ["1NRVE"]),
            _ev("2NR-VE", "1.5L", "Bensin", "1.5L Dual VVT-i FWD (Avanza G / Veloz)", ["2NRVE"]),
        ],
        2021, 2027, "toyota_dnga_fwd",
        "Platform DNGA penggerak depan (FWD) dengan transmisi D-CVT & CAN Bus modern.",
    ),
    _gen(
        "toyota_calya_agya_raize", "Asia", "Jepang", "Toyota", "Calya / Agya / Raize",
        ["calya", "agya", "raize", "agya gr"],
        "Toyota Calya / Agya / Raize",
        [
            _ev("3NR-VE", "1.2L", "Bensin", "1.2L 4-Silinder Dual VVT-i (Calya & Agya 2017-2022)", ["3NRVE", "3NR"]),
            _ev("1KR-DE", "1.0L", "Bensin", "1.0L 3-Silinder (Agya lama 2013-2017)", ["1KRDE", "1KR"]),
            _ev("1KR-VE", "1.0L", "Bensin", "1.0L 3-Silinder VVT-i (Agya 2017-2022)", ["1KRVE"]),
            _ev("WA-VE", "1.2L", "Bensin", "1.2L 3-Silinder Dual VVT-i (All New Agya 2023+ & Raize 1.2)", ["WAVE"]),
            _ev("1KR-VET", "1.0L", "Bensin", "1.0L 3-Silinder Turbo (Raize 1.0T)", ["1KRVET"]),
        ],
        2013, 2027, "toyota_lcgc_dnga",
        "Keluarga LCGC & SUV kompak Toyota-Daihatsu (NR-series, KR-series, WA-VE).",
    ),
    _gen(
        "toyota_rush", "Asia", "Jepang", "Toyota", "Rush",
        ["rush", "rush konde", "all new rush", "rush gr"],
        "Toyota Rush Gen 1 (3SZ-VE) & Gen 2 (2NR-VE)",
        [
            _ev("3SZ-VE", "1.5L", "Bensin", "1.5L VVT-i RWD (Rush Konde 2006-2017)", ["3SZVE"]),
            _ev("2NR-VE", "1.5L", "Bensin", "1.5L Dual VVT-i RWD (All New Rush 2018+)", ["2NRVE"]),
        ],
        2006, 2027, "toyota_rush_rwd",
        "Rush 2006–2017 memakai 3SZ-VE; All New Rush 2018+ memakai 2NR-VE Dual VVT-i.",
    ),
    _gen(
        "toyota_yaris_vios_sienta", "Asia", "Jepang", "Toyota", "Yaris / Vios / Sienta",
        ["yaris", "yaris bakpao", "yaris lele", "yaris joker", "yaris cross", "vios", "limo", "sienta", "ncp91", "nsp151"],
        "Toyota Yaris / Vios / Limo / Sienta / Yaris Cross",
        [
            _ev("1NZ-FE", "1.5L", "Bensin", "1.5L VVT-i (Yaris Bakpao/Lele, Vios/Limo Gen 1-3 awal)", ["1NZFE", "1NZ"]),
            _ev("2NR-FE", "1.5L", "Bensin", "1.5L Dual VVT-i (Yaris 2016+, Vios, Sienta)", ["2NRFE"]),
            _ev("2NR-VE", "1.5L", "Bensin", "1.5L Dual VVT-i (Vios Gen 4 & Yaris Cross Bensin 2023+)"),
            _ev("2NR-VEX", "1.5L", "Hybrid", "1.5L Atkinson Hybrid (Yaris Cross Hybrid 2023+)", ["2NRVEX"]),
        ],
        2003, 2027, "toyota_yaris_vios_platform",
        "1NZ-FE sangat populer hingga 2016; 2NR-FE/2NR-VE/2NR-VEX untuk generasi terbaru.",
    ),
    _gen(
        "toyota_corolla_camry_alphard", "Asia", "Jepang", "Toyota", "Corolla / Camry / Alphard",
        ["corolla", "altis", "corolla cross", "camry", "alphard", "vellfire", "voxy", "nav1", "harrier"],
        "Toyota Corolla Altis / Cross / Camry / Alphard / Voxy",
        [
            _ev("1ZZ-FE", "1.8L", "Bensin", "1.8L VVT-i (Corolla Altis lama)", ["1ZZFE"]),
            _ev("2ZR-FE", "1.8L", "Bensin", "1.8L Dual VVT-i (Altis, Corolla Cross Bensin)", ["2ZRFE"]),
            _ev("2ZR-FXE", "1.8L", "Hybrid", "1.8L Hybrid (Corolla Altis / Cross Hybrid, Prius)", ["2ZRFXE"]),
            _ev("3ZR-FAE", "2.0L", "Bensin", "2.0L Valvematic (Voxy lama, NAV1)", ["3ZRFAE"]),
            _ev("2AZ-FE", "2.4L", "Bensin", "2.4L VVT-i (Camry ACV40, Alphard ANH20, Harrier)", ["2AZFE"]),
            _ev("2AR-FE", "2.5L", "Bensin", "2.5L Dual VVT-i (Camry XV50, Alphard AGH30)", ["2ARFE"]),
            _ev("A25A-FXS", "2.5L", "Hybrid", "2.5L Dynamic Force Hybrid (Camry XV70, Alphard AH40)", ["A25A"]),
            _ev("2GR-FE", "3.5L", "Bensin", "3.5L V6 (Alphard/Vellfire 3.5, Camry 3.5)", ["2GRFE", "2GR-FKS"]),
        ],
        2004, 2027, "toyota_mid_luxury_platform",
        "Keluarga sedan, MPV premium & SUV Toyota (ZR, AZ, AR, A25A, GR).",
    ),
    _gen(
        "toyota_kijang_kapsul", "Asia", "Jepang", "Toyota", "Kijang Kapsul",
        ["kijang", "kijang kapsul", "kijang efi", "kijang krista", "kijang lgx"],
        "Toyota Kijang Kapsul EFI & Diesel (7K-E / 1RZ-E / 2L)",
        [
            _ev("7K-E", "1.8L", "Bensin", "1.8L EFI Bensin (Kijang LGX/SGX/Krista 1.8)", ["7KE"]),
            _ev("1RZ-E", "2.0L", "Bensin", "2.0L EFI Bensin (Kijang 2.0)", ["1RZE"]),
            _ev("2L", "2.4L", "Diesel", "2.4L Diesel Non-Turbo Konvensional"),
        ],
        1997, 2004, "toyota_kijang_kapsul",
        "Kijang generasi ke-4 sebelum Kijang Innova.",
    ),

    # --- DAIHATSU ---
    _gen(
        "daihatsu_xenia_all", "Asia", "Jepang", "Daihatsu", "Xenia",
        ["xenia", "great new xenia", "all new xenia", "xenia vvti"],
        "Daihatsu Xenia Gen 1–3 (EJ-VE / K3-VE / 1NR-VE / 2NR-VE)",
        [
            _ev("EJ-VE", "1.0L", "Bensin", "1.0L 3-Silinder VVT-i (Xenia Li/Mi/D/M)", ["EJ-DE", "EJVE"]),
            _ev("K3-VE", "1.3L", "Bensin", "1.3L VVT-i RWD (2004-2015)", ["K3VE"]),
            _ev("1NR-VE", "1.3L", "Bensin", "1.3L Dual VVT-i (2015-2027 RWD & FWD)", ["1NRVE"]),
            _ev("2NR-VE", "1.5L", "Bensin", "1.5L Dual VVT-i (2019-2027)", ["2NRVE"]),
        ],
        2004, 2027, "daihatsu_xenia_platform",
        "Xenia 2004–2015 (EJ-VE/K3-VE), 2015–2021 (1NR-VE/2NR-VE RWD), 2021+ (DNGA FWD CVT).",
    ),
    _gen(
        "daihatsu_granmax_luxio_terios", "Asia", "Jepang", "Daihatsu", "Gran Max / Luxio / Terios",
        ["gran max", "granmax", "luxio", "terios", "all new terios"],
        "Daihatsu Gran Max / Luxio / Terios",
        [
            _ev("K3-DE", "1.3L", "Bensin", "1.3L DOHC non-VVT (Gran Max 1.3)", ["K3DE"]),
            _ev("3SZ-VE", "1.5L", "Bensin", "1.5L VVT-i (Gran Max 1.5, Luxio, Terios lama)", ["3SZVE"]),
            _ev("2NR-VE", "1.5L", "Bensin", "1.5L Dual VVT-i (All New Terios 2018+ & New Gran Max 1.5 2022+)", ["2NRVE"]),
        ],
        2006, 2027, "daihatsu_rwd_commercial",
        "Gran Max 1.5 terbaru (2022+) sudah beralih dari 3SZ-VE ke 2NR-VE Dual VVT-i + EPS.",
    ),
    _gen(
        "daihatsu_sigra_ayla_rocky_sirion", "Asia", "Jepang", "Daihatsu", "Sigra / Ayla / Rocky / Sirion",
        ["sigra", "ayla", "rocky", "sirion"],
        "Daihatsu Sigra / Ayla / Rocky / Sirion",
        [
            _ev("1KR-VE", "1.0L", "Bensin", "1.0L 3-Silinder VVT-i (Sigra 1.0, Ayla 1.0)", ["1KR-DE", "1KRVE"]),
            _ev("3NR-VE", "1.2L", "Bensin", "1.2L 4-Silinder Dual VVT-i (Sigra 1.2, Ayla 1.2 lama)", ["3NRVE"]),
            _ev("WA-VE", "1.2L", "Bensin", "1.2L 3-Silinder (Rocky 1.2 & All New Ayla 1.2 2023+)", ["WAVE"]),
            _ev("1KR-VET", "1.0L", "Bensin", "1.0L 3-Silinder Turbo (Rocky 1.0T)", ["1KRVET"]),
            _ev("1NR-VE", "1.3L", "Bensin", "1.3L Dual VVT-i (New Sirion)"),
        ],
        2012, 2027, "daihatsu_compact_platform",
        "Keluarga kompak Daihatsu berbagi kode mesin dengan Toyota Agya/Calya/Raize.",
    ),

    # --- HONDA ---
    _gen(
        "honda_brio_gen1", "Asia", "Jepang", "Honda", "Brio",
        ["brio", "brio satya", "brio rs", "brio lama", "dd1"],
        "Honda Brio Gen 1 (DD1 / DD2)",
        [
            _ev("L12B", "1.2L", "Bensin", "1.2L SOHC i-VTEC (Satya & RS 2013-2018)", ["L12B1", "L12"]),
            _ev("L13A", "1.3L", "Bensin", "1.3L SOHC i-VTEC (Brio CBU 2012-2013)", ["L13"]),
        ],
        2012, 2018, "honda_dd1_brio",
        "Brio generasi pertama (CBU 1.3L 2012-2013 & Satya/RS 1.2L 2013-2018).",
    ),
    _gen(
        "honda_brio_gen2", "Asia", "Jepang", "Honda", "Brio",
        ["brio", "all new brio", "brio satya", "brio rs"],
        "All New Honda Brio Gen 2 (L12B3)",
        [_ev("L12B3", "1.2L", "Bensin", "1.2L SOHC i-VTEC (All New Brio 2018+)", ["L12B"])],
        2018, 2027, "honda_dd1_gen2",
        "All New Brio bodi lebih panjang dengan pembaruan ECU & BCM.",
    ),
    _gen(
        "honda_jazz_city_freed", "Asia", "Jepang", "Honda", "Jazz / City / Freed",
        ["jazz", "jazz gd3", "jazz ge8", "jazz gk5", "city", "city hatchback", "freed"],
        "Honda Jazz / City / Freed (L15A / L15Z / L15ZF)",
        [
            _ev("L15A", "1.5L", "Bensin", "1.5L i-DSI / VTEC / i-VTEC (Jazz GD3/GE8, Freed, City lama)", ["L15A1", "L15A7"]),
            _ev("L15Z1", "1.5L", "Bensin", "1.5L SOHC i-VTEC (Jazz GK5, City GM6)", ["L15Z"]),
            _ev("L15ZF", "1.5L", "Bensin", "1.5L DOHC i-VTEC (City Hatchback GN5, New City)", ["L15Z DOHC"]),
        ],
        2004, 2027, "honda_l15_platform",
        "Jazz GD3/GE8 memakai L15A (8 busi pada i-DSI); GK5 memakai L15Z1 SOHC; City Hatchback memakai L15ZF DOHC.",
    ),
    _gen(
        "honda_mobilio_brv_wrv", "Asia", "Jepang", "Honda", "Mobilio / BR-V / WR-V",
        ["mobilio", "br-v", "brv", "all new br-v", "wr-v", "wrv"],
        "Honda Mobilio / BR-V / WR-V (L15Z1 / L15ZF)",
        [
            _ev("L15Z1", "1.5L", "Bensin", "1.5L SOHC i-VTEC (Mobilio & BR-V Gen 1 2014-2023)", ["L15Z"]),
            _ev("L15ZF", "1.5L", "Bensin", "1.5L DOHC i-VTEC (All New BR-V Gen 2 & WR-V 2022+)", ["L15ZF DOHC"]),
        ],
        2014, 2027, "honda_l15z_mpv",
        "Mobilio & BR-V Gen 1 memakai L15Z1 SOHC; BR-V Gen 2 & WR-V memakai L15ZF DOHC.",
    ),
    _gen(
        "honda_hrv", "Asia", "Jepang", "Honda", "HR-V",
        ["hr-v", "hrv", "all new hr-v", "hrv turbo", "hrv rs"],
        "Honda HR-V Gen 1 & Gen 2 (L15Z6 / R18Z9 / L15ZF / L15C1)",
        [
            _ev("L15Z6", "1.5L", "Bensin", "1.5L SOHC i-VTEC (HR-V Gen 1 2015-2021)"),
            _ev("R18Z9", "1.8L", "Bensin", "1.8L SOHC i-VTEC (HR-V 1.8 Prestige 2015-2021)", ["R18"]),
            _ev("L15ZF", "1.5L", "Bensin", "1.5L DOHC i-VTEC (All New HR-V S/E/SE 2022+)"),
            _ev("L15C1", "1.5L", "Bensin", "1.5L VTEC Turbo (All New HR-V RS 2022+)", ["L15C"]),
        ],
        2015, 2027, "honda_hrv_platform",
        "HR-V Gen 1 (2015–2021) dan Gen 2 (2022+) berbeda total pada ECU, DOHC, dan Turbo RS.",
    ),
    _gen(
        "honda_crv_civic_accord", "Asia", "Jepang", "Honda", "CR-V / Civic / Accord",
        ["crv", "cr-v", "civic", "civic fd", "civic fb", "civic fc", "civic fe", "civic turbo", "accord", "odyssey"],
        "Honda CR-V / Civic / Accord (R20A / K24Z / L15B7 / LFB1)",
        [
            _ev("R18A", "1.8L", "Bensin", "1.8L SOHC i-VTEC (Civic FD1 / FB2)", ["R18A1", "R18Z1"]),
            _ev("R20A", "2.0L", "Bensin", "2.0L SOHC i-VTEC (CR-V Gen 3/4/5, Civic FD2 2.0)", ["R20A1", "R20A5"]),
            _ev("K24Z", "2.4L", "Bensin", "2.4L DOHC i-VTEC (CR-V Gen 3/4, Accord CP2/CR2, Odyssey)", ["K24A", "K24W", "K24"]),
            _ev("L15B7", "1.5L", "Bensin", "1.5L VTEC Turbo (CR-V Turbo Gen 5/6, Civic Turbo FC/FE, Accord 1.5T)", ["L15BG", "L15BE", "L15B"]),
            _ev("LFB1", "2.0L", "Hybrid", "2.0L e:HEV Hybrid (All New CR-V RS e:HEV & Accord e:HEV 2023+)", ["LFC", "e:HEV"]),
        ],
        2006, 2027, "honda_crv_civic_platform",
        "Keluarga mesin menengah-atas Honda: R-series NA, K24 DOHC, L15B Turbo, dan e:HEV Hybrid.",
    ),

    # --- MITSUBISHI ---
    _gen(
        "mitsubishi_xpander_gen1", "Asia", "Jepang", "Mitsubishi", "Xpander",
        ["xpander", "xpander cross"],
        "Mitsubishi Xpander Pre-Facelift (4A91 · 4AT/5MT)",
        [_ev("4A91", "1.5L", "Bensin", "1.5L DOHC MIVEC (4AT / 5MT)", ["4A91 MIVEC"])],
        2017, 2021, "mitsubishi_nc1w_pre",
        "Xpander keluaran awal (transmisi otomatis 4-percepatan konvensional).",
    ),
    _gen(
        "mitsubishi_xpander_cvt", "Asia", "Jepang", "Mitsubishi", "Xpander / XForce",
        ["xpander", "new xpander", "xpander cross", "xforce"],
        "New Mitsubishi Xpander / XForce (4A91 · CVT)",
        [_ev("4A91", "1.5L", "Bensin", "1.5L DOHC MIVEC + CVT (New Xpander & XForce)", ["4A91 CVT"])],
        2021, 2027, "mitsubishi_nc1w_cvt",
        "New Xpander facelift & XForce dengan transmisi CVT & modul ETACS/ABS terbaru.",
    ),
    _gen(
        "mitsubishi_pajero_triton_gen2", "Asia", "Jepang", "Mitsubishi", "Pajero Sport / Triton",
        ["pajero", "pajero sport", "pajero dakar", "pajero exceed", "triton", "strada triton"],
        "Pajero Sport Gen 2 / Strada Triton (4D56 Diesel)",
        [
            _ev("4D56", "2.5L", "Diesel", "2.5L DI-D / VGT Common-Rail Diesel (Exceed / Dakar lama)", ["4D56T", "4D56 VGT"]),
            _ev("6B31", "3.0L", "Bensin", "3.0L V6 MIVEC Bensin (Pajero Sport V6)"),
        ],
        2008, 2015, "mitsubishi_4d56_platform",
        "Pajero Sport lama & Strada Triton memakai mesin 4D56 timing belt.",
    ),
    _gen(
        "mitsubishi_pajero_triton_gen3", "Asia", "Jepang", "Mitsubishi", "Pajero Sport / Triton",
        ["pajero", "pajero sport", "all new pajero", "pajero dakar", "pajero ultimate", "triton", "new triton"],
        "All New Pajero Sport / New Triton (4N15 / 4N16 MIVEC Diesel)",
        [
            _ev("4N15", "2.4L", "Diesel", "2.4L MIVEC VGT Aluminium Diesel (Dakar / Ultimate 8AT)", ["4N15 MIVEC"]),
            _ev("4D56", "2.5L", "Diesel", "2.5L DI-D Diesel (Pajero Exceed / GLX)"),
            _ev("4N16", "2.4L", "Diesel", "2.4L Bi-Turbo / VGT Diesel (All New Triton 2024+)"),
        ],
        2016, 2027, "mitsubishi_4n15_platform",
        "All New Pajero Sport Dakar memakai 4N15 (timing chain) & transmisi 8AT; varian Exceed masih memakai 4D56.",
    ),
    _gen(
        "mitsubishi_l300_outlander_mirage", "Asia", "Jepang", "Mitsubishi", "L300 / Outlander / Mirage",
        ["l300", "l300 euro 4", "outlander", "outlander sport", "mirage", "grandis", "kuda"],
        "Mitsubishi L300 / Outlander Sport / Mirage / Grandis",
        [
            _ev("4D56", "2.5L", "Diesel", "2.5L Diesel Konvensional (L300 Euro 2)"),
            _ev("4N14", "2.2L", "Diesel", "2.2L Common-Rail Turbo Intercooler (L300 Euro 4 2022+)"),
            _ev("4B11", "2.0L", "Bensin", "2.0L DOHC MIVEC (Outlander Sport & Lancer EX)"),
            _ev("3A92", "1.2L", "Bensin", "1.2L 3-Silinder MIVEC (Mirage)"),
            _ev("4G69", "2.4L", "Bensin", "2.4L MIVEC (Grandis)"),
        ],
        2005, 2027, "mitsubishi_misc_platform",
        "Perhatikan perbedaan L300 lama (4D56 mekanikal) vs L300 Euro 4 2022+ (4N14 Common-Rail ECU).",
    ),

    # --- NISSAN ---
    _gen(
        "nissan_livina_march_juke", "Asia", "Jepang", "Nissan", "Livina / March / Juke",
        ["livina", "grand livina", "evalia", "march", "juke", "almera", "all new livina"],
        "Nissan Grand Livina / Evalia / March / Juke / All New Livina",
        [
            _ev("HR15DE", "1.5L", "Bensin", "1.5L DOHC CVTC (Grand Livina, Evalia, Juke)", ["HR15"]),
            _ev("MR18DE", "1.8L", "Bensin", "1.8L DOHC CVTC (Grand Livina 1.8)", ["MR18"]),
            _ev("HR12DE", "1.2L", "Bensin", "1.2L 3-Silinder (March 1.2 & Kicks e-Power)", ["HR12"]),
            _ev("4A91", "1.5L", "Bensin", "1.5L MIVEC (All New Livina 2019+ basis Xpander)"),
        ],
        2007, 2026, "nissan_hr_platform",
        "Grand Livina L10/L11 memakai HR15DE; All New Livina 2019+ berbagi mesin & platform 4A91 dengan Xpander.",
    ),
    _gen(
        "nissan_xtrail_serena_navara", "Asia", "Jepang", "Nissan", "X-Trail / Serena / Navara / Terra",
        ["x-trail", "xtrail", "serena", "navara", "terra", "teana"],
        "Nissan X-Trail / Serena / Navara / Terra",
        [
            _ev("QR20DE", "2.0L", "Bensin", "2.0L DOHC (X-Trail T30, Serena C24)", ["QR20"]),
            _ev("QR25DE", "2.5L", "Bensin", "2.5L DOHC (X-Trail T30/T31/T32 2.5, Teana)", ["QR25"]),
            _ev("MR20DE", "2.0L", "Bensin", "2.0L DOHC (X-Trail T31 2.0, Serena C26)", ["MR20", "MR20DD"]),
            _ev("MR20DD", "2.0L", "Bensin", "2.0L Direct Injection (X-Trail T32 2.0, Serena C26/C27)"),
            _ev("YD25DDTi", "2.5L", "Diesel", "2.5L VGS Turbo Diesel (Navara NP300 & Terra)", ["YD25"]),
        ],
        2003, 2027, "nissan_mid_suv_platform",
        "Perhatikan perbedaan MR20DE (port injection) vs MR20DD (Direct Injection tekanan tinggi).",
    ),

    # --- MAZDA ---
    _gen(
        "mazda_skyactiv_lineup", "Asia", "Jepang", "Mazda", "Mazda2 / CX-3 / CX-5 / Mazda3",
        ["mazda2", "mazda 2", "mazda3", "mazda 3", "cx-3", "cx3", "cx-5", "cx5", "cx-30", "cx-8", "cx-9", "biante"],
        "Mazda SkyActiv-G / MZR (Mazda2, CX-3, Mazda3, CX-5, Biante)",
        [
            _ev("ZY-VE", "1.5L", "Bensin", "1.5L MZR (Mazda2 non-SkyActiv 2009-2014)", ["ZYVE"]),
            _ev("P5-VPS", "1.5L", "Bensin", "1.5L SkyActiv-G Direct Injection (Mazda2 & CX-3 1.5)", ["P5VPS"]),
            _ev("PE-VPS", "2.0L", "Bensin", "2.0L SkyActiv-G (CX-5 2.0, CX-3 2.0, Mazda3, CX-30, Biante)", ["PEVPS"]),
            _ev("PY-VPS", "2.5L", "Bensin", "2.5L SkyActiv-G (CX-5 2.5, Mazda6, CX-8)", ["PYVPS", "PY-VPTS"]),
            _ev("SH-VPTS", "2.2L", "Diesel", "2.2L SkyActiv-D Twin-Turbo Diesel"),
        ],
        2009, 2027, "mazda_skyactiv_platform",
        "Mesin SkyActiv-G memiliki kompresi tinggi (13:1–14:1) dengan Direct Injection & sistem i-STOP.",
    ),

    # --- ISUZU ---
    _gen(
        "isuzu_panther_traga_mux", "Asia", "Jepang", "Isuzu", "Panther / MU-X / D-Max / Traga",
        ["panther", "panther touring", "panther kapsul", "traga", "mu-x", "mux", "d-max", "dmax", "elf"],
        "Isuzu Panther / Traga / MU-X / D-Max",
        [
            _ev("4JA1-L", "2.5L", "Diesel", "2.5L Direct Injection Turbo (Panther Touring/LV/LS & Traga)", ["4JA1"]),
            _ev("4JK1-TC", "2.5L", "Diesel", "2.5L VGS Common-Rail Diesel (MU-X & D-Max 2014-2021)", ["4JK1"]),
            _ev("RZ4E-TC", "1.9L", "Diesel", "1.9L BluePower Euro 4 Common-Rail (All New MU-X & D-Max 2021+)", ["RZ4E"]),
            _ev("4JJ1-TC", "3.0L", "Diesel", "3.0L Common-Rail Diesel (D-Max 3.0)", ["4JJ1", "4JJ3-TCX"]),
        ],
        1996, 2027, "isuzu_diesel_platform",
        "Panther & Traga memakai 4JA1-L (pompa injeksi mekanis); MU-X/D-Max memakai Common-Rail 4JK1/RZ4E.",
    ),

    # --- SUBARU ---
    _gen(
        "subaru_boxer_lineup", "Asia", "Jepang", "Subaru", "Forester / XV / Crosstrek / BRZ",
        ["forester", "xv", "crosstrek", "wrx", "brz", "outback"],
        "Subaru Boxer (FB20 / FB25 / FA20 / FA24)",
        [
            _ev("FB20", "2.0L", "Bensin", "2.0L Boxer NA (XV, Forester, Crosstrek)"),
            _ev("FB25", "2.5L", "Bensin", "2.5L Boxer NA (Outback, Forester 2.5)"),
            _ev("FA20", "2.0L", "Bensin", "2.0L Boxer Direct Injection / Turbo (BRZ, WRX, Forester XT)", ["FA24"]),
        ],
        2012, 2027, "subaru_boxer_platform",
        "Konfigurasi mesin Boxer horizontal berlawanan (bank 1 kanan, bank 2 kiri).",
    ),

    # =========================================================================
    # REGION: ASIA — KOREA SELATAN
    # =========================================================================
    # --- HYUNDAI ---
    _gen(
        "hyundai_stargazer_creta", "Asia", "Korea Selatan", "Hyundai", "Stargazer / Creta",
        ["stargazer", "stargazer x", "creta"],
        "Hyundai Stargazer / Creta (Smartstream G4FL 1.5)",
        [_ev("G4FL", "1.5L", "Bensin", "1.5L Smartstream DPI Dual-Port Injection + IVT", ["Smartstream 1.5"])],
        2022, 2027, "hyundai_smartstream_g4fl",
        "Mesin 1.5L Smartstream dengan 2 injektor per silinder (DPI) & transmisi IVT.",
    ),
    _gen(
        "hyundai_santafe_palisade_tucson_h1", "Asia", "Korea Selatan", "Hyundai", "Santa Fe / Palisade / Tucson / H-1",
        ["santa fe", "santafe", "palisade", "staria", "tucson", "h-1", "h1", "avega", "grand avega", "i20"],
        "Hyundai Santa Fe / Palisade / Staria / Tucson / H-1 / Avega",
        [
            _ev("D4HB", "2.2L", "Diesel", "2.2L CRDi e-VGT Diesel (Santa Fe, Palisade, Staria)", ["R2.2 CRDi"]),
            _ev("D4CB", "2.5L", "Diesel", "2.5L CRDi Diesel (Hyundai H-1)"),
            _ev("G4KM", "2.5L", "Bensin", "2.5L Smartstream MPi (Santa Fe Bensin 2021+)", ["G4KE", "G4KJ"]),
            _ev("G4NA", "2.0L", "Bensin", "2.0L Nu MPi (Tucson)"),
            _ev("G4FA", "1.4L", "Bensin", "1.4L Gamma (Grand Avega, i20)", ["G4EE"]),
            _ev("G4FT", "1.6L", "Hybrid", "1.6L T-GDi Turbo Hybrid (All New Santa Fe Hybrid 2024+)"),
        ],
        2008, 2027, "hyundai_multi_platform",
        "Diesel D4HB 2.2 CRDi sangat umum di Palisade, Santa Fe, & Staria.",
    ),
    # --- KIA ---
    _gen(
        "kia_indonesia_lineup", "Asia", "Korea Selatan", "Kia", "Sonet / Seltos / Carens / Carnival / Picanto",
        ["sonet", "seltos", "carens", "carnival", "grand sedona", "picanto", "rio", "sportage"],
        "Kia Sonet / Seltos / Carens / Carnival / Picanto / Rio",
        [
            _ev("G4FL", "1.5L", "Bensin", "1.5L Smartstream (Sonet, Carens 1.5, Seltos 1.5)"),
            _ev("G4LD", "1.4L", "Bensin", "1.4L Kappa T-GDi Turbo + DCT (Seltos 1.4T, Carens 1.4T)"),
            _ev("D4HB", "2.2L", "Diesel", "2.2L Smartstream CRDi Diesel (Grand Carnival / Sedona)"),
            _ev("G4LA", "1.2L", "Bensin", "1.2L Kappa (All New Picanto)"),
            _ev("G4FA", "1.4L", "Bensin", "1.4L Gamma (Kia Rio)"),
        ],
        2011, 2027, "kia_hyundai_shared",
        "Berbagi kode mesin & arsitektur ECU/CAN dengan grup Hyundai-Kia.",
    ),

    # =========================================================================
    # REGION: EROPA (JERMAN, PRANCIS, INGGRIS, SWEDIA)
    # =========================================================================
    # --- BMW ---
    _gen(
        "bmw_e46_e90_e60", "Eropa", "Jerman", "BMW", "3-Series / 5-Series (E46 / E90 / E60)",
        ["bmw", "318i", "320i", "325i", "330i", "520i", "523i", "530i", "e46", "e90", "e60", "x1 e84"],
        "BMW Generasi E-Series (N42 / N46 / M54 / N52)",
        [
            _ev("N46B20", "2.0L", "Bensin", "2.0L Valvetronic NA (E90 320i, E46 318i facelift, X1 E84)", ["N46", "N42B20", "N42"]),
            _ev("M54B25", "2.5L", "Bensin", "2.5L Inline-6 VANOS (E46 325i, E60 525i)", ["M54", "M54B30"]),
            _ev("N52B25", "2.5L", "Bensin", "2.5L Inline-6 Valvetronic (E90 325i, E60 523i)", ["N52", "N52B30"]),
        ],
        2000, 2012, "bmw_eseries_dme",
        "Perhatian khusus pada sistem Valvetronic motor, solenoid VANOS, dan kebocoran seal tutup klep.",
    ),
    _gen(
        "bmw_f30_f10_f48", "Eropa", "Jerman", "BMW", "3-Series / 5-Series / X1 / X3 (F-Series)",
        ["f30", "f10", "f48", "f25", "320i f30", "328i", "330i", "520i f10", "520d", "x1", "x3"],
        "BMW Generasi F-Series Turbo (N20 / N13 / N47)",
        [
            _ev("N20B20", "2.0L", "Bensin", "2.0L TwinPower Turbo (F30 320i/328i, F10 520i/528i, X3 F25)", ["N20"]),
            _ev("N13B16", "1.6L", "Bensin", "1.6L TwinPower Turbo (F30 316i, F20 116i)", ["N13"]),
            _ev("N47D20", "2.0L", "Diesel", "2.0L TwinPower Turbo Diesel (320d, 520d, X1 sDrive20d)", ["N47"]),
            _ev("N55B30", "3.0L", "Bensin", "3.0L Inline-6 Turbo (335i, 535i, X5 F15)", ["N55"]),
        ],
        2012, 2018, "bmw_fseries_dme",
        "Cek tensioner/guide timing chain pada N20/N47 & sensor boost/wastegate elektronik.",
    ),
    _gen(
        "bmw_g20_g30_bseries", "Eropa", "Jerman", "BMW", "3-Series / 5-Series / X1 / X3 / X5 (G-Series & Modular B)",
        ["g20", "g30", "g01", "g05", "320i g20", "330i g20", "520i g30", "530i", "x1 sdrive18i", "x3", "x5"],
        "BMW Generasi Modern B-Series Modular (B38 / B48 / B58 / B47)",
        [
            _ev("B38A15", "1.5L", "Bensin", "1.5L 3-Silinder Turbo (X1 F48/U11 sDrive18i, 218i)", ["B38"]),
            _ev("B48B20", "2.0L", "Bensin", "2.0L TwinPower Turbo (F30 LCI, G20 320i/330i, G30 520i/530i, X3)", ["B48", "B48A20"]),
            _ev("B58B30", "3.0L", "Bensin", "3.0L Inline-6 Turbo (X5 G05, 340i, Z4 M40i)", ["B58"]),
            _ev("B47D20", "2.0L", "Diesel", "2.0L Turbo Diesel (520d G30, X3 xDrive20d)", ["B47"]),
        ],
        2016, 2027, "bmw_bseries_dme",
        "Keluarga mesin modular BMW B-series; sering bermasalah di oil filter housing & coolant flange.",
    ),

    # --- MERCEDES-BENZ ---
    _gen(
        "mercedes_w203_w204_w212", "Eropa", "Jerman", "Mercedes-Benz", "C-Class / E-Class (W203 / W204 / W211 / W212)",
        ["mercedes", "mercy", "c180", "c200", "c250", "c300", "e200", "e250", "e300", "w203", "w204", "w211", "w212"],
        "Mercedes-Benz Kompressor / CGI / V6 (M271 / M272 / OM651)",
        [
            _ev("M271", "1.8L", "Bensin", "1.8L Kompressor / CGI Turbo (W203, W204 C200/C250, W212 E200/E250)", ["M271 EVO", "M271 CGI", "M271 KE"]),
            _ev("M272", "3.0L", "Bensin", "2.5L/3.0L/3.5L V6 NA (W204 C280/C300, W211/W212 E280/E300)", ["M272 E30"]),
            _ev("OM651", "2.1L", "Diesel", "2.1L CDI Turbo Diesel (C250 CDI, E250 CDI, ML/GLE 250d)"),
        ],
        2003, 2015, "mercedes_me97_sim271",
        "Pada M271 CGI perhatikan cam adjuster gear (sprocket), timing chain, & kabel sensor cam magnet.",
    ),
    _gen(
        "mercedes_w205_w213_glc_gla", "Eropa", "Jerman", "Mercedes-Benz", "C-Class / E-Class / GLC / GLA (W205 / W206 / W213)",
        ["w205", "w206", "w213", "glc", "gla", "cla", "a200", "c200 w205", "c300 w205", "e200 w213", "e300 w213", "glc200"],
        "Mercedes-Benz Turbo Modern (M270 / M274 / M264 / M254)",
        [
            _ev("M270", "1.6L", "Bensin", "1.6L / 2.0L Turbo FWD (A200, B200, CLA200, GLA200)", ["M270 DE16", "M270 DE20"]),
            _ev("M274", "2.0L", "Bensin", "2.0L Turbo RWD (W205 C200/C250/C300, W213 E200/E300, GLC250)", ["M274 DE20"]),
            _ev("M264", "2.0L", "Hybrid", "1.5L / 2.0L Turbo EQ Boost 48V (W205 Facelift, W213 Facelift, GLC200)", ["M264 EQ"]),
            _ev("M254", "2.0L", "Hybrid", "1.5L / 2.0L Turbo Mild Hybrid ISG (W206 C200/C300, GLC300)", ["M254 ISG"]),
            _ev("M282", "1.3L", "Bensin", "1.33L Turbo (A200 / GLA200 / GLB200 generasi baru)"),
        ],
        2014, 2027, "mercedes_med40_m274",
        "Generasi M264 & M254 menggunakan sistem kelistrikan Mild-Hybrid 48V — wajib prosedur safety HV/48V.",
    ),

    # --- VOLKSWAGEN & AUDI ---
    _gen(
        "vw_golf_tiguan_polo_scirocco", "Eropa", "Jerman", "Volkswagen", "Golf / Tiguan / Polo / Scirocco / Touran",
        ["vw", "volkswagen", "golf", "golf mk6", "golf mk7", "golf gti", "tiguan", "tiguan allspace", "polo", "scirocco", "touran", "caravelle"],
        "VW TSI / TFSI (EA111 / EA211 / EA888)",
        [
            _ev("CAVD", "1.4L", "Bensin", "1.4L TSI Twincharger EA111 (Golf Mk6, Scirocco, Tiguan lama, Touran)", ["EA111", "CTHD", "CAXA"]),
            _ev("CZDA", "1.4L", "Bensin", "1.4L TSI Turbo EA211 (Golf Mk7, Tiguan Allspace 1.4)", ["EA211", "CHPA", "CZEA"]),
            _ev("CJZC", "1.2L", "Bensin", "1.2L TSI Turbo (VW Polo 1.2 TSI)", ["CJZ", "CBZB"]),
            _ev("EA888", "2.0L", "Bensin", "2.0L TSI Turbo (Golf GTI Mk6/Mk7/Mk8, Scirocco R, Tiguan 2.0)", ["CCZB", "CHHB", "CAWB", "DNPA"]),
        ],
        2009, 2027, "vag_mqb_pq35",
        "Perhatian umum VAG: mekatronik DSG DQ200 (kering 7-speed), pompa air (waterpump), & PCV valve.",
    ),
    _gen(
        "audi_a4_a6_q3_q5", "Eropa", "Jerman", "Audi", "A4 / A6 / Q3 / Q5 / Q7",
        ["audi", "a3", "a4", "a5", "a6", "q3", "q5", "q7", "q8"],
        "Audi TFSI (EA888 2.0 TFSI / EA211 1.4 TFSI / EA837)",
        [
            _ev("EA888", "2.0L", "Bensin", "2.0L TFSI Turbo (A4 B8/B9, A6, Q5, Q7 2.0)", ["CDNC", "CNCD", "CYMC", "DKNA", "2.0 TFSI"]),
            _ev("EA211", "1.4L", "Bensin", "1.4L TFSI (Audi A3, Q3 1.4)", ["CZEA", "CHPA"]),
            _ev("EA837", "3.0L", "Bensin", "3.0L V6 Supercharged / Turbo (Q7 3.0, A6 3.0)", ["CREC", "EA839"]),
        ],
        2009, 2027, "vag_audi_mlb",
        "Berbagi kode mesin VAG grup & protokol diagnostik UDS/CAN dengan Volkswagen.",
    ),

    # --- PEUGEOT & CITROEN ---
    _gen(
        "peugeot_citroen_lineup", "Eropa", "Prancis", "Peugeot", "206 / 307 / 308 / 3008 / 5008 / 2008",
        ["peugeot", "206", "207", "307", "308", "408", "508", "2008", "3008", "5008", "rcz", "citroen", "c3", "c3 aircross"],
        "Peugeot & Citroën (TU5JP4 / EP6 THP / EB2 PureTech)",
        [
            _ev("EP6CDT", "1.6L", "Bensin", "1.6L THP Prince Turbo (3008, 5008, 308, 408, 508, RCZ)", ["EP6", "5FV", "5G02", "EP6FDTM", "THP"]),
            _ev("EB2DTS", "1.2L", "Bensin", "1.2L PureTech 3-Silinder Turbo (Peugeot 2008, Citroën C3 Aircross)", ["EB2", "PureTech"]),
            _ev("TU5JP4", "1.6L", "Bensin", "1.6L DOHC NA (Peugeot 206, 207, 307)", ["NFU", "TU5"]),
        ],
        2001, 2027, "psa_stellantis_bsi",
        "Pada EP6 THP periksa High Pressure Fuel Pump (HPFP), rantai keteng, & katup PCV; pada EB2 perhatikan wet timing belt.",
    ),

    # --- RENAULT ---
    _gen(
        "renault_indonesia", "Eropa", "Prancis", "Renault", "Triber / Kwid / Kiger / Duster",
        ["renault", "triber", "kwid", "kiger", "duster", "koleos"],
        "Renault Triber / Kwid / Kiger / Duster",
        [
            _ev("B4D", "1.0L", "Bensin", "1.0L 3-Silinder NA (Triber & Kwid Climber)", ["BR10"]),
            _ev("HRA0", "1.0L", "Bensin", "1.0L 3-Silinder Turbo (Kiger / Magnite)", ["HRA0DET"]),
            _ev("K9K", "1.5L", "Diesel", "1.5L dCi Turbo Diesel (Renault Duster)"),
        ],
        2013, 2027, "renault_nissan_cmf",
        "Renault Triber/Kiger berbagi arsitektur mesin dengan Nissan Magnite.",
    ),

    # --- MINI & VOLVO ---
    _gen(
        "mini_cooper_all", "Eropa", "Inggris", "MINI", "Cooper / Countryman / Clubman",
        ["mini", "mini cooper", "countryman", "clubman", "r56", "f56", "f60"],
        "MINI Cooper (R56 N14/N18 · F56/F60 B38/B48)",
        [
            _ev("N18B16", "1.6L", "Bensin", "1.6L Turbo (MINI R56/R60 Cooper S 2011-2015)", ["N14B16", "N16B16", "N18"]),
            _ev("B38A15", "1.5L", "Bensin", "1.5L 3-Silinder Turbo (MINI F55/F56/F60 Cooper)", ["B38"]),
            _ev("B48A20", "2.0L", "Bensin", "2.0L Turbo (MINI F56/F60 Cooper S & JCW)", ["B48"]),
        ],
        2007, 2027, "bmw_mini_platform",
        "MINI generasi F (2014+) memakai mesin modular BMW B38/B48.",
    ),
    _gen(
        "volvo_drive_e", "Eropa", "Swedia", "Volvo", "XC40 / XC60 / XC90",
        ["volvo", "xc40", "xc60", "xc90", "s60", "s90"],
        "Volvo Drive-E (B4204T / B420T PHEV)",
        [
            _ev("B4204T", "2.0L", "Hybrid", "2.0L Drive-E Turbo / Supercharged PHEV T8 (XC60 / XC90)", ["B420T", "Drive-E"]),
            _ev("B3154T", "1.5L", "Bensin", "1.5L 3-Silinder Turbo (XC40 T3/T5)"),
        ],
        2016, 2027, "volvo_spa_cma",
        "Platform Volvo SPA/CMA modern dengan protokol DoIP/CAN.",
    ),

    # =========================================================================
    # REGION: CHINA (MEREK CHINA POPULER DI INDONESIA)
    # =========================================================================
    # --- WULING ---
    _gen(
        "wuling_confero_formo_alvez", "Asia" if False else "China", "China", "Wuling", "Confero / Formo / Alvez",
        ["wuling", "confero", "confero s", "formo", "formo max", "alvez"],
        "Wuling Confero / Formo / Alvez (L2B / N15 / LAR)",
        [
            _ev("L2B", "1.5L", "Bensin", "1.5L P-TEC DOHC DVVT NA (Confero, Formo Max, Alvez)", ["N15", "L2B 1.5"]),
            _ev("LAR", "1.2L", "Bensin", "1.2L DOHC (Wuling Formo 1.2)", ["LAQ"]),
        ],
        2017, 2027, "sgmw_wuling_na",
        "Mesin L2B 1.5L P-TEC (GM-SAIC) banyak digunakan pada Confero, Formo Max, dan Alvez.",
    ),
    _gen(
        "wuling_cortez_almaz", "China", "China", "Wuling", "Cortez / Almaz",
        ["wuling", "cortez", "cortez ct", "almaz", "almaz rs", "almaz hybrid"],
        "Wuling Cortez / Almaz / Almaz RS & Hybrid (LJO Turbo / LJM20A)",
        [
            _ev("LJO", "1.5L", "Bensin", "1.5L Turbocharged DVVT (Almaz, Almaz RS, Cortez CT/New Cortez)", ["LJ0", "LL5", "N15T"]),
            _ev("LJ479QNE2", "1.8L", "Bensin", "1.8L NA i-AMT (Cortez 1.8 lama 2018-2020)"),
            _ev("LJM20A", "2.0L", "Hybrid", "2.0L Atkinson Cycle DHT Hybrid (Almaz Hybrid 2022+)"),
        ],
        2018, 2027, "sgmw_wuling_turbo",
        "Mesin 1.5T LJO dilengkapi turbo Honeywell & transmisi CVT Bosch.",
    ),
    _gen(
        "wuling_ev_lineup", "China", "China", "Wuling", "Air EV / BinguoEV / Cloud EV",
        ["air ev", "airev", "binguo", "binguoev", "cloud ev", "cloudev"],
        "Wuling EV (Air EV / BinguoEV / Cloud EV — Motor Listrik)",
        [
            _ev("TZ155X030", "EV 30kW", "EV", "Motor Listrik PMSM 30 kW (Wuling Air EV)", ["Air EV Motor"]),
            _ev("TZ180XS050", "EV 50kW", "EV", "Motor Listrik PMSM 50 kW (Wuling BinguoEV)", ["Binguo Motor"]),
            _ev("TZ180XS100", "EV 100kW", "EV", "Motor Listrik PMSM 100 kW (Wuling Cloud EV)", ["Cloud EV Motor"]),
        ],
        2022, 2027, "sgmw_gsev_ev",
        "Kendaraan listrik murni (BEV) dengan BMS baterai LFP — wajib prosedur tegangan tinggi (HV)!",
    ),

    # --- CHERY & OMODA & JAECOO ---
    _gen(
        "chery_tiggo_omoda", "China", "China", "Chery", "Tiggo / Omoda 5 / J6",
        ["chery", "tiggo", "tiggo 5x", "tiggo cross", "tiggo 7", "tiggo 7 pro", "tiggo 8", "tiggo 8 pro", "omoda", "omoda 5", "omoda 5 gt", "jaecoo", "j7"],
        "Chery Tiggo 5X / 7 Pro / 8 Pro / Omoda 5 (Acteco SQRE / SQRF)",
        [
            _ev("SQRE4T15C", "1.5L", "Bensin", "1.5L Acteco Turbo (Omoda 5 Z/RZ, Tiggo 7 Pro)", ["E4T15C", "4T15C"]),
            _ev("SQRE4G15C", "1.5L", "Bensin", "1.5L Acteco NA (Tiggo 5X / Tiggo Cross)", ["E4G15C"]),
            _ev("SQRF4J16", "1.6L", "Bensin", "1.6L TGDI Direct Injection Turbo (Omoda 5 GT, Tiggo 8, Jaecoo J7)", ["F4J16", "4J16"]),
            _ev("SQRF4J20", "2.0L", "Bensin", "2.0L TGDI Turbo (Tiggo 8 Pro / Pro Max)", ["F4J20", "4J20"]),
        ],
        2022, 2027, "chery_t1x_acteco",
        "Keluarga mesin Acteco Chery (1.5T port injection vs 1.6T/2.0T TGDI direct injection).",
    ),

    # --- DFSK & SERES ---
    _gen(
        "dfsk_glory_supercab_gelora", "China", "China", "DFSK", "Glory 560 / 580 / i-Auto / Super Cab / Gelora",
        ["dfsk", "glory", "glory 560", "glory 580", "glory i-auto", "super cab", "supercab", "gelora", "seres"],
        "DFSK Glory / Super Cab / Gelora (SFG15T / DK15 / SFD13T)",
        [
            _ev("SFG15T", "1.5L", "Bensin", "1.5L Turbocharged (Glory 560, Glory 580, Glory i-Auto)", ["SFG15"]),
            _ev("SFG18", "1.8L", "Bensin", "1.8L NA (Glory 580 1.8)"),
            _ev("DK15", "1.5L", "Bensin", "1.5L NA Niaga (Super Cab 1.5, Gelora Bensin)"),
            _ev("SFD13T", "1.3L", "Diesel", "1.3L Turbo Diesel (Super Cab 1.3 Diesel)"),
        ],
        2018, 2027, "dfsk_dongfeng_platform",
        "Mesin SFG15T Turbo digunakan pada lini SUV DFSK Glory dengan transmisi CVT Punch.",
    ),

    # --- MG (SAIC CHINA) ---
    _gen(
        "mg_zs_hs_5gt_vs", "China", "China", "MG", "ZS / HS / 5 GT / VS HEV",
        ["mg", "mg zs", "mg hs", "mg 5 gt", "mg5", "mg vs", "mg4 ev"],
        "MG (SAIC) ZS / HS / 5 GT / VS HEV (15S4C / 15E4E)",
        [
            _ev("15S4C", "1.5L", "Bensin", "1.5L NSE DOHC NA / Hybrid (MG ZS, MG 5 GT, MG VS HEV)"),
            _ev("15E4E", "1.5L", "Bensin", "1.5L NetBlue Turbo + 7-DCT (MG HS)"),
            _ev("TZ180XS0951", "EV 125kW", "EV", "Motor Listrik RWD (MG 4 EV / MG ZS EV)", ["MG4 Motor"]),
        ],
        2020, 2027, "saic_mg_platform",
        "MG (SAIC Motor) menggunakan ECU Bosch/UAES dengan standar OBD-II CAN.",
    ),

    # --- BYD ---
    _gen(
        "byd_ev_lineup", "China", "China", "BYD", "Atto 3 / Dolphin / Seal / M6 / Denza",
        ["byd", "atto 3", "atto3", "dolphin", "seal", "byd m6", "m6", "sealion", "denza"],
        "BYD e-Platform 3.0 Blade Battery (EV)",
        [
            _ev("TZ200XSQ", "EV 150kW", "EV", "Motor Listrik e-Platform 3.0 (Atto 3, M6, Sealion)", ["BYD Atto3", "BYD M6"]),
            _ev("TZ180XSF", "EV 70-130kW", "EV", "Motor Listrik (BYD Dolphin)", ["BYD Dolphin"]),
            _ev("TZ200XYC", "EV 230-390kW", "EV", "Motor Listrik Performa RWD/AWD (BYD Seal)", ["BYD Seal"]),
        ],
        2024, 2027, "byd_eplatform3",
        "Sistem EV 8-in-1 BYD Blade Battery LFP — diagnosa melalui BMS/VCU & wajib APD tegangan tinggi.",
    ),

    # --- GWM (HAVAL / TANK), BAIC, JETOUR ---
    _gen(
        "gwm_haval_tank", "China", "China", "GWM", "Haval H6 / Jolion / Tank 300 / Tank 500",
        ["gwm", "haval", "haval h6", "jolion", "tank 300", "tank 500", "ora"],
        "GWM Haval & Tank Hybrid (GW4B15D / E20NA)",
        [
            _ev("GW4B15D", "1.5L", "Hybrid", "1.5L Turbo DHT Hybrid (Haval H6 HEV & Jolion HEV)", ["GW4B15"]),
            _ev("E20NA", "2.0L", "Hybrid", "2.0L Turbo Hybrid 9HAT (Tank 300 HEV & Tank 500 HEV)"),
        ],
        2024, 2027, "gwm_lemon_hybrid",
        "Sistem Dedicated Hybrid Transmission (DHT) Great Wall Motor.",
    ),
    _gen(
        "baic_jetour_lineup", "China", "China", "BAIC / Jetour", "X55 II / BJ40 Plus / Dashing / X70 Plus",
        ["baic", "x55", "x55 ii", "bj40", "bj40 plus", "jetour", "dashing", "x70", "x70 plus"],
        "BAIC X55 II / BJ40 Plus & Jetour Dashing / X70 Plus",
        [
            _ev("A156T2H", "1.5L", "Bensin", "1.5L Magic Core Turbo VGT (BAIC X55 II)"),
            _ev("HY4C20B", "2.0L", "Bensin", "2.0L Turbo 8AT ZF (BAIC BJ40 Plus)"),
            _ev("SQRE4T15C", "1.5L", "Bensin", "1.5L Turbo + 6DCT (Jetour Dashing & X70 Plus)", ["E4T15C"]),
        ],
        2024, 2027, "china_new_wave_turbo",
        "Merek China gelombang baru di Indonesia (BAIC Magic Core & Jetour sub-brand Chery).",
    ),
]


# ---------------------------------------------------------------------------
# 3. PENYIMPANAN, DIREKTORI KODE MESIN & REGISTRY PAKET MANUAL KUSTOM
# ---------------------------------------------------------------------------

CUSTOM_PACKS_PATH = Path(__file__).resolve().parent.parent / "data" / "custom_manual_packs.json"


class CustomManualPackSummary(BaseModel):
    pack_id: str
    brand: str
    model: str
    generation_id: str | None = None
    generation_label: str = ""
    year_start: int
    year_end: int
    engine_codes: list[str] = []
    title: str
    dtc_count: int = 0
    pinout_count: int = 0
    sensor_spec_count: int = 0
    is_builtin: bool = False


class VehicleTransitionCandidate(BaseModel):
    generation_id: str
    generation_label: str
    engine_codes: list[str]
    year_range: str
    notes: str = ""


class EngineChoiceChip(BaseModel):
    code: str
    cc: str = ""
    fuel: str = "Bensin"
    desc: str = ""
    aliases: list[str] = []


class ModelOptionChip(BaseModel):
    brand: str
    model: str
    generation_label: str
    year_range: str
    suggested_year: int


class VehicleApplicabilityInfo(BaseModel):
    brand: str = ""
    model: str = ""
    year: int | None = None
    engine_code: str = ""
    region: str = "Asia"
    resolved_fuel_type: str = "Bensin"  # Bensin | Diesel | Hybrid | EV
    is_high_voltage: bool = False
    hv_safety_warning: str | None = None
    resolved_generation_id: str | None = None
    resolved_generation_label: str = "Belum Ditentukan"
    resolved_engine_label: str = "-"
    coverage_level: str = "UNIVERSAL_OBD_ONLY"  # EXACT_OEM_MANUAL | SAME_BRAND_REFERENCE | UNIVERSAL_OBD_ONLY
    is_pinout_verified: bool = False
    is_transition_year: bool = False
    transition_candidates: list[VehicleTransitionCandidate] = []
    available_engine_choices: list[EngineChoiceChip] = []
    matched_model_options: list[ModelOptionChip] = []
    active_manual_source: str = "Standar Universal OBD-II (SAE J2012)"
    safety_warning_title: str | None = None
    safety_warning_desc: str | None = None


def build_engine_directory() -> list[dict[str, Any]]:
    """
    Menyusun kamus lengkap kode mesin terindeks (Asia, Eropa, China) untuk fitur
    pencarian & pemilih cepat kode mesin di UI Web & Aplikasi Android.
    """
    grouped: dict[tuple[str, str], dict[str, Any]] = {}

    for g in VEHICLE_GENERATION_CATALOG:
        brand = g["brand"]
        model = g["model"]
        region = g.get("region", "Asia")
        country = g.get("origin_country", "")
        ys = int(g["year_start"])
        ye = int(g["year_end"])
        for v in g.get("engine_variants", []):
            code = v["code"]
            key = (brand.lower(), code.lower())
            if key not in grouped:
                grouped[key] = {
                    "code": code,
                    "aliases": list(v.get("aliases", [])),
                    "brand": brand,
                    "region": region,
                    "origin_country": country,
                    "cc": v.get("cc", ""),
                    "fuel": v.get("fuel", "Bensin"),
                    "desc": v.get("desc", ""),
                    "models": [model],
                    "generation_labels": [g["generation_label"]],
                    "year_min": ys,
                    "year_max": ye,
                    "suggested_model": model.split("/")[0].strip(),
                    "suggested_year": min(max(2018, ys), ye),
                }
            else:
                entry = grouped[key]
                for al in v.get("aliases", []):
                    if al not in entry["aliases"]:
                        entry["aliases"].append(al)
                if model not in entry["models"]:
                    entry["models"].append(model)
                if g["generation_label"] not in entry["generation_labels"]:
                    entry["generation_labels"].append(g["generation_label"])
                entry["year_min"] = min(entry["year_min"], ys)
                entry["year_max"] = max(entry["year_max"], ye)
                entry["suggested_year"] = min(max(2018, entry["year_min"]), entry["year_max"])
                if v.get("desc") and v["desc"] not in entry["desc"] and len(entry["desc"]) < 140:
                    entry["desc"] = f"{entry['desc']} | {v['desc']}"

    region_order = {"Asia": 0, "Eropa": 1, "China": 2}
    result = sorted(
        grouped.values(),
        key=lambda x: (region_order.get(x["region"], 9), x["brand"].lower(), x["code"].lower()),
    )
    return result


def _ensure_custom_packs_file() -> None:
    CUSTOM_PACKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CUSTOM_PACKS_PATH.exists():
        CUSTOM_PACKS_PATH.write_text(json.dumps({"packs": []}, indent=2), encoding="utf-8")


def load_custom_manual_packs() -> list[dict[str, Any]]:
    """Membaca semua paket manual kustom tambahan yang sudah diimpor oleh bengkel."""
    _ensure_custom_packs_file()
    try:
        raw = json.loads(CUSTOM_PACKS_PATH.read_text(encoding="utf-8"))
        packs = raw.get("packs", [])
        return packs if isinstance(packs, list) else []
    except Exception:
        return []


def save_custom_manual_pack(pack_data: dict[str, Any]) -> dict[str, Any]:
    """Menyimpan atau memperbarui paket manual kustom ke custom_manual_packs.json."""
    _ensure_custom_packs_file()
    try:
        raw = json.loads(CUSTOM_PACKS_PATH.read_text(encoding="utf-8"))
        packs: list[dict[str, Any]] = raw.get("packs", []) if isinstance(raw.get("packs"), list) else []
    except Exception:
        packs = []

    pack_id = str(pack_data.get("pack_id") or "").strip()
    if not pack_id:
        slug_brand = re.sub(r"[^a-z0-9]+", "_", str(pack_data.get("brand", "custom")).lower()).strip("_")
        slug_model = re.sub(r"[^a-z0-9]+", "_", str(pack_data.get("model", "model")).lower()).strip("_")
        yr_s = pack_data.get("year_start", 2015)
        yr_e = pack_data.get("year_end", 2026)
        pack_id = f"{slug_brand}_{slug_model}_{yr_s}_{yr_e}"
        pack_data["pack_id"] = pack_id

    updated = [p for p in packs if p.get("pack_id") != pack_id]
    updated.append(pack_data)
    CUSTOM_PACKS_PATH.write_text(
        json.dumps({"packs": updated}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return pack_data


def delete_custom_manual_pack(pack_id: str) -> bool:
    """Menghapus paket manual kustom berdasarkan pack_id."""
    if pack_id == "suzuki_jb420_builtin":
        return False
    _ensure_custom_packs_file()
    packs = load_custom_manual_packs()
    filtered = [p for p in packs if p.get("pack_id") != pack_id]
    if len(filtered) == len(packs):
        return False
    CUSTOM_PACKS_PATH.write_text(
        json.dumps({"packs": filtered}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return True


def list_all_manual_pack_summaries() -> list[CustomManualPackSummary]:
    """Mengembalikan daftar lengkap paket manual aktif (Bawaan JB420 + Custom Upload)."""
    jb420_summary = CustomManualPackSummary(
        pack_id="suzuki_jb420_builtin",
        brand="Suzuki",
        model="Grand Vitara",
        generation_id="suzuki_jb420",
        generation_label="Grand Vitara Gen 2 (JB420)",
        year_start=2006,
        year_end=2015,
        engine_codes=["J20A"],
        title="Buku Pedoman Resmi Suzuki Grand Vitara JB420 (Vol 1 & Vol 2)",
        dtc_count=207,
        pinout_count=251,
        sensor_spec_count=9,
        is_builtin=True,
    )
    out = [jb420_summary]
    for p in load_custom_manual_packs():
        out.append(
            CustomManualPackSummary(
                pack_id=str(p.get("pack_id", "")),
                brand=str(p.get("brand", "")),
                model=str(p.get("model", "")),
                generation_id=p.get("generation_id"),
                generation_label=str(p.get("generation_label", p.get("model", ""))),
                year_start=int(p.get("year_start", 2010)),
                year_end=int(p.get("year_end", 2026)),
                engine_codes=list(p.get("engine_codes", [])),
                title=str(p.get("title", "Manual Tambahan Bengkel")),
                dtc_count=len(p.get("dtc_catalog", [])),
                pinout_count=len(p.get("wiring_pinouts", [])),
                sensor_spec_count=len(p.get("sensor_specs", [])),
                is_builtin=False,
            )
        )
    return out


def _matches_brand_and_model(
    brand_q: str,
    model_q: str,
    entry_brand: str,
    entry_model: str,
    aliases: list[str] | None = None,
) -> bool:
    b_low = (brand_q or "").strip().lower()
    m_low = (model_q or "").strip().lower()
    eb_low = (entry_brand or "").strip().lower()
    em_low = (entry_model or "").strip().lower()

    if not m_low:
        return False

    if b_low and eb_low and (b_low not in eb_low and eb_low not in b_low):
        return False

    if em_low and (em_low in m_low or m_low in em_low):
        return True
    for al in aliases or []:
        al_low = al.lower()
        if al_low in m_low or m_low in al_low:
            return True
    return False


def _gen_matches_engine(gen: dict[str, Any], engine_q: str) -> dict[str, Any] | None:
    """Mencocokkan input kode mesin (termasuk alias seperti 1TR-VE -> 1TR-FE, 2GD -> 2GD-FTV)."""
    norm_q = _norm_code(engine_q)
    if not norm_q or len(norm_q) < 2:
        return None
    for v in gen.get("engine_variants", []):
        candidates = [v["code"]] + list(v.get("aliases", []))
        for cand in candidates:
            nc = _norm_code(cand)
            if not nc:
                continue
            if norm_q == nc or norm_q in nc or nc in norm_q:
                return v
    return None


def find_matching_custom_pack(
    brand: str,
    model: str,
    year: int | None,
    engine_code: str = "",
) -> dict[str, Any] | None:
    """Mencari paket manual kustom yang cocok secara ketat berdasarkan model + rentang tahun (+ kode mesin bila ada)."""
    packs = load_custom_manual_packs()
    eng_norm = _norm_code(engine_code)

    candidates: list[dict[str, Any]] = []
    for p in packs:
        p_brand = str(p.get("brand", ""))
        p_model = str(p.get("model", ""))
        p_aliases = list(p.get("model_aliases", [p_model]))
        if not _matches_brand_and_model(brand, model, p_brand, p_model, p_aliases):
            continue
        if year is not None:
            ys = int(p.get("year_start", 1980))
            ye = int(p.get("year_end", 2030))
            if not (ys <= year <= ye):
                continue
        candidates.append(p)

    if not candidates:
        return None
    if eng_norm and len(candidates) > 1:
        for c in candidates:
            codes = [_norm_code(str(ec)) for ec in c.get("engine_codes", [])]
            if any(ec and (ec in eng_norm or eng_norm in ec) for ec in codes):
                return c
    return candidates[0]


def _extract_engine_chips(gen: dict[str, Any] | None) -> list[EngineChoiceChip]:
    if not gen:
        return []
    return [
        EngineChoiceChip(
            code=v["code"],
            cc=v.get("cc", ""),
            fuel=v.get("fuel", "Bensin"),
            desc=v.get("desc", ""),
            aliases=list(v.get("aliases", [])),
        )
        for v in gen.get("engine_variants", [])
    ]


def resolve_vehicle_applicability(
    brand: str | None = "",
    model: str | None = "",
    year: int | None = None,
    engine_code: str | None = "",
) -> tuple[VehicleApplicabilityInfo, dict[str, Any] | None]:
    """
    Memetakan input kendaraan (Merek, Model, Tahun, Kode Mesin) ke Generasi & Paket Manual yang tepat.
    Mendukung normalisasi alias mesin (mis. 1TR-VE -> 1TR-FE, 2GD -> 2GD-FTV) dan pencarian
    langsung berdasarkan kode mesin saja bila model belum diketik.
    """
    b_clean = (brand or "").strip()
    m_clean = (model or "").strip()
    eng_clean = (engine_code or "").strip()

    # 1. Cari kandidat generasi dari VEHICLE_GENERATION_CATALOG berdasarkan Merek+Model
    model_matches = [
        g for g in VEHICLE_GENERATION_CATALOG
        if _matches_brand_and_model(b_clean, m_clean, g["brand"], g["model"], g.get("model_aliases"))
    ]

    # Fallback pintar: jika model kosong / tidak cocok tapi mekanik memasukkan kode mesin (mis. "2GD", "1TR-VE", "N20B20", "SQRE4T15C")
    is_reverse_engine_lookup = False
    if not model_matches and eng_clean:
        b_low = b_clean.lower()
        model_matches = [
            g for g in VEHICLE_GENERATION_CATALOG
            if _gen_matches_engine(g, eng_clean) is not None
            and (not b_low or b_low in g["brand"].lower() or g["brand"].lower() in b_low)
        ]
        if model_matches:
            is_reverse_engine_lookup = True

    # Saring berdasarkan rentang tahun jika diisi
    year_matches: list[dict[str, Any]] = []
    if year is not None and model_matches:
        year_matches = [
            g for g in model_matches if g["year_start"] <= year <= g["year_end"]
        ]

    # Deteksi tahun peralihan (lebih dari 1 generasi aktif pada tahun yang sama)
    transition_candidates: list[VehicleTransitionCandidate] = []
    matched_model_options: list[ModelOptionChip] = []
    is_transition = False
    chosen_gen: dict[str, Any] | None = None

    if is_reverse_engine_lookup:
        # Kode mesin dipakai lintas beberapa model (mis. 2GD -> Innova Reborn, Fortuner, Hilux):
        # Ambil model utama pertama di katalog (Innova Reborn / Ertiga) & tawarkan semua pilihan model!
        pool = year_matches if year_matches else model_matches
        seen_models: set[str] = set()
        for g in pool:
            m_key = f"{g['brand']}|{g['model']}".lower()
            if m_key in seen_models:
                continue
            seen_models.add(m_key)
            matched_model_options.append(
                ModelOptionChip(
                    brand=g["brand"],
                    model=g["model"].split("/")[0].strip(),
                    generation_label=g["generation_label"],
                    year_range=f"{g['year_start']}–{g['year_end']}",
                    suggested_year=year if (year and g["year_start"] <= year <= g["year_end"]) else min(max(2018, g["year_start"]), g["year_end"]),
                )
            )
        chosen_gen = pool[0]
    elif year_matches:
        if len(year_matches) > 1:
            eng_filtered = [
                g for g in year_matches
                if eng_clean and _gen_matches_engine(g, eng_clean) is not None
            ]
            if len(eng_filtered) == 1:
                chosen_gen = eng_filtered[0]
            else:
                is_transition = True
                transition_candidates = [
                    VehicleTransitionCandidate(
                        generation_id=g["generation_id"],
                        generation_label=g["generation_label"],
                        engine_codes=g["engine_codes"],
                        year_range=f"{g['year_start']}–{g['year_end']}",
                        notes=g.get("notes", ""),
                    )
                    for g in year_matches
                ]
                chosen_gen = eng_filtered[-1] if eng_filtered else year_matches[-1]
        else:
            chosen_gen = year_matches[0]
    elif model_matches:
        if eng_clean:
            eng_only = [g for g in model_matches if _gen_matches_engine(g, eng_clean) is not None]
            if eng_only:
                model_matches = eng_only
        if year is not None:
            model_matches_sorted = sorted(
                model_matches,
                key=lambda g: min(abs(year - g["year_start"]), abs(year - g["year_end"])),
            )
            chosen_gen = model_matches_sorted[0]
        else:
            chosen_gen = model_matches[-1]

    matched_variant = _gen_matches_engine(chosen_gen, eng_clean) if (chosen_gen and eng_clean) else None
    engine_chips = _extract_engine_chips(chosen_gen)
    region = chosen_gen.get("region", "Asia") if chosen_gen else "Asia"

    # Tentukan jenis bahan bakar & status tegangan tinggi (HV Safety) secara akurat
    hint_low = f"{m_clean} {eng_clean}".lower()
    if matched_variant and matched_variant.get("fuel"):
        resolved_fuel_type = str(matched_variant["fuel"])
    elif any(k in hint_low for k in ("air ev", "binguo", "cloud ev", "atto 3", "dolphin", "seal", "byd m6", "mg4 ev", " bev", "listrik")):
        resolved_fuel_type = "EV"
    elif any(k in hint_low for k in ("hybrid", "hev", "phev", "zenix hybrid", "e:hev", "shvs", "eq boost")):
        resolved_fuel_type = "Hybrid"
    elif any(k in hint_low for k in ("diesel", "solar", "2gd", "2kd", "1gd", "1kd", "4n15", "4d56", "d4hb", "4ja1", "rz4e", "crdi", "vnt", "vrz")):
        resolved_fuel_type = "Diesel"
    elif chosen_gen and chosen_gen.get("fuel_types"):
        resolved_fuel_type = str(chosen_gen["fuel_types"][0])
    else:
        resolved_fuel_type = "Bensin"

    is_high_voltage = resolved_fuel_type in {"EV", "Hybrid"}
    hv_safety_warning: str | None = None
    if resolved_fuel_type == "EV":
        hv_safety_warning = (
            "BAHAYA TEGANGAN TINGGI EV (300V–400V DC): Wajib pakai sarung tangan isolasi 1000V (Class 0), "
            "cabut Service Plug / HV Disconnect, & tunggu 10 menit sebelum menyentuh kabel oranye, inverter, atau kompresor AC listrik (oli AC wajib POE isolasi, DILARANG oli PAG!)."
        )
    elif resolved_fuel_type == "Hybrid":
        hv_safety_warning = (
            "PERINGATAN SISTEM HYBRID / MILD-HYBRID (48V–350V DC): Patuhi prosedur keselamatan HV — "
            "jangan menyentuh kabel berwarna oranye tanpa APD isolasi 1000V, matikan kontak & jauhkan smart key, dan pastikan oli kompresor AC khusus listrik (POE/ND-11)."
        )

    # 2. Cek Paket Manual Kustom (upload baru)
    eff_brand = b_clean or (chosen_gen["brand"] if chosen_gen else "")
    eff_model = m_clean or (chosen_gen["model"] if chosen_gen else "")
    custom_pack = find_matching_custom_pack(eff_brand, eff_model, year, eng_clean)
    if custom_pack:
        gen_lbl = chosen_gen["generation_label"] if chosen_gen else f"{eff_brand} {eff_model} ({custom_pack.get('year_start')}–{custom_pack.get('year_end')})"
        eng_lbl = (
            f"{matched_variant['code']} ({matched_variant['cc']} {matched_variant['fuel']})"
            if matched_variant
            else (", ".join(custom_pack.get("engine_codes", [])) or (chosen_gen["engine_codes"][0] if chosen_gen else eng_clean or "-"))
        )
        return (
            VehicleApplicabilityInfo(
                brand=eff_brand or custom_pack.get("brand", ""),
                model=eff_model or custom_pack.get("model", ""),
                year=year,
                engine_code=matched_variant["code"] if matched_variant else (eng_clean or eng_lbl),
                region=region,
                resolved_fuel_type=resolved_fuel_type,
                is_high_voltage=is_high_voltage,
                hv_safety_warning=hv_safety_warning,
                resolved_generation_id=custom_pack.get("generation_id") or (chosen_gen["generation_id"] if chosen_gen else None),
                resolved_generation_label=gen_lbl,
                resolved_engine_label=eng_lbl,
                coverage_level="EXACT_OEM_MANUAL",
                is_pinout_verified=True,
                is_transition_year=is_transition,
                transition_candidates=transition_candidates,
                available_engine_choices=engine_chips,
                matched_model_options=matched_model_options,
                active_manual_source=str(custom_pack.get("title", "Buku Manual Kustom Bengkel")),
                safety_warning_title=(
                    f"⚠️ Tahun Peralihan {year}: Konfirmasi Kode Mesin"
                    if is_transition
                    else None
                ),
                safety_warning_desc=(
                    f"Tahun {year} adalah masa transisi generasi pada model {eff_model}. Pastikan kode mesin ({eng_lbl}) sesuai dengan nomor mesin di STNK."
                    if is_transition
                    else None
                ),
            ),
            custom_pack,
        )

    # 3. Cek Suzuki Grand Vitara JB420 (Manual Bawaan Terverifikasi untuk J20A 2006–2015)
    is_jb420_j20a = (
        chosen_gen is not None
        and chosen_gen["generation_id"] == "suzuki_jb420"
        and (not matched_variant or matched_variant["code"] == "J20A")
        and (year is None or year <= 2015)
    )
    if is_jb420_j20a:
        return (
            VehicleApplicabilityInfo(
                brand="Suzuki",
                model=m_clean or "Grand Vitara",
                year=year,
                engine_code="J20A",
                region="Asia",
                resolved_fuel_type="Bensin",
                is_high_voltage=False,
                hv_safety_warning=None,
                resolved_generation_id="suzuki_jb420",
                resolved_generation_label="Grand Vitara Gen 2 (JB420)",
                resolved_engine_label="J20A (2.0L Bensin)",
                coverage_level="EXACT_OEM_MANUAL",
                is_pinout_verified=True,
                is_transition_year=False,
                transition_candidates=[],
                available_engine_choices=engine_chips,
                matched_model_options=matched_model_options,
                active_manual_source="Buku Pedoman Resmi Suzuki Grand Vitara JB420 (Vol 1 & Vol 2)",
                safety_warning_title=None,
                safety_warning_desc=None,
            ),
            None,
        )

    # 4. Model lain yang belum punya file manual spesifik
    disp_vehicle = f"{eff_brand} {eff_model}".strip() or "Kendaraan Umum"
    if year:
        disp_vehicle = f"{disp_vehicle} ({year})"

    is_suzuki_family = "suzuki" in eff_brand.lower() or (chosen_gen and chosen_gen["brand"].lower() == "suzuki")

    if chosen_gen:
        gen_lbl = chosen_gen["generation_label"]
        if matched_variant:
            alias_note = f" [alias: {', '.join(matched_variant['aliases'][:2])}]" if matched_variant.get("aliases") else ""
            eng_lbl = f"{matched_variant['code']} ({matched_variant['cc']} {matched_variant['fuel']}){alias_note}"
        else:
            eng_lbl = ", ".join(chosen_gen["engine_codes"])
        gen_id = chosen_gen["generation_id"]
        notes = chosen_gen.get("notes", "")
    else:
        gen_lbl = f"{disp_vehicle} (Klasifikasi Standar)"
        eng_lbl = eng_clean or "-"
        gen_id = None
        notes = ""

    if is_transition:
        cand_names = " vs ".join(f"{c.generation_label} [{', '.join(c.engine_codes)}]" for c in transition_candidates)
        warn_title = f"⚠️ TAHUN PERALIHAN {year} & MANUAL KHUSUS {disp_vehicle.upper()} BELUM DIUNGGAH"
        warn_desc = (
            f"Tahun {year} mencakup pergantian generasi ({cand_names}). Cek kode mesin pada STNK/blok mesin. "
            "Selain itu, file Buku Manual resmi untuk model ini belum diunggah — analisa diagnosa dan kode DTC "
            f"mengikuti standar Universal OBD-II ({resolved_fuel_type}), namun pinout/warna kabel fisik wajib diverifikasi dengan multitester."
        )
    elif is_suzuki_family:
        warn_title = f"⚠️ PERHATIAN WIRING: MANUAL KHUSUS {disp_vehicle.upper()} BELUM TERSEDIA"
        warn_desc = (
            f"Terdeteksi sebagai {gen_lbl} (Mesin {eng_lbl}). {notes} "
            "File Buku Manual resmi khusus model/generasi ini belum ditanamkan — diagnosa gejala & DTC tetap valid secara prinsip kerja Suzuki/OBD-II, "
            "namun pinout ECU wajib diukur fisik dengan multitester sebelum melakukan jumper kabel."
        )
    else:
        warn_title = f"⚠️ MODE STANDAR UNIVERSAL OBD-II ({disp_vehicle.upper()} · {region.upper()} · {resolved_fuel_type.upper()})"
        warn_desc = (
            f"Terdeteksi sebagai {gen_lbl} (Mesin {eng_lbl}). {notes} "
            f"Analisa kerusakan & kode DTC menggunakan Katalog Universal {resolved_fuel_type} (SAE J2012) & database kasus bengkel. "
            "File Buku Manual OEM spesifik model ini belum diunggah — jangan memakai pinout konektor referensi model lain tanpa pengukuran fisik."
        )

    coverage = "SAME_BRAND_REFERENCE" if is_suzuki_family else "UNIVERSAL_OBD_ONLY"
    return (
        VehicleApplicabilityInfo(
            brand=eff_brand,
            model=eff_model,
            year=year,
            engine_code=matched_variant["code"] if matched_variant else (eng_clean or eng_lbl),
            region=region,
            resolved_fuel_type=resolved_fuel_type,
            is_high_voltage=is_high_voltage,
            hv_safety_warning=hv_safety_warning,
            resolved_generation_id=gen_id,
            resolved_generation_label=gen_lbl,
            resolved_engine_label=eng_lbl,
            coverage_level=coverage,
            is_pinout_verified=False,
            is_transition_year=is_transition,
            transition_candidates=transition_candidates,
            available_engine_choices=engine_chips,
            matched_model_options=matched_model_options,
            active_manual_source=f"Standar Universal OBD-II {resolved_fuel_type} & Kasus Bengkel (Manual {disp_vehicle} Belum Tersedia)",
            safety_warning_title=warn_title,
            safety_warning_desc=warn_desc,
        ),
        None,
    )
