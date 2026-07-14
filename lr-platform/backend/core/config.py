import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

PROJECT_ENV = Path(PROJECT_DIR) / ".env"
BACKEND_ENV = Path(BASE_DIR) / ".env"
load_dotenv(PROJECT_ENV)
load_dotenv(BACKEND_ENV)


class Settings(BaseSettings):
    MONGODB_URL: str
    MONGODB_DATABASE: str
    MONGODB_SERVER_SELECTION_TIMEOUT_MS: int = 5000

    SECRET_KEY: str
    CREDENTIAL_ENCRYPTION_KEY: str | None = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ENVIRONMENT: str = "development"

    GUACAMOLE_URL: str | None = None
    GUACAMOLE_PUBLIC_URL: str | None = None
    GUACAMOLE_USER: str | None = None
    GUACAMOLE_PASSWORD: str | None = None
    GUACAMOLE_DATA_SOURCE: str | None = None

    PORTAL_HOME_URL: str | None = None
    FRONTEND_URL: str | None = None
    LR_SERVER_URL: str | None = None
    LR_BACKEND_URL: str | None = None
    RDP_PRECHECK_ENABLED: str = "true"
    FILE_TRANSFER_ROOT: str | None = None
    FILE_TRANSFER_MAX_UPLOAD_BYTES: int = 100_000_000
    FILE_TRANSFER_MAX_READ_BYTES: int = 1_000_000
    FLASK_ENV: str | None = None
    CORS_ORIGINS: str | None = None
    SOCKETIO_CORS_ORIGINS: str | None = None

    model_config = SettingsConfigDict(
        env_file=(str(PROJECT_ENV), str(BACKEND_ENV)),
        extra="ignore",
    )


settings = Settings()

SECRET_KEY = settings.SECRET_KEY
CREDENTIAL_ENCRYPTION_KEY = settings.CREDENTIAL_ENCRYPTION_KEY
MONGODB_URL = settings.MONGODB_URL
MONGODB_DATABASE = settings.MONGODB_DATABASE

GUACAMOLE_URL = settings.GUACAMOLE_URL
GUACAMOLE_PUBLIC_URL = settings.GUACAMOLE_PUBLIC_URL or settings.GUACAMOLE_URL
GUACAMOLE_USER = settings.GUACAMOLE_USER
GUACAMOLE_PASSWORD = settings.GUACAMOLE_PASSWORD
GUACAMOLE_DATA_SOURCE = settings.GUACAMOLE_DATA_SOURCE
PORTAL_HOME_URL = settings.PORTAL_HOME_URL
FRONTEND_URL = settings.FRONTEND_URL
LR_SERVER_URL = settings.LR_SERVER_URL
LR_BACKEND_URL = settings.LR_BACKEND_URL
RDP_PRECHECK_ENABLED = settings.RDP_PRECHECK_ENABLED
FILE_TRANSFER_ROOT = settings.FILE_TRANSFER_ROOT
FILE_TRANSFER_MAX_UPLOAD_BYTES = settings.FILE_TRANSFER_MAX_UPLOAD_BYTES
FILE_TRANSFER_MAX_READ_BYTES = settings.FILE_TRANSFER_MAX_READ_BYTES
ENVIRONMENT = settings.ENVIRONMENT
CORS_ORIGINS = settings.CORS_ORIGINS
SOCKETIO_CORS_ORIGINS = settings.SOCKETIO_CORS_ORIGINS

SESSION_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = settings.ENVIRONMENT == "production" or settings.FLASK_ENV == "production"
PREFERRED_URL_SCHEME = "https" if SESSION_COOKIE_SECURE else "http"
