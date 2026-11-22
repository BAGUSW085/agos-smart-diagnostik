/**
 * AGOS Smart Diagnostik — Offline Multi-Model, Engine Catalog (Asia/Eropa/China),
 * Modern DTC (Diesel/Turbo/VVT/Hybrid/EV), Adaptive Live Data & Admin PIN Module
 * ==============================================================================
 * Menyamakan 100% logika backend FastAPI ke dalam APK Android Offline.
 */
(function (global) {
  'use strict';

  const KEY_CUSTOM_PACKS = 'agos_offline_custom_manual_packs_v1';
  const KEY_ADMIN_PIN = 'agos_offline_workshop_pin_v1';
  const DEFAULT_PIN = '1234';

  function normCode(raw) {
    return String(raw || '').trim().toLowerCase().replace(/[^a-z0-9]/g, '');
  }

  function getGenerations() {
    return (global.AGOS_OFFLINE_DATA && global.AGOS_OFFLINE_DATA.vehicle_generations) || [];
  }

  function getEngineDirectory() {
    return (global.AGOS_OFFLINE_DATA && global.AGOS_OFFLINE_DATA.engine_directory) || [];
  }

  function getModernDtcCatalog() {
    return (global.AGOS_OFFLINE_DATA && global.AGOS_OFFLINE_DATA.modern_dtc_catalog) || {};
  }

  function loadCustomPacks() {
    try {
      const raw = global.localStorage.getItem(KEY_CUSTOM_PACKS);
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch (_) {
      return [];
    }
  }

  function saveCustomPack(packData) {
    const packs = loadCustomPacks();
    const copy = { ...packData };
    if (!copy.pack_id) {
      const sb = String(copy.brand || 'custom').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
      const sm = String(copy.model || 'model').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
      copy.pack_id = `${sb}_${sm}_${copy.year_start || 2015}_${copy.year_end || 2026}`;
    }
    const updated = packs.filter((p) => p.pack_id !== copy.pack_id);
    updated.push(copy);
    try {
      global.localStorage.setItem(KEY_CUSTOM_PACKS, JSON.stringify(updated));
    } catch (_) {}
    return copy;
  }

  function deleteCustomPack(packId) {
    if (packId === 'suzuki_jb420_builtin') return false;
    const packs = loadCustomPacks();
    const filtered = packs.filter((p) => p.pack_id !== packId);
    if (filtered.length === packs.length) return false;
    try {
      global.localStorage.setItem(KEY_CUSTOM_PACKS, JSON.stringify(filtered));
    } catch (_) {}
    return true;
  }

  function listAllPackSummaries() {
    const builtin = {
      pack_id: 'suzuki_jb420_builtin',
      brand: 'Suzuki',
      model: 'Grand Vitara',
      generation_id: 'suzuki_jb420',
      generation_label: 'Grand Vitara Gen 2 (JB420)',
      year_start: 2006,
      year_end: 2015,
      engine_codes: ['J20A'],
      title: 'Buku Pedoman Resmi Suzuki Grand Vitara JB420 (Vol 1 & Vol 2)',
      dtc_count: 207,
      pinout_count: 251,
      sensor_spec_count: 9,
      is_builtin: true
    };
    return [builtin].concat(
      loadCustomPacks().map((p) => ({
        pack_id: String(p.pack_id || ''),
        brand: String(p.brand || ''),
        model: String(p.model || ''),
        generation_id: p.generation_id || null,
        generation_label: String(p.generation_label || p.model || ''),
        year_start: Number(p.year_start || 2010),
        year_end: Number(p.year_end || 2026),
        engine_codes: Array.isArray(p.engine_codes) ? p.engine_codes : [],
        title: String(p.title || 'Manual Tambahan Bengkel'),
        dtc_count: Array.isArray(p.dtc_catalog) ? p.dtc_catalog.length : 0,
        pinout_count: Array.isArray(p.wiring_pinouts) ? p.wiring_pinouts.length : 0,
        sensor_spec_count: Array.isArray(p.sensor_specs) ? p.sensor_specs.length : 0,
        is_builtin: false
      }))
    );
  }

  // --- ADMIN PIN GUARD (OFFLINE LOCALSTORAGE) ---
  function getStoredPin() {
    try {
      return global.localStorage.getItem(KEY_ADMIN_PIN) || DEFAULT_PIN;
    } catch (_) {
      return DEFAULT_PIN;
    }
  }

  function verifyPin(pin) {
    return Boolean(pin) && String(pin).trim() === getStoredPin();
  }

  function changePin(currentPin, newPin) {
    if (!verifyPin(currentPin)) return { ok: false, status: 401, detail: 'PIN lama salah.' };
    if (!/^\d{4,8}$/.test(String(newPin || '').trim())) {
      return { ok: false, status: 400, detail: 'PIN baru harus berupa 4 sampai 8 digit angka.' };
    }
    try {
      global.localStorage.setItem(KEY_ADMIN_PIN, String(newPin).trim());
    } catch (_) {}
    return { ok: true, message: 'PIN Kepala Bengkel offline berhasil diperbarui.' };
  }

  function getSecurityStatus() {
    const cur = getStoredPin();
    const isDef = cur === DEFAULT_PIN;
    return {
      pin_enabled: true,
      is_default_pin: isDef,
      default_hint: isDef ? 'PIN standar awal: 1234 (segera ubah melalui Mode Admin)' : null
    };
  }

  // --- RESOLUSI KENDARAAN, GENERASI, ALIAS MESIN & GUARDRAIL ---
  function matchesBrandModel(bq, mq, eb, em, aliases) {
    const bLow = String(bq || '').trim().toLowerCase();
    const mLow = String(mq || '').trim().toLowerCase();
    const ebLow = String(eb || '').trim().toLowerCase();
    const emLow = String(em || '').trim().toLowerCase();
    if (!mLow) return false;
    if (bLow && ebLow && !ebLow.includes(bLow) && !bLow.includes(ebLow)) return false;
    if (emLow && (emLow.includes(mLow) || mLow.includes(emLow))) return true;
    return (aliases || []).some((al) => {
      const a = String(al || '').toLowerCase();
      return a && (a.includes(mLow) || mLow.includes(a));
    });
  }

  function genMatchesEngine(gen, engineQ) {
    const nq = normCode(engineQ);
    if (!nq || nq.length < 2) return null;
    for (const v of (gen.engine_variants || [])) {
      const cands = [v.code].concat(v.aliases || []);
      for (const c of cands) {
        const nc = normCode(c);
        if (nc && (nq === nc || nq.includes(nc) || nc.includes(nq))) return v;
      }
    }
    return null;
  }

  function findCustomPack(brand, model, year, eng) {
    const packs = loadCustomPacks();
    const engNorm = normCode(eng);
    const cands = packs.filter((p) => {
      if (!matchesBrandModel(brand, model, p.brand, p.model, p.model_aliases || [p.model])) return false;
      if (year !== null && year !== undefined && !isNaN(year)) {
        if (Number(year) < Number(p.year_start || 1980) || Number(year) > Number(p.year_end || 2030)) return false;
      }
      return true;
    });
    if (!cands.length) return null;
    if (engNorm && cands.length > 1) {
      const hit = cands.find((c) => (c.engine_codes || []).some((ec) => {
        const n = normCode(ec);
        return n && (n.includes(engNorm) || engNorm.includes(n));
      }));
      if (hit) return hit;
    }
    return cands[0];
  }

  function resolveVehicleApplicability(brand, model, year, engineCode) {
    const bClean = String(brand || '').trim();
    const mClean = String(model || '').trim();
    const engClean = String(engineCode || '').trim();
    const yr = (year !== null && year !== undefined && year !== '' && !isNaN(Number(year))) ? Number(year) : null;
    const catalog = getGenerations();

    let modelMatches = catalog.filter((g) => matchesBrandModel(bClean, mClean, g.brand, g.model, g.model_aliases));
    let isReverse = false;
    if (!modelMatches.length && engClean) {
      const bLow = bClean.toLowerCase();
      modelMatches = catalog.filter((g) => genMatchesEngine(g, engClean) && (!bLow || g.brand.toLowerCase().includes(bLow) || bLow.includes(g.brand.toLowerCase())));
      if (modelMatches.length) isReverse = true;
    }

    const yearMatches = (yr !== null && modelMatches.length)
      ? modelMatches.filter((g) => g.year_start <= yr && yr <= g.year_end)
      : [];

    let transitionCandidates = [];
    let matchedModelOptions = [];
    let isTransition = false;
    let chosenGen = null;

    if (isReverse) {
      const pool = yearMatches.length ? yearMatches : modelMatches;
      const seen = new Set();
      pool.forEach((g) => {
        const k = `${g.brand}|${g.model}`.toLowerCase();
        if (seen.has(k)) return;
        seen.add(k);
        matchedModelOptions.push({
          brand: g.brand,
          model: String(g.model).split('/')[0].trim(),
          generation_label: g.generation_label,
          year_range: `${g.year_start}–${g.year_end}`,
          suggested_year: (yr && g.year_start <= yr && yr <= g.year_end) ? yr : Math.min(Math.max(2018, g.year_start), g.year_end)
        });
      });
      chosenGen = pool[0];
    } else if (yearMatches.length) {
      if (yearMatches.length > 1) {
        const ef = yearMatches.filter((g) => engClean && genMatchesEngine(g, engClean));
        if (ef.length === 1) {
          chosenGen = ef[0];
        } else {
          isTransition = true;
          transitionCandidates = yearMatches.map((g) => ({
            generation_id: g.generation_id,
            generation_label: g.generation_label,
            engine_codes: g.engine_codes || [],
            year_range: `${g.year_start}–${g.year_end}`,
            notes: g.notes || ''
          }));
          chosenGen = ef.length ? ef[ef.length - 1] : yearMatches[yearMatches.length - 1];
        }
      } else {
        chosenGen = yearMatches[0];
      }
    } else if (modelMatches.length) {
      let pool = modelMatches;
      if (engClean) {
        const ef = pool.filter((g) => genMatchesEngine(g, engClean));
        if (ef.length) pool = ef;
      }
      if (yr !== null) {
        pool = [...pool].sort((a, b) => Math.min(Math.abs(yr - a.year_start), Math.abs(yr - a.year_end)) - Math.min(Math.abs(yr - b.year_start), Math.abs(yr - b.year_end)));
        chosenGen = pool[0];
      } else {
        chosenGen = pool[pool.length - 1];
      }
    }

    const matchedVar = (chosenGen && engClean) ? genMatchesEngine(chosenGen, engClean) : null;
    const engineChips = chosenGen
      ? (chosenGen.engine_variants || []).map((v) => ({
          code: v.code, cc: v.cc || '', fuel: v.fuel || 'Bensin', desc: v.desc || '', aliases: v.aliases || []
        }))
      : [];
    const region = (chosenGen && chosenGen.region) || 'Asia';

    const hintLow = `${mClean} ${engClean}`.toLowerCase();
    let fuel = 'Bensin';
    if (matchedVar && matchedVar.fuel) fuel = matchedVar.fuel;
    else if (/air ev|binguo|cloud ev|atto 3|dolphin|seal|byd m6|mg4 ev|listrik/.test(hintLow)) fuel = 'EV';
    else if (/hybrid|hev|phev|zenix hybrid|e:hev|shvs|eq boost/.test(hintLow)) fuel = 'Hybrid';
    else if (/diesel|solar|2gd|2kd|1gd|1kd|4n15|4d56|d4hb|4ja1|rz4e|crdi|vnt|vrz/.test(hintLow)) fuel = 'Diesel';
    else if (chosenGen && chosenGen.fuel_types && chosenGen.fuel_types.length) fuel = chosenGen.fuel_types[0];

    const isHv = fuel === 'EV' || fuel === 'Hybrid';
    const hvWarn = fuel === 'EV'
      ? 'BAHAYA TEGANGAN TINGGI EV (300V–400V DC): Wajib pakai sarung tangan isolasi 1000V (Class 0), cabut Service Plug, & tunggu 10 menit sebelum menyentuh kabel oranye, inverter, atau kompresor AC (oli wajib POE isolasi, DILARANG oli PAG!).'
      : (fuel === 'Hybrid'
        ? 'PERINGATAN SISTEM HYBRID / MILD-HYBRID (48V–350V DC): Patuhi prosedur keselamatan HV — jangan menyentuh kabel oranye tanpa APD isolasi 1000V & pastikan oli kompresor AC khusus POE/ND-11.'
        : null);

    const effBrand = bClean || (chosenGen ? chosenGen.brand : '');
    const effModel = mClean || (chosenGen ? chosenGen.model : '');
    const customPack = findCustomPack(effBrand, effModel, yr, engClean);

    if (customPack) {
      const genLbl = chosenGen ? chosenGen.generation_label : `${effBrand} ${effModel} (${customPack.year_start}–${customPack.year_end})`;
      const engLbl = matchedVar ? `${matchedVar.code} (${matchedVar.cc} ${matchedVar.fuel})` : ((customPack.engine_codes || []).join(', ') || engClean || '-');
      return {
        appInfo: {
          brand: effBrand || customPack.brand || '',
          model: effModel || customPack.model || '',
          year: yr,
          engine_code: matchedVar ? matchedVar.code : (engClean || engLbl),
          region,
          resolved_fuel_type: fuel,
          is_high_voltage: isHv,
          hv_safety_warning: hvWarn,
          resolved_generation_id: customPack.generation_id || (chosenGen ? chosenGen.generation_id : null),
          resolved_generation_label: genLbl,
          resolved_engine_label: engLbl,
          coverage_level: 'EXACT_OEM_MANUAL',
          is_pinout_verified: true,
          is_transition_year: isTransition,
          transition_candidates: transitionCandidates,
          available_engine_choices: engineChips,
          matched_model_options: matchedModelOptions,
          active_manual_source: customPack.title || 'Buku Manual Kustom Bengkel',
          safety_warning_title: isTransition ? `⚠️ Tahun Peralihan ${yr}: Konfirmasi Kode Mesin` : null,
          safety_warning_desc: isTransition ? `Tahun ${yr} adalah masa transisi generasi pada ${effModel}.` : null
        },
        customPack
      };
    }

    const isJb420 = chosenGen && chosenGen.generation_id === 'suzuki_jb420' && (!matchedVar || matchedVar.code === 'J20A') && (yr === null || yr <= 2015);
    if (isJb420) {
      return {
        appInfo: {
          brand: 'Suzuki',
          model: mClean || 'Grand Vitara',
          year: yr,
          engine_code: 'J20A',
          region: 'Asia',
          resolved_fuel_type: 'Bensin',
          is_high_voltage: false,
          hv_safety_warning: null,
          resolved_generation_id: 'suzuki_jb420',
          resolved_generation_label: 'Grand Vitara Gen 2 (JB420)',
          resolved_engine_label: 'J20A (2.0L Bensin)',
          coverage_level: 'EXACT_OEM_MANUAL',
          is_pinout_verified: true,
          is_transition_year: false,
          transition_candidates: [],
          available_engine_choices: engineChips,
          matched_model_options: matchedModelOptions,
          active_manual_source: 'Buku Pedoman Resmi Suzuki Grand Vitara JB420 (Vol 1 & Vol 2)',
          safety_warning_title: null,
          safety_warning_desc: null
        },
        customPack: null
      };
    }

    const dispVehicle = `${effBrand} ${effModel}`.trim() + (yr ? ` (${yr})` : '') || 'Kendaraan Umum';
    const isSuzuki = effBrand.toLowerCase().includes('suzuki') || (chosenGen && chosenGen.brand.toLowerCase() === 'suzuki');
    const genLbl = chosenGen ? chosenGen.generation_label : `${dispVehicle} (Klasifikasi Standar)`;
    const engLbl = matchedVar
      ? `${matchedVar.code} (${matchedVar.cc} ${matchedVar.fuel})`
      : (chosenGen ? (chosenGen.engine_codes || []).join(', ') : (engClean || '-'));

    return {
      appInfo: {
        brand: effBrand,
        model: effModel,
        year: yr,
        engine_code: matchedVar ? matchedVar.code : (engClean || engLbl),
        region,
        resolved_fuel_type: fuel,
        is_high_voltage: isHv,
        hv_safety_warning: hvWarn,
        resolved_generation_id: chosenGen ? chosenGen.generation_id : null,
        resolved_generation_label: genLbl,
        resolved_engine_label: engLbl,
        coverage_level: isSuzuki ? 'SAME_BRAND_REFERENCE' : 'UNIVERSAL_OBD_ONLY',
        is_pinout_verified: false,
        is_transition_year: isTransition,
        transition_candidates: transitionCandidates,
        available_engine_choices: engineChips,
        matched_model_options: matchedModelOptions,
        active_manual_source: `Standar Universal OBD-II ${fuel} & Kasus Bengkel (Manual ${dispVehicle} Belum Tersedia)`,
        safety_warning_title: `⚠️ MODE STANDAR UNIVERSAL OBD-II (${dispVehicle.toUpperCase()} · ${region.toUpperCase()} · ${fuel.toUpperCase()})`,
        safety_warning_desc: `Terdeteksi sebagai ${genLbl} (Mesin ${engLbl}). Diagnosa & kode DTC memakai Katalog Universal ${fuel} & kasus bengkel. Manual OEM khusus model ini belum diunggah — cek soket fisik dengan multitester sebelum jumper kabel.`
      },
      customPack: null
    };
  }

  // --- MODERN DTC, FUEL FILTER, ADAPTIVE LIVE DATA & CUTOFF ---
  const EV_FORBIDDEN = ['sensor o2', 'ho2s', 'oksigen', 'busi', 'spark plug', 'koil', 'ignition coil', 'injektor', 'fuel pump', 'pompa bensin', 'bahan bakar', 'bbm', 'katalis', 'egr', 'throttle body', 'turbo', 'misfire'];
  const DIESEL_FORBIDDEN = ['busi', 'spark plug', 'koil pengapian', 'ignition coil', 'kabel busi', 'pertalite', 'pertamax'];

  function isFuelCompatible(text, fuel) {
    const fl = String(fuel || 'Bensin').toLowerCase();
    const tl = String(text || '').toLowerCase();
    if (fl === 'ev') return !EV_FORBIDDEN.some((k) => tl.includes(k));
    if (fl === 'diesel') return !DIESEL_FORBIDDEN.some((k) => tl.includes(k));
    return true;
  }

  function stripJb420Pins(txt) {
    if (!txt) return txt;
    return String(txt)
      .replace(/\s*\((?:[ECGB]\d{2}-\d{1,2}(?:\s*,\s*[ECGB]\d{2}-\d{1,2})*)\)/g, '')
      .replace(/\b[EC]\d{2}-\d{1,2}\b/g, 'Pin Soket Terkait')
      .replace(/\s{2,}/g, ' ')
      .trim();
  }

  function lookupModernDtc(code, fuelType) {
    const cat = getModernDtcCatalog();
    const c = String(code || '').trim().toUpperCase();
    const entry = cat[c];
    if (!entry) return null;
    if (c === 'P0087' && fuelType !== 'Diesel') return null;
    return entry;
  }

  function evaluateAdaptiveLiveData(req) {
    const out = [];
    const n = (v) => (v !== null && v !== undefined && v !== '' && !isNaN(Number(v))) ? Number(v) : null;
    const rp = n(req.rail_pressure_mpa), bp = n(req.boost_kpa), inj = n(req.inj_feedback_mm3), egr = n(req.egr_pct);
    const soc = n(req.hv_soc_pct), del = n(req.hv_cell_delta_mv), iso = n(req.hv_insulation_mohm), tmp = n(req.hv_temp_c);

    if (rp !== null) {
      if (rp < 22) out.push({ parameter: 'Fuel Rail Pressure', value: `${rp.toFixed(1)} MPa`, status: 'CRITICAL', note: 'Tekanan Common-Rail TERLALU RENDAH (< 22 MPa) — Cek Filter Solar, Masuk Angin, SCV, atau Backleak Injektor.' });
      else if (rp > 195) out.push({ parameter: 'Fuel Rail Pressure', value: `${rp.toFixed(1)} MPa`, status: 'HIGH', note: 'Tekanan Common-Rail TERLALU TINGGI (> 195 MPa) — Cek SCV / Return / Sensor FRP.' });
      else out.push({ parameter: 'Fuel Rail Pressure', value: `${rp.toFixed(1)} MPa`, status: 'NORMAL', note: 'Tekanan Fuel Rail Common-Rail normal (25–190 MPa).' });
    }
    if (bp !== null) {
      if (bp < 95) out.push({ parameter: 'Boost Turbo', value: `${bp.toFixed(0)} kPa`, status: 'HIGH', note: 'Boost di bawah atmosfer — cek filter udara/sensor MAP.' });
      else if (bp > 260) out.push({ parameter: 'Boost Turbo', value: `${bp.toFixed(0)} kPa`, status: 'HIGH', note: 'OVERBOOST (> 260 kPa) — VNT/Wastegate macet (risiko P0234).' });
      else out.push({ parameter: 'Boost Turbo', value: `${bp.toFixed(0)} kPa`, status: 'NORMAL', note: 'Tekanan Boost Turbo normal.' });
    }
    if (inj !== null) {
      if (Math.abs(inj) >= 3.0) out.push({ parameter: 'Koreksi Injektor', value: `${inj >= 0 ? '+' : ''}${inj.toFixed(2)} mm³/st`, status: 'CRITICAL', note: 'Melebihi ±3.0 mm³/st — Injektor aus/mampet/bocor atau kompresi silinder lemah!' });
      else if (Math.abs(inj) >= 2.0) out.push({ parameter: 'Koreksi Injektor', value: `${inj >= 0 ? '+' : ''}${inj.toFixed(2)} mm³/st`, status: 'MEDIUM', note: 'Koreksi mulai melebar — disarankan purging/cek filter solar.' });
      else out.push({ parameter: 'Koreksi Injektor', value: `${inj >= 0 ? '+' : ''}${inj.toFixed(2)} mm³/st`, status: 'NORMAL', note: 'Keseimbangan injektor sehat.' });
    }
    if (egr !== null) {
      out.push({ parameter: 'Posisi EGR', value: `${egr.toFixed(0)}%`, status: egr > 85 ? 'MEDIUM' : 'NORMAL', note: egr > 85 ? 'Bukaan EGR tinggi (> 85%) — waspada katup macet terbuka saat beban penuh.' : 'Bukaan EGR normal.' });
    }
    if (iso !== null) {
      if (iso < 1.0) out.push({ parameter: 'Tahanan Isolasi HV', value: `${iso.toFixed(2)} MOhm`, status: 'CRITICAL', note: 'BAHAYA KEBOCORAN HV (< 1 MOhm)! Wajib APD 1000V — cek kompresor AC (wajib oli POE) & konektor oranye!' });
      else if (iso < 10.0) out.push({ parameter: 'Tahanan Isolasi HV', value: `${iso.toFixed(2)} MOhm`, status: 'HIGH', note: 'Isolasi HV menurun (< 10 MOhm) — cek kelembaban konektor & kompresor AC HV.' });
      else out.push({ parameter: 'Tahanan Isolasi HV', value: `${iso.toFixed(1)} MOhm`, status: 'NORMAL', note: 'Isolasi tegangan tinggi aman (> 10 MOhm).' });
    }
    if (del !== null) {
      if (del >= 150) out.push({ parameter: 'Delta Tegangan Sel HV', value: `${del.toFixed(0)} mV`, status: 'CRITICAL', note: 'CELL IMBALANCE BERAT (≥ 150 mV) — Ada modul/sel baterai HV drop (pemicu P0A80).' });
      else if (del >= 60) out.push({ parameter: 'Delta Tegangan Sel HV', value: `${del.toFixed(0)} mV`, status: 'MEDIUM', note: 'Selisih sel mulai melebar (60–150 mV).' });
      else out.push({ parameter: 'Delta Tegangan Sel HV', value: `${del.toFixed(0)} mV`, status: 'NORMAL', note: 'Keseimbangan sel baterai HV sehat.' });
    }
    if (soc !== null) {
      out.push({ parameter: 'SoC Baterai HV', value: `${soc.toFixed(0)}%`, status: soc < 15 ? 'HIGH' : 'NORMAL', note: soc < 15 ? 'SoC sangat rendah (< 15%) — risiko gagal READY.' : 'Muatan baterai HV memadai.' });
    }
    if (tmp !== null) {
      out.push({ parameter: 'Suhu HV / Inverter', value: `${tmp.toFixed(0)} °C`, status: tmp >= 50 ? 'CRITICAL' : 'NORMAL', note: tmp >= 50 ? 'OVERHEAT SISTEM HV (≥ 50°C) — Cek pompa coolant inverter & kipas baterai!' : 'Suhu sistem HV normal.' });
    }
    return out;
  }

  function extractReqDtcs(raw) {
    const tokens = String(raw || '').toUpperCase().split(/[,;\s/]+/).map((s) => s.trim()).filter(Boolean);
    const out = [];
    tokens.forEach((t) => {
      const m = t.match(/^([PCBU][0-9A-F]{4})(?:[-]?[0-9A-F]{2})?$/);
      const norm = m ? m[1] : null;
      if (norm && !out.includes(norm)) out.push(norm);
    });
    return out;
  }

  function enhanceOfflineSearchResult(req, rawRes) {
    const { appInfo, customPack } = resolveVehicleApplicability(req.brand, req.model, req.year, req.engine_code);
    const fuel = appInfo.resolved_fuel_type || 'Bensin';
    const adaptiveLive = evaluateAdaptiveLiveData(req);
    const reqCodes = extractReqDtcs(req.dtc);

    // Filter ranked_matches untuk kesesuaian bahan bakar
    const compatMatches = (rawRes.ranked_matches || []).filter((m) =>
      isFuelCompatible(`${m.final_diagnosis} ${m.repair_action} ${m.complaint} ${m.symptom}`, fuel)
    );

    const out = {
      ...rawRes,
      ranked_matches: compatMatches,
      vehicle_applicability: appInfo
    };

    // 1. Cek apakah ada DTC di Custom Pack atau Katalog Modern (Diesel/Turbo/VVT/Hybrid/EV/CAN)
    let matchedModern = null;
    let matchedCustomDtc = null;
    if (reqCodes.length) {
      const firstCode = reqCodes[0];
      if (customPack && Array.isArray(customPack.dtc_catalog)) {
        matchedCustomDtc = customPack.dtc_catalog.find((d) => String(d.code || '').toUpperCase() === firstCode) || null;
      }
      if (!matchedCustomDtc) {
        const mh = lookupModernDtc(firstCode, fuel);
        const jbExists = global.AGOS_OFFLINE_DATA && global.AGOS_OFFLINE_DATA.dtc_codes &&
          global.AGOS_OFFLINE_DATA.dtc_codes.some((d) => String(d.code || '').toUpperCase() === firstCode);
        if (mh && (fuel === 'Diesel' || fuel === 'EV' || fuel === 'Hybrid' || !jbExists)) {
          matchedModern = mh;
        }
      }
    }

    if (matchedCustomDtc) {
      const c = matchedCustomDtc.code.toUpperCase();
      out.top_case_code = `MANUAL-${c}`;
      out.top_diagnosis = `${matchedCustomDtc.description_id || c} (DTC ${c})`;
      out.top_score_percent = 94.0;
      out.top_category_label = 'SANGAT MIRIP';
      out.top_headline = `${out.top_diagnosis} — 94.0% (Paket Manual Kustom Terverifikasi)`;
      out.direct_manual_advice = {
        diagnosis_title: matchedCustomDtc.description_id || c,
        system_category: 'Manual Kustom',
        group_category: customPack.title || 'Manual Kustom',
        manual_book_section: `${customPack.title || 'Manual Kustom'} — Kode ${c}`,
        cause_summary: Array.isArray(matchedCustomDtc.common_causes) ? matchedCustomDtc.common_causes.join('; ') : String(matchedCustomDtc.common_causes || '-'),
        cause_items: [{ category: 'Manual Kustom', detail: String(matchedCustomDtc.common_causes || matchedCustomDtc.description_id || '-') }],
        repair_options: matchedCustomDtc.repair_options || [{ title: (matchedCustomDtc.repair_steps && matchedCustomDtc.repair_steps[0]) || 'Ikuti langkah SOP manual kustom', tag: 'Manual Kustom', priority: 'UTAMA', why: 'Sesuai paket manual terverifikasi.', verify: 'DTC hilang setelah uji jalan.' }],
        step_by_step_repair: matchedCustomDtc.repair_steps || [],
        sensor_standards: matchedCustomDtc.standard_specs || [],
        wiring_pinout: matchedCustomDtc.wiring_pinout || customPack.wiring_pinouts || [],
        relearn_reset_steps: [`1. Hapus DTC ${c} via scanner & lakukan test drive.`],
        is_pinout_verified: true,
        safety_warning: appInfo.safety_warning_desc,
        hv_safety_warning: appInfo.hv_safety_warning,
        is_low_confidence_fallback: false,
        adaptive_live_findings: adaptiveLive
      };
      return out;
    }

    if (matchedModern) {
      const c = matchedModern.code;
      const causes = String(matchedModern.root_causes || '').split(';').map((s) => s.trim()).filter(Boolean);
      out.top_case_code = `MANUAL-${c}`;
      out.top_diagnosis = `${matchedModern.title_id} (DTC ${c})`;
      out.top_score_percent = 94.0;
      out.top_category_label = 'SANGAT MIRIP';
      out.top_headline = `${out.top_diagnosis} — 94.0% (Katalog Universal ${fuel} / Modern OBD-II)`;
      out.direct_manual_advice = {
        diagnosis_title: matchedModern.title_id,
        system_category: matchedModern.system_category || 'Kelistrikan',
        group_category: `Universal ${fuel}`,
        manual_book_section: `Katalog Universal ${fuel} / Modern OBD-II — Kode ${c}`,
        cause_summary: matchedModern.root_causes || '-',
        cause_items: causes.slice(0, 6).map((d, i) => ({ category: i === 0 ? 'Prioritas Utama' : (i === 1 ? 'Kemungkinan Tinggi' : 'Cek Pendukung'), detail: d })),
        repair_options: matchedModern.repair_options || [],
        step_by_step_repair: matchedModern.repair_steps || [],
        sensor_standards: matchedModern.standard_specs || [],
        wiring_pinout: (matchedModern.requires_hv_safety || fuel === 'EV')
          ? [{ pin: 'Konektor HV / BMS (Wajib APD 1000V)', signal: 'Baterai HV / Inverter / CAN', function: 'Cek via Scanner BMS & Insulation Tester 500V (Jangan tusuk kabel oranye!)' }]
          : [{ pin: `Soket Komponen ${c}`, signal: `Sirkuit ${matchedModern.system_category} (${fuel})`, function: 'Manual pinout OEM model ini belum diunggah — ukur fisik dengan multitester.' }],
        relearn_reset_steps: [`1. Hapus DTC ${c} dengan scanner.`, '2. Lakukan learning/kalibrasi sistem terkait lalu uji jalan.'],
        is_pinout_verified: false,
        safety_warning: appInfo.safety_warning_desc,
        hv_safety_warning: (matchedModern.requires_hv_safety || appInfo.is_high_voltage) ? appInfo.hv_safety_warning : null,
        is_low_confidence_fallback: false,
        adaptive_live_findings: adaptiveLive
      };
      return out;
    }

    // 2. Confidence Cutoff (< 25%) jika tidak ada kecocokan kuat / kompatibel
    const topCompat = compatMatches[0] || null;
    const isManualFromRaw = String(out.top_case_code || '').startsWith('MANUAL-') && isFuelCompatible(out.top_diagnosis, fuel);
    if (!isManualFromRaw && (!topCompat || Number(topCompat.total_score || 0) < 25.0)) {
      const dtcTxt = reqCodes.length ? ` (${reqCodes.join(', ')})` : '';
      const safeTitle = fuel === 'EV'
        ? `Kasus Baru EV / Kode Belum Terpetakan${dtcTxt} — Panduan Pemeriksaan Awal Aman`
        : (fuel === 'Diesel'
          ? `Kasus Baru Diesel / Kode Belum Terpetakan${dtcTxt} — Panduan Pemeriksaan Awal Common-Rail`
          : `Kasus Baru / Kode Belum Terpetakan${dtcTxt} — Panduan Pemeriksaan Awal Sistematis`);
      const safeOpts = fuel === 'EV'
        ? [
            { title: 'Cek Tegangan Aki 12V Aux, Sekering Utama & Scan Modul BMS/VCU', tag: 'Langkah Aman #1', priority: 'UTAMA', why: 'Mayoritas gangguan gagal READY EV berasal dari aki 12V atau komunikasi BMS.', verify: 'Aki 12V ≥ 12.4V & BMS merespons.' },
            { title: 'Periksa Live Data BMS: SoC (%), Delta Sel (mV) & Tahanan Isolasi HV (MOhm)', tag: 'Wajib APD HV 1000V', priority: 'UTAMA', why: 'Mendeteksi cell imbalance atau kebocoran isolasi tegangan tinggi.', verify: 'Delta sel < 50 mV & Isolasi > 10 MOhm.' }
          ]
        : (fuel === 'Diesel'
          ? [
              { title: 'Cek Filter Solar, Masuk Angin & Live Data Fuel Rail Pressure', tag: 'Langkah Utama Diesel', priority: 'UTAMA', why: 'Suplai solar & tekanan common-rail adalah penyebab utama drop tenaga diesel.', verify: 'Tekanan rail idle 30–45 MPa stabil.' },
              { title: 'Periksa Selang Intercooler/Turbo, Kerja VNT & Katup EGR', tag: 'Udara & Turbo', priority: 'SEKUNDER', why: 'Kebocoran boost atau EGR macet memicu asap hitam & ngempos.', verify: 'Jalur boost kedap & EGR responsif.' }
            ]
          : [
              { title: 'Periksa Live Data Sensor Utama (STFT/LTFT, MAP/MAF, ECT, O2) & Aki/Ground', tag: 'Langkah Pertama', priority: 'UTAMA', why: 'Memastikan arah diagnosa berbasis data sebelum mengganti komponen.', verify: 'Pengisian 13.8–14.4V & data sensor wajar.' },
              { title: 'Cek Fisik Konektor, Kebocoran Vakum, Busi/Koil & Tekanan BBM', tag: 'Verifikasi Fisik', priority: 'SEKUNDER', why: 'Menangkap penyebab paling umum di lapangan secara cepat.', verify: 'Mesin normal lalu simpan kasus ke database.' }
            ]);
      out.top_case_code = 'BELUM-TERPETAKAN';
      out.top_diagnosis = safeTitle;
      out.top_score_percent = topCompat ? topCompat.total_score : 0;
      out.top_category_label = 'PERLU PEMERIKSAAN AWAL';
      out.top_headline = `${safeTitle} — Kecocokan historis rendah (${out.top_score_percent}%), gunakan panduan cek awal aman.`;
      out.direct_manual_advice = {
        diagnosis_title: safeTitle,
        system_category: fuel === 'EV' ? 'Kelistrikan' : (fuel === 'Diesel' ? 'Bahan Bakar' : 'Umum'),
        group_category: `Pemeriksaan Awal (${fuel})`,
        manual_book_section: `Mode Pemeriksaan Awal Aman — ${appInfo.resolved_generation_label}`,
        cause_summary: `Belum ada kecocokan kuat (< 25%) pada database lokal untuk ${appInfo.resolved_generation_label}. Lakukan pemeriksaan sistematis sesuai jenis mesin ${fuel}.`,
        cause_items: [{ category: 'Status Database', detail: `Kasus baru / DTC belum terdaftar untuk ${appInfo.resolved_generation_label} (${fuel}).` }],
        repair_options: safeOpts,
        step_by_step_repair: ['1. Baca seluruh DTC & Freeze Frame dari scanner.', `2. Lakukan pemeriksaan dasar aman khusus ${fuel}.`, '3. Setelah sembuh, klik Simpan Kasus agar AI offline mempelajarinya.'],
        sensor_standards: [],
        wiring_pinout: [{ pin: 'Soket Fisik Terkait', signal: `Pengukuran Aman (${fuel})`, function: 'Ukur langsung menggunakan multitester.' }],
        relearn_reset_steps: ['1. Reset DTC setelah perbaikan dan simpan kasus baru.'],
        is_pinout_verified: false,
        safety_warning: appInfo.safety_warning_desc,
        hv_safety_warning: appInfo.hv_safety_warning,
        is_low_confidence_fallback: true,
        adaptive_live_findings: adaptiveLive
      };
      return out;
    }

    // 3. Terapkan guardrail wiring & HV safety pada hasil normal
    const adv = { ...(out.direct_manual_advice || {}) };
    adv.adaptive_live_findings = adaptiveLive;
    adv.hv_safety_warning = appInfo.hv_safety_warning || adv.hv_safety_warning || null;
    if (!appInfo.is_pinout_verified) {
      adv.is_pinout_verified = false;
      adv.safety_warning = appInfo.safety_warning_desc;
      adv.repair_options = (adv.repair_options || []).map((o) => ({
        ...o,
        title: stripJb420Pins(o.title),
        why: stripJb420Pins(o.why),
        verify: stripJb420Pins(o.verify)
      }));
      adv.step_by_step_repair = (adv.step_by_step_repair || []).map(stripJb420Pins);
      adv.wiring_pinout = (adv.wiring_pinout || []).map((w) => ({
        ...w,
        function: String(w.function || '').includes('[Contoh Ref') ? w.function : `[Contoh Ref. JB420 — Cek Soket Fisik] ${w.function || ''}`
      }));
    } else {
      adv.is_pinout_verified = true;
      adv.safety_warning = appInfo.safety_warning_desc;
    }
    out.direct_manual_advice = adv;
    return out;
  }

  global.AgosOfflineMultiModel = {
    getGenerations,
    getEngineDirectory,
    getModernDtcCatalog,
    loadCustomPacks,
    saveCustomPack,
    deleteCustomPack,
    listAllPackSummaries,
    verifyPin,
    changePin,
    getSecurityStatus,
    resolveVehicleApplicability,
    lookupModernDtc,
    enhanceOfflineSearchResult
  };
})(typeof window !== 'undefined' ? window : globalThis);
