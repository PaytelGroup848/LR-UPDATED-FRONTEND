import platform
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from backend.extensions import socketio
from backend.security.credential_crypto import encrypt_secret


class WindowsAccountService:
    INVALID_USERNAME_CHARS = re.compile(r'[\\/"\[\]:;|=,+*?<>@]')

    @staticmethod
    def clean_text(value):
        return str(value or "").strip()

    @staticmethod
    def normalize_bool(value, default=True):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() not in {"false", "0", "no", "off"}

    @classmethod
    def build_updates(
        cls,
        data,
        default_username,
        default_password,
        create_local_account=True,
    ):
        enabled = cls.normalize_bool(data.get("windows_account_enabled"), True)
        if not enabled:
            return {
                "windows_account_enabled": False,
                "windows_username": None,
                "windows_domain": None,
                "windows_password": None,
            }, None

        username = (
            cls.clean_text(data.get("windows_username"))
            or cls.clean_text(data.get("rdp_username"))
            or cls.clean_text(default_username)
        )
        password = (
            str(data.get("windows_password") or "")
            or str(data.get("rdp_password") or "")
            or str(default_password or "")
        )
        domain = cls.clean_text(data.get("windows_domain")) or cls.clean_text(data.get("rdp_domain"))

        if not username or not password:
            return None, "Windows username and password are required"

        if create_local_account:
            provision = cls.create_local_user(
                username=username,
                password=password,
                full_name=cls.clean_text(data.get("full_name")) or username,
                description="LR Remote published-app user",
                domain=domain,
            )
            if not provision["success"]:
                return None, provision["message"]

        return {
            "windows_username": username,
            "windows_domain": domain or None,
            "windows_password": encrypt_secret(password),
            "windows_account_enabled": True,
            "windows_account_provisioned": bool(create_local_account),
            "windows_account_provisioned_at": datetime.utcnow() if create_local_account else None,
        }, None

    @classmethod
    def create_local_user(cls, username, password, full_name="", description="", domain=""):
        username = cls.clean_text(username)
        domain = cls.clean_text(domain)

        if domain or "\\" in username:
            return {
                "success": False,
                "message": "Domain Windows accounts cannot be created locally. Use a local username without DOMAIN\\.",
            }

        if len(username) > 20 or cls.INVALID_USERNAME_CHARS.search(username) or username.endswith("."):
            return {
                "success": False,
                "message": "Windows username is invalid. Use 1-20 characters without special Windows account symbols.",
            }

        if platform.system().lower() != "windows":
            return cls.create_via_agent(username, password, full_name, description)

        result = cls.run_account_script(username, password, full_name or username, description)

        if result.returncode == 0:
            return {"success": True, "message": "Windows account created"}
        if result.returncode == 10:
            return {"success": False, "message": "Windows username already exists"}

        detail = (result.stderr or result.stdout or "").strip()
        if "InvalidPasswordException" in detail or "FullyQualifiedErrorId : InvalidPassword" in detail:
            return {
                "success": False,
                "message": (
                    "Windows rejected this password. Use a stronger password that meets the local Windows policy, "
                    "for example 8+ characters with uppercase, lowercase, number, and symbol."
                ),
            }
        agent_result = cls.create_via_agent(username, password, full_name, description)
        if agent_result.get("success"):
            return agent_result

        agent_message = agent_result.get("message")
        if agent_message:
            detail = f"{detail or 'PowerShell returned an error'} Agent fallback: {agent_message}"

        return {
            "success": False,
            "message": f"Windows account creation failed: {detail or 'PowerShell returned an error'}",
        }

    @staticmethod
    def run_account_script(username, password, full_name, description):
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

    @classmethod
    def create_via_agent(cls, username, password, full_name="", description="", agent_id=None):
        try:
            from backend.sockets.agent_socket import connected_agents, get_agent_sid
        except Exception as error:
            return {
                "success": False,
                "message": f"Windows account creation requires a connected Windows Agent: {error}",
            }

        target_sid = get_agent_sid(agent_id) if agent_id else None
        if not target_sid:
            for sid, info in connected_agents.items():
                os_name = str(info.get("os") or "").lower()
                if "windows" in os_name or os_name.startswith("win"):
                    target_sid = sid
                    break

        if not target_sid:
            connected_count = len(connected_agents)
            return {
                "success": False,
                "message": (
                    "Windows account creation requires the backend to run on Windows with administrator rights, "
                    "or a connected Windows Agent running with administrator rights. "
                    "Start the agent with LIVEPANEL_SERVER_URL pointing to the web backend, usually http://localhost:8004. "
                    f"Connected agents seen by this backend: {connected_count}."
                ),
            }

        try:
            result = socketio.call(
                "create_windows_user",
                {
                    "agent_id": agent_id,
                    "username": username,
                    "password": password,
                    "full_name": full_name or username,
                    "description": description,
                },
                namespace="/agent",
                to=target_sid,
                timeout=35,
            )
        except Exception as error:
            return {
                "success": False,
                "message": f"Windows Agent did not create the account: {error}",
            }

        if isinstance(result, dict):
            return result

        return {
            "success": False,
            "message": "Windows Agent returned an invalid account creation response.",
        }
