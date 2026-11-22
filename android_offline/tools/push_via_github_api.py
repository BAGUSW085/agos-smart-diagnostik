"""
Push Branch `apk-offline` ke GitHub via Git Data REST API (Anti-HTTP 408 Timeout)
=================================================================================
Mengunggah setiap file pada branch `apk-offline` satu per satu dalam potongan
JSON kecil melalui GitHub REST API agar tidak terputus oleh batas upload Wi-Fi
(`HTTP 408 curl 22` pada `git send-pack`).
"""

from pathlib import Path
import base64
import json
import subprocess
import urllib.error
import urllib.request

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
REPO = "BAGUSW085/agos-smart-diagnostik"
API_BASE = f"https://api.github.com/repos/{REPO}"

FILES_TO_PUSH = [
    "PROMPT_APK_OFFLINE.md",
    "PROGRES_APK_OFFLINE.md",
    "backend/app/db/seed_historical_cases.py",
    "backend/app/services/vehicle_applicability.py",
    "backend/app/services/modern_dtc_catalog.py",
    ".github/workflows/build_apk_offline.yml",
    "android_offline/CARA_INSTAL_APK.md",
    "android_offline/capacitor.config.json",
    "android_offline/package.json",
    "android_offline/tailwind.config.js",
    "android_offline/src/input.css",
    "android_offline/tools/export_data.py",
    "android_offline/tools/verify_engine.py",
    "android_offline/tools/build_css_and_test_ui.py",
    "android_offline/tools/sync_web_to_offline.py",
    "android_offline/tools/patch_android_project.py",
    "android_offline/tools/push_via_github_api.py",
    "android_offline/www/index.html",
    "android_offline/www/icon-192.png",
    "android_offline/www/icon-512.png",
    "android_offline/www/static/icon-192.png",
    "android_offline/www/static/icon-512.png",
    "android_offline/www/css/app.css",
    "android_offline/www/js/data-store.js",
    "android_offline/www/js/engine.js",
    "android_offline/www/js/manual-search.js",
    "android_offline/www/js/offline-multi-model.js",
    "android_offline/www/js/offline-api.js",
]


def get_github_token() -> str:
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True,
        text=True,
        check=True,
    )
    creds = dict(
        line.split("=", 1) for line in p.stdout.strip().splitlines() if "=" in line
    )
    return creds["password"]


def gh_request(method: str, path: str, token: str, payload: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "AGOS-Offline-Deployer",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    token = get_github_token()
    print("[1/4] Mengambil commit terakhir branch main di GitHub...")
    main_ref = gh_request("GET", "/git/ref/heads/main", token)
    base_commit_sha = main_ref["object"]["sha"]
    base_commit = gh_request("GET", f"/git/commits/{base_commit_sha}", token)
    base_tree_sha = base_commit["tree"]["sha"]
    print(f"      Base commit: {base_commit_sha[:7]} (tree: {base_tree_sha[:7]})")

    print(f"[2/4] Mengunggah {len(FILES_TO_PUSH)} file satu per satu (Anti-Timeout)...")
    tree_items = []
    for idx, rel_path in enumerate(FILES_TO_PUSH, start=1):
        full_path = ROOT_DIR / rel_path
        raw_bytes = full_path.read_bytes()
        b64_content = base64.b64encode(raw_bytes).decode("ascii")
        blob = gh_request(
            "POST",
            "/git/blobs",
            token,
            {"content": b64_content, "encoding": "base64"},
        )
        tree_items.append(
            {
                "path": rel_path,
                "mode": "100644",
                "type": "blob",
                "sha": blob["sha"],
            }
        )
        print(f"      [{idx:02d}/{len(FILES_TO_PUSH):02d}] Terunggah: {rel_path} ({len(raw_bytes)/1024:.1f} KB)")

    print("[3/4] Menyusun Git Tree & Commit baru di GitHub...")
    new_tree = gh_request(
        "POST",
        "/git/trees",
        token,
        {"base_tree": base_tree_sha, "tree": tree_items},
    )
    new_commit = gh_request(
        "POST",
        "/git/commits",
        token,
        {
            "message": "fix(apk-offline): override Android API 26+ adaptive icon foreground with custom AGOS logo PNG",
            "tree": new_tree["sha"],
            "parents": [base_commit_sha],
        },
    )
    commit_sha = new_commit["sha"]
    print(f"      Commit baru berhasil dibuat: {commit_sha[:7]}")

    print("[4/4] Memperbarui branch `apk-offline` di GitHub...")
    try:
        gh_request(
            "PATCH",
            "/git/refs/heads/apk-offline",
            token,
            {"sha": commit_sha, "force": True},
        )
    except urllib.error.HTTPError as e:
        if e.code == 404 or e.code == 422:
            gh_request(
                "POST",
                "/git/refs",
                token,
                {"ref": "refs/heads/apk-offline", "sha": commit_sha},
            )
        else:
            raise
    print(f"[SUKSES] Branch `apk-offline` berhasil ter-push ke GitHub ({commit_sha[:7]})!")


if __name__ == "__main__":
    main()
