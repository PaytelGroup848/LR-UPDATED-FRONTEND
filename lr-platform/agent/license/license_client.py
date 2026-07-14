import requests
import base64
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken

from agent.license.device_id import get_fingerprint
from agent.license.license_token import verify_license_token


class LicenseClient:
    # Thin wrapper around the backend /license endpoints, used by both
    # the floating product-key panel and the agent's main loop.

    def __init__(self, base_url: str, timeout: int = 8):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._enforce_https()

    def _enforce_https(self):
        parsed = urlparse(self.base_url)
        if parsed.scheme == "https":
            return
        if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
            return
        raise ValueError("License API must use HTTPS outside localhost")

    def start_trial(self, device_id: str, device_name: str | None):
        response = requests.post(
            f"{self.base_url}/license/trial/start",
            json={
                "device_id": device_id,
                "device_name": device_name,
                "fingerprint": get_fingerprint(),
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def get_status(self, device_id: str):
        try:
            response = requests.post(
                f"{self.base_url}/license/status",
                json={
                    "device_id": device_id,
                    "fingerprint": get_fingerprint(),
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return self._verified_response(response.json(), device_id)
        except requests.RequestException:
            cached = self._load_cached_token(device_id)
            if cached:
                return cached
            raise

    def activate(
        self,
        key_code: str,
        device_id: str,
        device_name: str | None
    ):
        response = requests.post(
            f"{self.base_url}/license/activate",
            json={
                "key_code": key_code,
                "device_id": device_id,
                "device_name": device_name,
                "fingerprint": get_fingerprint(),
            },
            timeout=self.timeout
        )

        if response.status_code >= 400:
            detail = response.json().get("detail", "Activation failed")
            raise ValueError(detail)

        payload = self._verified_response(response.json(), device_id)
        self._cache_token(device_id, payload.get("license_token"))
        return payload

    def hold(self, device_id: str, context: str | None):
        response = requests.post(
            f"{self.base_url}/license/hold",
            json={
                "device_id": device_id,
                "context": context,
                "fingerprint": get_fingerprint(),
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def _verified_response(self, payload, device_id):
        if payload.get("status") == "LICENSED":
            token = payload.get("license_token")
            if not token:
                raise ValueError("Server did not return a signed license token")
            payload["license_claims"] = verify_license_token(token, expected_device_id=device_id)
            self._cache_token(device_id, token)
        return payload

    def _cache_path(self, device_id):
        root = Path.home() / ".lr_remote_access"
        root.mkdir(parents=True, exist_ok=True)
        return root / f"license-{hashlib.sha256(device_id.encode()).hexdigest()[:16]}.bin"

    def _fernet(self, device_id):
        key = base64.urlsafe_b64encode(hashlib.sha256(device_id.encode("utf-8")).digest())
        return Fernet(key)

    def _cache_token(self, device_id, token):
        if not token:
            return
        data = json.dumps({"token": token, "cached_at": datetime.now(timezone.utc).isoformat()}).encode("utf-8")
        self._cache_path(device_id).write_bytes(self._fernet(device_id).encrypt(data))

    def _load_cached_token(self, device_id):
        path = self._cache_path(device_id)
        if not path.exists():
            return None
        try:
            data = json.loads(self._fernet(device_id).decrypt(path.read_bytes()).decode("utf-8"))
            claims = verify_license_token(data.get("token"), expected_device_id=device_id)
            cached_at = datetime.fromisoformat(data.get("cached_at"))
            if cached_at.tzinfo is None:
                cached_at = cached_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - cached_at > timedelta(days=7):
                return None
            return {
                "status": "LICENSED",
                "plan_name": claims.get("plan"),
                "expires_at": claims.get("expires_at"),
                "license_token": data.get("token"),
                "license_claims": claims,
                "offline_grace": True,
            }
        except (OSError, ValueError, InvalidToken, json.JSONDecodeError):
            return None
