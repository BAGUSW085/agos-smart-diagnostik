/**
 * AGOS Smart Diagnostik — Lapisan Offline API (offline-api.js)
 * ============================================================
 * Menggantikan seluruh panggilan `fetch(API_BASE...)` dan `fetch('/health')`
 * dengan eksekusi lokal 100% offline di perangkat Android tanpa server.
 * Mendukung Multi-Merek (Asia/Eropa/China), Modern DTC (Diesel/Turbo/EV),
 * Paket Manual Kustom (localStorage), serta PIN Kepala Bengkel & Backup/Restore.
 */
(function (global) {
  'use strict';

  function makeJsonResponse(data, status = 200) {
    const bodyStr = JSON.stringify(data);
    return {
      ok: status >= 200 && status < 300,
      status,
      json: async () => data,
      text: async () => bodyStr
    };
  }

  function readHeaderPin(options) {
    const h = (options && options.headers) || {};
    return h['X-Workshop-Pin'] || h['x-workshop-pin'] || '';
  }

  async function offlineFetch(url, options = {}) {
    const fullUrl = String(url || '').trim();
    const [path, queryStr] = fullUrl.split('?');
    const method = String(options.method || 'GET').toUpperCase();
    let bodyObj = {};
    if (options.body) {
      try {
        bodyObj = typeof options.body === 'string' ? JSON.parse(options.body) : options.body;
      } catch (_) {
        bodyObj = {};
      }
    }
    const mm = global.AgosOfflineMultiModel;

    try {
      // 1. GET /health
      if (path === '/health' || path.endsWith('/health')) {
        return makeJsonResponse({
          status: 'healthy',
          service: 'Mode Offline v2.0 (174 Mesin · Diesel/EV)',
          version: '2.0.0-offline',
          jb420_catalog_loaded: true
        });
      }

      // 2. POST /api/v1/diagnostics/search-case
      if (path.endsWith('/diagnostics/search-case') && method === 'POST') {
        const raw = await global.AgosDiagnosticEngine.searchWeightedCases(bodyObj);
        const result = mm ? mm.enhanceOfflineSearchResult(bodyObj, raw) : raw;
        return makeJsonResponse(result, 200);
      }

      // 3. GET /api/v1/diagnostics/cases
      if (path.endsWith('/diagnostics/cases') && method === 'GET') {
        const cases = await global.AgosDataStore.getAllCases();
        return makeJsonResponse(cases, 200);
      }

      // 4. POST /api/v1/diagnostics/cases
      if (path.endsWith('/diagnostics/cases') && method === 'POST') {
        const res = await global.AgosDataStore.addCase(bodyObj);
        return makeJsonResponse(res, 201);
      }

      // 5. DELETE /api/v1/diagnostics/cases/{id} (PIN Protected)
      const delMatch = path.match(/\/diagnostics\/cases\/(\d+)$/);
      if (delMatch && method === 'DELETE') {
        if (mm && !mm.verifyPin(readHeaderPin(options))) {
          return makeJsonResponse({ detail: 'PIN Kepala Bengkel diperlukan atau salah.' }, 401);
        }
        const res = await global.AgosDataStore.deleteCaseById(delMatch[1]);
        return makeJsonResponse(res, 200);
      }

      // 6. POST /api/v1/manuals/ask-assistant
      if (path.endsWith('/manuals/ask-assistant') && method === 'POST') {
        const res = await global.AgosManualSearch.askRagAssistant(bodyObj);
        if (mm && bodyObj.query) {
          const codes = String(bodyObj.query).toUpperCase().match(/[PCBU][0-9A-F]{4}/g) || [];
          const extra = [];
          codes.forEach((c) => {
            const mh = mm.lookupModernDtc(c, /diesel|2gd|2kd|4n15/i.test(bodyObj.query) ? 'Diesel' : 'Bensin');
            if (mh) {
              const opts = (mh.repair_options || []).slice(0, 3).map((o) => o.title).join(' | ');
              extra.push(`[KATALOG UNIVERSAL MODERN — ${mh.code}]\n• Deskripsi: ${mh.title_id}\n• Penyebab: ${mh.root_causes}\n• Opsi Perbaikan: ${opts}`);
            }
          });
          if (extra.length) {
            res.synthesized_guidance = extra.join('\n\n') + '\n\n' + (res.synthesized_guidance || '');
          }
        }
        return makeJsonResponse(res, 200);
      }

      // 7. GET /api/v1/manuals/vehicle-matrix
      if (path.endsWith('/manuals/vehicle-matrix') && method === 'GET' && mm) {
        const engines = mm.getEngineDirectory();
        const region_counts = { Asia: 0, Eropa: 0, China: 0 };
        engines.forEach((e) => {
          const r = e.region || 'Asia';
          region_counts[r] = (region_counts[r] || 0) + 1;
        });
        return makeJsonResponse({
          generations: mm.getGenerations(),
          installed_packs: mm.listAllPackSummaries(),
          engine_directory: engines,
          region_counts
        }, 200);
      }

      // 8. GET /api/v1/manuals/engine-catalog
      if (path.endsWith('/manuals/engine-catalog') && method === 'GET' && mm) {
        const params = new URLSearchParams(queryStr || '');
        const reg = (params.get('region') || '').toLowerCase();
        const q = (params.get('q') || '').toLowerCase();
        let list = mm.getEngineDirectory();
        if (reg && reg !== 'semua') list = list.filter((e) => (e.region || '').toLowerCase() === reg);
        if (q) {
          const qn = q.replace(/[^a-z0-9]/g, '');
          list = list.filter((e) => {
            const h = `${e.code} ${(e.aliases || []).join(' ')} ${e.brand} ${(e.models || []).join(' ')} ${e.desc}`.toLowerCase();
            return h.includes(q) || (qn && h.replace(/[^a-z0-9]/g, '').includes(qn));
          });
        }
        return makeJsonResponse({ total: list.length, engines: list }, 200);
      }

      // 9. POST /api/v1/manuals/resolve-vehicle
      if (path.endsWith('/manuals/resolve-vehicle') && method === 'POST' && mm) {
        const { appInfo } = mm.resolveVehicleApplicability(bodyObj.brand, bodyObj.model, bodyObj.year, bodyObj.engine_code);
        return makeJsonResponse(appInfo, 200);
      }

      // 10. POST /api/v1/manuals/packs/import (PIN Protected)
      if (path.endsWith('/manuals/packs/import') && method === 'POST' && mm) {
        if (!mm.verifyPin(readHeaderPin(options))) {
          return makeJsonResponse({ detail: 'PIN Kepala Bengkel diperlukan untuk mengimpor paket manual.' }, 401);
        }
        const saved = mm.saveCustomPack(bodyObj);
        return makeJsonResponse({ status: 'success', message: `Paket manual '${saved.title}' aktif di memori HP!`, pack: saved }, 201);
      }

      // 11. DELETE /api/v1/manuals/packs/{pack_id} (PIN Protected)
      const delPack = path.match(/\/manuals\/packs\/([^/]+)$/);
      if (delPack && method === 'DELETE' && mm) {
        if (!mm.verifyPin(readHeaderPin(options))) {
          return makeJsonResponse({ detail: 'PIN Kepala Bengkel diperlukan untuk menghapus paket manual.' }, 401);
        }
        const ok = mm.deleteCustomPack(decodeURIComponent(delPack[1]));
        return makeJsonResponse(ok ? { status: 'deleted' } : { detail: 'Tidak dapat menghapus paket ini.' }, ok ? 200 : 400);
      }

      // 12. POST /api/v1/manuals/packs/preview-pdf (Offline notice)
      if (path.endsWith('/manuals/packs/preview-pdf') && method === 'POST') {
        return makeJsonResponse({
          detail: 'Auto-Prescan PDF langsung memerlukan server web. Pada mode APK Offline, gunakan tombol "Salin Template Prompt AI" lalu impor file JSON hasil ekstraksinya.'
        }, 400);
      }

      // 13. ADMIN SECURITY & BACKUP / RESTORE
      if (path.endsWith('/admin/security-status') && method === 'GET' && mm) {
        return makeJsonResponse(mm.getSecurityStatus(), 200);
      }
      if (path.endsWith('/admin/verify-pin') && method === 'POST' && mm) {
        if (!mm.verifyPin(bodyObj.pin)) return makeJsonResponse({ detail: 'PIN Kepala Bengkel salah.' }, 401);
        return makeJsonResponse({ valid: true, is_default_pin: mm.getSecurityStatus().is_default_pin, message: 'Mode Kepala Bengkel aktif.' }, 200);
      }
      if (path.endsWith('/admin/change-pin') && method === 'POST' && mm) {
        const r = mm.changePin(bodyObj.current_pin, bodyObj.new_pin);
        return makeJsonResponse(r.ok ? { status: 'success', message: r.message } : { detail: r.detail }, r.ok ? 200 : r.status);
      }
      if (path.endsWith('/admin/backup') && method === 'GET' && mm) {
        if (!mm.verifyPin(readHeaderPin(options))) return makeJsonResponse({ detail: 'PIN Kepala Bengkel diperlukan.' }, 401);
        const cases = await global.AgosDataStore.getAllCases();
        const packs = mm.loadCustomPacks();
        return makeJsonResponse({
          backup_format: 'agos_smart_diagnostik_backup_v1',
          exported_at: new Date().toISOString(),
          total_cases: cases.length,
          total_custom_packs: packs.length,
          historical_cases: cases,
          custom_manual_packs: packs
        }, 200);
      }
      if (path.endsWith('/admin/restore') && method === 'POST' && mm) {
        if (!mm.verifyPin(readHeaderPin(options))) return makeJsonResponse({ detail: 'PIN Kepala Bengkel diperlukan.' }, 401);
        let addedCases = 0;
        const existing = await global.AgosDataStore.getAllCases();
        const existingCodes = new Set(existing.map((c) => c.case_code));
        for (const item of (bodyObj.historical_cases || [])) {
          if (item && item.case_code && !existingCodes.has(item.case_code)) {
            await global.AgosDataStore.addCase(item);
            existingCodes.add(item.case_code);
            addedCases++;
          }
        }
        let restoredPacks = 0;
        for (const p of (bodyObj.custom_manual_packs || [])) {
          if (p && p.brand && p.model) {
            mm.saveCustomPack(p);
            restoredPacks++;
          }
        }
        return makeJsonResponse({ status: 'success', added_cases: addedCases, restored_packs: restoredPacks, message: `Restore offline selesai: ${addedCases} kasus & ${restoredPacks} paket manual.` }, 200);
      }

      return makeJsonResponse({ detail: 'Endpoint offline tidak dikenali: ' + path }, 404);
    } catch (err) {
      return makeJsonResponse({ detail: err && err.message ? err.message : String(err) }, 500);
    }
  }

  global.offlineFetch = offlineFetch;
})(typeof window !== 'undefined' ? window : globalThis);
