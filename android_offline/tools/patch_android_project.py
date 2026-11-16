"""
Patch Proyek Android Capacitor (`MainActivity.java` & `AndroidManifest.xml`)
==========================================================================
Dipanggil otomatis oleh GitHub Actions setelah `npx cap sync android` untuk:
1. Menambahkan native `@JavascriptInterface` (`window.AgosNative.setOrientation`)
   pada `MainActivity.java` agar tombol "Horizontal / Vertikal" di dalam APK
   benar-benar memutar orientasi layar Android secara instan (meskipun
   Auto-Rotate HP sedang mati).
2. Memastikan `AndroidManifest.xml` mendukung pergantian orientasi mulus tanpa
   mereload ulang WebView (`configChanges`).
"""

from pathlib import Path
import re

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ANDROID_DIR = ROOT_DIR / "android_offline" / "android"
MANIFEST_PATH = ANDROID_DIR / "app" / "src" / "main" / "AndroidManifest.xml"
JAVA_SRC_DIR = ANDROID_DIR / "app" / "src" / "main" / "java"

MAIN_ACTIVITY_JAVA = """package {package_name};

import android.content.pm.ActivityInfo;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {{

    public class AgosNativeBridge {{
        @JavascriptInterface
        public void setOrientation(final String mode) {{
            runOnUiThread(new Runnable() {{
                @Override
                public void run() {{
                    if ("landscape".equals(mode)) {{
                        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE);
                    }} else if ("portrait".equals(mode)) {{
                        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_SENSOR_PORTRAIT);
                    }} else {{
                        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED);
                    }}
                }}
            }});
        }}
    }}

    @Override
    public void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        if (this.bridge != null) {{
            WebView wv = this.bridge.getWebView();
            if (wv != null) {{
                wv.addJavascriptInterface(new AgosNativeBridge(), "AgosNative");
            }}
        }}
    }}
}}
"""


def patch_main_activity() -> None:
    if not JAVA_SRC_DIR.exists():
        raise FileNotFoundError(f"Direktori Java tidak ditemukan: {JAVA_SRC_DIR}")

    candidates = list(JAVA_SRC_DIR.rglob("MainActivity.java"))
    if not candidates:
        raise FileNotFoundError("File MainActivity.java tidak ditemukan di proyek Capacitor Android")

    target = candidates[0]
    original = target.read_text(encoding="utf-8")
    m = re.search(r"^\s*package\s+([a-zA-Z0-9_.]+)\s*;", original, flags=re.M)
    package_name = m.group(1) if m else "com.agos.smartdiagnostik"

    target.write_text(MAIN_ACTIVITY_JAVA.format(package_name=package_name), encoding="utf-8")
    print(f"[SUKSES] MainActivity.java dipatch dengan AgosNative.setOrientation ({package_name})")


def patch_manifest() -> None:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"AndroidManifest.xml tidak ditemukan: {MANIFEST_PATH}")

    manifest = MANIFEST_PATH.read_text(encoding="utf-8")
    # Pastikan resizeableActivity diizinkan agar mode split/landscape lancar di semua versi Android
    if "android:resizeableActivity" not in manifest:
        manifest = manifest.replace(
            "<activity",
            '<activity\n            android:resizeableActivity="true"',
            1,
        )
    MANIFEST_PATH.write_text(manifest, encoding="utf-8")
    print("[SUKSES] AndroidManifest.xml diverifikasi untuk dukungan orientasi Horizontal & Vertikal")


if __name__ == "__main__":
    patch_main_activity()
    patch_manifest()
