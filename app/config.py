import os
import secrets
from dataclasses import dataclass


def _get_jwt_secret() -> str:
    """Get JWT secret key from environment or generate a secure one for development."""
    env_secret = os.getenv("JWT_SECRET_KEY")
    if env_secret:
        return env_secret
    
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment == "production":
        raise ValueError(
            "CRITICAL: JWT_SECRET_KEY environment variable is required for production. "
            "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    
    # Use a consistent development key (not random to maintain test reproducibility)
    return "dev-secret-key-do-not-use-in-production"


@dataclass(frozen=True)
class Settings:
    app_name: str = "Finance Data Processing API"
    app_version: str = "1.0.0"
    environment: str = os.getenv("ENVIRONMENT", "development").lower()
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./finance_dashboard.db")
    jwt_secret_key: str = _get_jwt_secret()
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    default_admin_email: str = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@financeapp.com")
    default_admin_password: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin@123")
    default_admin_name: str = os.getenv("DEFAULT_ADMIN_NAME", "System Admin")


settings = Settings()
