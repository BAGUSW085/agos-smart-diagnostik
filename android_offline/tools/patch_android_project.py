"""
Patch Proyek Android Capacitor (`MainActivity.java`, `AndroidManifest.xml`,
`build.gradle`, Ikon Launcher Adaptive/Legacy/Round & Splash Screen)
==========================================================================
Dipanggil otomatis oleh GitHub Actions setelah `npx cap sync android` untuk:
1. Menambahkan native `@JavascriptInterface` (`window.AgosNative.setOrientation`)
   pada `MainActivity.java` agar tombol "Horizontal / Vertikal" memutar layar instan.
2. Memastikan `AndroidManifest.xml` mendukung orientasi mulus (`resizeableActivity`).
3. Mengganti seluruh ikon launcher APK (`mipmap-*`: `ic_launcher.png`,
   `ic_launcher_round.png`, `ic_launcher_foreground.png`, `ic_launcher_background.xml`)
   dan `splash.png` menggunakan logo resmi AGOS Smart Diagnostik (`www/icon-512.png`)
   dengan latar `#131A2C` agar rapi tanpa potongan di seluruh tipe HP Android.
4. Memperbarui `versionCode` (200) & `versionName` ("2.0.0").
"""

from pathlib import Path
import re

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ANDROID_DIR = ROOT_DIR / "android_offline" / "android"
RES_DIR = ANDROID_DIR / "app" / "src" / "main" / "res"
MANIFEST_PATH = ANDROID_DIR / "app" / "src" / "main" / "AndroidManifest.xml"
BUILD_GRADLE_PATH = ANDROID_DIR / "app" / "build.gradle"
JAVA_SRC_DIR = ANDROID_DIR / "app" / "src" / "main" / "java"
LOGO_SRC_512 = ROOT_DIR / "android_offline" / "www" / "icon-512.png"
LOGO_SRC_1024 = ROOT_DIR / "android_offline" / "www" / "icon-1024.png"

ICON_BG_HEX = "#131A2C"
ICON_BG_RGB = (19, 26, 44)

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
    if "android:resizeableActivity" not in manifest:
        manifest = manifest.replace(
            "<activity",
            '<activity\n            android:resizeableActivity="true"',
            1,
        )
    MANIFEST_PATH.write_text(manifest, encoding="utf-8")
    print("[SUKSES] AndroidManifest.xml diverifikasi untuk dukungan orientasi Horizontal & Vertikal")


def patch_version_gradle() -> None:
    if not BUILD_GRADLE_PATH.exists():
        return
    txt = BUILD_GRADLE_PATH.read_text(encoding="utf-8")
    txt = re.sub(r"versionCode\s+\d+", "versionCode 200", txt, count=1)
    txt = re.sub(r'versionName\s+"[^"]+"', 'versionName "2.0.0"', txt, count=1)
    BUILD_GRADLE_PATH.write_text(txt, encoding="utf-8")
    print("[SUKSES] build.gradle diperbarui ke versionCode 200 / versionName 2.0.0")


def patch_launcher_icons_and_splash() -> None:
    from PIL import Image, ImageDraw

    logo_path = LOGO_SRC_1024 if LOGO_SRC_1024.exists() else LOGO_SRC_512
    if not logo_path.exists():
        raise FileNotFoundError(f"File logo sumber tidak ditemukan: {logo_path}")

    src_img = Image.open(logo_path).convert("RGBA")

    # 1. Generate seluruh ukuran mipmap (ic_launcher, ic_launcher_round, ic_launcher_foreground)
    densities = {
        "mipmap-mdpi": (48, 108),
        "mipmap-hdpi": (72, 162),
        "mipmap-xhdpi": (96, 216),
        "mipmap-xxhdpi": (144, 324),
        "mipmap-xxxhdpi": (192, 432),
    }

    for folder, (icon_px, fg_px) in densities.items():
        d_path = RES_DIR / folder
        d_path.mkdir(parents=True, exist_ok=True)

        # Legacy full-bleed square icon
        sq = src_img.resize((icon_px, icon_px), Image.Resampling.LANCZOS)
        sq.save(d_path / "ic_launcher.png", "PNG")

        # Circular masked round icon
        mask = Image.new("L", (icon_px, icon_px), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, icon_px - 1, icon_px - 1), fill=255)
        rnd = Image.new("RGBA", (icon_px, icon_px), (0, 0, 0, 0))
        rnd.paste(sq, (0, 0), mask)
        rnd.save(d_path / "ic_launcher_round.png", "PNG")

        # Adaptive icon foreground (logo diletakkan di zona aman 76% di atas latar transparan / serasi)
        fg_canvas = Image.new("RGBA", (fg_px, fg_px), (*ICON_BG_RGB, 255))
        inner_px = int(round(fg_px * 0.76))
        inner = src_img.resize((inner_px, inner_px), Image.Resampling.LANCZOS)
        offset = (fg_px - inner_px) // 2
        fg_canvas.paste(inner, (offset, offset), inner)
        fg_canvas.save(d_path / "ic_launcher_foreground.png", "PNG")

    # 2. Set warna latar adaptive icon agar 100% menyatu dengan tepi logo (#131A2C)
    values_dir = RES_DIR / "values"
    values_dir.mkdir(parents=True, exist_ok=True)
    bg_xml = values_dir / "ic_launcher_background.xml"
    bg_xml.write_text(
        f'<?xml version="1.0" encoding="utf-8"?>\n'
        f'<resources>\n'
        f'    <color name="ic_launcher_background">{ICON_BG_HEX}</color>\n'
        f'</resources>\n',
        encoding="utf-8",
    )

    # 3. Hapus vector default Capacitor (`drawable*/ic_launcher_foreground*.xml`) & arahkan Adaptive Icon (API 26+)
    #    langsung ke PNG resolusi tinggi `@mipmap/ic_launcher_foreground` + `@color/ic_launcher_background`!
    removed_defaults = 0
    for old_fg in list(RES_DIR.rglob("ic_launcher_foreground*.xml")) + list(RES_DIR.rglob("$ic_launcher_foreground*.xml")):
        try:
            old_fg.unlink()
            removed_defaults += 1
        except Exception:
            pass

    vec_bg = RES_DIR / "drawable" / "ic_launcher_background.xml"
    if vec_bg.exists():
        vec_bg.write_text(
            f'<?xml version="1.0" encoding="utf-8"?>\n'
            f'<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">\n'
            f'    <solid android:color="{ICON_BG_HEX}" />\n'
            f'</shape>\n',
            encoding="utf-8",
        )

    anydpi_dir = RES_DIR / "mipmap-anydpi-v26"
    anydpi_dir.mkdir(parents=True, exist_ok=True)
    adaptive_xml = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '    <background android:drawable="@color/ic_launcher_background" />\n'
        '    <foreground android:drawable="@mipmap/ic_launcher_foreground" />\n'
        '</adaptive-icon>\n'
    )
    (anydpi_dir / "ic_launcher.xml").write_text(adaptive_xml, encoding="utf-8")
    (anydpi_dir / "ic_launcher_round.xml").write_text(adaptive_xml, encoding="utf-8")
    print(f"[SUKSES] Adaptive Icon API 26+ diarahkan ke @mipmap/ic_launcher_foreground (dihapus {removed_defaults} vector default)")

    # 4. Perbarui seluruh file splash.png bawaan Capacitor dengan logo baru di tengah latar #131A2C
    splash_count = 0
    for splash_file in RES_DIR.rglob("splash.png"):
        try:
            with Image.open(splash_file) as existing:
                w, h = existing.size
            canvas = Image.new("RGBA", (w, h), (*ICON_BG_RGB, 255))
            logo_side = max(96, int(min(w, h) * 0.44))
            resized_logo = src_img.resize((logo_side, logo_side), Image.Resampling.LANCZOS)
            canvas.paste(resized_logo, ((w - logo_side) // 2, (h - logo_side) // 2), resized_logo)
            canvas.convert("RGB").save(splash_file, "PNG")
            splash_count += 1
        except Exception as exc:
            print(f"[WARN] Lewati splash {splash_file}: {exc}")

    print(f"[SUKSES] Ikon Launcher (5 densitas + Adaptive + Round) & {splash_count} Splash Screen diperbarui dari {logo_path.name}")


if __name__ == "__main__":
    patch_main_activity()
    patch_manifest()
    patch_version_gradle()
    patch_launcher_icons_and_splash()
