import base64
import json
from datetime import datetime, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


LICENSE_PUBLIC_KEY_B64 = "oOQslbVzZcJRb6KpOvksJ7loyUcUdan8_5qdYBtDkuM="


def _decode(segment: str) -> bytes:
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))


def verify_license_token(token: str, expected_device_id: str | None = None) -> dict:
    try:
        header_b64, payload_b64, signature_b64 = str(token or "").split(".")
    except ValueError as error:
        raise ValueError("Invalid license token format") from error

    header = json.loads(_decode(header_b64))
    if header.get("alg") != "EdDSA" or header.get("typ") != "LR-LICENSE":
        raise ValueError("Unsupported license token")

    public_key = Ed25519PublicKey.from_public_bytes(_decode(LICENSE_PUBLIC_KEY_B64))
    try:
        public_key.verify(_decode(signature_b64), f"{header_b64}.{payload_b64}".encode("ascii"))
    except InvalidSignature as error:
        raise ValueError("Invalid license token signature") from error

    claims = json.loads(_decode(payload_b64))
    if expected_device_id and claims.get("device_id") != expected_device_id:
        raise ValueError("License token belongs to a different device")

    expires_at = claims.get("expires_at") or claims.get("expiry")
    if expires_at:
        expiry = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if expiry <= datetime.now(timezone.utc):
            raise ValueError("License token is expired")

    return claims
