from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from backend.api.deps.database import get_db
from backend.core.config import settings
from backend.repositories.user_repository import UserRepository
from backend.schemas.auth import LoginRequest
from backend.schemas.auth import RegisterRequest
from shared.security.jwt import create_access_token
from shared.security.password import hash_password
from shared.security.password import verify_password


router = APIRouter(tags=["Auth"])


def _user_response(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
    }


def _login_response(request: LoginRequest, db):
    repository = UserRepository(db)
    user = repository.get_by_username(request.username)

    if (
        not user
        or not user.password
        or not verify_password(request.password, user.password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is disabled",
        )

    access_token = create_access_token(
        data={"sub": user.id, "username": user.username, "role": user.role},
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "success": True,
        "redirect": "/portal",
        "user": {
            **_user_response(user),
        },
    }


@router.post("/auth/login")
def auth_login(request: LoginRequest, db=Depends(get_db)):
    return _login_response(request, db)


@router.post("/login")
def login_alias(request: LoginRequest, db=Depends(get_db)):
    return _login_response(request, db)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db=Depends(get_db)):
    username = request.username.strip() if request.username else ""
    password = request.password or ""

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required",
        )

    repository = UserRepository(db)

    if repository.exists_by_username(username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    email = request.email or f"{username}@local.lr"
    if repository.exists_by_email(email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    user = repository.create(
        {
            "username": username,
            "email": email,
            "password": hash_password(password),
            "role": "USER",
            "is_active": True,
        }
    )

    return {
        "success": True,
        "message": "User registered successfully",
        **_user_response(user),
    }


@router.post("/logout")
def logout():
    return {"success": True}
