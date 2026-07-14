import hashlib
import platform
import subprocess
import uuid


def _run_windows(command):
    try:
        output = subprocess.check_output(command, stderr=subprocess.DEVNULL, timeout=5)
        lines = [
            line.strip()
            for line in output.decode(errors="ignore").splitlines()
            if line.strip()
        ]
        return lines[1] if len(lines) > 1 else None
    except Exception:
        return None


def _reg_value(path, name):
    try:
        output = subprocess.check_output(
            ["reg", "query", path, "/v", name],
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).decode(errors="ignore")
        for line in output.splitlines():
            if name in line:
                parts = line.split()
                return parts[-1] if parts else None
    except Exception:
        return None
    return None


def _normalize(value):
    value = str(value or "").strip()
    if not value or value.lower() in {"none", "null", "unknown", "to be filled by o.e.m.", "default string"}:
        return None
    return value.lower()


def _sha(value):
    value = _normalize(value)
    return hashlib.sha256(value.encode("utf-8")).hexdigest() if value else None


def _windows_sid():
    try:
        output = subprocess.check_output(["whoami", "/user"], stderr=subprocess.DEVNULL, timeout=5).decode(errors="ignore")
        for line in output.splitlines():
            parts = line.split()
            for part in parts:
                if part.startswith("S-1-"):
                    return part
    except Exception:
        return None
    return None


def get_fingerprint() -> dict:
    values = {
        "machine_guid": None,
        "bios_serial": None,
        "motherboard_serial": None,
        "cpu_id": None,
        "disk_serial": None,
        "mac_address": hex(uuid.getnode()),
        "windows_sid": None,
        "hostname": platform.node(),
        "os": platform.platform(),
    }

    if platform.system() == "Windows":
        values.update({
            "machine_guid": _reg_value(r"HKLM\SOFTWARE\Microsoft\Cryptography", "MachineGuid"),
            "bios_serial": _run_windows(["wmic", "bios", "get", "serialnumber"]),
            "motherboard_serial": _run_windows(["wmic", "baseboard", "get", "serialnumber"]),
            "cpu_id": _run_windows(["wmic", "cpu", "get", "processorid"]),
            "disk_serial": _run_windows(["wmic", "diskdrive", "get", "serialnumber"]),
            "windows_sid": _windows_sid(),
        })

    normalized = {key: _normalize(value) for key, value in values.items()}
    material = "|".join(
        normalized.get(key) or ""
        for key in ("machine_guid", "bios_serial", "motherboard_serial", "cpu_id", "disk_serial", "mac_address", "windows_sid")
    )
    fingerprint_hash = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return {
        **normalized,
        "fingerprint_hash": fingerprint_hash,
        "machine_guid_hash": _sha(values.get("machine_guid")),
        "disk_serial_hash": _sha(values.get("disk_serial")),
    }


def get_device_id() -> str:
    # Stable per-machine id (not tied to OS user), used so the trial /
    # license stays attached to this PC even if reinstalled.
    raw = None

    try:
        if platform.system() == "Windows":
            output = subprocess.check_output(
                ["wmic", "csproduct", "get", "UUID"],
                stderr=subprocess.DEVNULL
            )
            raw = output.decode(errors="ignore").split("\n")[1].strip()

    except Exception:
        raw = None

    if not raw:
        raw = platform.node() + platform.machine()

    fingerprint = get_fingerprint()
    return (fingerprint.get("fingerprint_hash") or hashlib.sha256(raw.encode()).hexdigest())[:32]
