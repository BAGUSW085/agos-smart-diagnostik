/**
 * AGOS Smart Diagnostik — Lapisan Offline API (offline-api.js)
 * ============================================================
 * Menggantikan seluruh panggilan `fetch(API_BASE...)` dan `fetch('/health')`
 * dengan eksekusi lokal 100% offline di perangkat Android tanpa server.
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

  async function offlineFetch(url, options = {}) {
    const path = String(url || '').trim();
    const method = String(options.method || 'GET').toUpperCase();
    let bodyObj = {};
    if (options.body) {
      try {
        bodyObj = typeof options.body === 'string' ? JSON.parse(options.body) : options.body;
      } catch (_) {
        bodyObj = {};
      }
    }

    try {
      // 1. GET /health
      if (path === '/health' || path.endsWith('/health')) {
        return makeJsonResponse({
          status: 'healthy',
          service: 'Mode Offline (Database Lokal Aktif)',
          version: '1.2.0-offline',
          jb420_catalog_loaded: true
        });
      }

      // 2. POST /api/v1/diagnostics/search-case
      if (path.endsWith('/diagnostics/search-case') && method === 'POST') {
        const result = await global.AgosDiagnosticEngine.searchWeightedCases(bodyObj);
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

      // 5. DELETE /api/v1/diagnostics/cases/{id}
      const delMatch = path.match(/\/diagnostics\/cases\/(\d+)$/);
      if (delMatch && method === 'DELETE') {
        const res = await global.AgosDataStore.deleteCaseById(delMatch[1]);
        return makeJsonResponse(res, 200);
      }

      // 6. POST /api/v1/manuals/ask-assistant
      if (path.endsWith('/manuals/ask-assistant') && method === 'POST') {
        const res = await global.AgosManualSearch.askRagAssistant(bodyObj);
        return makeJsonResponse(res, 200);
      }

      return makeJsonResponse({ detail: 'Endpoint offline tidak dikenali: ' + path }, 404);
    } catch (err) {
      return makeJsonResponse({ detail: err && err.message ? err.message : String(err) }, 500);
    }
  }

  global.offlineFetch = offlineFetch;
})(typeof window !== 'undefined' ? window : globalThis);
