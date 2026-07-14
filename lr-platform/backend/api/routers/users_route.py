from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from backend.api.deps.database import (
    get_db
)

from backend.repositories.user_repository import (
    UserRepository
)

from backend.repositories.role_repository import (
    RoleRepository
)

from backend.services.user_service import (
    UserService
)

from backend.schemas.user import (
    UserCreateRequest
)
from backend.api.deps.current_user import (
    get_current_user
)

from backend.api.deps.permissions import (
    require_role
)
from backend.models.user import User


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("/me")
def get_me(
    current_user=Depends(get_current_user)
):

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role_id": current_user.role_id,
        "role": current_user.role,
        "is_active": current_user.is_active
    }

@router.get("/admin-only")
def admin_only(
    current_user=Depends(
        require_role(
            "SUPER_ADMIN"
        )
    )
):

    return {
        "message": (
            "Welcome Super Admin"
        ),
        "username": (
            current_user.username
        )
    }

@router.post("/")
def create_user(
    request: UserCreateRequest,
    db=Depends(get_db),
    current_user=Depends(
        require_role(
            "SUPER_ADMIN"
        )
    )
):

    service = UserService(
        UserRepository(db),
        RoleRepository(db)
    )

    try:

        user = service.create_user(
            username=request.username,
            email=request.email or f"{request.username}@local.lr",
            password=request.password,
            role_name=request.role_name,
            windows_username=request.windows_username,
            windows_password=request.windows_password,
            windows_domain=request.windows_domain,
            windows_account_enabled=request.windows_account_enabled,
            windows_create_account=request.windows_create_account,
        )

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
@router.get("/")
def get_users(
    db=Depends(get_db),
    current_user=Depends(
        require_role(
            "SUPER_ADMIN",
            "ADMIN"
        )
    )
):

    repository = UserRepository(db)

    users = repository.get_all()

    return [User.to_dict(user) for user in users]

@router.get("/{user_id}")
def get_user(
    user_id: str,
    db=Depends(get_db),
    current_user=Depends(
        require_role(
            "SUPER_ADMIN",
            "ADMIN"
        )
    )
):

    repository = UserRepository(db)

    user = repository.get_by_id(
        user_id
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return User.to_dict(user)
