"""
Builds the LR Admin Panel into a single Windows exe with the LR logo.

Usage (from repo root, inside a venv with admin-panel/requirements.txt
installed):

    python installer/build/build_admin_panel.py

Output:
    backend/static/admin/Admin Panel.exe
"""

import os
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
ADMIN_PANEL_DIR = ROOT_DIR / "admin-panel"
ADMIN_RESOURCES_DIR = ADMIN_PANEL_DIR / "resources"
BUILD_DIR = ROOT_DIR / "installer" / "build"
INSTALLER_RESOURCES_DIR = ROOT_DIR / "installer" / "resources"
DOWNLOAD_DIR = ROOT_DIR / "backend" / "static" / "admin"
UPDATER_EXE = ROOT_DIR / "backend" / "static" / "updater" / "LR Updater.exe"
MANIFEST_DIR = ROOT_DIR / "backend" / "static" / "app-updates"
VERSION_FILE = ADMIN_PANEL_DIR / "build_version.py"

WORK_DIR = BUILD_DIR / "work"
SPEC_DIR = BUILD_DIR / "specs"
LEGACY_OUTPUT_DIR = BUILD_DIR / "output"

APP_NAME = "Admin Panel"
LEGACY_APP_NAME = "LR_Admin_Panel"
ENTRY_SCRIPT = ADMIN_PANEL_DIR / "main.py"
LOGO_PATH = ADMIN_RESOURCES_DIR / "lr-remote-logo.png"
ICON_PATH = INSTALLER_RESOURCES_DIR / "lr_admin_panel.ico"
FALLBACK_ICON_PATH = ROOT_DIR / "desktop-client" / "resources" / "lr-remote-logo.ico"


def _build_version():
    return datetime.now(timezone.utc).strftime("%Y.%m.%d.%H%M%S")


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_version_file(version):
    VERSION_FILE.write_text(
        f'APP_VERSION = "{version}"\n',
        encoding="utf-8",
    )


def _write_manifest(version, exe_path):
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "app_id": "admin-panel",
        "app_name": APP_NAME,
        "version": version,
        "file_name": exe_path.name,
        "file_path": str(exe_path),
        "sha256": _sha256(exe_path),
        "released_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    (MANIFEST_DIR / "admin-panel.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _ensure_updater():
    if UPDATER_EXE.exists():
        return

    subprocess.run(
        [sys.executable, str(BUILD_DIR / "build_updater.py")],
        check=True,
    )


def _ensure_icon():
    if ICON_PATH.exists() or not LOGO_PATH.exists():
        return

    try:
        from PIL import Image
    except ImportError:
        print("Pillow is not installed; building without an icon.")
        return

    ICON_PATH.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(LOGO_PATH).convert("RGBA")
    image.save(
        ICON_PATH,
        sizes=[
            (16, 16),
            (24, 24),
            (32, 32),
            (48, 48),
            (64, 64),
            (128, 128),
            (256, 256),
        ],
    )
    print(f"Created icon: {ICON_PATH}")


def _remove_old_outputs():
    stale_paths = [
        LEGACY_OUTPUT_DIR / LEGACY_APP_NAME,
        DOWNLOAD_DIR / f"{LEGACY_APP_NAME}.exe",
        DOWNLOAD_DIR / f"{APP_NAME}.exe",
    ]

    for path in stale_paths:
        if path.is_dir():
            shutil.rmtree(path)
            print(f"Removed old folder: {path}")
        elif path.exists():
            path.unlink()
            print(f"Removed old file: {path}")


def main():
    version = _build_version()

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    SPEC_DIR.mkdir(parents=True, exist_ok=True)

    _ensure_updater()
    _ensure_icon()
    _remove_old_outputs()
    _write_version_file(version)

    command = [
        sys.executable, "-m", "PyInstaller",
        str(ENTRY_SCRIPT),
        "--name", APP_NAME,
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        "--distpath", str(DOWNLOAD_DIR),
        "--workpath", str(WORK_DIR),
        "--specpath", str(SPEC_DIR),
        "--paths", str(ADMIN_PANEL_DIR),
        "--add-data", f"{ADMIN_RESOURCES_DIR}{os.pathsep}resources",
        "--add-data", f"{UPDATER_EXE}{os.pathsep}resources",
    ]

    icon_path = ICON_PATH if ICON_PATH.exists() else FALLBACK_ICON_PATH
    if icon_path.exists():
        command += ["--icon", str(icon_path)]

    print("Running:", " ".join(command))

    subprocess.run(command, check=True)

    exe_path = DOWNLOAD_DIR / f"{APP_NAME}.exe"
    if not exe_path.exists():
        raise FileNotFoundError(f"Build failed: {exe_path} was not created.")

    _write_manifest(version, exe_path)
    print(f"\nDone. Admin Panel exe ready at: {exe_path}")


if __name__ == "__main__":
    main()
