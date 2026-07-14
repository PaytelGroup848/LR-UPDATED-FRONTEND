import platform
import re
import subprocess
import tempfile
from pathlib import Path


INVALID_USERNAME_CHARS = re.compile(r'[\\/"\[\]:;|=,+*?<>@]')


def _clean_text(value):
    return str(value or "").strip()


def create_windows_user(username, password, full_name="", description=""):
    username = _clean_text(username)
    password = str(password or "")

    if platform.system().lower() != "windows":
        return False, "Windows account creation must run on Windows."

    if not username or not password:
        return False, "Windows username and password are required."

    if len(username) > 20 or INVALID_USERNAME_CHARS.search(username) or username.endswith("."):
        return False, "Windows username is invalid. Use 1-20 characters without special Windows account symbols."

    result = _run_account_script(
        username=username,
        password=password,
        full_name=full_name or username,
        description=description or "LR Remote published-app user",
    )

    if result.returncode == 0:
        return True, "Windows account created"
    if result.returncode == 10:
        return False, "Windows username already exists"

    detail = (result.stderr or result.stdout or "").strip()
    if "InvalidPasswordException" in detail or "FullyQualifiedErrorId : InvalidPassword" in detail:
        return False, (
            "Windows rejected this password. Use a stronger password that meets the local Windows policy, "
            "for example 8+ characters with uppercase, lowercase, number, and symbol."
        )
    return False, f"Windows account creation failed: {detail or 'PowerShell returned an error'}"


def _run_account_script(username, password, full_name, description):
    script = """param(
    [string]$name,
    [string]$plain,
    [string]$full,
    [string]$desc
)
$ErrorActionPreference = 'Stop'
if (Get-LocalUser -Name $name -ErrorAction SilentlyContinue) { exit 10 }
$secure = ConvertTo-SecureString $plain -AsPlainText -Force
New-LocalUser -Name $name -Password $secure -FullName $full -Description $desc -PasswordNeverExpires:$true | Out-Null
Add-LocalGroupMember -Group 'Remote Desktop Users' -Member $name -ErrorAction SilentlyContinue
exit 0
"""
    script_path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8") as handle:
            handle.write(script)
            script_path = handle.name

        return subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                script_path,
                username,
                password,
                full_name,
                description,
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    finally:
        if script_path:
            try:
                Path(script_path).unlink(missing_ok=True)
            except OSError:
                pass
