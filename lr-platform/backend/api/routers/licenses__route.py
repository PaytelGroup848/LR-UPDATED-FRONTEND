from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
import time

from backend.api.deps.database import get_db
from backend.api.deps.permissions import require_role

from backend.repositories.license_repository import (
    ProductKeyRepository
)
from backend.repositories.license_repository import (
    LicenseActivationRepository
)
from backend.repositories.license_repository import (
    TrialSessionRepository
)

from backend.services.license_service import LicenseService

from backend.schemas.license import ProductKeyCreateRequest
from backend.schemas.license import ProductKeyResponse
from backend.schemas.license import ActivateKeyRequest
from backend.schemas.license import ActivateKeyResponse
from backend.schemas.license import TrialStartRequest
from backend.schemas.license import LicenseStatusResponse
from backend.schemas.license import LicenseStatusRequest
from backend.schemas.license import HoldRequest


router = APIRouter(
    prefix="/license",
    tags=["License"]
)


_RATE_BUCKETS = {}


def _rate_limit(request: Request, action: str, limit: int = 30, window_seconds: int = 60):
    ip_address = request.client.host if request.client else "unknown"
    key = (action, ip_address)
    now = time.time()
    bucket = [stamp for stamp in _RATE_BUCKETS.get(key, []) if now - stamp < window_seconds]
    if len(bucket) >= limit:
        raise HTTPException(status_code=429, detail="Too many license requests. Try again later.")
    bucket.append(now)
    _RATE_BUCKETS[key] = bucket


def get_license_service(
    db=Depends(get_db)
) -> LicenseService:

    return LicenseService(
        key_repository=ProductKeyRepository(db),
        activation_repository=LicenseActivationRepository(db),
        trial_repository=TrialSessionRepository(db)
    )


# ----------------------------------------------------------------------
# Admin: issue / list / revoke product keys (LR Admin Panel uses these)
# ----------------------------------------------------------------------

@router.post(
    "/admin/keys",
    response_model=list[ProductKeyResponse]
)
def create_product_keys(
    payload: ProductKeyCreateRequest,
    service: LicenseService = Depends(get_license_service),
    current_user=Depends(
        require_role("SUPER_ADMIN", "ADMIN")
    )
):

    keys = service.create_keys(
        plan_name=payload.plan_name,
        max_activations=1,
        valid_days=payload.valid_days,
        issued_to=payload.issued_to,
        quantity=payload.quantity,
        created_by_id=current_user.id
    )

    return keys


@router.get(
    "/admin/keys",
    response_model=list[ProductKeyResponse]
)
def list_product_keys(
    service: LicenseService = Depends(get_license_service),
    current_user=Depends(
        require_role("SUPER_ADMIN", "ADMIN")
    )
):

    return service.list_keys()


@router.post(
    "/admin/keys/{key_code}/revoke",
    response_model=ProductKeyResponse
)
def revoke_product_key(
    key_code: str,
    service: LicenseService = Depends(get_license_service),
    current_user=Depends(
        require_role("SUPER_ADMIN", "ADMIN")
    )
):

    try:
        return service.revoke_key(key_code)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


# ----------------------------------------------------------------------
# Device-facing: trial start / status / activate / hold
# Used by the desktop agent's floating panel and the web floating widget.
# No login required here - identification is by device_id, since this
# runs before a user account/session may even exist on this machine.
# ----------------------------------------------------------------------

@router.post(
    "/trial/start",
    response_model=LicenseStatusResponse
)
def start_trial(
    payload: TrialStartRequest,
    request: Request,
    service: LicenseService = Depends(get_license_service)
):
    _rate_limit(request, "trial", limit=20)

    trial = service.start_trial(
        device_id=payload.device_id,
        device_name=payload.device_name,
        fingerprint=payload.fingerprint,
        public_ip=request.client.host if request.client else None,
    )

    return service.get_status(payload.device_id, fingerprint=payload.fingerprint)


@router.get(
    "/status/{device_id}",
    response_model=LicenseStatusResponse
)
def get_license_status(
    device_id: str,
    request: Request,
    service: LicenseService = Depends(get_license_service)
):
    _rate_limit(request, "status", limit=120)

    return service.get_status(device_id)


@router.post(
    "/status",
    response_model=LicenseStatusResponse
)
def post_license_status(
    payload: LicenseStatusRequest,
    request: Request,
    service: LicenseService = Depends(get_license_service)
):
    _rate_limit(request, "status", limit=120)
    return service.get_status(payload.device_id, fingerprint=payload.fingerprint)


@router.post(
    "/activate",
    response_model=ActivateKeyResponse
)
def activate_key(
    payload: ActivateKeyRequest,
    request: Request,
    service: LicenseService = Depends(get_license_service)
):
    _rate_limit(request, "activate", limit=10)

    try:
        return service.activate(
            key_code=payload.key_code,
            device_id=payload.device_id,
            device_name=payload.device_name,
            fingerprint=payload.fingerprint,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.post(
    "/hold"
)
def hold_session(
    payload: HoldRequest,
    request: Request,
    service: LicenseService = Depends(get_license_service)
):
    _rate_limit(request, "hold", limit=60)
    # Client calls this the instant it pauses work because the trial or
    # license has run out, so progress can be resumed after activation.

    service.hold(
        device_id=payload.device_id,
        context=payload.context,
        fingerprint=payload.fingerprint,
    )

    return {"status": "held"}
