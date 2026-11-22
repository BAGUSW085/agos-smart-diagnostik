/**
 * AGOS Smart Diagnostik — Offline Manual & Wiring RAG Search (manual-search.js)
 * =============================================================================
 * Port 1:1 dari `backend/app/services/manual_wiring_service.py` (`ask_rag_assistant`
 * dan `retrieve_repair_manuals`). Menjalankan pencarian kode DTC, spesifikasi
 * sensor, pinout ECU/TCM/BCM, dan 1.381 potongan buku manual Vol 1 & Vol 2
 * secara 100% offline di HP tanpa API AI online.
 */
(function (global) {
  'use strict';

  const MANUAL_STOPWORDS = new Set([
    'yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'pada', 'dengan', 'atau',
    'apakah', 'bagaimana', 'cara', 'cek', 'periksa', 'mobil', 'mesin',
    'berapa', 'letak', 'dimana', 'tolong', 'tampilkan', 'cari', 'suzuki',
    'grand', 'vitara', 'jb420', 'j20a'
  ]);

  function extractTokens(text) {
    if (!text) return [];
    return String(text)
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, ' ')
      .split(/\s+/)
      .filter((t) => t.length >= 2 && !MANUAL_STOPWORDS.has(t));
  }

  function extractDtcFromText(query, explicitDtc) {
    const found = [];
    const combined = `${explicitDtc || ''} ${query || ''}`.toUpperCase();
    for (const m of combined.matchAll(/\b([PCBU][0-9A-F]{4})(?:-?[0-9A-F]{2})?\b/g)) {
      if (!found.includes(m[1])) found.push(m[1]);
    }
    for (const m of combined.matchAll(/\bKLS-(\d{1,2})\b/g)) {
      const k = `KLS-${m[1]}`;
      if (!found.includes(k)) found.push(k);
    }
    for (const m of combined.matchAll(/\bDTC\s*NO\.?\s*(\d{1,2})\b/g)) {
      const k = `KLS-${m[1]}`;
      if (!found.includes(k)) found.push(k);
    }
    return found;
  }

  function parsePinoutJson(rawPj) {
    let obj = rawPj || {};
    if (typeof obj === 'string') {
      try { obj = JSON.parse(obj); } catch (_) { obj = {}; }
    }
    const list = [];
    if (obj && typeof obj === 'object') {
      for (const [pinCode, detail] of Object.entries(obj)) {
        if (detail && typeof detail === 'object') {
          list.push({
            pin_code: pinCode,
            wire_color: String(detail.wire_color || '-'),
            function: String(detail.function || '-')
          });
        }
      }
    }
    return list;
  }

  function lookupDtcCodes(store, codes) {
    const out = [];
    for (const raw of codes) {
      const c = String(raw || '').trim().toUpperCase();
      const row = store.dtcCodeMap[c];
      if (row) {
        const causes = String(row.possible_causes || '')
          .split(/[;|]+/)
          .map((s) => s.trim())
          .filter(Boolean);
        out.push({
          code: row.code,
          system: row.system,
          description_id: row.description_id,
          possible_causes: causes,
          recommended_fix: row.recommended_fix || null,
          severity_level: row.severity_level || 'MEDIUM'
        });
      }
    }
    return out;
  }

  function searchSensorSpecs(store, sensorKeyword) {
    if (!sensorKeyword) return [];
    const kw = String(sensorKeyword).toLowerCase();
    return store.sensorSpecs.filter((s) => {
      const hay = `${s.sensor_name || ''} ${s.testing_notes || ''}`.toLowerCase();
      return hay.includes(kw);
    });
  }

  function searchWiringDiagrams(store) {
    return store.wiringDiagrams.map((r) => ({
      id: r.id,
      brand: r.brand,
      model: r.model,
      year_range: r.year_range,
      system_name: r.system_name,
      ecu_connector_code: r.ecu_connector_code,
      pinouts: parsePinoutJson(r.pinout_json),
      ground_locations: r.ground_locations,
      diagram_image_url: r.diagram_image_url
    }));
  }

  function retrieveRepairManuals(store, queryText, topK = 3) {
    const coreTokens = new Set(extractTokens(queryText));
    if (coreTokens.size === 0) return [];

    const scored = [];
    for (const m of store.repairManuals) {
      const docText = `${m.brand || ''} ${m.model || ''} ${m.section_title || ''} ${m.content_text || ''} ${m.tags || ''}`;
      const docTokens = new Set(extractTokens(docText));
      const tagList = String(m.tags || '').split(',').map((t) => t.trim().toLowerCase()).filter(Boolean);
      const titleTokens = new Set(extractTokens(m.section_title || ''));

      let titleHits = 0;
      let coreOverlap = 0;
      let tagHits = 0;
      for (const tok of coreTokens) {
        if (titleTokens.has(tok)) titleHits++;
        if (docTokens.has(tok)) coreOverlap++;
        if (tagList.includes(tok)) tagHits++;
      }
      if (coreOverlap + tagHits === 0) continue;

      const isGlossary = String(m.content_text || '').toLowerCase().includes('singkatan') ||
        String(m.section_title || '').toLowerCase().includes('bab 0a');
      const glossaryPenalty = isGlossary ? -4.0 : 0.0;
      const rawScore = coreOverlap * 2.5 + titleHits * 6.0 + tagHits * 4.0 + glossaryPenalty;
      if (rawScore <= 0) continue;

      const normScore = Math.round(Math.min(100.0, (rawScore / Math.max(coreTokens.size, 1)) * 35.0) * 10) / 10;
      scored.push({
        id: m.id,
        brand: m.brand,
        model: m.model,
        section_title: m.section_title,
        content_text: m.content_text,
        tags: tagList,
        relevance_score: normScore
      });
    }
    scored.sort((a, b) => b.relevance_score - a.relevance_score);
    return scored.slice(0, topK);
  }

  async function askRagAssistant(payload) {
    const store = await global.AgosDataStore.ensureLoaded();
    const query = String(payload.query || '').trim();
    const detectedDtcs = extractDtcFromText(query, payload.dtc_code);
    const dtcDetails = lookupDtcCodes(store, detectedDtcs);
    const catMap = store.dtcCatalogMap;

    let combinedHint = query.toLowerCase();
    if (dtcDetails.length > 0) {
      combinedHint += ' ' + dtcDetails.map((d) => `${d.code} ${d.description_id} ${d.possible_causes.join(' ')}`.toLowerCase()).join(' ');
    }

    let sensorKw = null;
    let moduleKw = null;
    const candidates = [
      'kipas', 'cooling fan', 'p0480', 'p0481',
      'maf', 'o2', 'oxygen', 'ho2s', 'ect', 'coolant', 'map',
      'ckp', 'cmp', 'tps', 'throttle', 'iat', 'app', 'pedal',
      'coil', 'ignition', 'injector', 'injektor', 'fuel pump', 'pompa bensin',
      'evap', 'purge', 'egr',
      'abs', 'wheel speed', 'e03',
      'solenoid', 'tcm', 'matic', 'transmisi', 'e92', 'e93',
      'hvac', 'blower', 'evaporator', 'suhu kabin', 'g52',
      'airbag', 'air bag', 'srs', 'sdm', 'pretensioner', 'g47',
      'bcm', 'door lock', 'power window', 'wiper', 'g30', 'g31', 'g32',
      'immobilizer', 'icm', 'transponder', 'g24',
      'keyless', 'kscm', 'steering lock', 'g44',
      'can'
    ];

    for (const cand of candidates) {
      if (combinedHint.includes(cand)) {
        if (['kipas', 'cooling fan', 'p0480', 'p0481'].includes(cand)) sensorKw = 'fan';
        else if (['oxygen', 'ho2s'].includes(cand)) sensorKw = 'o2';
        else if (cand === 'coolant') sensorKw = 'ect';
        else if (cand === 'throttle') sensorKw = 'tps';
        else if (cand === 'pedal') sensorKw = 'app';
        else if (['injector', 'injektor'].includes(cand)) sensorKw = 'injector';
        else if (['fuel pump', 'pompa bensin'].includes(cand)) sensorKw = 'fuel_pump';
        else if (['evap', 'purge'].includes(cand)) sensorKw = 'evap';
        else if (['abs', 'wheel speed', 'e03'].includes(cand)) moduleKw = 'abs';
        else if (['solenoid', 'tcm', 'matic', 'transmisi', 'e92', 'e93'].includes(cand)) moduleKw = 'tcm';
        else if (['hvac', 'blower', 'evaporator', 'suhu kabin', 'g52'].includes(cand)) moduleKw = 'hvac';
        else if (['airbag', 'air bag', 'srs', 'sdm', 'pretensioner', 'g47'].includes(cand)) moduleKw = 'sdm';
        else if (['bcm', 'door lock', 'power window', 'wiper', 'g30', 'g31', 'g32'].includes(cand)) moduleKw = 'bcm';
        else if (['immobilizer', 'icm', 'transponder', 'g24'].includes(cand)) moduleKw = 'icm';
        else if (['keyless', 'kscm', 'steering lock', 'g44'].includes(cand)) moduleKw = 'kscm';
        else sensorKw = cand;
        break;
      }
    }

    const specSearchKw = ['maf', 'o2', 'ect', 'map', 'ckp', 'cmp', 'tps', 'iat', 'app'].includes(sensorKw)
      ? sensorKw
      : null;
    const sensorSpecs = specSearchKw ? searchSensorSpecs(store, specSearchKw) : [];
    const wiringDiagrams = searchWiringDiagrams(store);
    const primaryCatEntry = detectedDtcs.length > 0 ? (catMap[detectedDtcs[0].toUpperCase()] || null) : null;

    const summaryParts = [];

    // 1. BLOK PENYEBAB & SARAN PENYELESAIAN DTC BUKU MANUAL
    if (dtcDetails.length > 0) {
      for (const dtcInfo of dtcDetails) {
        const cEntry = catMap[dtcInfo.code.toUpperCase()];
        const docRef = (cEntry && cEntry.suzuki_doc_id) ? ` [Dokumen ID: ${cEntry.suzuki_doc_id}]` : '';
        const cleanCauses = dtcInfo.possible_causes.filter(
          (c) => !c.toLowerCase().startsWith('pinout & warna kabel:')
        );
        const causesStr = cleanCauses.length > 0 ? cleanCauses.slice(0, 4).join('; ') : dtcInfo.description_id;

        const fixLines = [];
        if (cEntry && Array.isArray(cEntry.remedies) && cEntry.remedies.length > 0) {
          const remSummary = cEntry.remedies.slice(0, 3).map((r) => String(r).trim()).filter(Boolean).join('; ');
          if (remSummary) fixLines.push(`• Solusi Inti Buku Manual: ${remSummary}`);
        }
        if (cEntry && Array.isArray(cEntry.repair_steps) && cEntry.repair_steps.length > 0) {
          const stepsPreview = cEntry.repair_steps.slice(0, 4).map((s) => `  ${String(s).trim()}`).join('\n');
          if (stepsPreview) fixLines.push(`• Langkah Pemeriksaan & Perbaikan:\n${stepsPreview}`);
        } else if (dtcInfo.recommended_fix) {
          const stepsPreview = String(dtcInfo.recommended_fix)
            .split(/\r?\n/)
            .slice(0, 4)
            .map((ln) => `  ${ln.trim()}`)
            .filter((ln) => ln.trim())
            .join('\n');
          if (stepsPreview) fixLines.push(`• Langkah Pemeriksaan & Perbaikan:\n${stepsPreview}`);
        }

        const fixBlock = fixLines.length > 0 ? '\n' + fixLines.join('\n') : '';
        summaryParts.push(
          `[PENYEBAB & SARAN PENYELESAIAN DTC ${dtcInfo.code} — ${dtcInfo.severity_level}]\n` +
          `• Deskripsi: ${dtcInfo.description_id}\n` +
          `• Buku Pedoman: ${dtcInfo.system}${docRef}\n` +
          `• Area Masalah / Penyebab: ${causesStr}` +
          fixBlock
        );
      }
    }

    // 2. BLOK SPESIFIKASI STANDAR PEMERIKSAAN
    if (sensorSpecs.length > 0) {
      const sp = sensorSpecs[0];
      const notesStr = sp.testing_notes ? `\n• Catatan Pemeriksaan: ${sp.testing_notes}` : '';
      summaryParts.push(
        `[SPESIFIKASI SENSOR ${sp.sensor_name} (${sp.brand} ${sp.model})]\n` +
        `• Konfigurasi Pinout: ${sp.pin_configuration}\n` +
        `• Tegangan Idle: ${sp.voltage_idle}\n` +
        `• Tegangan Kerja/WOT: ${sp.voltage_wot}\n` +
        `• Standar Tahanan: ${sp.resistance_ohm}` +
        notesStr
      );
    } else if (sensorKw === 'fan') {
      summaryParts.push(
        '[SPESIFIKASI SIRKUIT KONTROL KIPAS RADIATOR (Suzuki Grand Vitara JB420 Bab 1A-133 & 1A-233)]\n' +
        '• Konfigurasi Pinout: E23-46 (RED/BLK): Relay Kipas No.1 | E23-47 (RED): Relay Kipas No.2 | C37-24 (PPL/YEL): Sinyal Suhu ECT\n' +
        '• Tegangan Kipas OFF (Standby IG ON): 10.0 - 14.0 V pada terminal E23-46 / E23-47\n' +
        '• Tegangan Kipas ON (ECT ≥ 97.5°C / AC ON): 0.0 - 1.5 V (Ground Switched oleh ECM)\n' +
        '• Standar Tahanan Koil Relay: 60 - 120 Ohm (pada 20°C)'
      );
    } else if (primaryCatEntry && Array.isArray(primaryCatEntry.standard_specs) && primaryCatEntry.standard_specs.length > 0) {
      const specLines = primaryCatEntry.standard_specs
        .slice(0, 5)
        .map((spI) => `• ${spI.parameter || 'Pemeriksaan'}: ${spI.normal_range || '-'}`)
        .join('\n');
      summaryParts.push(
        `[SPESIFIKASI STANDAR PEMERIKSAAN BUKU MANUAL — DTC ${primaryCatEntry.code}]\n${specLines}`
      );
    } else if (moduleKw || dtcDetails.length > 0) {
      let effMod = moduleKw;
      if (!effMod && detectedDtcs.length > 0) {
        const c0 = detectedDtcs[0];
        if (c0.startsWith('C10')) effMod = 'abs';
        else if (['P07', 'P09', 'P17', 'P18', 'P27'].some((p) => c0.startsWith(p))) effMod = 'tcm';
        else if (c0.startsWith('B15')) effMod = 'hvac';
        else if (c0.startsWith('B10')) effMod = 'sdm';
        else if (c0.startsWith('B11')) effMod = 'bcm';
        else if (c0.startsWith('P161') || ['P1610', 'P1614', 'P1615', 'P1616', 'P1618', 'P1621', 'P1623', 'P1636', 'P1638'].includes(c0)) effMod = 'icm';
        else if (c0.startsWith('KLS-')) effMod = 'kscm';
        else if (c0.startsWith('U')) sensorKw = 'can';
      }

      const moduleStdMap = {
        abs:
          '[SPESIFIKASI STANDAR MODUL ABS / HECU (Vol 1 Bab 4E Hal. 636-649)]\n' +
          '• Tegangan Suplai IG1 (E03-07) & +B Solenoid/Motor (E03-13, E03-26): 10.0 - 14.0 V\n' +
          '• Tahanan Ground Modul ABS (E03-01 & E03-14): < 1.0 Ohm ke bodi\n' +
          '• Celah Wheel Speed Sensor: Rapat pada knuckle tanpa serbuk besi pada rotor magnetik',
        tcm:
          '[SPESIFIKASI STANDAR MODUL TRANSMISI OTOMATIS TCM (Vol 2 Bab 5A Hal. 102-104)]\n' +
          '• Suplai Daya Utama TCM IG ON (E92-06) & Backup +B (E92-22): 10.0 - 14.0 V\n' +
          '• Tegangan Shift Solenoid-A/B pada Posisi P/N (E92-16 / E92-15): 9.0 - 14.0 V\n' +
          '• Ground Utama TCM (E92-01 & E92-23): < 0.5 V (< 1.0 Ohm ke massa)',
        hvac:
          '[SPESIFIKASI STANDAR MODUL KONTROL AC OTOMATIS / HVAC (Vol 2 Bab 7B Hal. 327-330)]\n' +
          '• Suplai Daya Modul HVAC IG ON (G52-01) & Memori +B (G52-02): 10.0 - 14.0 V\n' +
          '• Tegangan Referensi Sensor/Aktuator +5V (G52-14): 4.0 - 6.0 V\n' +
          '• Ground Utama & Sensor HVAC (G52-15 & G52-27): < 1.0 Ohm',
        sdm:
          '[SPESIFIKASI STANDAR MODUL SRS AIR BAG / SDM (Vol 2 Bab 8B Hal. 370)]\n' +
          '• Suplai Daya Utama SDM IG ON (G47-16): ≥ 8.0 V (Normal 10.0 - 14.0 V)\n' +
          '• Tahanan Sirkuit Inflator Air Bag / Pretensioner (dengan Special Tool): 1.8 - 2.5 Ohm\n' +
          '• Ground Utama SDM (G47-20): < 1.0 Ohm (PERINGATAN: Jangan ukur inflator langsung dengan ohmmeter tanpa melepas konektor!)',
        bcm:
          '[SPESIFIKASI STANDAR BODY ELECTRICAL CONTROL MODULE / BCM (Vol 2 Bab 10B Hal. 754-758)]\n' +
          '• Suplai Daya +B Utama BCM (G30-01) & IG1 (G30-21) & ACC (G30-09): 10.0 - 14.0 V\n' +
          '• Tegangan Pengisian Normal Bodi (Bebas B1133): 9.5 - 15.5 V\n' +
          '• Ground Utama BCM (G30-10 & G32-39): < 1.0 Ohm ke titik massa pilar dashboard',
        icm:
          '[SPESIFIKASI STANDAR IMMOBILIZER CONTROL MODULE / ICM (Vol 2 Bab 10C Hal. 785)]\n' +
          '• Suplai Daya +B ICM (G24-01) & IG1 ON (G24-04): 10.0 - 14.0 V\n' +
          '• Komunikasi Serial ICM ↔ ECM (G24-02 & G24-03): Kontinuitas < 2.0 Ohm, bebas koslet ke +B/Ground\n' +
          '• Ground ICM (G24-07): < 1.0 Ohm',
        kscm:
          '[SPESIFIKASI STANDAR KEYLESS START CONTROL MODULE / KSCM (Vol 2 Bab 10E Hal. 803-804)]\n' +
          '• Suplai Daya +B KSCM (G44-01) & IG1 ON (G44-08): 10.0 - 14.0 V\n' +
          '• Tegangan Baterai Remote Keyless (CR2032): ≥ 2.8 V\n' +
          '• Ground Utama KSCM (G44-16): < 1.0 Ohm'
      };
      if (moduleStdMap[effMod]) {
        summaryParts.push(moduleStdMap[effMod]);
      } else if (sensorKw === 'can') {
        summaryParts.push(
          '[SPESIFIKASI JARINGAN KOMUNIKASI CAN BUS (ECM E23 / TCM E92 / ABS E03 / BCM G32)]\n' +
          '• Tegangan CAN High (WHT/RED): 2.5 - 3.6 V (Pulsa Data Aktif)\n' +
          '• Tegangan CAN Low (RED / BLU): 1.6 - 2.5 V (Pulsa Data Aktif)\n' +
          '• Tahanan Terminasi Total Bus CAN (Aki Dilepas): 54 - 66 Ohm (2 Resistor 120Ω Paralel)'
        );
      }
    }

    // 3. BLOK JALUR WIRING, PINOUT KONEKTOR MODUL & WARNA KABEL BUKU MANUAL
    if (primaryCatEntry && Array.isArray(primaryCatEntry.wiring_pinout) && primaryCatEntry.wiring_pinout.length > 0) {
      const dtcPins = primaryCatEntry.wiring_pinout.slice(0, 8);
      const firstPinPrefix = String(dtcPins[0].pin || '').split('-')[0].trim().toUpperCase();
      const matchedWd = wiringDiagrams.find(
        (w) => firstPinPrefix && String(w.ecu_connector_code || '').toUpperCase().includes(firstPinPrefix)
      );
      const connTitle = matchedWd ? matchedWd.ecu_connector_code : `Konektor Modul ${firstPinPrefix || 'JB420'}`;
      const pinPreview = dtcPins
        .map((p) => `• ${p.pin || '-'}: ${p.wire_color || '-'} — ${p.function || p.signal || '-'}`)
        .join('\n');
      const groundNote = (matchedWd && matchedWd.ground_locations)
        ? `\n• Titik Massa (Ground): ${matchedWd.ground_locations}`
        : '';
      summaryParts.push(
        `[JALUR WIRING & PINOUT BUKU MANUAL — DTC ${primaryCatEntry.code} (${connTitle})]\n${pinPreview}${groundNote}`
      );
    } else if (wiringDiagrams.length > 0) {
      let matchedWd = null;
      let matchedPins = [];
      const moduleConnMap = {
        abs: 'E03', tcm: 'E92', hvac: 'G52', sdm: 'G47', bcm: 'G30', icm: 'G24', kscm: 'G44'
      };
      if (moduleConnMap[moduleKw]) {
        const targetConn = moduleConnMap[moduleKw];
        matchedWd = wiringDiagrams.find((w) => String(w.ecu_connector_code || '').toUpperCase().includes(targetConn));
        if (matchedWd) matchedPins = matchedWd.pinouts.slice(0, 8);
      }
      if (!matchedWd && sensorKw) {
        const kwAliasesMap = {
          fan: ['radiator', 'cooling fan', 'e23-46', 'e23-47', 'c37-24', 'c37-57'],
          maf: ['maf', 'intake air', 'air flow', 'c37-26', 'c37-25', 'c37-27', 'c37-57'],
          o2: ['o2', 'ho2s', 'oxygen', 'heater', 'e23-50', 'e23-49', 'c37-65', 'c37-38', 'c37-37', 'c37-57'],
          ect: ['ect', 'coolant', 'water temp', 'c37-24', 'c37-57'],
          map: ['map', 'manifold', 'c37-55', 'c37-14', 'c37-57'],
          ckp: ['ckp', 'crank', 'cmp', 'cam', 'c37-51', 'c37-36', 'c37-52'],
          cmp: ['cmp', 'cam', 'ckp', 'c37-52'],
          tps: ['tps', 'throttle', 'etcs', 'vta', 'c37-53', 'c37-54', 'c37-40'],
          app: ['app', 'e23-55', 'e23-56', 'e23-52', 'e23-53'],
          injector: ['injektor', 'injector', 'c37-60', 'c37-59', 'c37-58', 'c37-44'],
          fuel_pump: ['fuel pump', 'pompa bensin', 'e23-45'],
          evap: ['evap', 'canister', 'purge', 'c37-31'],
          egr: ['egr', 'c37-18', 'c37-19', 'c37-04', 'c37-05'],
          can: ['can ', 'komunikasi can', 'e23-04', 'e23-19', 'e03-06', 'e92-17'],
          coil: ['coil', 'ignition', 'igt', 'c37-33', 'c37-34', 'c37-47', 'c37-48'],
          ignition: ['coil', 'ignition', 'igt', 'c37-33', 'c37-34', 'c37-47', 'c37-48']
        };
        const aliases = kwAliasesMap[sensorKw] || [sensorKw];
        for (let i = wiringDiagrams.length - 1; i >= 0; i--) {
          const wd = wiringDiagrams[i];
          const pins = wd.pinouts.filter((p) => {
            const hay = `${p.pin_code} ${p.function}`.toLowerCase();
            return aliases.some((k) => hay.includes(k));
          });
          if (pins.length > 0) {
            matchedWd = wd;
            matchedPins = pins;
            break;
          }
        }
      }
      if (!matchedWd && (sensorKw || moduleKw || dtcDetails.length > 0)) {
        matchedWd = wiringDiagrams.find(
          (w) => String(w.ecu_connector_code || '').includes('C37') && String(w.ecu_connector_code || '').includes('E23')
        ) || wiringDiagrams[0];
        if (matchedWd) matchedPins = matchedWd.pinouts.slice(0, 6);
      }
      if (matchedWd && matchedPins.length > 0) {
        const pinPreview = matchedPins
          .slice(0, 8)
          .map((p) => `• ${p.pin_code}: ${p.wire_color} — ${p.function}`)
          .join('\n');
        summaryParts.push(
          `[JALUR WIRING & PINOUT MODUL (${matchedWd.ecu_connector_code})]\n${pinPreview}\n• Titik Massa (Ground): ${matchedWd.ground_locations}`
        );
      }
    }

    // 4. JIKA BELUM ADA RINGKASAN DTC/SENSOR, CARI DI 1.381 POTONGAN BUKU MANUAL VOL 1 & VOL 2
    const manualChunks = retrieveRepairManuals(store, query, 2);
    if (summaryParts.length === 0 && manualChunks.length > 0) {
      for (const ch of manualChunks) {
        const excerpt = String(ch.content_text || '').trim().slice(0, 650);
        summaryParts.push(
          `[KUTIPAN BUKU MANUAL RESMI — ${ch.section_title} (Relevansi ${ch.relevance_score}%)]\n${excerpt}`
        );
      }
    }

    const synthesized = summaryParts.length > 0
      ? summaryParts.join('\n\n')
      : 'Data spesifikasi, penyebab & solusi DTC, atau jalur wiring belum ditemukan untuk kata kunci tersebut. ' +
        'Masukkan kode DTC Buku Manual (contoh: P0480, C1021, P0756, B1502, B1017, B1133, P1614, KLS-11) ' +
        'atau nama sensor/modul (MAF, O2, ECT, TPS, CKP, ABS, TCM, HVAC, SRS Airbag, BCM, Immobilizer, Keyless).';

    return {
      query,
      detected_dtc_codes: detectedDtcs,
      synthesized_guidance: synthesized,
      matched_dtc_details: dtcDetails,
      matched_sensor_specs: sensorSpecs,
      matched_wiring_diagrams: wiringDiagrams,
      matched_manual_sections: manualChunks
    };
  }

  global.AgosManualSearch = {
    askRagAssistant,
    retrieveRepairManuals
  };
})(typeof window !== 'undefined' ? window : globalThis);
