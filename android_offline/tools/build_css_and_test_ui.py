"""
Build Local Offline CSS (app.css) & Uji Responsivitas Mobile + Visual Integrity
===============================================================================
1. Mengompilasi seluruh kelas Tailwind CSS dari `www/index.html` dan `www/js/*.js`
   ditambah aturan mobile & landscape dari `src/input.css` menjadi `www/css/app.css`.
2. Menguji tampilan `www/index.html` menggunakan Edge headless dengan `--window-size`
   asli pada ukuran layar HP Portrait (360x800, 393x800, 412x800) dan Landscape
   Horizontal (800x380) untuk memverifikasi:
   - 0 overflow horizontal (`scrollWidth <= clientWidth`) di seluruh 4 tab
   - Seluruh tombol `#man-pill-*` tampil horizontal (tinggi <= 48px, lebar >= 70px)
   - Seluruh ke-4 SVG simulasi muat penuh 100% tanpa geser samping.
"""

from pathlib import Path
import json
import re
import subprocess
import urllib.request

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
OFFLINE_DIR = ROOT_DIR / "android_offline"
WWW_DIR = OFFLINE_DIR / "www"
EDGE_BIN = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")


def build_offline_css() -> None:
    tw_script_url = "https://cdn.tailwindcss.com/3.4.14"
    req = urllib.request.Request(tw_script_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        tw_js = resp.read().decode("utf-8")

    html_text = (WWW_DIR / "index.html").read_text(encoding="utf-8")
    js_texts = "\n".join(
        p.read_text(encoding="utf-8")
        for p in (WWW_DIR / "js").glob("*.js")
        if p.name != "embedded-data.js"
    )
    custom_css = (OFFLINE_DIR / "src" / "input.css").read_text(encoding="utf-8")
    custom_css = re.sub(r"@tailwind\s+\w+;\s*", "", custom_css)

    body_match = re.search(r"<body[^>]*>(.*)</body>", html_text, flags=re.S | re.I)
    body_inner = body_match.group(1) if body_match else html_text
    body_no_scripts = re.sub(r"<script\b[^>]*>.*?</script>", "", body_inner, flags=re.S | re.I)

    dynamic_classes = (
        "sm:grid-cols-2 sm:grid-cols-3 sm:grid-cols-4 md:grid-cols-2 "
        "w-6 h-6 sm:w-7 sm:h-7 h-12 sm:h-14 text-[13px] whitespace-normal "
        "col-span-1 col-span-2 grid-cols-3 grid-cols-2 md:col-span-5 md:col-span-6 "
        "md:col-span-7 md:col-span-8 md:col-span-12 md:grid-cols-2 md:grid-cols-12 md:flex-row"
    )

    tmp_html = OFFLINE_DIR / "tools" / "_tw_extract.html"
    tmp_html.write_text(
        f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script>{tw_js}</script>
<script>
tailwind.config = {{
  darkMode: 'class',
  theme: {{
    extend: {{
      colors: {{
        brand: {{
          50: '#f0f7ff', 100: '#e0effe', 300: '#7dd3fc', 400: '#38bdf8',
          500: '#0284c7', 600: '#0369a1', 700: '#075985', 800: '#0c4a6e',
          900: '#0f172a', 950: '#082f49'
        }},
        accent: {{ 400: '#f59e0b', 500: '#d97706', 600: '#b45309' }}
      }}
    }}
  }}
}};
</script>
</head>
<body class="bg-slate-900 text-slate-100">
{body_no_scripts}
<div class="hidden {dynamic_classes}">{js_texts}</div>
</body>
</html>""",
        encoding="utf-8",
    )

    try:
        file_url = tmp_html.resolve().as_uri()
        proc = subprocess.run(
            [
                str(EDGE_BIN),
                "--headless=new",
                "--disable-gpu",
                "--virtual-time-budget=3000",
                "--dump-dom",
                file_url,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=True,
        )
        styles = re.findall(r"<style[^>]*>(.*?)</style>", proc.stdout, flags=re.S)
        tw_compiled = "\n".join(styles).strip()
        if len(tw_compiled) < 5000:
            raise RuntimeError("Hasil ekstraksi CSS terlalu pendek.")
        final_css = (
            "/* AGOS Smart Diagnostik — Offline Compiled Tailwind v3.4.14 + Mobile & Landscape Rules */\n"
            + tw_compiled
            + "\n\n"
            + custom_css
        )
        out_path = WWW_DIR / "css" / "app.css"
        out_path.write_text(final_css, encoding="utf-8")
        print(f"[SUKSES] www/css/app.css berhasil dibangun ({len(final_css)/1024:.2f} KB)")
    finally:
        if tmp_html.exists():
            tmp_html.unlink()


def probe_single_viewport(orig_html: str, width: int, height: int) -> dict:
    test_html = WWW_DIR / "_viewport_test.html"
    probe_script = f"""
<script>
window.addEventListener('load', async () => {{
  await new Promise(r => setTimeout(r, 250));
  await loadSample('K001');
  await new Promise(r => setTimeout(r, 150));

  const w = window.innerWidth || {width};
  const report = {{ innerW: w, innerH: window.innerHeight, tabs: {{}}, pills: {{}}, svgs: {{}} }};

  for (const t of ['diagnostic', 'database', 'manuals', 'tools']) {{
    switchTab(t);
    if (t === 'manuals') renderManualComponentSimulator();
    await new Promise(r => setTimeout(r, 120));
    const sw = document.documentElement.scrollWidth;
    const cw = document.documentElement.clientWidth;
    const offenders = [];
    if (sw > cw + 1) {{
      document.querySelectorAll('#tab-content-' + t + ' *, header *').forEach(el => {{
        const r = el.getBoundingClientRect();
        if (r.right > cw + 2 && r.width > 0 && r.height > 0 && el.children.length <= 2) {{
          offenders.push({{
            tag: el.tagName,
            id: el.id || '',
            cls: String(el.className || '').slice(0, 50),
            right: Math.round(r.right),
            txt: (el.textContent || '').trim().slice(0, 35)
          }});
        }}
      }});
    }}
    report.tabs[t] = {{
      clientWidth: cw,
      scrollWidth: sw,
      overflowX: sw > cw + 1,
      offenders: offenders.slice(0, 8)
    }};

    if (t === 'manuals') {{
      document.querySelectorAll('[id^="man-pill-"]').forEach(btn => {{
        const r = btn.getBoundingClientRect();
        report.pills[btn.id] = {{ width: Math.round(r.width), height: Math.round(r.height), text: btn.textContent }};
      }});
      ['man-workflow-loop-svg', 'man-component-anatomy-svg', 'man-engine-bay-svg'].forEach(id => {{
        const svg = document.getElementById(id);
        const wrap = svg ? svg.parentElement : null;
        if (svg && wrap) {{
          const sr = svg.getBoundingClientRect();
          report.svgs[id] = {{
            svgW: Math.round(sr.width),
            wrapInnerW: Math.round(wrap.clientWidth),
            viewBox: svg.getAttribute('viewBox'),
            fitsFull: sr.width <= wrap.clientWidth + 1 && sr.height > 70
          }};
        }}
      }});
    }}
    if (t === 'diagnostic') {{
      const svg = document.getElementById('sim-wiring-svg');
      const wrap = svg ? svg.parentElement : null;
      if (svg && wrap) {{
        const sr = svg.getBoundingClientRect();
        report.svgs['sim-wiring-svg'] = {{
          svgW: Math.round(sr.width),
          wrapInnerW: Math.round(wrap.clientWidth),
          viewBox: svg.getAttribute('viewBox'),
          fitsFull: sr.width <= wrap.clientWidth + 1 && sr.height > 70
        }};
      }}
    }}
  }}
  const el = document.createElement('pre');
  el.id = 'agos-viewport-report';
  el.textContent = JSON.stringify(report);
  document.body.appendChild(el);
}});
</script>
"""
    test_html.write_text(orig_html.replace("</body>", probe_script + "\n</body>"), encoding="utf-8")
    try:
        proc = subprocess.run(
            [
                str(EDGE_BIN),
                "--headless=new",
                "--disable-gpu",
                f"--window-size={width},{height}",
                "--virtual-time-budget=4500",
                "--dump-dom",
                test_html.resolve().as_uri(),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=True,
        )
        m = re.search(r'<pre id="agos-viewport-report">(.*?)</pre>', proc.stdout, flags=re.S)
        if not m:
            raise RuntimeError(f"Gagal membaca laporan viewport {width}x{height}")
        return json.loads(m.group(1))
    finally:
        if test_html.exists():
            test_html.unlink()


def verify_mobile_and_layout() -> None:
    print("\n=== UJI TAMPILAN MOBILE PORTRAIT (360, 393, 412px) & LANDSCAPE (800x380px) ===")
    orig_html = (WWW_DIR / "index.html").read_text(encoding="utf-8")

    targets = [(360, 800), (393, 800), (412, 800), (800, 380)]
    for width, height in targets:
        rep = probe_single_viewport(orig_html, width, height)
        mode_lbl = "Landscape" if width > height else "Portrait"
        print(f"Layar {width}x{height}px ({mode_lbl} | actual innerW={rep['innerW']}px):")
        for tab_name, info in rep["tabs"].items():
            status = "LULUS (Rapi, 0 Scroll Samping)" if not info["overflowX"] else f"OVERFLOW! ({info['offenders']})"
            print(
                f"  - Tab {tab_name:<12}: clientW={info['clientWidth']}px, "
                f"scrollW={info['scrollWidth']}px -> {status}"
            )
        if width == 360 or width == 800:
            print(f"  [Cek Tombol Komponen Sensor @ {width}px]:")
            for pid, pinfo in rep["pills"].items():
                ok = pinfo["height"] <= 48 and pinfo["width"] >= 70
                print(f"    - {pid:<18}: {pinfo['width']}x{pinfo['height']}px ({pinfo['text']}) -> {'LULUS Horizontal' if ok else 'GAGAL!'}")
            print(f"  [Cek Gambar Simulasi SVG Full-View @ {width}px]:")
            for sid, sinfo in rep["svgs"].items():
                print(f"    - {sid:<28}: svgW={sinfo['svgW']}px / wrapW={sinfo['wrapInnerW']}px, viewBox={sinfo['viewBox']} -> {'LULUS Full-View' if sinfo['fitsFull'] else 'GAGAL!'}")


if __name__ == "__main__":
    build_offline_css()
    verify_mobile_and_layout()
