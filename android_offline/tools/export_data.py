"""
Export Data SQLite & Katalog JSON ke Aset Offline APK (Mode Read-Only)
======================================================================
Membaca `backend/bengkel_masa_depan.db` menggunakan koneksi URI `mode=ro`
(100% hanya baca, tidak menyentuh/mengubah file database backend) serta
menghasilkan file JSON di `android_offline/www/data/` dan bundle JS
`android_offline/www/js/embedded-data.js`.
"""

from pathlib import Path
import json
import sqlite3
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
DB_PATH = BACKEND_DIR / "bengkel_masa_depan.db"
CATALOG_PATH = BACKEND_DIR / "app" / "jb420_extracted_catalog.json"
OUT_DATA_DIR = ROOT_DIR / "android_offline" / "www" / "data"
OUT_JS_DIR = ROOT_DIR / "android_offline" / "www" / "js"


def export_all() -> None:
    OUT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JS_DIR.mkdir(parents=True, exist_ok=True)

    # Koneksi SQLite Read-Only (R1 Compliance)
    db_uri = f"file:{DB_PATH.as_posix()}?mode=ro"
    conn = sqlite3.connect(db_uri, uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Historical Cases (baca HISTORICAL_CASES_DATA via AST tanpa butuh library eksternal)
    import ast
    seed_src = (BACKEND_DIR / "app" / "db" / "seed_historical_cases.py").read_text(encoding="utf-8")
    seed_tree = ast.parse(seed_src)
    HISTORICAL_CASES_DATA = []
    for node in seed_tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "HISTORICAL_CASES_DATA":
                    HISTORICAL_CASES_DATA = ast.literal_eval(node.value)
                    break

    db_cases = [dict(r) for r in cur.execute("SELECT * FROM historical_cases ORDER BY id").fetchall()]
    by_code: dict[str, dict] = {}
    next_id = 1
    for seed_item in HISTORICAL_CASES_DATA:
        c_code = seed_item["case_code"]
        by_code[c_code] = {
            "id": next_id,
            **seed_item,
            "created_at": "2026-11-03 11:22:31",
        }
        next_id += 1

    for row in db_cases:
        c_code = row["case_code"]
        by_code[c_code] = row

    # Urutkan berdasarkan case_code (K001 .. K018) dan beri id berurutan
    sorted_cases = sorted(by_code.values(), key=lambda x: x["case_code"])
    for idx, item in enumerate(sorted_cases, start=1):
        item["id"] = idx

    # 2. DTC Codes
    dtc_codes = [
        dict(r)
        for r in cur.execute(
            "SELECT id, code, system, description_id, possible_causes, severity_level, "
            "system_category, common_causes, recommended_fix FROM dtc_codes ORDER BY code"
        ).fetchall()
    ]

    # 3. Wiring Diagrams
    wiring_diagrams = [
        dict(r)
        for r in cur.execute(
            "SELECT id, brand, model, year_range, system_name, ecu_connector_code, "
            "pinout_json, ground_locations, diagram_image_url FROM wiring_diagrams ORDER BY id"
        ).fetchall()
    ]

    # 4. Sensor Specs
    sensor_specs = [
        dict(r)
        for r in cur.execute(
            "SELECT id, brand, model, sensor_name, pin_configuration, voltage_idle, "
            "voltage_wot, resistance_ohm, testing_notes FROM sensor_specs ORDER BY id"
        ).fetchall()
    ]

    # 5. Repair Manuals (buang kolom source_file_path & created_at agar hemat ukuran)
    repair_manuals = [
        dict(r)
        for r in cur.execute(
            "SELECT id, brand, model, section_title, content_text, tags FROM repair_manuals ORDER BY id"
        ).fetchall()
    ]

    conn.close()

    # 6. JB420 Extracted Catalog
    jb420_catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

    datasets = {
        "historical_cases.json": sorted_cases,
        "dtc_codes.json": dtc_codes,
        "wiring_diagrams.json": wiring_diagrams,
        "sensor_specs.json": sensor_specs,
        "repair_manuals.json": repair_manuals,
        "jb420_catalog.json": jb420_catalog,
    }

    print("=== HASIL EKSPOR DATA OFFLINE ===")
    for filename, payload in datasets.items():
        out_file = OUT_DATA_DIR / filename
        out_file.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        size_kb = out_file.stat().st_size / 1024.0
        count_info = len(payload) if isinstance(payload, list) else len(payload.get("dtc_catalog", []))
        print(f" - {filename:24s} : {size_kb:8.2f} KB ({count_info} entri)")

    # Buat juga embedded-data.js agar bekerja 100% baik via fetch() maupun file:// langsung di WebView
    embedded_bundle = {
        "historical_cases": sorted_cases,
        "dtc_codes": dtc_codes,
        "wiring_diagrams": wiring_diagrams,
        "sensor_specs": sensor_specs,
        "repair_manuals": repair_manuals,
        "jb420_catalog": jb420_catalog,
    }
    embedded_js_path = OUT_JS_DIR / "embedded-data.js"
    embedded_js_path.write_text(
        "window.AGOS_OFFLINE_DATA = "
        + json.dumps(embedded_bundle, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )
    print(f" - {'js/embedded-data.js':24s} : {embedded_js_path.stat().st_size / 1024.0:8.2f} KB")


if __name__ == "__main__":
    export_all()
