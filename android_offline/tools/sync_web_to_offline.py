"""
Sinkronisasi Otomatis Web Dashboard (`backend/app/static/index.html`) ke APK Offline (`android_offline/www/index.html`)
========================================================================================================================
Menjaga 100% paritas fitur antara Web/PWA dan APK Android Offline:
- Mengganti Tailwind CDN & FontAwesome CDN dengan aset lokal (`css/fontawesome.min.css` & `css/app.css`)
- Memuat seluruh engine lokal offline (`embedded-data.js`, `data-store.js`, `engine.js`, `manual-search.js`,
  `offline-multi-model.js`, `offline-api.js`)
- Membelokkan seluruh panggilan `fetch('/api/v1/...')` & `fetch('/health')` ke `offlineFetch` secara otomatis
- Mempertahankan tombol orientasi layar Horizontal/Vertikal & handler tombol Back Android!
"""

from pathlib import Path
import re

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
WEB_HTML = ROOT_DIR / "backend" / "app" / "static" / "index.html"
OFFLINE_HTML = ROOT_DIR / "android_offline" / "www" / "index.html"

OFFLINE_SCRIPTS = """  <!-- AGOS Offline Local Engine Bundle (100% Tanpa Server) -->
  <script src="js/embedded-data.js"></script>
  <script src="js/data-store.js"></script>
  <script src="js/engine.js"></script>
  <script src="js/manual-search.js"></script>
  <script src="js/offline-multi-model.js"></script>
  <script src="js/offline-api.js"></script>
  <script>
    (function () {
      const _origFetch = window.fetch ? window.fetch.bind(window) : null;
      window.fetch = function (input, init) {
        const url = typeof input === 'string' ? input : (input && input.url) || '';
        if (url.startsWith('/api/v1') || url === '/health' || url.endsWith('/health')) {
          return window.offlineFetch(url, init);
        }
        return _origFetch ? _origFetch(input, init) : Promise.reject(new Error('Offline mode'));
      };
    })();
  </script>
"""

ORIENTATION_AND_BACK_JS = """
    // ---------- TOMBOL ORIENTASI LAYAR ANDROID & HANDLER TOMBOL BACK ----------
    let isHorizontalOrientation = false;
    function syncOrientationButtonUI() {
      const isLand = window.innerWidth > window.innerHeight;
      const lbl = document.getElementById('label-orientation');
      const icon = document.getElementById('icon-orientation');
      if (isLand) {
        if (lbl) lbl.textContent = 'Vertikal';
        if (icon) icon.classList.remove('rotate-90');
      } else {
        if (lbl) lbl.textContent = 'Horizontal';
        if (icon) icon.classList.add('rotate-90');
      }
    }

    function toggleAppOrientation() {
      const targetHorizontal = !(window.innerWidth > window.innerHeight || isHorizontalOrientation);
      isHorizontalOrientation = targetHorizontal;
      const vp = document.querySelector('meta[name="viewport"]');
      const hasNative = Boolean(window.AgosNative && typeof window.AgosNative.setOrientation === 'function');
      if (targetHorizontal) {
        if (hasNative) {
          try { window.AgosNative.setOrientation('landscape'); } catch (e) {}
        } else if (screen.orientation && typeof screen.orientation.lock === 'function') {
          screen.orientation.lock('landscape').catch(() => {});
        }
      } else {
        if (hasNative) {
          try { window.AgosNative.setOrientation('portrait'); } catch (e) {}
        } else if (screen.orientation && typeof screen.orientation.lock === 'function') {
          screen.orientation.lock('portrait').catch(() => {});
        }
      }
      if (vp) vp.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=3.0, user-scalable=yes, viewport-fit=cover');
      syncOrientationButtonUI();
      setTimeout(() => { renderManualComponentSimulator(); renderWiringSimulator(); }, 200);
    }

    window.addEventListener('resize', () => { syncOrientationButtonUI(); });
    window.addEventListener('orientationchange', () => { syncOrientationButtonUI(); });
    syncOrientationButtonUI();

    document.addEventListener('backbutton', (e) => {
      const modals = [
        ['modal-engine-picker', () => closeEnginePickerModal()],
        ['modal-admin-security', () => closeAdminSecurityModal()],
        ['modal-manual-importer', () => toggleModalManualImporter(false)],
        ['modal-new-case', () => toggleModalNewCase(false)]
      ];
      for (const [id, closer] of modals) {
        const el = document.getElementById(id);
        if (el && !el.classList.contains('hidden')) {
          closer();
          e.preventDefault();
          return;
        }
      }
    }, false);
"""


def sync() -> None:
    html = WEB_HTML.read_text(encoding="utf-8")

    # 1. Ganti title & icon path agar relatif (file:// / Capacitor WebView)
    html = html.replace('href="/static/icon-192.png"', 'href="icon-192.png"')
    html = html.replace('src="/static/icon-192.png"', 'src="icon-192.png"')
    html = html.replace('>App v2.0<', '>APK Offline v2.0<')
    html = html.replace('href="/manifest.json"', '')
    html = html.replace(
        "<title>AGOS SMART DIAGNOSTIK by Agos Corporation — Aplikasi Bengkel AI</title>",
        "<title>AGOS SMART DIAGNOSTIK — Aplikasi Android Offline Bengkel AI</title>",
    )

    # 2. Hapus CDN Tailwind + config script & FontAwesome CDN, ganti ke CSS lokal offline
    html = re.sub(
        r'<script\s+src="https://cdn\.tailwindcss\.com"[^>]*></script>\s*<script>[\s\S]*?tailwind\.config\s*=[\s\S]*?</script>',
        '<!-- Local Offline Compiled Tailwind CSS -->\n  <link rel="stylesheet" href="css/app.css">',
        html,
        count=1,
    )
    html = re.sub(
        r'<link\s+rel="stylesheet"\s+href="https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/[^"]+"[^>]*>',
        '<!-- Local Offline Font Awesome -->\n  <link rel="stylesheet" href="css/fontawesome.min.css">',
        html,
        count=1,
    )

    # 3. Ganti tombol Pasang App dengan tombol Orientasi Horizontal/Vertikal untuk APK Offline
    html = re.sub(
        r'<button type="button" onclick="toggleModalAppInstall\(true\)" id="btn-header-install-app"[\s\S]*?</button>',
        (
            '<button type="button" id="btn-toggle-orientation" onclick="toggleAppOrientation()" '
            'class="flex items-center gap-1.5 text-[11px] sm:text-xs font-semibold text-cyan-300 bg-cyan-950/80 '
            'hover:bg-cyan-900 border border-cyan-700/80 px-2.5 py-1.5 rounded-full shrink-0 active:scale-95 transition whitespace-nowrap" '
            'title="Putar Layar Horizontal / Vertikal">'
            '<i class="fa-solid fa-mobile-screen-button rotate-90 text-cyan-400" id="icon-orientation"></i>'
            '<span id="label-orientation">Horizontal</span></button>'
        ),
        html,
        count=1,
    )

    # 4. Hapus gambar QR CDN eksternal agar tidak panggil internet di mode offline (berhenti juga pada backtick & spasi!)
    html = re.sub(r'https://api\.qrserver\.com/[^"\'`\s]+', 'icon-192.png', html)

    # 5. Sisipkan bundle JS Offline sebelum <!-- JAVASCRIPT LOGIC CLIENT -->
    html = html.replace(
        "  <!-- JAVASCRIPT LOGIC CLIENT -->",
        OFFLINE_SCRIPTS + "\n  <!-- JAVASCRIPT LOGIC CLIENT -->",
        1,
    )

    # 6. Tambahkan orientation & Android back button handler sebelum </script> penutup terakhir
    last_script_end = html.rfind("</script>")
    if last_script_end != -1:
        html = html[:last_script_end] + ORIENTATION_AND_BACK_JS + "\n  " + html[last_script_end:]

    # 7. Lewati registrasi Service Worker pada Capacitor offline
    html = html.replace("if ('serviceWorker' in navigator)", "if (false && 'serviceWorker' in navigator)")

    OFFLINE_HTML.write_text(html, encoding="utf-8")
    print(f"[SUKSES] android_offline/www/index.html disinkronkan ({len(html)/1024:.1f} KB)")


if __name__ == "__main__":
    sync()
