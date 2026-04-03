import os
from dataclasses import dataclass


def _raise_missing_env(key: str) -> None:
    raise ValueError(f"Missing required environment variable: {key}")


@dataclass(frozen=True)
class Settings:
    app_name: str = "Finance Data Processing API"
    app_version: str = "1.0.0"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./finance_dashboard.db")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY") or _raise_missing_env("JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    default_admin_email: str = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@financeapp.com")
    default_admin_password: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin@123")
    default_admin_name: str = os.getenv("DEFAULT_ADMIN_NAME", "System Admin")


settings = Settings()
