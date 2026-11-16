/**
 * AGOS Smart Diagnostik — Offline Weighted Diagnostic Engine (engine.js)
 * ======================================================================
 * Port 1:1 dari `backend/app/services/diagnostic_service.py` (WeightedDiagnosticEngine).
 * Menjamin akurasi skor teks (85%), skor live data scanner (15%), klasifikasi
 * kategori, dan saran ManualRepairAdvice identik dengan mesin Python.
 */
(function (global) {
  'use strict';

  const INDONESIAN_STOPWORDS = new Set([
    'yang', 'dan', 'di', 'ke', 'dari', 'saat', 'ketika', 'kalau', 'bila',
    'pada', 'untuk', 'dengan', 'atau', 'ada', 'tidak', 'agak', 'sangat',
    'sekali', 'mobil', 'mesin', 'tiba', 'terus', 'habis', 'setelah', 'baru'
  ]);

  const AUTOMOTIVE_SYNONYM_MAP = {
    brebet: 'mbrebet',
    berebet: 'mbrebet',
    ndut: 'mbrebet',
    ndutan: 'mbrebet',
    nyendat: 'mbrebet',
    tersendat: 'mbrebet',
    pincang: 'pincang',
    getar: 'getar',
    goyang: 'getar',
    langsam: 'idle',
    stasioner: 'idle',
    ngempos: 'ngempos',
    lelet: 'berat',
    boyo: 'berat',
    kempos: 'ngempos',
    panas: 'overheat',
    mendidih: 'overheat',
    temperatur: 'overheat',
    mogok: 'mogok',
    mati: 'mati',
    susah: 'sulit',
    berat: 'berat'
  };

  const SYSTEM_DEFINITIONS = [
    { name: 'Udara', group: 'Pembakaran', params: 'MAF, MAP, TPS, IAT' },
    { name: 'Bahan Bakar', group: 'Pembakaran', params: 'STFT, LTFT, O2/AFR, tekanan BBM, injector pulse' },
    { name: 'Pengapian', group: 'Pembakaran', params: 'Misfire counter, spark advance, busi, koil' },
    { name: 'Mekanis', group: 'Pembakaran', params: 'Kompresi silinder, vakum idle, timing chain/belt' },
    { name: 'Pendingin', group: 'Pendukung', params: 'ECT sensor, kerja kipas, thermostat, radiator' },
    { name: 'Pelumasan', group: 'Pendukung', params: 'Tekanan oli, level oli, switch tekanan oli' },
    { name: 'Kelistrikan', group: 'Pendukung', params: 'Tegangan aki, charging alternator, massa bodi' },
    { name: 'Emisi', group: 'Pendukung', params: 'O2 sensor downstream, catalytic converter, EVAP purge' }
  ];

  const DTC_SUBSYSTEM_FAMILIES = [
    new Set(['P0030', 'P0031', 'P0032', 'P0036', 'P0037', 'P0038', 'P0130', 'P0131', 'P0132', 'P0133', 'P0134', 'P0135', 'P0136', 'P0137', 'P0138', 'P0140', 'P0141', 'P2195', 'P2196']),
    new Set(['P0100', 'P0101', 'P0102', 'P0103', 'P0104']),
    new Set(['P0105', 'P0106', 'P0107', 'P0108', 'P2227', 'P2228', 'P2229']),
    new Set(['P0110', 'P0111', 'P0112', 'P0113', 'P0114']),
    new Set(['P0115', 'P0116', 'P0117', 'P0118', 'P0119', 'P0125', 'P0128']),
    new Set(['P0120', 'P0121', 'P0122', 'P0123', 'P0220', 'P0222', 'P0223', 'P2101', 'P2102', 'P2103', 'P2111', 'P2119', 'P2135', 'P0506', 'P0507']),
    new Set(['P2122', 'P2123', 'P2127', 'P2128', 'P2138']),
    new Set(['P0171', 'P0174']),
    new Set(['P0172', 'P0175']),
    new Set(['P0200', 'P0201', 'P0202', 'P0203', 'P0204', 'P0205', 'P0206']),
    new Set(['P0300', 'P0301', 'P0302', 'P0303', 'P0304', 'P0305', 'P0306']),
    new Set(['P0325', 'P0327', 'P0328']),
    new Set(['P0335', 'P0336', 'P0340', 'P0341']),
    new Set(['P0350', 'P0351', 'P0352', 'P0353', 'P0354']),
    new Set(['P0400', 'P0401', 'P0402', 'P0403', 'P0404']),
    new Set(['P0420', 'P0430']),
    new Set(['P0440', 'P0441', 'P0442', 'P0443', 'P0446', 'P0455', 'P0456']),
    new Set(['P0480', 'P0481', 'P0482', 'P0483', 'P0484', 'P0485'])
  ];

  const STANDARD_OBD_FALLBACK = {
    P0481: {
      system: 'Engine / Powertrain (ECM) — Cooling Fan Control',
      description_id: 'Sirkuit Kontrol Kipas Radiator 2 (High Speed / Sub Fan)',
      possible_causes: 'Relay Kipas Radiator No. 2 putus/macet, sekering kipas putus, motor kipas No. 2 rusak, atau kabel kontrol E23-47 (RED) ke ECM putus/hubung singkat.',
      severity_level: 'HIGH'
    },
    P0482: {
      system: 'Engine / Powertrain (ECM) — Cooling Fan Control',
      description_id: 'Sirkuit Kontrol Kipas Radiator 3',
      possible_causes: 'Relay atau kabel kontrol kipas pendingin 3 putus/konslet.',
      severity_level: 'HIGH'
    },
    P0128: {
      system: 'Engine / Powertrain (ECM) — Cooling System',
      description_id: 'Suhu Kerja Coolant di Bawah Temperatur Regulasi Thermostat',
      possible_causes: 'Thermostat macet terbuka (stuck open) atau sensor ECT (C37-24) membaca terlalu dingin.',
      severity_level: 'MEDIUM'
    },
    P0201: { system: 'Engine / Powertrain (ECM) — Fuel Injector', description_id: 'Sirkuit Injektor Silinder 1 Putus / Bermasalah', possible_causes: 'Koil injektor No.1 putus (normal 11.5-14.5 Ohm), soket injektor kendor, atau jalur pulsa ground ECM putus.', severity_level: 'HIGH' },
    P0202: { system: 'Engine / Powertrain (ECM) — Fuel Injector', description_id: 'Sirkuit Injektor Silinder 2 Putus / Bermasalah', possible_causes: 'Koil injektor No.2 putus (normal 11.5-14.5 Ohm), soket injektor kendor, atau jalur pulsa ground ECM putus.', severity_level: 'HIGH' },
    P0203: { system: 'Engine / Powertrain (ECM) — Fuel Injector', description_id: 'Sirkuit Injektor Silinder 3 Putus / Bermasalah', possible_causes: 'Koil injektor No.3 putus (normal 11.5-14.5 Ohm), soket injektor kendor, atau jalur pulsa ground ECM putus.', severity_level: 'HIGH' },
    P0204: { system: 'Engine / Powertrain (ECM) — Fuel Injector', description_id: 'Sirkuit Injektor Silinder 4 Putus / Bermasalah', possible_causes: 'Koil injektor No.4 putus (normal 11.5-14.5 Ohm), soket injektor kendor, atau jalur pulsa ground ECM putus.', severity_level: 'HIGH' },
    P0230: { system: 'Engine / Powertrain (ECM) — Fuel Pump', description_id: 'Sirkuit Primer Relay Pompa Bensin (Fuel Pump Primary Circuit)', possible_causes: 'Relay Fuel Pump rusak, sekering pompa bensin putus, atau jalur kontrol E23-15 (WHT/GRN) dari ECM putus.', severity_level: 'CRITICAL' },
    P0351: { system: 'Engine / Powertrain (ECM) — Ignition System', description_id: "Sirkuit Primer/Sekunder Ignition Coil 'A' (Silinder 1)", possible_causes: 'Ignition coil No.1 mati, soket 3/4-pin koil kendor, atau kabel trigger IGT1 dari ECM putus.', severity_level: 'HIGH' },
    P0352: { system: 'Engine / Powertrain (ECM) — Ignition System', description_id: "Sirkuit Primer/Sekunder Ignition Coil 'B' (Silinder 2)", possible_causes: 'Ignition coil No.2 mati, soket koil kendor, atau kabel trigger IGT2 dari ECM putus.', severity_level: 'HIGH' },
    P0353: { system: 'Engine / Powertrain (ECM) — Ignition System', description_id: "Sirkuit Primer/Sekunder Ignition Coil 'C' (Silinder 3)", possible_causes: 'Ignition coil No.3 mati, soket koil kendor, atau kabel trigger IGT3 dari ECM putus.', severity_level: 'HIGH' },
    P0354: { system: 'Engine / Powertrain (ECM) — Ignition System', description_id: "Sirkuit Primer/Sekunder Ignition Coil 'D' (Silinder 4)", possible_causes: 'Ignition coil No.4 mati, soket koil kendor, atau kabel trigger IGT4 dari ECM putus.', severity_level: 'HIGH' },
    P0560: { system: 'Engine / Powertrain (ECM) — Charging / Power', description_id: 'Tegangan Sistem Kelistrikan Tidak Normal (System Voltage Malfunction)', possible_causes: 'Aki soak, alternator overcharge/undercharge, atau kabel suplai utama E23-01 / backup E23-02 korosi.', severity_level: 'MEDIUM' },
    P0562: { system: 'Engine / Powertrain (ECM) — Charging / Power', description_id: 'Tegangan Sistem Kelistrikan Terlalu Rendah (< 10.5V)', possible_causes: 'Alternator tidak mengisi, aki lemah, atau terminal massa mesin kendur.', severity_level: 'HIGH' },
    P0563: { system: 'Engine / Powertrain (ECM) — Charging / Power', description_id: 'Tegangan Sistem Kelistrikan Terlalu Tinggi (> 16.0V)', possible_causes: 'IC Regulator alternator rusak (overcharging).', severity_level: 'HIGH' }
  };

  const NO_DTC_TOKENS = new Set(['-', 'TIDAK', 'ADA', 'NONE', 'NIL', 'KOSONG']);
  const DTC_SCANNER_SUFFIX_RE = /^([PCBU][0-9A-F]{4})-?[0-9A-F]{2}$/;

  function preprocessSymptomTokens(text) {
    if (!text) return [];
    const cleaned = String(text).toLowerCase().replace(/[^a-z0-9\s]/g, ' ');
    const rawTokens = cleaned.split(/\s+/).filter(Boolean);
    const normalized = [];
    for (const tok of rawTokens) {
      if (tok.length <= 1 || INDONESIAN_STOPWORDS.has(tok)) continue;
      normalized.push(AUTOMOTIVE_SYNONYM_MAP[tok] || tok);
    }
    return normalized;
  }

  function splitDtcCodes(raw) {
    const codes = [];
    const parts = String(raw || '').trim().toUpperCase().split(/[,;\s]+/);
    for (let tok of parts) {
      if (!tok || NO_DTC_TOKENS.has(tok)) continue;
      const m = tok.match(DTC_SCANNER_SUFFIX_RE);
      if (m) tok = m[1];
      if (!codes.includes(tok)) codes.push(tok);
    }
    return codes;
  }

  function extractAllRequestDtcs(req) {
    const codes = splitDtcCodes(req.dtc);
    const combined = `${req.dtc || ''} ${req.complaint || ''} ${req.symptom || ''}`.toUpperCase();
    const stdMatches = combined.matchAll(/\b([PCBU][0-9A-F]{4})(?:-?[0-9A-F]{2})?\b/g);
    for (const m of stdMatches) {
      if (!codes.includes(m[1])) codes.push(m[1]);
    }
    const klsMatches = combined.matchAll(/\bKLS-(\d{1,2})\b/g);
    for (const m of klsMatches) {
      const k = `KLS-${m[1]}`;
      if (!codes.includes(k)) codes.push(k);
    }
    const noMatches = combined.matchAll(/\bDTC\s*NO\.?\s*(\d{1,2})\b/g);
    for (const m of noMatches) {
      const k = `KLS-${m[1]}`;
      if (!codes.includes(k)) codes.push(k);
    }
    return codes;
  }

  function areSameDtcSubsystem(c1, c2) {
    if (c1 === c2) return true;
    for (const fam of DTC_SUBSYSTEM_FAMILIES) {
      if (fam.has(c1) && fam.has(c2)) return true;
    }
    return false;
  }

  function setIntersectionCount(setA, setB) {
    let count = 0;
    for (const v of setA) {
      if (setB.has(v)) count++;
    }
    return count;
  }

  function calculateTextSimilarity(req, c) {
    let simBrand = 0.0;
    const bReq = String(req.brand || '').trim().toLowerCase();
    if (bReq) {
      const bCase = String(c.brand || '').trim().toLowerCase();
      if (bReq === bCase || (bCase && bCase.includes(bReq)) || (bCase && bReq.includes(bCase))) {
        simBrand = 1.0;
      }
    }

    let simModel = 0.0;
    const mReqStr = String(req.model || '').trim().toLowerCase();
    if (mReqStr) {
      const mReq = new Set(mReqStr.split(/\s+/).filter(Boolean));
      const mCase = new Set(String(c.model || '').trim().toLowerCase().split(/\s+/).filter(Boolean));
      if (mReq.size > 0 && mCase.size > 0) {
        const overlap = setIntersectionCount(mReq, mCase);
        simModel = overlap / Math.max(mReq.size, mCase.size);
      }
    }

    let simComplaint = 0.0;
    if (String(req.complaint || '').trim()) {
      const cReq = new Set(preprocessSymptomTokens(req.complaint));
      const cCase = new Set(preprocessSymptomTokens(c.complaint || ''));
      if (cReq.size > 0 && cCase.size > 0) {
        simComplaint = setIntersectionCount(cReq, cCase) / Math.max(cReq.size, cCase.size);
      }
    }

    let simSymptom = 0.0;
    if (String(req.symptom || '').trim()) {
      const sReq = new Set(preprocessSymptomTokens(req.symptom));
      const sCase = new Set(preprocessSymptomTokens(c.symptom || ''));
      if (sReq.size > 0 && sCase.size > 0) {
        simSymptom = setIntersectionCount(sReq, sCase) / Math.max(sReq.size, sCase.size);
      }
    }

    const reqCodes = new Set(extractAllRequestDtcs(req));
    const caseCodes = new Set(splitDtcCodes(c.dtc));
    let simDtc = 0.0;
    if (reqCodes.size === 0 && caseCodes.size === 0) {
      simDtc = 1.0;
    } else if (reqCodes.size === 0 || caseCodes.size === 0) {
      simDtc = 0.0;
    } else {
      let matched = 0.0;
      for (const code of reqCodes) {
        if (caseCodes.has(code)) {
          matched += 1.0;
        } else {
          let subMatch = false;
          for (const other of caseCodes) {
            if (areSameDtcSubsystem(code, other)) {
              subMatch = true;
              break;
            }
          }
          if (subMatch) matched += 0.60;
        }
      }
      simDtc = Math.min(matched / Math.max(reqCodes.size, caseCodes.size), 1.0);
    }

    const totalText =
      0.10 * simBrand +
      0.15 * simModel +
      0.20 * simComplaint +
      0.20 * simSymptom +
      0.20 * simDtc;

    let normalizedText = Math.min(totalText / 0.85, 1.0);
    if (reqCodes.size > 0 && simDtc === 0.0) {
      normalizedText *= 0.30;
    }
    return normalizedText;
  }

  function calculateLiveSimilarity(req, c) {
    const weightsConfig = [
      [req.stft, c.stft, 0.20, 5.0],
      [req.ltft, c.ltft, 0.15, 5.0],
      [req.rpm, c.rpm, 0.10, 300.0],
      [req.map_kpa, c.map_kpa, 0.15, 10.0],
      [req.maf_gps, c.maf_gps, 0.10, 2.0],
      [req.ect_c, c.ect_c, 0.15, 10.0]
    ];

    let activeWeights = 0.0;
    let weightedScoreSum = 0.0;

    for (const [reqVal, caseVal, weight, tol] of weightsConfig) {
      if (reqVal !== null && reqVal !== undefined && caseVal !== null && caseVal !== undefined) {
        const diff = Math.abs(Number(reqVal) - Number(caseVal));
        const simParam = Math.max(0.0, 1.0 - diff / tol);
        weightedScoreSum += weight * simParam;
        activeWeights += weight;
      }
    }

    if (req.o2 !== null && req.o2 !== undefined && c.o2_voltage) {
      try {
        const cleanO2 = String(c.o2_voltage).replace(/V/gi, '').replace(/,/g, '.').replace(/–/g, '-');
        const parts = cleanO2
          .split('-')
          .map((p) => parseFloat(p.trim()))
          .filter((n) => !Number.isNaN(n));
        if (parts.length > 0) {
          const avg = parts.reduce((a, b) => a + b, 0) / parts.length;
          const diffO2 = Math.abs(Number(req.o2) - avg);
          const simO2 = Math.max(0.0, 1.0 - diffO2 / 0.15);
          weightedScoreSum += 0.15 * simO2;
          activeWeights += 0.15;
        }
      } catch (_) {}
    }

    if (activeWeights <= 0) return null;
    return Math.min(weightedScoreSum / activeWeights, 1.0);
  }

  function determineCategory(score) {
    if (score >= 0.80) return 'Sangat mirip';
    if (score >= 0.60) return 'Mirip';
    if (score >= 0.40) return 'Cukup mirip';
    return 'Kurang mirip';
  }

  function hasAnyCode(codeSet, list) {
    return list.some((c) => codeSet.has(c));
  }

  function getRepairManualGuidance(diagnosis, dtc) {
    const diagClean = String(diagnosis || '').toLowerCase();
    const dtcClean = String(dtc || '').toUpperCase();
    const dtcCodes = new Set(splitDtcCodes(dtcClean));

    if (diagClean.includes('vakum') || diagClean.includes('selang intake') || dtcCodes.has('P0171')) {
      return {
        diagnosis_title: 'Kebocoran Udara / Vakum pada Saluran Intake (Lean Mixture)',
        system_category: 'Udara',
        group_category: 'Pembakaran',
        manual_book_section: 'Buku Pedoman Resmi Suzuki Vitara JB420 / Toyota 1NR-VE Bab 1A-68 (Air Metering) & Bab 1D (Intake Manifold)',
        cause_summary: 'Udara liar (unmetered air) bocor masuk ke intake manifold setelah sensor MAF, menyebabkan campuran bensin terlalu kurus (Lean - P0171) dan mesin brebet saat idle.',
        cause_items: [
          { badge: 'Penyebab Utama #1', title: 'Selang Vakum & Gasket Intake Manifold Bocor', desc: 'Selang vakum booster rem, selang PCV, atau paking intake manifold getas/retak sehingga menghisap udara luar.' },
          { badge: 'Penyebab #2', title: 'Sensor Aliran Udara (MAF Sensor) Kotor', desc: 'Kawat sensor MAF tertutup debu sehingga membaca debit udara lebih rendah dari kondisi nyata.' },
          { badge: 'Penyebab #3', title: 'Tekanan Pompa Bensin (Fuel Pump) Lemah / Injektor Mampet', desc: 'Suplai tekanan fuel rail turun (< 3.0 bar) atau filter bensin tersumbat kotoran.' }
        ],
        repair_options: [
          { tag: 'Opsi 1 • Utama (Vakum)', title: 'Ganti Selang Vakum Retak & Rapatkan Gasket Intake', desc: 'Ganti selang vakum/PCV yang getas dengan selang SAE J30R7 dan kencangkan klem atau ganti paking intake.' },
          { tag: 'Opsi 2 • Sensor Udara', title: 'Bersihkan Sensor MAF & Cek Belalai Karet Intake', desc: 'Semprot elemen sensor MAF dengan MAF cleaner khusus dan pastikan karet belalai udara tidak sobek.' },
          { tag: 'Opsi 3 • Sistem BBM', title: 'Servis Injektor & Periksa Tekanan Fuel Pump / Filter Bensin', desc: 'Ukur tekanan fuel rail (standar 3.0–3.5 bar), ganti filter bensin, atau servis injektor yang tersumbat.' }
        ],
        sensor_standards: [
          { parameter: 'Tekanan Manifold MAP (Idle)', normal_range: '30 - 42 kPa', unit: 'kPa' },
          { parameter: 'Aliran Udara MAF (Idle Mesin Hangat)', normal_range: '2.0 - 3.2 g/s', unit: 'g/s' },
          { parameter: 'Short Term Fuel Trim (STFT)', normal_range: '-10% s/d +10%', unit: '%' },
          { parameter: 'Long Term Fuel Trim (LTFT)', normal_range: '-10% s/d +10%', unit: '%' }
        ],
        wiring_pinout: [
          { pin: 'C37-55', signal: 'MAP Sensor Output (RED/WHT)', function: 'Sinyal tekanan manifold ke ECM (idle: ~1.2V)' },
          { pin: 'C37-14', signal: 'Sensor +5V Reference (GRY/RED)', function: 'Tegangan referensi 5.0V dari regulator ECM' },
          { pin: 'C37-57', signal: 'Sensor Ground (GRY/GRN)', function: 'Massa sensor referensi ECM (tahanan < 0.5 Ohm)' }
        ],
        step_by_step_repair: [
          '1. Lakukan smoke test atau semprotkan sedikit intake cleaner di sepanjang selang vakum dan sambungan intake saat idle. Bila RPM naik, titik bocor terkonfirmasi.',
          '2. Periksa selang vakum brake booster, selang PCV, dan selang pernapasan kanister EVAP dari keretakan atau kerapuhan.',
          '3. Lepas klem selang menggunakan tang khusus, ganti selang vakum retak dengan selang berstandar SAE J30R7 (tahan panas/minyak).',
          '4. Pastikan klem terpasang kuat pada posisi dudukannya tanpa meremas selang hingga robek.'
        ],
        relearn_reset_steps: [
          "1. Sambungkan OBD-II scanner, lakukan 'Clear DTC P0171'.",
          "2. Lakukan 'Reset Fuel Trim Learned Values' via scanner (atau lepas terminal minus aki selama 15 menit).",
          '3. Hidupkan mesin tanpa beban kelistrikan (AC, lampu, audio OFF) hingga suhu air radiator mencapai 85-90°C.',
          '4. Pantau live data: pastikan STFT dan LTFT kembali normal ke rentang -5% s/d +5%.'
        ]
      };
    }

    if (diagClean.includes('pcv')) {
      return {
        diagnosis_title: 'Kebocoran / Kerusakan Katup PCV (Positive Crankcase Ventilation)',
        system_category: 'Udara',
        group_category: 'Pembakaran',
        manual_book_section: 'Buku Pedoman Servis Bab 1B (Emission Control System - PCV Valve)',
        cause_summary: 'Katup ventilasi karter (PCV Valve) macet terbuka atau selang PCV pecah akibat uap oli panas, memicu kebocoran vakum dan mesin pincang saat idle.',
        cause_items: [
          { badge: 'Penyebab Utama #1', title: 'Katup PCV Macet Terbuka (Tertahan Kerak Oli)', desc: 'Pegas katup satu arah PCV terganjal endapan lumpur oli sehingga udara terhisap terus-menerus ke intake.' },
          { badge: 'Penyebab #2', title: 'Selang Karet & Grommet PCV Getas / Pecah', desc: 'Karet selang penghubung tutup klep (valve cover) ke intake manifold mengeras dan sobek.' }
        ],
        repair_options: [
          { tag: 'Opsi 1 • Utama (Ganti Part)', title: 'Ganti Katup PCV Baru & Selang Karet PCV', desc: 'Pasang katup PCV satu arah baru (torsi 12 N·m) beserta selang karet tahan panas/oli.' },
          { tag: 'Opsi 2 • Servis Bersih', title: 'Bersihkan Katup PCV, Saluran Breather & Reset ECU', desc: 'Semprot bersih kerak oli pada katup PCV dan lubang breather tutup klep bila pegas katup masih normal.' }
        ],
        sensor_standards: [
          { parameter: 'Vakum Intake saat Idle', normal_range: '18 - 22 inHg (60 - 74 kPa vakum)', unit: 'inHg' },
          { parameter: 'STFT Idle', normal_range: '-10% s/d +10%', unit: '%' }
        ],
        wiring_pinout: [
          { pin: 'Bodi Mesin', signal: 'Ground Massa', function: 'Ground katup dan manifold bodi mesin' }
        ],
        step_by_step_repair: [
          '1. Lepas katup PCV dari tutup klep (valve cover). Kocok katup: harus terdengar bunyi peluru klik-klik bebas di dalamnya. Jika macet, katup rusak/berkerak oli.',
          '2. Tiup katup dari arah manifold: udara TIDAK BOLEH tembus (katup satu arah). Tiup dari arah klep: udara harus lolos.',
          '3. Ganti katup PCV dan selang karet PCV jika mengeras atau retak.',
          '4. Pasang katup PCV baru dengan torsi 12 N·m.'
        ],
        relearn_reset_steps: [
          '1. Hapus memori adaptasi fuel trim ECU.',
          '2. Nyalakan mesin dan amati kestabilan idle pada 750 ± 50 RPM.'
        ]
      };
    }

    if (
      /\bo2\b|oksigen|oxygen|lambda/.test(diagClean) ||
      hasAnyCode(dtcCodes, ['P0030', 'P0031', 'P0032', 'P0036', 'P0037', 'P0038', 'P0130', 'P0131', 'P0132', 'P0135', 'P0136', 'P0137', 'P0138', 'P0141'])
    ) {
      return {
        diagnosis_title: 'Gangguan Sensor Oksigen / Sirkuit Pemanas HO2S (Hulu & Hilir)',
        system_category: 'Bahan Bakar',
        group_category: 'Pembakaran',
        manual_book_section: 'Suzuki Grand Vitara JB420 Manual Bab 1A-140 & Toyota Manual Section 1A (Oxygen Sensor)',
        cause_summary: 'Elemen pemanas (heater) sensor O2 putus atau ujung keramik sensor tertutup jelaga karbon, sehingga pembacaan kadar oksigen gas buang meleset dan BBM menjadi boros.',
        cause_items: [
          { badge: 'Penyebab Utama #1', title: 'Elemen Heater Putus / Sensor O2 Jenuh Karbon', desc: 'Kumparan pemanas internal sensor O2 putus (tahanan > 16 Ohm / ∞) atau ujung sensor tertutup jelaga tebal.' },
          { badge: 'Penyebab #2', title: 'Soket 4-Pin Kendor / Kabel Meleleh Terkena Knalpot', desc: 'Isolasi kabel sensor O2 terkelupas atau hubung singkat karena menempel pada pipa exhaust manifold panas.' },
          { badge: 'Penyebab #3', title: 'Kualitas Bahan Bakar Buruk / Kebocoran Paking Knalpot', desc: 'Kontaminasi aditif BBM kualitas rendah atau udara luar menyusup lewat paking knalpot yang bocor.' }
        ],
        repair_options: [
          { tag: 'Opsi 1 • Utama (Ganti Sensor)', title: 'Ganti Sensor Oksigen (HO2S) Baru', desc: 'Ganti unit sensor O2 yang putus heater/lemah menggunakan kunci soket 22 mm (torsi 44 N·m).' },
          { tag: 'Opsi 2 • Kelistrikan & Soket', title: 'Perbaiki Kabel Harness Sensor O2, Soket 4-Pin & Sekering', desc: 'Isolasi ulang kabel yang meleleh terkena knalpot, bersihkan pin konektor, dan cek sekering heater O2.' },
          { tag: 'Opsi 3 • BBM & Knalpot', title: 'Bersihkan Jelaga Sensor, Ganti BBM & Rapatkan Paking Knalpot', desc: 'Bersihkan ujung pelindung sensor O2, gunakan BBM sesuai oktan mesin, dan cek kerapatan exhaust manifold.' }
        ],
        sensor_standards: [
          { parameter: 'Voltase Sinyal O2 (Closed Loop)', normal_range: '0.10 - 0.90 V (berosilasi cepat)', unit: 'V' },
          { parameter: 'Frekuensi Osilasi (pada 2.500 RPM)', normal_range: '> 1 Hz (minimal 1 kali per detik)', unit: 'Hz' },
          { parameter: 'Tahanan Pemanas Sensor (20°C)', normal_range: '11.0 - 16.0 Ohm', unit: 'Ohm' }
        ],
        wiring_pinout: [
          { pin: 'E23-50 (Pin 1)', signal: 'Heater +12V Power (BLK/YEL)', function: 'Suplai arus +12V IG ke elemen pemanas sensor O2' },
          { pin: 'E23-49 (Pin 2)', signal: 'HT / Heater PWM Control (BLK/WHT)', function: 'Kontrol duty-cycle pemanas heater O2 dari ECM' },
          { pin: 'C37-65 (Pin 3)', signal: 'OX / Sinyal Output O2 (WHT/RED)', function: 'Tegangan sinyal pembacaan oksigen 0.1 - 0.9V ke ECM' },
          { pin: 'C37-57 (Pin 4)', signal: 'E2 / Massa Sensor O2 (GRY/GRN)', function: 'Ground referensi sinyal sensor O2 ke ECM' }
        ],
        step_by_step_repair: [
          '1. Periksa kabel dan soket sensor O2 di exhaust manifold dari leleh/terbakar akibat panas knalpot.',
          '2. Gunakan multimeter untuk mengukur tahanan heater pada 2 pin sensor O2 (normal 11-16 Ohm). Bila putus/infinite, sensor wajib ganti.',
          '3. Lepas sensor O2 menggunakan kunci soket berbelah 22 mm (oxygen sensor socket).',
          '4. Oleskan anti-seize paste pada ulir sensor baru (jangan sampai mengenai ujung tip sensor!), kencangkan dengan torsi 44 N·m.'
        ],
        relearn_reset_steps: [
          '1. Reset DTC P0131 dan reset fuel trim via scanner.',
          '2. Jalankan kendaraan pada kecepatan konstan 60-80 km/jam selama 10 menit untuk melengkapi OBD-II O2 Monitor readiness.'
        ]
      };
    }

    if (/\bect\b/.test(diagClean) || diagClean.includes('suhu')) {
      return {
        diagnosis_title: 'Penyimpangan Nilai Sensor Suhu Pendingin (Engine Coolant Temperature - ECT)',
        system_category: 'Pendingin',
        group_category: 'Pendukung',
        manual_book_section: 'Buku Pedoman Resmi Suzuki Vitara JB420 Bab 1A-108 (ECT Sensor Inspection)',
        cause_summary: 'Termistor NTC pada sensor ECT mengalami penyimpangan nilai tahanan atau konektornya berkarat, membuat ECU salah mengatur semprotan bensin dingin dan putaran kipas radiator.',
        cause_items: [
          { badge: 'Penyebab Utama #1', title: 'Sensor ECT Rusak / Nilai Tahanan NTC Menyimpang', desc: 'Sensor membaca suhu mesin tidak akurat sehingga suplai bensin starter pagi kurang atau kipas salah bekerja.' },
          { badge: 'Penyebab #2', title: 'Pin Soket 2-Pin ECT Berkarat / Kabel C37-24 Longgar', desc: 'Rembesan coolant atau korosi pada pin konektor memicu resistansi kontak tinggi.' },
          { badge: 'Penyebab #3', title: 'Thermostat Macet atau Ada Udara Terjebak di Radiator', desc: 'Thermostat macet terbuka/tertutup atau level air coolant kurang sehingga pembacaan suhu kacau.' }
        ],
        repair_options: [
          { tag: 'Opsi 1 • Utama (Ganti Sensor)', title: 'Ganti Sensor Suhu ECT Baru & Bleeding Air Radiator', desc: 'Ganti sensor ECT di rumah thermostat (kunci 19 mm, torsi 15 N·m) dan buang udara palsu di sistem pendingin.' },
          { tag: 'Opsi 2 • Soket & Kabel', title: 'Bersihkan Soket 2-Pin ECT & Perbaiki Jalur Kabel C37-24', desc: 'Semprot contact cleaner pada terminal soket ECT dan rapatkan penjepit pin konektor.' },
          { tag: 'Opsi 3 • Sistem Pendingin', title: 'Ganti Thermostat & Kuras Air Radiator Coolant', desc: 'Ganti thermostat jika macet serta isi ulang coolant sesuai standar kapasitas pabrik.' }
        ],
        sensor_standards: [
          { parameter: 'Tahanan ECT pada 20°C (Mesin Dingin)', normal_range: '2.21 - 2.69 kOhm (tegangan ~3.0V)', unit: 'kOhm' },
          { parameter: 'Tahanan ECT pada 80°C (Suhu Kerja)', normal_range: '290 - 354 Ohm (tegangan ~0.5V)', unit: 'Ohm' }
        ],
        wiring_pinout: [
          { pin: 'C37-24', signal: 'THW / ECT Signal (PPL/YEL)', function: 'Input tegangan sinyal suhu pendingin ke ECM' },
          { pin: 'C37-57', signal: 'E2 / Ground Sensor (GRY/GRN)', function: 'Massa sensor ECM' }
        ],
        step_by_step_repair: [
          '1. Dinginkan mesin semalaman, sambungkan scanner sebelum start pagi, bandingkan data ECT dengan IAT (keduanya harus selisih < 3°C).',
          '2. Buka kran kuras radiator dan tampung 1-2 liter coolant bersih.',
          '3. Lepas sensor ECT di rumah thermostat menggunakan kunci ring 19 mm.',
          '4. Bersihkan ulir, lapisi ulir sensor ECT baru dengan liquid gasket / Teflon tape, kencangkan torsi 15 N·m.',
          '5. Tuangkan kembali coolant dan lakukan bleeding udara terjebak di radiator.'
        ],
        relearn_reset_steps: [
          '1. Nyalakan mesin sampai mencapai suhu kerja 85-90°C.',
          '2. Pastikan kipas radiator otomatis berputar saat ECT mencapai 96-98°C dan mati pada 92°C.'
        ]
      };
    }

    if (diagClean.includes('maf') || dtcCodes.has('P0101')) {
      return {
        diagnosis_title: 'Sensor Aliran Udara MAF Kotor / Terkontaminasi Jelaga',
        system_category: 'Udara',
        group_category: 'Pembakaran',
        manual_book_section: 'Buku Pedoman Servis Bab 1A-62 (Mass Air Flow Sensor Inspection)',
        cause_summary: 'Kawat pemanas (hot-wire) sensor MAF tertutup debu dan uap oli dari filter udara kotor, menyebabkan pembacaan debit udara meleset (P0101) dan tarikan mesin kehilangan tenaga.',
        cause_items: [
          { badge: 'Penyebab Utama #1', title: 'Elemen Kawat Sensor MAF Tertutup Debu / Uap Oli', desc: 'Kotoran menempel pada kawat platinum MAF sehingga pembacaan debit udara (g/s) tidak responsif.' },
          { badge: 'Penyebab #2', title: 'Elemen Filter Udara Kotor atau Seal Boks Bocor', desc: 'Saringan udara yang tersumbat debu meloloskan partikel halus langsung ke sensor MAF.' },
          { badge: 'Penyebab #3', title: 'Sensor MAF Rusak Permanen atau Soket 5-Pin Longgar', desc: 'Sirkuit internal sensor MAF mati atau tegangan suplai +12V pada pin E23-31 terputus.' }
        ],
        repair_options: [
          { tag: 'Opsi 1 • Utama (Cleaning)', title: 'Bersihkan Sensor MAF dengan MAF Sensor Cleaner', desc: 'Semprot elemen kawat sensor MAF menggunakan cairan khusus MAF cleaner dan keringkan sempurna.' },
          { tag: 'Opsi 2 • Ganti Komponen', title: 'Ganti Unit Sensor MAF Baru & Elemen Filter Udara', desc: 'Ganti sensor MAF assy bila nilai g/s tetap tidak normal setelah dibersihkan, serta ganti filter udara.' },
          { tag: 'Opsi 3 • Soket & Intake', title: 'Perbaiki Konektor 5-Pin MAF & Rapatkan Belalai Intake', desc: 'Kencangkan pin terminal soket MAF dan pastikan tidak ada kebocoran pada karet belalai udara.' }
        ],
        sensor_standards: [
          { parameter: 'Tegangan MAF (Kunci Kontak ON Mesin Mati)', normal_range: '0.90 - 1.20 V (0 g/s)', unit: 'V' },
          { parameter: 'Tegangan MAF (Idle Mesin Hangat 750 RPM)', normal_range: '1.30 - 1.80 V (2.0 - 3.5 g/s)', unit: 'V' },
          { parameter: 'Tegangan MAF (Akselerasi Penuh WOT)', normal_range: '3.50 - 4.50 V (>50 g/s)', unit: 'V' }
        ],
        wiring_pinout: [
          { pin: 'E23-31 (Pin 1)', signal: 'MAF +12V Power (BLK/WHT)', function: 'Suplai daya +12V Main Relay ke elemen Hot-Wire MAF' },
          { pin: 'C37-63 (Pin 2)', signal: 'MAF Ground (BLK/GRN)', function: 'Massa utama pemanas sensor MAF' },
          { pin: 'C37-62 (Pin 3)', signal: 'MAF Signal Output (PNK/BLK)', function: 'Sinyal debit aliran udara (idle ~1.15V) ke ECM' },
          { pin: 'C37-25 (Pin 4)', signal: 'IAT Signal +5V Pull-Up (LT GRN/BLK)', function: 'Sinyal sensor suhu udara masuk (IAT) terintegrasi' },
          { pin: 'C37-57 (Pin 5)', signal: 'IAT Sensor Ground (GRY/GRN)', function: 'Massa referensi sensor IAT ke ECM' }
        ],
        step_by_step_repair: [
          '1. Matikan kunci kontak, lepas konektor terminal sensor MAF di boks filter udara.',
          '2. Buka 2 sekrup pengikat sensor MAF menggunakan obeng kembang presisi.',
          '3. Semprotkan cairan khusus MAF Sensor Cleaner ke kawat tipis dan termistor sensor dari jarak 10 cm (JANGAN SENTUH DENGAN JARI ATAU KUAS!).',
          '4. Biarkan mengering sempurna selama 10 menit, lalu pasang kembali sensor beserta seal karetnya.'
        ],
        relearn_reset_steps: [
          '1. Reset DTC P0101 melalui OBD scanner.',
          '2. Hidupkan mesin dan tes akselerasi mendadak: pastikan nilai MAF g/s melonjak responsif.'
        ]
      };
    }

    if (diagClean.includes('throttle') || diagClean.includes('trotel') || dtcCodes.has('P0507')) {
      return {
        diagnosis_title: 'Endapan Karbon pada Throttle Body / Malfungsi Idle Air Control',
        system_category: 'Udara',
        group_category: 'Pembakaran',
        manual_book_section: 'Buku Pedoman Suzuki Vitara JB420 Bab 1A-88 & Bab 1A-173 (Electric Throttle Body Service)',
        cause_summary: 'Tumpukan kerak karbon mengganjal katup kupu-kupu Electronic Throttle Body (ETC), membuat katup tidak menutup rapat sehingga RPM idle mengayun tinggi (P0507) atau brebet saat AC menyala.',
        cause_items: [
          { badge: 'Penyebab Utama #1', title: 'Kerak Karbon Menumpuk di Dinding & Katup Throttle Body', desc: 'Endapan jelaga uap oli menghalangi katup kupu-kupu menutup presisi pada posisi bukaan idle.' },
          { badge: 'Penyebab #2', title: 'Kalibrasi Sudut Throttle (Idle Air Volume Learning) Berubah', desc: 'ECU kehilangan titik referensi bukaan 0% pasca pembersihan throttle atau pelepasan aki.' },
          { badge: 'Penyebab #3', title: 'Gasket Throttle Body Bocor atau Motor ETC / Sensor TPS Aus', desc: 'Paking throttle body rembes udara luar atau gigi reduksi motor ETC/TPS mengalami keausan.' }
        ],
        repair_options: [
          { tag: 'Opsi 1 • Utama (Carbon Clean)', title: 'Bersihkan Throttle Body & Lakukan Kalibrasi Idle Relearn', desc: 'Bersihkan kerak karbon pada katup throttle dengan cleaner khusus, lalu jalankan prosedur Idle Air Volume Learning.' },
          { tag: 'Opsi 2 • Paking & Seal', title: 'Ganti Gasket Throttle Body Baru & Rapatkan Baut', desc: 'Ganti paking/seal throttle body yang sudah kempes dan kencangkan 4 baut pengikat dengan torsi 10 N·m.' },
          { tag: 'Opsi 3 • Ganti Unit ETC', title: 'Ganti Unit Electronic Throttle Body Assy / Perbaiki Soket 6-Pin', desc: 'Ganti unit Throttle Body Assy bila motor aktuator atau sensor TPS internal rusak.' }
        ],
        sensor_standards: [
          { parameter: 'Tegangan TPS Main (C37-54 saat Idle)', normal_range: '0.72 - 1.04 V', unit: 'V' },
          { parameter: 'Tegangan TPS Sub (C37-40 saat Idle)', normal_range: '1.60 - 1.91 V', unit: 'V' },
          { parameter: 'Target RPM Idle Normal (AC OFF)', normal_range: '750 ± 50 RPM', unit: 'RPM' },
          { parameter: 'Target RPM Idle (AC ON)', normal_range: '850 ± 50 RPM', unit: 'RPM' }
        ],
        wiring_pinout: [
          { pin: 'E23-42 (Pin 1)', signal: 'Throttle Motor M+ (RED)', function: 'Penggerak motor aktuator katup gas (+)' },
          { pin: 'E23-41 (Pin 2)', signal: 'Throttle Motor M- (YLW)', function: 'Penggerak motor aktuator katup gas (-)' },
          { pin: 'C37-14 (Pin 3)', signal: 'TPS +5V Reference (GRY/RED)', function: 'Suplai referensi 5.0V untuk TPS1 & TPS2' },
          { pin: 'C37-66 (Pin 4)', signal: 'VTA1 / TPS 1 Main (GRN)', function: 'Sinyal utama bukaan katup gas (~0.68V saat idle)' },
          { pin: 'C37-67 (Pin 5)', signal: 'VTA2 / TPS 2 Sub (WHT)', function: 'Sinyal redundansi pembanding (~4.32V saat idle)' },
          { pin: 'C37-57 (Pin 6)', signal: 'E2 / TPS Ground Return (GRY/GRN)', function: 'Massa referensi sensor posisi throttle ke ECM' }
        ],
        step_by_step_repair: [
          '1. Lepas selang belalai intake duct dari moncong throttle body.',
          '2. Semprotkan Electronic Throttle Body Cleaner ke kain lap microfiber halus.',
          '3. Bersihkan deposit jelaga hitam di sekeliling dinding silinder dan katup throttle (buka katup perlahan dengan dorongan jari yang lembut).',
          '4. Jika melepas seluruh unit throttle body, ganti gasket orisinil baru dan kencangkan 4 baut pengikat dengan torsi 10 N·m.'
        ],
        relearn_reset_steps: [
          "1. Lakukan prosedur 'Throttle Valve Closed Position Learning': Kunci kontak ON 10 detik, lalu OFF 10 detik.",
          "2. Lakukan 'Idle Air Volume Learning': Hidupkan mesin, matikan seluruh beban (AC/lampu), biarkan idle selama 15 menit hingga RPM stabil di 750 RPM."
        ]
      };
    }

    if (diagClean.includes('injektor') || dtcCodes.has('P0172')) {
      return {
        diagnosis_title: 'Injektor Bocor Menetes / Campuran Bahan Bakar Terlalu Kaya (Rich Mixture)',
        system_category: 'Bahan Bakar',
        group_category: 'Pembakaran',
        manual_book_section: 'Buku Pedoman Servis Bab 1G (Fuel Delivery Pipe & Injector Overhaul)',
        cause_summary: 'Salah satu nosel injektor tidak menutup sempurna (menetes) atau tekanan BBM berlebih, menyebabkan bensin terlalu pekat (Rich - P0172), busi basah hitam, dan mesin pincang.',
        cause_items: [
          { badge: 'Penyebab Utama #1', title: 'Injektor Bocor Menetes atau Pengabutan Tidak Rata', desc: 'Jarum nosel injektor terganjal kotoran sehingga bensin menetes terus ke ruang bakar dan membuat busi basah.' },
          { badge: 'Penyebab #2', title: 'Regulator Tekanan Bensin (FPR) / Katup EVAP Purge Bocor', desc: 'Tekanan fuel rail melebihi standar (> 3.8 bar) atau uap bensin kanister EVAP tersedot liar ke intake.' },
          { badge: 'Penyebab #3', title: 'Sirkuit Koil Injektor / Sensor MAP & O2 Membaca Meleset', desc: 'Soket injektor bermasalah atau sensor pembacaan udara/oksigen memberi sinyal palsu ke ECM.' }
        ],
        repair_options: [
          { tag: 'Opsi 1 • Utama (Injektor)', title: 'Ultrasonic Cleaning / Ganti Fuel Injector & Seal O-Ring', desc: 'Bersihkan dan kalibrasi injektor di alat ukur, atau ganti unit injektor yang terbukti bocor menetes.' },
          { tag: 'Opsi 2 • Regulator & EVAP', title: 'Perbaiki Fuel Pressure Regulator / Ganti Katup EVAP Purge', desc: 'Normalkan tekanan fuel rail ke 3.0–3.5 bar dan pastikan katup solenoid EVAP menutup rapat.' },
          { tag: 'Opsi 3 • Busi & BBM', title: 'Bersihkan / Ganti Busi yang Basah Karbon & Kuras Filter BBM', desc: 'Bersihkan keempat busi yang menghitam akibat campuran kaya serta ganti filter bensin.' }
        ],
        sensor_standards: [
          { parameter: 'Tekanan Fuel Rail (Mesin Idle)', normal_range: '300 - 350 kPa (3.0 - 3.5 bar)', unit: 'kPa' },
          { parameter: 'Tahanan Koil Injektor (20°C)', normal_range: '11.5 - 14.5 Ohm', unit: 'Ohm' },
          { parameter: 'Uji Kebocoran Injektor (Tekanan 3.5 bar)', normal_range: 'Maksimal 1 tetes per 2 menit', unit: 'tetes' }
        ],
        wiring_pinout: [
          { pin: 'C37-29 s/d 32', signal: 'INJ1 - INJ4 (Ground Pulse)', function: 'Sinyal penyemprotan bahan bakar dari ECM' },
          { pin: 'Relay EFI', signal: '+12V Constant Power', function: 'Daya positif injektor saat kunci kontak ON' }
        ],
        step_by_step_repair: [
          '1. Lepas sambungan pipa fuel delivery dan cabut keempat injektor.',
          '2. Uji injektor di mesin kalibrasi injector tester untuk melihat pola semprotan (spray pattern) dan uji kebocoran (leak test).',
          '3. Ganti injektor yang menetes atau lakukan ultrasonic cleaning jika hanya tersumbat ringan.',
          '4. Wajib pasang O-ring atas dan seal bawah baru dengan melumasi sedikit oli mesin bersih sebelum dipasang kembali.'
        ],
        relearn_reset_steps: [
          '1. Hapus DTC P0172 dan reset adaptive fuel trim.',
          '2. Cek apakah LTFT kembali ke rentang -5% s/d +5% pada putaran stasioner.'
        ]
      };
    }

    if (
      diagClean.includes('busi') ||
      diagClean.includes('koil') ||
      diagClean.includes('coil') ||
      diagClean.includes('misfire') ||
      diagClean.includes('pengapian') ||
      hasAnyCode(dtcCodes, ['P0300', 'P0301', 'P0302', 'P0303', 'P0304', 'P0351', 'P0352', 'P0353', 'P0354'])
    ) {
      const cylMap = {
        P0301: 'Silinder 1', P0302: 'Silinder 2', P0303: 'Silinder 3', P0304: 'Silinder 4',
        P0351: 'Silinder 1', P0352: 'Silinder 2', P0353: 'Silinder 3', P0354: 'Silinder 4'
      };
      const matchedCyls = Array.from(dtcCodes).sort().filter((c) => cylMap[c]).map((c) => cylMap[c]);
      const cylLabel = matchedCyls.length > 0 ? ` pada ${matchedCyls.join(', ')}` : ' pada Silinder Mesin (Random / Multi-Cylinder)';
      return {
        diagnosis_title: `Gagal Pengapian / Engine Misfire${cylLabel} (Sistem Ignition Coil, Busi, & Injeksi)`,
        system_category: 'Pengapian',
        group_category: 'Pembakaran',
        manual_book_section: 'Buku Pedoman Resmi Suzuki Grand Vitara JB420 Vol 1.pdf Bab 1A-111 (Hal. 169-170) & Bab 1H (Ignition System)',
        cause_summary: `Terjadi kegagalan pembakaran (misfire)${cylLabel} yang menyebabkan mesin pincang/brebet dan getaran kasar. Penyebab utama di lapangan adalah lemahnya Ignition Coil atau busi aus, disusul oleh gangguan injektor, kualitas bahan bakar, atau kebocoran vakum/kompresi.`,
        cause_items: [
          { badge: 'Penyebab Utama #1', title: 'Koil Pengapian (Ignition Coil) Bocor / Lemah & Busi Aus', desc: 'Isolator karet selongsong koil retak (api bocor ke dinding silinder), kumparan koil drop saat panas, atau celah elektroda busi sudah melebar (> 1.1 mm).' },
          { badge: 'Penyebab #2', title: 'Injektor Kotor / Tersumbat & Tekanan Pompa Bensin Turun', desc: 'Suplai pengabutan bensin ke silinder tidak mencukupi akibat nosel injektor mampet, soket injektor kendor, atau tekanan fuel pump lemah (< 3.0 bar).' },
          { badge: 'Penyebab #3', title: 'Kualitas Bahan Bakar Jelek / Tercampur Air atau Oktan Rendah', desc: 'Bahan bakar di dalam tangki terkontaminasi air/endapan kotoran atau basi sehingga gagal terbakar sempurna di ruang bakar.' },
          { badge: 'Penyebab #4', title: 'Kebocoran Vakum Intake, Katup EGR Macet, atau Kompresi Bocor', desc: 'Udara liar masuk melalui selang vakum/gasket intake, katup EGR gagal menutup rapat, atau kompresi mekanikal klep/ring piston lemah.' }
        ],
        repair_options: [
          { tag: 'Opsi 1 • Utama (Pengapian)', title: 'Ganti Ignition Coil (Koil Pengapian) & Busi Baru', desc: 'Ganti unit koil pengapian yang bocor/mati beserta busi yang sudah aus (setel celah 0.8–1.1 mm, kencangkan torsi 18–22 N·m).' },
          { tag: 'Opsi 2 • Sistem Injeksi', title: 'Bersihkan / Servis Injektor & Periksa Tekanan Fuel Pump', desc: 'Lakukan ultrasonic cleaning injektor yang mampet, rapatkan soket konektor injektor, dan pastikan tekanan fuel rail 3.0–3.5 bar.' },
          { tag: 'Opsi 3 • Bahan Bakar', title: 'Kuras Sirkuit Bahan Bakar & Ganti Bahan Bakar Jelek / Filter BBM', desc: 'Kuras tangki bensin bila kualitas BBM buruk/tercampur air, ganti filter bensin, dan isi bahan bakar beroktan sesuai spesifikasi.' },
          { tag: 'Opsi 4 • Vakum & Mekanis', title: 'Perbaiki Kebocoran Vakum / EGR, Bersihkan Filter Udara & Cek Kompresi', desc: 'Perbaiki selang vakum retak, bersihkan katup EGR & saringan udara, atau periksa kompresi silinder serta kabel soket ECM.' }
        ],
        sensor_standards: [
          { parameter: 'Celah Busi Standar (Spark Plug Gap)', normal_range: '0.80 - 1.10 mm', unit: 'mm' },
          { parameter: 'Tahanan Resistor Internal Busi', normal_range: '4.0 - 6.5 kOhm', unit: 'kOhm' },
          { parameter: 'Tegangan Suplai Konektor Koil (IG ON)', normal_range: '11.5 - 14.2 V', unit: 'V' },
          { parameter: 'Misfire Counter per Silinder (Idle/RPM Tinggi)', normal_range: '0 count', unit: 'hit' }
        ],
        wiring_pinout: [
          { pin: 'IG-FUSE (Pin 1)', signal: '+12V Ignition Feed (BLK/WHT)', function: 'Arus positif utama ke soket 4-pin Ignition Coil' },
          { pin: 'E23-35 (Pin 2)', signal: 'IGT1-4 Trigger (WHT/RED)', function: 'Pulsa pemicu pengapian 5V dari ECM ke Igniter Koil' },
          { pin: 'E23-40 (Pin 3)', signal: 'IGF Confirmation (YEL/GRN)', function: 'Sinyal konfirmasi percikan pengapian balik ke ECM' },
          { pin: 'GND-ENG (Pin 4)', signal: 'Cylinder Head Ground (BLK)', function: 'Titik massa igniter koil pada kepala silinder (< 0.3 Ohm)' }
        ],
        step_by_step_repair: [
          '1. Lepas konektor dan baut 10 mm pengikat Ignition Coil, periksa karet selongsong (boot) koil dari retakan atau jejak loncatan bunga api putih.',
          '2. Buka keempat busi menggunakan kunci busi magnet 16 mm (atau 14 mm sesuai tipe mesin), periksa warna keramik dan ukur celah elektroda menggunakan feeler gauge (standar 0.8 - 1.1 mm).',
          '3. Ganti koil pengapian yang lemah/bocor serta ganti busi yang elektrodanya aus, kencangkan busi baru dengan torsi 18 - 22 N·m.',
          '4. Bila pengapian normal namun masih misfire, periksa bunyi kerja tiap injektor, ukur tekanan fuel rail (3.0 - 3.5 bar), dan pastikan bahan bakar tidak tercampur air.'
        ],
        relearn_reset_steps: [
          '1. Hapus histori DTC Misfire (P0300 - P0304) dan reset mempelajari ulang fuel trim.',
          '2. Hidupkan mesin, pantau Misfire Counter di scanner pada saat idle dan saat digas 2.500 - 3.000 RPM (pastikan bernilai 0).'
        ]
      };
    }

    if (diagClean.includes('filter udara') || diagClean.includes('saringan udara')) {
      return {
        diagnosis_title: 'Penyumbatan Elemen Filter Udara (Air Cleaner Element Restricted)',
        system_category: 'Udara',
        group_category: 'Pembakaran',
        manual_book_section: 'Buku Pedoman Perawatan Berkala Bab 0B & Bab 1D (Air Intake System)',
        cause_summary: 'Elemen saringan udara dipenuhi debu tebal sehingga menghambat suplai oksigen ke ruang bakar, menyebabkan tarikan berat, brebet pada putaran tinggi, dan konsumsi BBM boros.',
        cause_items: [
          { badge: 'Penyebab Utama #1', title: 'Elemen Kertas Filter Udara Tersumbat Debu Tebal', desc: 'Pori-pori saringan udara tertutup kotoran sehingga aliran udara masuk ke mesin terhambat.' },
          { badge: 'Penyebab #2', title: 'Boks Rumah Filter Udara & Saluran Ducting Kotor', desc: 'Endapan pasir dan debu menumpuk di dasar boks filter udara.' }
        ],
        repair_options: [
          { tag: 'Opsi 1 • Utama (Ganti Baru)', title: 'Ganti Elemen Filter Udara Baru', desc: 'Pasang elemen saringan udara baru yang bersih dan pastikan seal karet pinggir duduk rapat.' },
          { tag: 'Opsi 2 • Servis Bersih', title: 'Semprot Bersih Filter Udara & Bersihkan Boks Filter', desc: 'Semprot dengan udara bertekanan dari sisi bersih ke sisi kotor dan lap bagian dalam boks filter.' }
        ],
        sensor_standards: [
          { parameter: 'Tekanan Manifold MAP (Idle)', normal_range: '30 - 38 kPa', unit: 'kPa' },
          { parameter: 'Debit Aliran Udara MAF (2.500 RPM)', normal_range: '7.5 - 12.0 g/s', unit: 'g/s' }
        ],
        wiring_pinout: [
          { pin: 'C37-25', signal: 'IAT / Intake Air Temp (GRN/ORN)', function: 'Sinyal sensor suhu udara masuk di rumah filter udara' }
        ],
        step_by_step_repair: [
          '1. Lepas pengait tutup boks filter udara dan keluarkan elemen filter udara.',
          '2. Bersihkan bagian dalam boks bawah filter udara dari pasir/debu menggunakan kain lembap.',
          '3. Pasang elemen filter udara baru (pastikan karet seal pinggir duduk rata agar udara kotor tidak bocor ke throttle body).'
        ],
        relearn_reset_steps: [
          '1. Reset nilai adaptasi ECM dan lakukan uji jalan akselerasi.'
        ]
      };
    }

    if (diagClean.includes('ckp') || diagClean.includes('cmp') || hasAnyCode(dtcCodes, ['P0335', 'P0340'])) {
      return {
        diagnosis_title: 'Malfungsi Sirkuit Sensor Posisi Poros Engkol / Camshaft (CKP / CMP Sensor)',
        system_category: 'Pengapian',
        group_category: 'Pembakaran',
        manual_book_section: 'Suzuki Grand Vitara JB420 Manual Bab 1A-95 & Bab 1A-101 (CKP & CMP Sensor)',
        cause_summary: 'Kumparan/Hall-IC sensor CKP/CMP melemah saat suhu mesin panas atau ujung sensor tertutup serbuk besi, menyebabkan sinyal putaran mesin hilang mendadak (P0335/P0340) dan mesin mati/sulit starter.',
        cause_items: [
          { badge: 'Penyebab Utama #1', title: 'Sensor CKP / CMP Melemah Saat Mesin Panas', desc: 'Kumparan atau IC Hall di dalam sensor putus kontak ketika suhu kerja mesin tinggi sehingga mesin mati mendadak.' },
          { badge: 'Penyebab #2', title: 'Ujung Magnet Sensor Tertutup Gram Besi / Oli', desc: 'Kotoran serbuk logam menempel pada kepala sensor sehingga mengganggu pembacaan gigi reluctor.' },
          { badge: 'Penyebab #3', title: 'Soket 3-Pin Kendor / Kabel Putus atau Timing Melar', desc: 'Konektor sensor kemasukan rembesan oli atau posisi rantai timing (timing chain) bergeser.' }
        ],
        repair_options: [
          { tag: 'Opsi 1 • Utama (Ganti Sensor)', title: 'Ganti Sensor CKP / CMP Baru (Orisinil)', desc: 'Ganti unit sensor CKP/CMP yang lemah beserta O-ring baru (kencangkan baut 10 mm torsi 10 N·m).' },
          { tag: 'Opsi 2 • Pembersihan & Soket', title: 'Bersihkan Ujung Sensor dari Gram Besi & Perbaiki Soket', desc: 'Bersihkan kepala magnet sensor, semprot soket 3-pin dengan contact cleaner, dan periksa kabel C37-46/47.' },
          { tag: 'Opsi 3 • Mekanis Timing', title: 'Periksa Ketepatan Timing Chain / Belt & Roda Gigi Reluctor', desc: 'Periksa tanda top timing mesin jika kode CKP/CMP tetap muncul setelah ganti sensor.' }
        ],
        sensor_standards: [
          { parameter: 'Tegangan Suplai Sensor (IG ON)', normal_range: '10.5 - 14.0 V (atau Vref 5.0 V)', unit: 'V' },
          { parameter: 'Sinyal Output CKP/CMP (Saat Starter)', normal_range: 'Pulsa gelombang kotak 0 - 5.0 V', unit: 'V' },
          { parameter: 'Celah Udara (Air Gap) Ujung Sensor', normal_range: '0.5 - 1.5 mm', unit: 'mm' }
        ],
        wiring_pinout: [
          { pin: 'C37-47', signal: 'CKP Sensor Signal (PNK)', function: 'Input pulsa posisi poros engkol ke ECM' },
          { pin: 'C37-46', signal: 'CMP Sensor Signal (BLU)', function: 'Input pulsa posisi poros nok ke ECM' },
          { pin: 'C37-57', signal: 'Sensor Ground (GRY/GRN)', function: 'Ground referensi sensor' }
        ],
        step_by_step_repair: [
          '1. Periksa soket 3-pin sensor CKP/CMP dari rembesan oli mesin atau kabel yang getas.',
          '2. Lepas baut pengikat sensor (10 mm), bersihkan ujung magnet sensor dari kotoran gram besi.',
          '3. Ganti sensor CKP/CMP dengan part orisinil beserta O-ring baru, kencangkan baut dengan torsi 10 N·m.'
        ],
        relearn_reset_steps: [
          '1. Hapus kode DTC P0335/P0340 via scanner.',
          '2. Hidupkan mesin hingga suhu kerja >85°C dan pastikan tidak ada gejala mati mendadak.'
        ]
      };
    }

    if (
      diagClean.includes('kipas') ||
      diagClean.includes('cooling fan') ||
      diagClean.includes('radiator fan') ||
      hasAnyCode(dtcCodes, ['P0480', 'P0481', 'P0482', 'P0483', 'P0484', 'P0485'])
    ) {
      const isFan2 = dtcCodes.has('P0481') || diagClean.includes('kipas radiator 2');
      const fanLabel = isFan2 ? 'No. 2 (High Speed / Sub Fan)' : 'No. 1 (Low Speed / Main Fan)';
      const fanPin = isFan2 ? 'E23-47' : 'E23-46';
      const fanWire = isFan2 ? 'RED' : 'RED/BLK';
      const sortedCodes = Array.from(dtcCodes).sort();
      const dtcTag = sortedCodes.length > 0 ? sortedCodes.join(', ') : 'P0480';
      return {
        diagnosis_title: `Malfungsi Sirkuit Kontrol Kipas Radiator ${fanLabel} (${dtcTag})`,
        system_category: 'Pendingin',
        group_category: 'Pendukung',
        manual_book_section: 'Buku Pedoman Resmi Suzuki Grand Vitara JB420 Vol 1.pdf Bab 1A-133 (Hal. 191) & Bab 1A-233 (Hal. 291)',
        cause_summary: `ECM mendeteksi rangkaian terbuka (putus) atau hubung singkat pada jalur kendali Relay Kipas Radiator ${fanLabel} (terminal ECM ${fanPin} kabel ${fanWire}), sehingga kipas pendingin tidak dapat diaktifkan secara normal.`,
        cause_items: [
          { badge: 'Penyebab Utama #1', title: `Relay Kipas Radiator ${fanLabel} Putus / Macet`, desc: 'Kumparan koil relay putus (normal 60–120 Ohm) atau kontak platina di dalam relay aus terbakar.' },
          { badge: 'Penyebab #2', title: 'Motor Kipas Radiator Lemah / Habis Sikat Karbon (Brush)', desc: 'Motor extra fan macet atau carbon brush habis sehingga tidak berputar saat diberi suplai +12V.' },
          { badge: 'Penyebab #3', title: `Sekering Kipas Putus / Kabel Kontrol ${fanPin} (${fanWire}) Putus`, desc: 'Sekering utama 30A/40A putus, soket kipas meleleh, atau jalur kabel dari boks relay ke ECM terputus.' }
        ],
        repair_options: [
          { tag: 'Opsi 1 • Utama (Relay)', title: `Ganti Relay Kipas Radiator ${fanLabel} Baru`, desc: 'Ganti relay cooling fan di Fuse & Relay Box ruang mesin dengan relay baru sesuai spesifikasi OEM.' },
          { tag: 'Opsi 2 • Motor Kipas', title: 'Ganti Motor Kipas Radiator (Extra Fan) / Servis Brush', desc: 'Ganti unit motor kipas radiator bila putaran lemah, macet, atau berbunyi kasar.' },
          { tag: 'Opsi 3 • Sekering & Kabel', title: `Ganti Sekering Kipas & Perbaiki Soket / Kabel ${fanPin}`, desc: `Ganti sekering yang putus, perbaiki soket kipas yang kendor, dan sambung jalur kabel ${fanWire} ke ECM.` }
        ],
        sensor_standards: [
          { parameter: `Tegangan Terminal ${fanPin} (Kipas OFF / Standby IG ON)`, normal_range: '10.0 - 14.0 V', unit: 'V' },
          { parameter: `Tegangan Terminal ${fanPin} (Kipas ON Aktif)`, normal_range: '0.0 - 1.5 V (Ground Switched ECM)', unit: 'V' },
          { parameter: 'Tahanan Koil Relay Kipas Radiator (pada 20°C)', normal_range: '60 - 120 Ohm', unit: 'Ohm' },
          { parameter: 'Suhu ECT Aktivasi Kipas Low-Speed (Bab 1A-233)', normal_range: 'ON ≥ 97.5°C / OFF ≤ 93.0°C', unit: '°C' }
        ],
        wiring_pinout: [
          { pin: 'E23-46 (Pin 1)', signal: 'Cooling Fan Relay No.1 (RED/BLK)', function: 'Output kendali massa ECM ke koil Relay Kipas No.1 (10-14V OFF, <1V ON)' },
          { pin: 'E23-47 (Pin 2)', signal: 'Cooling Fan Relay No.2 (RED)', function: 'Output kendali massa ECM ke koil Relay Kipas No.2 (High Speed / A/C)' },
          { pin: 'C37-24 (Pin 3)', signal: 'ECT Sensor Signal (PPL/YEL)', function: 'Sinyal suhu air radiator ke ECM pemicu kipas (0.40-0.53V @ 100°C)' },
          { pin: 'C37-57 (Pin 4)', signal: 'Sensor Ground (GRY/GRN)', function: 'Massa referensi sensor suhu pendingin ke ECM (< 0.3V)' }
        ],
        step_by_step_repair: [
          '1. Buka tutup Fuse & Relay Box di ruang mesin, periksa sekering utama Cooling Fan (30A/40A) dan sekering IG koil relay dari putus atau kaki gosong.',
          '2. Cabut Relay Kipas Radiator No. 1, ukur tahanan kumparan koil relay (terminal 85-86: normal 60 - 120 Ohm), lalu uji beri tegangan 12V untuk memastikan kontak 30-87 terhubung (< 0.5 Ohm).',
          `3. Kunci kontak ON (mesin mati, AC OFF): ukur tegangan pada jalur kabel ${fanWire} (terminal ECM ${fanPin}) terhadap massa bodi — harus terbaca 10 - 14 V. Jika 0 V, jalur koil relay atau kabel ${fanWire} putus.`,
          '4. Uji langsung motor kipas radiator dengan memberi suplai 12V & massa sesaat pada konektor 2-pin motor kipas: pastikan kipas berputar kencang tanpa bunyi kasar (sikat karbon motor tidak habis).'
        ],
        relearn_reset_steps: [
          `1. Sambungkan scan tool ke DLC (kunci kontak OFF -> ON), hapus memori DTC ${dtcTag}.`,
          "2. Gunakan fitur 'Active Test -> Cooling Fan Relay 1 ON' pada scanner, atau hidupkan mesin hingga suhu ECT mencapai ≥ 97.5°C (atau nyalakan AC) dan pastikan kipas radiator berputar otomatis tanpa memunculkan DTC kembali."
        ]
      };
    }

    return {
      diagnosis_title: `Panduan Diagnosa & Perbaikan: ${diagnosis}`,
      system_category: 'Umum',
      group_category: 'Pembakaran',
      manual_book_section: 'Buku Pedoman Perbaikan Workshop Manual - Prosedur Servis Standar',
      cause_summary: `Penyebab teridentifikasi pada komponen/sistem: ${diagnosis}. Periksa komponen utama, soket kelistrikan, dan jalur pendukung terkait.`,
      cause_items: [
        { badge: 'Penyebab Utama #1', title: `Kerusakan / Keausan Komponen Utama (${diagnosis})`, desc: 'Komponen sensor atau aktuator terkait telah melampaui batas usia pakai atau mengalami malfungsi internal.' },
        { badge: 'Penyebab #2', title: 'Soket Konektor Kendor / Korosi atau Kabel Putus', desc: 'Tahanan kontak tinggi pada pin konektor atau kabel bodi (wire harness) terkelupas/hubung singkat.' },
        { badge: 'Penyebab #3', title: 'Suplai Tegangan / Titik Massa Ground Tidak Stabil', desc: 'Tegangan suplai dari sekering/relay drop atau baut titik massa bodi/mesin berkarat.' }
      ],
      repair_options: [
        { tag: 'Opsi 1 • Utama (Komponen)', title: `Ganti / Servis Komponen Utama (${diagnosis})`, desc: 'Lakukan penggantian atau kalibrasi ulang komponen utama yang teridentifikasi bermasalah.' },
        { tag: 'Opsi 2 • Soket & Kabel', title: 'Bersihkan Soket Konektor & Perbaiki Jalur Kabel Harness', desc: 'Semprot pin konektor dengan contact cleaner, kencangkan pin longgar, dan perbaiki kabel yang putus.' },
        { tag: 'Opsi 3 • Suplai & Reset', title: 'Periksa Sekering, Massa Ground & Reset Adaptasi ECU', desc: 'Pastikan suplai daya 12V/5V dan massa normal, lalu hapus memori DTC dengan scanner.' }
      ],
      sensor_standards: [
        { parameter: 'Tegangan Pengisian Aki', normal_range: '13.8 - 14.4 V', unit: 'V' },
        { parameter: 'Tekanan Vakum Idle', normal_range: '60 - 75 kPa vakum', unit: 'kPa' }
      ],
      wiring_pinout: [
        { pin: 'Terminal ECM', signal: 'Sinyal Kontrol', function: 'Sinyal kendali aktuator dan sensor' }
      ],
      step_by_step_repair: [
        '1. Lakukan inspeksi visual menyeluruh pada sambungan mekanis, selang karet, dan kabel konektor.',
        '2. Bersihkan komponen dari debu/karbon menggunakan cairan pembersih yang sesuai.',
        '3. Lakukan pengujian komponen menggunakan multitester atau scanner live data.',
        '4. Ganti part yang telah melampaui batas keausan servis.'
      ],
      relearn_reset_steps: [
        '1. Reset DTC dan lakukan kalibrasi idle relearn sesuai buku panduan servis.'
      ]
    };
  }

  function classifyDtcWorkshopSystem(code, sysLabel, desc) {
    const c = String(code || '').toUpperCase();
    const txt = `${sysLabel || ''} ${desc || ''}`.toLowerCase();
    const coolingSet = new Set(['P0480', 'P0481', 'P0482', 'P0483', 'P0484', 'P0485', 'P0115', 'P0116', 'P0117', 'P0118', 'P0119', 'P0125', 'P0128', 'B1561']);
    if (coolingSet.has(c) || ['kipas radiator', 'cooling fan', 'coolant', 'thermostat'].some((k) => txt.includes(k))) {
      return ['Pendingin', 'Pendukung'];
    }
    if (/^P03[0-5][0-9]$/.test(c) || ['misfire', 'pengapian', 'knock', 'crankshaft', 'camshaft', 'ckp', 'cmp', 'ignition coil'].some((k) => txt.includes(k))) {
      return ['Pengapian', 'Pembakaran'];
    }
    const fuelSet = new Set(['P0087', 'P0171', 'P0172', 'P0174', 'P0175', 'P0230', 'P0462', 'P0463', 'P2195', 'P2196']);
    if (fuelSet.has(c) || /^P0(03[0-8]|13[0-9]|14[01]|20[0-8])$/.test(c) || ['bahan bakar', 'fuel', 'ho2s', 'o2 sensor', 'injektor', 'injector'].some((k) => txt.includes(k))) {
      return ['Bahan Bakar', 'Pembakaran'];
    }
    if (/^P(010[0-9]|011[0-4]|012[0-4]|022[0-4]|050[5-7]|0660|210[0-9]|211[0-9]|212[0-9]|213[0-9]|222[7-9])$/.test(c) || ['mass air flow', 'manifold absolute', 'intake air', 'throttle', 'pedal position', 'barometric'].some((k) => txt.includes(k))) {
      return ['Udara', 'Pembakaran'];
    }
    if (/^P04([0-5][0-9])$/.test(c) || ['catalyst', 'evaporative', 'purge', 'daur ulang gas buang', 'egr'].some((k) => txt.includes(k))) {
      return ['Emisi', 'Pendukung'];
    }
    if (/^P(07|08|09|17|18|27)[0-9]{2}$/.test(c) || ['transmission', 'tcm', 'torque converter', 'shift solenoid'].some((k) => txt.includes(k))) {
      return ['Mekanis', 'Pembakaran'];
    }
    if (['oil', 'pelumas', 'oli'].some((k) => txt.includes(k))) {
      return ['Pelumasan', 'Pendukung'];
    }
    return ['Kelistrikan', 'Pendukung'];
  }

  function cleanManualPhrase(text) {
    if (!text) return '';
    let s = String(text).replace(/\|\s*Pinout\s*&\s*Warna\s*Kabel:.*$/i, '').trim();
    s = s.replace(/^Solusi\s*Manual\s*:\s*/i, '').trim();
    s = s.replace(/\bG\s+anti\b/g, 'Ganti');
    s = s.replace(/\bSistim\b/g, 'Sistem');
    s = s.replace(/\bsistim\b/g, 'sistem');
    s = s.replace(/\bkoslet\b/gi, 'hubung singkat (korsleting)');
    s = s.replace(/\bbattery\b/gi, 'Baterai (Aki)');
    s = s.replace(/\bcoupler\b/gi, 'soket konektor (coupler)');
    s = s.replace(/\bwire\s+harness\b/gi, 'kabel bodi (wire harness)');
    s = s.replace(/\s*Lanjut\s+ke\s+Langkah\s+\d+\.?\s*/gi, ' ');
    s = s.replace(/\s*Periksa\s+intermittent\s+lihat.*$/i, '');
    s = s.replace(/\s+/g, ' ').replace(/^[ .;,\-|]+|[ .;,\-|]+$/g, '');
    return s;
  }

  function selectPinoutsForManualDtc(codes, combinedDesc, wiringRows) {
    const codeSet = new Set(codes.map((c) => c.toUpperCase()));
    const txt = String(combinedDesc || '').toLowerCase();
    const pinMap = {};
    for (const wd of wiringRows) {
      let rawPj = wd.pinout_json || {};
      if (typeof rawPj === 'string') {
        try { rawPj = JSON.parse(rawPj); } catch (_) { rawPj = {}; }
      }
      if (rawPj && typeof rawPj === 'object') {
        for (const [pinCode, detail] of Object.entries(rawPj)) {
          if (detail && typeof detail === 'object') {
            pinMap[pinCode] = [String(detail.wire_color || '-'), String(detail.function || '-')];
          }
        }
      }
    }

    let wantedPins = [];
    if (hasAnyCode(codeSet, ['P0480', 'P0481', 'P0482']) || txt.includes('kipas') || txt.includes('cooling fan')) {
      wantedPins = ['E23-46', 'E23-47', 'C37-24', 'C37-57'];
    } else if (hasAnyCode(codeSet, ['P0115', 'P0116', 'P0117', 'P0118', 'P0125', 'P0128', 'B1561']) || txt.includes('coolant')) {
      wantedPins = ['C37-24', 'C37-57', 'E23-46'];
    } else if (hasAnyCode(codeSet, ['P0100', 'P0101', 'P0102', 'P0103', 'P0111', 'P0112', 'P0113']) || txt.includes('mass air flow') || txt.includes('intake air temp')) {
      wantedPins = ['E23-01', 'C37-26', 'C37-27', 'C37-25', 'C37-57'];
    } else if (hasAnyCode(codeSet, ['P0106', 'P0107', 'P0108', 'P2227', 'P2228', 'P2229']) || txt.includes('manifold absolute') || txt.includes('barometric')) {
      wantedPins = ['C37-14', 'C37-55', 'C37-57'];
    } else if (hasAnyCode(codeSet, ['P0122', 'P0123', 'P0222', 'P0223', 'P2101', 'P2102', 'P2103', 'P2111', 'P2119', 'P2135', 'P0507']) || txt.includes('throttle')) {
      wantedPins = ['C37-53', 'C37-54', 'C37-40', 'C37-41', 'C37-44', 'C37-45'];
    } else if (hasAnyCode(codeSet, ['P2122', 'P2123', 'P2127', 'P2128', 'P2138']) || txt.includes('pedal position')) {
      wantedPins = ['E23-56', 'E23-55', 'E23-53', 'E23-52', 'C37-57'];
    } else if (hasAnyCode(codeSet, ['P0030', 'P0031', 'P0032', 'P0037', 'P0038', 'P0131', 'P0132', 'P0133', 'P0134', 'P0137', 'P0138', 'P0140', 'P2195', 'P2196']) || txt.includes('ho2s') || txt.includes('o2 sensor')) {
      wantedPins = ['C37-38', 'C37-37', 'C37-32', 'C37-11', 'C37-47', 'C37-57'];
    } else if (hasAnyCode(codeSet, ['P0335', 'P0340', 'B1556']) || txt.includes('crankshaft') || txt.includes('camshaft')) {
      wantedPins = ['C37-51', 'C37-36', 'C37-52', 'C37-57'];
    } else if (hasAnyCode(codeSet, ['P0327', 'P0328']) || txt.includes('knock')) {
      wantedPins = ['C37-56', 'C37-57'];
    } else if (hasAnyCode(codeSet, ['P0087', 'P0230', 'P0462', 'P0463']) || txt.includes('fuel')) {
      wantedPins = ['E23-15', 'E23-01', 'E23-60', 'C37-15'];
    } else {
      wantedPins = ['E23-01', 'E23-29', 'E23-60', 'C37-57', 'C37-15'];
    }

    const out = [];
    wantedPins.forEach((pCode, i) => {
      if (pinMap[pCode]) {
        const [wColor, wFunc] = pinMap[pCode];
        out.push({
          pin: `${pCode} (Pin ${i + 1})`,
          signal: `${wColor} — ${wFunc.slice(0, 42)}`,
          function: wFunc
        });
      }
    });
    return out;
  }

  function buildAdviceFromManualDtcEntries(dtcEntries, wiringRows, sensorRows, dtcCatalogMap) {
    const codes = dtcEntries.map((d) => d.code);
    const primary = dtcEntries[0];
    const dtcStr = codes.join(', ');
    const combinedDesc = dtcEntries.map((d) => `${d.code} ${d.system} ${d.description_id} ${d.possible_causes}`).join(' ');
    const catEntry = dtcCatalogMap[String(primary.code || '').toUpperCase()] || null;

    const specialist = getRepairManualGuidance(primary.description_id, dtcStr);
    if (specialist.system_category !== 'Umum') {
      if (primary.system && primary.system.includes('Vol ')) {
        const docTag = catEntry && catEntry.suzuki_doc_id ? ` [ID: ${catEntry.suzuki_doc_id}]` : '';
        specialist.manual_book_section = `Buku Pedoman Resmi: ${primary.system}${docTag} — Kode DTC ${dtcStr}`;
      }
      if (dtcEntries.length > 1) {
        const multiDesc = dtcEntries.map((d) => `${d.code} (${d.description_id})`).join('; ');
        specialist.diagnosis_title = `Terdeteksi Multi-DTC Manual Book: ${multiDesc}`;
      }
      return specialist;
    }

    const [sysCat, grpCat] = classifyDtcWorkshopSystem(primary.code, primary.system, primary.description_id);

    let pinouts = [];
    if (catEntry && Array.isArray(catEntry.wiring_pinout) && catEntry.wiring_pinout.length > 0) {
      pinouts = catEntry.wiring_pinout.slice(0, 6).map((p) => ({
        pin: String(p.pin || '-'),
        signal: String(p.signal || '-'),
        function: String(p.function || '-')
      }));
    }
    if (pinouts.length === 0) {
      pinouts = selectPinoutsForManualDtc(codes, combinedDesc, wiringRows);
    }
    if (pinouts.length === 0) {
      pinouts = [
        { pin: 'E23-01 (Pin 1)', signal: 'BLU/BLK — Main Power Supply', function: 'Suplai tegangan utama 10-14V IG ON dari Main Relay' },
        { pin: 'C37-57 (Pin 2)', signal: 'GRY/GRN — Main Sensor Ground', function: 'Jalur massa referensi sensor/aktuator (< 0.3V)' }
      ];
    }

    let standards = [];
    if (catEntry && Array.isArray(catEntry.standard_specs) && catEntry.standard_specs.length > 0) {
      standards = catEntry.standard_specs.slice(0, 4).map((sp) => ({
        parameter: String(sp.parameter || 'Pemeriksaan Multimeter'),
        normal_range: String(sp.normal_range || '-'),
        unit: String(sp.unit || 'V')
      }));
    }
    if (standards.length < 2) {
      standards.push(
        { parameter: 'Tegangan Suplai Modul Kontrol (IG ON)', normal_range: '10.0 - 14.0 V', unit: 'V' },
        { parameter: 'Tahanan Kontinuitas Kabel Harness Ujung-ke-Ujung', normal_range: '< 2.0 Ohm', unit: 'Ohm' }
      );
    }
    standards = standards.slice(0, 4);

    let authenticSteps = [];
    if (catEntry && Array.isArray(catEntry.repair_steps) && catEntry.repair_steps.length > 0) {
      authenticSteps = catEntry.repair_steps.map((s) => String(s).trim()).filter(Boolean);
    } else if (primary.recommended_fix) {
      authenticSteps = String(primary.recommended_fix).split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
    }
    if (authenticSteps.length === 0) {
      const pinSummary = pinouts.slice(0, 4).map((p) => p.pin.split(' ')[0]).join(', ');
      authenticSteps = [
        `1. Verifikasi kode ${dtcStr} menggunakan scan tool OBD-II dan catat data Freeze Frame (${primary.system}).`,
        `2. Matikan kunci kontak, periksa konektor komponen terkait serta jalur terminal modul (${pinSummary}) dari pin longgar, korosi, atau kabel koslet.`,
        '3. Ukur tegangan suplai (+12V / +5V), tahanan kabel harness (< 2 Ohm), dan ground bodi/mesin menggunakan multimeter sesuai spesifikasi standar.',
        `4. Perbaiki wiring harness yang putus/koslet atau ganti komponen pada sirkuit '${primary.description_id}' sesuai petunjuk Buku Manual.`
      ];
    }

    const rawCausesStr = String(
      (catEntry && catEntry.common_causes) ? catEntry.common_causes : (primary.possible_causes || '')
    ).replace(/\|\s*Pinout\s*&\s*Warna\s*Kabel:.*$/i, '').trim();
    const rawParts = rawCausesStr.split(/[;|]+/).map(cleanManualPhrase).filter((p) => p.length >= 3);
    const causeItems = rawParts.slice(0, 4).map((p, idx) => {
      const titleClean = p.charAt(0).toUpperCase() + p.slice(1);
      return {
        badge: idx === 0 ? 'Penyebab Utama #1' : `Penyebab #${idx + 1}`,
        title: titleClean,
        desc: `Terdeteksi gangguan komponen atau rangkaian kelistrikan pada bagian ${titleClean.toLowerCase()} sesuai buku manual.`
      };
    });
    if (causeItems.length === 0) {
      causeItems.push(
        { badge: 'Penyebab Utama #1', title: `Kerusakan Komponen / Sensor (${primary.description_id})`, desc: `Komponen utama pada sirkuit ${primary.description_id} mengalami keausan atau nilai di luar spesifikasi standar.` },
        { badge: 'Penyebab #2', title: 'Konektor Soket Kendor / Kabel Harness Putus', desc: 'Terjadi resistansi kontak tinggi pada pin soket atau kabel bodi terkelupas.' }
      );
    }

    const pinStr = pinouts.slice(0, 3).map((p) => p.pin.split(' ')[0]).join(', ') || 'terminal modul';
    const repairOptions = [
      {
        tag: 'Opsi 1 • Utama (Komponen)',
        title: `Ganti / Servis Komponen Utama (${primary.description_id})`,
        desc: `Periksa dan ganti unit sensor/aktuator pada sirkuit '${primary.description_id}' bila hasil ukur multimeter di luar standar.`
      },
      {
        tag: 'Opsi 2 • Soket & Kabel',
        title: `Perbaiki Soket Konektor & Jalur Kabel (${pinStr})`,
        desc: `Bersihkan pin konektor dengan contact cleaner, rapatkan pin kendor, dan perbaiki kabel putus menuju ${pinStr}.`
      },
      {
        tag: 'Opsi 3 • Suplai & Reset',
        title: `Periksa Sekering / Massa Ground & Reset Memori DTC ${primary.code}`,
        desc: 'Pastikan suplai tegangan kerja (12V/5V) dan titik ground normal (< 0.3V), lalu hapus DTC via scan tool.'
      }
    ];

    const titleDesc = dtcEntries.length === 1
      ? primary.description_id
      : dtcEntries.map((d) => `${d.code}: ${d.description_id}`).join('; ');
    const docTag = catEntry && catEntry.suzuki_doc_id ? ` [ID: ${catEntry.suzuki_doc_id}]` : '';

    return {
      diagnosis_title: `DTC ${dtcStr}: ${titleDesc}`,
      system_category: sysCat,
      group_category: grpCat,
      manual_book_section: `Buku Pedoman Resmi: ${primary.system}${docTag} (Kode ${dtcStr})`,
      cause_summary: `Kode ${primary.code} (${primary.description_id}) menunjukkan adanya gangguan pada ${causeItems[0].title.toLowerCase()}, baik akibat kerusakan komponen utama maupun masalah pada soket dan jalur kabelnya.`,
      cause_items: causeItems,
      repair_options: repairOptions,
      sensor_standards: standards,
      wiring_pinout: pinouts,
      step_by_step_repair: authenticSteps,
      relearn_reset_steps: [
        `1. Hapus memori kode DTC ${dtcStr} melalui scan tool dengan kunci kontak posisi ON (mesin mati).`,
        `2. Jalankan mesin / lakukan uji jalan sesuai 'Prosedur Menentukan DTC' pada ${primary.system} dan pastikan kode tidak muncul kembali.`
      ]
    };
  }

  async function searchWeightedCases(req) {
    const store = await global.AgosDataStore.ensureLoaded();
    const cases = await global.AgosDataStore.getAllCases();
    const wiringRows = store.wiringDiagrams;
    const sensorRows = store.sensorSpecs;
    const dtcCodeMap = store.dtcCodeMap;
    const dtcCatalogMap = store.dtcCatalogMap;

    const reqCodes = extractAllRequestDtcs(req);
    const manualDtcEntries = [];

    if (reqCodes.length > 0) {
      for (const code of reqCodes) {
        if (dtcCodeMap[code]) {
          const r = dtcCodeMap[code];
          manualDtcEntries.push({
            code: r.code,
            system: r.system,
            description_id: r.description_id,
            possible_causes: r.possible_causes,
            recommended_fix: r.recommended_fix || '',
            severity_level: r.severity_level
          });
        } else if (STANDARD_OBD_FALLBACK[code]) {
          const fb = STANDARD_OBD_FALLBACK[code];
          manualDtcEntries.push({
            code,
            system: fb.system,
            description_id: fb.description_id,
            possible_causes: fb.possible_causes,
            recommended_fix: '',
            severity_level: fb.severity_level
          });
        }
      }
    } else {
      const rawTextLow = `${req.complaint || ''} ${req.symptom || ''}`.toLowerCase();
      const keywordDtcHints = [
        [['kipas radiator', 'cooling fan', 'extra fan', 'kipas mati'], 'P0480'],
        [['wheel speed', 'sensor abs', 'lampu abs'], 'C1021'],
        [['pompa abs', 'abs pump'], 'C1061'],
        [['air bag', 'airbag', 'lampu srs', 'pretensioner'], 'B1031'],
        [['shift solenoid', 'transmisi matic', 'gigi matic'], 'P0751'],
        [['sensor suhu kabin', 'inside air', 'ac otomatis', 'blower ac'], 'B1502'],
        [['pedal gas', 'app sensor'], 'P2122'],
        [['generator', 'alternator', 'aki tekor', 'pengisian'], 'P0620'],
        [['starter relay', 'tidak bisa starter'], 'P0616'],
        [['steering lock', 'keyless start'], 'KLS-11'],
        [['immobilizer', 'transponder'], 'P1614']
      ];
      for (const [phrases, targetDtc] of keywordDtcHints) {
        if (phrases.some((p) => rawTextLow.includes(p))) {
          const rowKw = dtcCodeMap[targetDtc];
          if (rowKw) {
            manualDtcEntries.push({
              code: rowKw.code,
              system: rowKw.system,
              description_id: rowKw.description_id,
              possible_causes: rowKw.possible_causes,
              recommended_fix: rowKw.recommended_fix || '',
              severity_level: rowKw.severity_level
            });
          }
          break;
        }
      }
    }

    const rawFilter = req.system_filter ? String(req.system_filter).trim() : '';
    const filteredSystem = rawFilter && !['', 'semua', 'all'].includes(rawFilter.toLowerCase()) ? rawFilter : null;

    const hasAnyLiveData = [req.stft, req.ltft, req.rpm, req.o2, req.map_kpa, req.maf_gps, req.ect_c].some(
      (v) => v !== null && v !== undefined
    );

    const systemStats = {};
    SYSTEM_DEFINITIONS.forEach((s) => { systemStats[s.name] = []; });

    let exactHistoricalDtcBest = 0.0;
    const reqCodesSet = new Set(reqCodes);
    const scoredItems = [];

    for (const c of cases) {
      const tScore = calculateTextSimilarity(req, c);
      const lScore = calculateLiveSimilarity(req, c);
      let totScore = (hasAnyLiveData && lScore !== null)
        ? (0.85 * tScore + 0.15 * lScore)
        : tScore;
      totScore = Math.round(Math.min(Math.max(totScore, 0.0), 1.0) * 10000) / 10000;
      const catLabel = determineCategory(totScore);

      const caseCodesSet = new Set(splitDtcCodes(c.dtc));
      if (reqCodesSet.size > 0 && setIntersectionCount(reqCodesSet, caseCodesSet) > 0) {
        if (totScore > exactHistoricalDtcBest) exactHistoricalDtcBest = totScore;
      }

      const cSys = c.system_category || 'Udara';
      if (systemStats[cSys]) {
        systemStats[cSys].push([totScore, c.final_diagnosis, c.case_code]);
      }

      if (filteredSystem && cSys.toLowerCase() !== filteredSystem.toLowerCase()) {
        continue;
      }

      const advice = getRepairManualGuidance(c.final_diagnosis, c.dtc);
      scoredItems.push({
        rank: 1,
        case_code: c.case_code,
        brand: c.brand,
        model: c.model,
        year: c.year,
        engine_capacity: c.engine_capacity,
        complaint: c.complaint,
        symptom: c.symptom,
        dtc: c.dtc || 'Tidak ada',
        final_diagnosis: c.final_diagnosis,
        repair_action: c.repair_action,
        system_category: c.system_category,
        group_category: c.group_category,
        text_score: Math.round(tScore * 1000) / 10,
        live_score: lScore !== null ? Math.round(lScore * 1000) / 10 : null,
        total_score: Math.round(totScore * 1000) / 10,
        category_label: catLabel,
        inspection_findings: c.inspection_findings,
        manual_advice: advice
      });
    }

    if (manualDtcEntries.length > 0) {
      const manualAdvice = buildAdviceFromManualDtcEntries(manualDtcEntries, wiringRows, sensorRows, dtcCatalogMap);
      const primaryDtc = manualDtcEntries[0];
      const allCodesStr = manualDtcEntries.map((d) => d.code).join(', ');
      let [mSys, mGrp] = classifyDtcWorkshopSystem(primaryDtc.code, primaryDtc.system, primaryDtc.description_id);
      if (systemStats[manualAdvice.system_category]) {
        mSys = manualAdvice.system_category;
        mGrp = manualAdvice.group_category;
      }

      const manualScore = reqCodes.length > 0
        ? (exactHistoricalDtcBest < 0.88 ? 0.94 : 0.88)
        : 0.84;

      const manualCaseCode = `MANUAL-${primaryDtc.code}`;
      const manualDiagLabel = manualDtcEntries.length === 1
        ? `${primaryDtc.description_id} (DTC ${allCodesStr})`
        : 'Multi-DTC Manual Resmi: ' + manualDtcEntries.map((d) => `${d.code} ${d.description_id}`).join('; ');

      let manualRepairShort = '';
      if (manualAdvice.repair_options && manualAdvice.repair_options.length > 0) {
        manualRepairShort = manualAdvice.repair_options.slice(0, 2).map((o) => o.title).join(' / ');
      } else if (manualAdvice.step_by_step_repair && manualAdvice.step_by_step_repair.length > 0) {
        manualRepairShort = manualAdvice.step_by_step_repair[0].replace(/^[0-9.\s]+/, '');
      } else {
        manualRepairShort = `Periksa sirkuit & konektor sesuai ${primaryDtc.system}`;
      }

      if (systemStats[mSys]) {
        systemStats[mSys].push([manualScore, manualDiagLabel, manualCaseCode]);
      }

      if (!filteredSystem || filteredSystem.toLowerCase() === mSys.toLowerCase() || reqCodes.length > 0) {
        scoredItems.push({
          rank: 1,
          case_code: manualCaseCode,
          brand: String(req.brand || '').trim() || 'Suzuki / OBD-II',
          model: String(req.model || '').trim() || 'Manual Book JB420',
          year: null,
          engine_capacity: null,
          complaint: String(req.complaint || '').trim() || `Indikator MIL / DTC ${allCodesStr}`,
          symptom: String(req.symptom || '').trim() || primaryDtc.description_id,
          dtc: allCodesStr,
          final_diagnosis: manualDiagLabel,
          repair_action: manualRepairShort,
          system_category: mSys,
          group_category: mGrp,
          text_score: Math.round(manualScore * 1000) / 10,
          live_score: null,
          total_score: Math.round(manualScore * 1000) / 10,
          category_label: determineCategory(manualScore),
          inspection_findings: primaryDtc.possible_causes,
          manual_advice: manualAdvice
        });
      }
    }

    scoredItems.sort((a, b) => b.total_score - a.total_score);
    scoredItems.forEach((itm, idx) => { itm.rank = idx + 1; });

    const summaries = SYSTEM_DEFINITIONS.map((sDef) => {
      const sName = sDef.name;
      const cList = systemStats[sName] || [];
      if (cList.length > 0) {
        cList.sort((a, b) => b[0] - a[0]);
        const [topS, topDiag, topCode] = cList[0];
        return {
          system_name: sName,
          group_name: sDef.group,
          parameters_checked: sDef.params,
          cases_count: cList.length,
          top_score: Math.round(topS * 1000) / 10,
          category_label: determineCategory(topS),
          top_diagnosis: topDiag,
          top_case_code: topCode
        };
      }
      return {
        system_name: sName,
        group_name: sDef.group,
        parameters_checked: sDef.params,
        cases_count: 0,
        top_score: 0.0,
        category_label: 'Belum ada kasus di database',
        top_diagnosis: '-',
        top_case_code: '-'
      };
    });

    const topMatch = scoredItems[0] || null;
    const topHeadline = topMatch
      ? `${topMatch.final_diagnosis} — ${topMatch.total_score}% (${topMatch.category_label}), referensi ${topMatch.case_code}, sistem ${topMatch.system_category}`
      : 'Tidak ada kasus yang cocok';
    const directAdvice = (topMatch && topMatch.manual_advice)
      ? topMatch.manual_advice
      : getRepairManualGuidance('Umum', null);

    return {
      top_headline: topHeadline,
      top_case_code: topMatch ? topMatch.case_code : '-',
      top_diagnosis: topMatch ? topMatch.final_diagnosis : '-',
      top_score_percent: topMatch ? topMatch.total_score : 0.0,
      top_category_label: topMatch ? topMatch.category_label : 'Kurang mirip',
      system_filter_applied: filteredSystem,
      ranked_matches: scoredItems.slice(0, 20),
      system_summaries: summaries,
      direct_manual_advice: directAdvice
    };
  }

  global.AgosDiagnosticEngine = {
    preprocessSymptomTokens,
    splitDtcCodes,
    extractAllRequestDtcs,
    calculateTextSimilarity,
    calculateLiveSimilarity,
    getRepairManualGuidance,
    searchWeightedCases
  };
})(typeof window !== 'undefined' ? window : globalThis);
