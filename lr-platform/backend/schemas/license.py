from datetime import datetime

from pydantic import BaseModel


class ProductKeyCreateRequest(BaseModel):

    plan_name: str = "STANDARD"

    max_activations: int = 1

    valid_days: int = 365

    issued_to: str | None = None

    quantity: int = 1


class ProductKeyResponse(BaseModel):

    id: str

    key_code: str

    plan_name: str

    max_activations: int

    valid_days: int

    is_revoked: bool

    issued_to: str | None

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class ActivateKeyRequest(BaseModel):

    key_code: str

    device_id: str

    device_name: str | None = None

    fingerprint: dict | None = None


class ActivateKeyResponse(BaseModel):

    status: str

    plan_name: str

    expires_at: datetime

    device_id: str | None = None

    transfer_locked_until: datetime | None = None

    resume_context: str | None = None
    # If the device had paused work while waiting for a key (trial expired
    # mid-session), this carries back whatever the client stored so it can
    # continue from exactly that point instead of restarting.

    license_token: str | None = None


class TrialStartRequest(BaseModel):

    device_id: str

    device_name: str | None = None

    fingerprint: dict | None = None


class LicenseStatusResponse(BaseModel):

    status: str
    # one of: TRIAL_ACTIVE, TRIAL_EXPIRED, LICENSED, HELD, NOT_FOUND

    expires_at: datetime | None = None

    days_remaining: int | None = None

    plan_name: str | None = None

    license_token: str | None = None


class LicenseStatusRequest(BaseModel):

    device_id: str

    fingerprint: dict | None = None


class HoldRequest(BaseModel):

    device_id: str

    context: str | None = None

    fingerprint: dict | None = None


class ResumeRequest(BaseModel):

    device_id: str

    key_code: str
