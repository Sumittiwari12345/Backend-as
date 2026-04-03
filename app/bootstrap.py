from sqlalchemy import select

from .config import settings
from .database import Base, SessionLocal, engine
from .models import User, UserRole
from .security import hash_password


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    seed_default_admin()


def seed_default_admin() -> None:
    admin_email = settings.default_admin_email.strip().lower()
    with SessionLocal() as db:
        existing_admin = db.scalar(select(User).where(User.email == admin_email))
        if existing_admin is not None:
            return

        admin = User(
            full_name=settings.default_admin_name,
            email=admin_email,
            password_hash=hash_password(settings.default_admin_password),
            role=UserRole.admin,
            is_active=True,
        )
        db.add(admin)
        db.commit()

