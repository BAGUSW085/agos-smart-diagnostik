"""
Verifikasi Mesin Diagnosa & Pencarian Manual (Python vs JavaScript Offline)
===========================================================================
Menjalankan perbandingan langsung antara:
1. Mesin Python (`WeightedDiagnosticEngine` & `ManualAndWiringService.ask_rag_assistant`)
2. Mesin JavaScript (`www/js/engine.js` & `www/js/manual-search.js`)
untuk seluruh kasus di database dan 10 kueri manual/DTC.
Batas toleransi perbedaan skor: maksimal ±0.5%.
"""

from pathlib import Path
from types import SimpleNamespace
import json
import shutil
import subprocess
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
OFFLINE_WWW = ROOT_DIR / "android_offline" / "www"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.diagnostic_service import WeightedCaseSearchRequest, WeightedDiagnosticEngine


def find_node_executable() -> str:
    node_path = shutil.which("node")
    if node_path:
        return node_path
    agy_node = Path.home() / "AppData" / "Roaming" / "Antigravity" / "bin" / "agy-node.cmd"
    if agy_node.exists():
        return str(agy_node)
    raise RuntimeError("Node.js executable tidak ditemukan.")


def run_python_engine_on_case(case_dict: dict, all_cases: list[dict]) -> dict:
    req = WeightedCaseSearchRequest(
        brand=case_dict["brand"] or "",
        model=case_dict["model"] or "",
        complaint=case_dict["complaint"] or "",
        symptom=case_dict["symptom"] or "",
        dtc="" if (case_dict["dtc"] or "") == "Tidak ada" else (case_dict["dtc"] or ""),
        stft=case_dict.get("stft"),
        ltft=case_dict.get("ltft"),
        rpm=case_dict.get("rpm"),
        o2=0.45 if case_dict.get("o2_voltage") else None,
        map_kpa=case_dict.get("map_kpa"),
        maf_gps=case_dict.get("maf_gps"),
        ect_c=case_dict.get("ect_c"),
    )
    has_live = any(
        v is not None for v in [req.stft, req.ltft, req.rpm, req.o2, req.map_kpa, req.maf_gps, req.ect_c]
    )
    best_score = -1.0
    best_code = "-"
    for c in all_cases:
        c_obj = SimpleNamespace(**c)
        t_score = WeightedDiagnosticEngine._calculate_text_similarity(req, c_obj)
        l_score = WeightedDiagnosticEngine._calculate_live_similarity(req, c_obj)
        tot = ((1.0 - 0.15) * t_score + 0.15 * l_score) if (has_live and l_score is not None) else t_score
        tot_pct = round(round(min(max(tot, 0.0), 1.0), 4) * 100, 1)
        if tot_pct > best_score:
            best_score = tot_pct
            best_code = c["case_code"]
    return {"case_code": best_code, "score": best_score}


def main() -> None:
    cases_path = OFFLINE_WWW / "data" / "historical_cases.json"
    all_cases = json.loads(cases_path.read_text(encoding="utf-8"))

    node_runner_js = OFFLINE_WWW / " data_verify_tmp.js"
    node_script = """
const fs = require('fs');
const path = require('path');
const wwwDir = process.argv[2];

global.window = global;
global.localStorage = { getItem: () => null, setItem: () => {} };

require(path.join(wwwDir, 'js', 'embedded-data.js'));
require(path.join(wwwDir, 'js', 'data-store.js'));
require(path.join(wwwDir, 'js', 'engine.js'));
require(path.join(wwwDir, 'js', 'manual-search.js'));

(async () => {
  const cases = await global.AgosDataStore.getAllCases();
  const caseResults = [];
  for (const c of cases) {
    const req = {
      brand: c.brand || '',
      model: c.model || '',
      complaint: c.complaint || '',
      symptom: c.symptom || '',
      dtc: (c.dtc === 'Tidak ada') ? '' : (c.dtc || ''),
      stft: c.stft,
      ltft: c.ltft,
      rpm: c.rpm,
      o2: c.o2_voltage ? 0.45 : null,
      map_kpa: c.map_kpa,
      maf_gps: c.maf_gps,
      ect_c: c.ect_c
    };
    const res = await global.AgosDiagnosticEngine.searchWeightedCases(req);
    const topHist = res.ranked_matches.find(m => !m.case_code.startsWith('MANUAL-')) || res.ranked_matches[0];
    caseResults.push({
      input_code: c.case_code,
      js_best_hist_code: topHist.case_code,
      js_best_hist_score: topHist.total_score,
      js_top_overall_code: res.top_case_code,
      js_top_overall_score: res.top_score_percent
    });
  }

  const queries = [
    'P0122', 'P0480 kipas', 'MAF', 'O2 heater P0037', 'pinout C37',
    'TCM E92', 'ECT suhu', 'P0300 misfire', 'C1021 ABS', 'B1133 BCM'
  ];
  const ragResults = [];
  for (const q of queries) {
    const r = await global.AgosManualSearch.askRagAssistant({ query: q, brand: 'Suzuki', model: 'Grand Vitara' });
    ragResults.push({
      query: q,
      dtcs: r.detected_dtc_codes,
      guidance_len: (r.synthesized_guidance || '').length,
      has_content: !(r.synthesized_guidance || '').startsWith('Data spesifikasi, penyebab')
    });
  }

  console.log(JSON.stringify({ caseResults, ragResults }));
})();
"""
    tmp_js = ROOT_DIR / "android_offline" / "tools" / "_tmp_verify.js"
    tmp_js.write_text(node_script, encoding="utf-8")
    try:
        node_bin = find_node_executable()
        proc = subprocess.run(
            [node_bin, str(tmp_js), str(OFFLINE_WWW)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        out_data = json.loads(proc.stdout.strip())
    finally:
        if tmp_js.exists():
            tmp_js.unlink()

    print("=== 1. VERIFIKASI SKOR MESIN DIAGNOSA (PYTHON vs JS OFFLINE) ===")
    print(f"{'Kasus':<8} | {'Py Best':<8} | {'Py Skor':<8} | {'JS Hist':<8} | {'JS Skor':<8} | {'Selisih':<8} | {'Status'}")
    print("-" * 74)
    all_passed = True
    for c, js_r in zip(all_cases, out_data["caseResults"]):
        py_r = run_python_engine_on_case(c, all_cases)
        diff = abs(py_r["score"] - js_r["js_best_hist_score"])
        ok = diff <= 0.5
        if not ok:
            all_passed = False
        status_str = "LULUS (OK)" if ok else "GAGAL"
        print(
            f"{c['case_code']:<8} | {py_r['case_code']:<8} | {py_r['score']:>6.1f}% | "
            f"{js_r['js_best_hist_code']:<8} | {js_r['js_best_hist_score']:>6.1f}% | "
            f"{diff:>6.2f}% | {status_str}"
        )

    print("\n=== 2. VERIFIKASI 10 KUERI PENCARIAN MANUAL / DTC OFFLINE ===")
    for item in out_data["ragResults"]:
        ok_q = item["has_content"] and item["guidance_len"] > 80
        if not ok_q:
            all_passed = False
        print(
            f" - Kueri: {item['query']:<18} | DTC: {str(item['dtcs']):<16} | "
            f"Panjang Jawaban: {item['guidance_len']:4d} karakter | {'LULUS' if ok_q else 'GAGAL'}"
        )

    if not all_passed:
        sys.exit(1)
    print("\n[SUKSES] Seluruh 17 Kasus & 10 Kueri Manual LULUS Verifikasi 100%!")


if __name__ == "__main__":
    main()
