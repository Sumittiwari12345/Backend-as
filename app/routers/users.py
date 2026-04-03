from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_roles
from ..models import User, UserRole
from ..schemas import UserCreate, UserResponse, UserUpdate
from ..security import hash_password

router = APIRouter(prefix="/users", tags=["Users"])


def _ensure_not_last_active_admin(
    db: Session,
    user: User,
    target_role: UserRole,
    target_is_active: bool,
) -> None:
    is_demoting_or_deactivating_admin = (
        user.role == UserRole.admin
        and user.is_active
        and (target_role != UserRole.admin or not target_is_active)
    )
    if not is_demoting_or_deactivating_admin:
        return

    active_admin_count = db.scalar(
        select(func.count(User.id)).where(
            User.role == UserRole.admin,
            User.is_active.is_(True),
            User.id != user.id,
        )
    )
    if not active_admin_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate or demote the last active admin.",
        )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> User:
    normalized_email = payload.email.strip().lower()
    existing = db.scalar(select(User).where(User.email == normalized_email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    user = User(
        full_name=payload.full_name.strip(),
        email=normalized_email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[UserResponse])
def list_users(
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> list[User]:
    query = select(User)
    if role is not None:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active.is_(is_active))

    return list(db.scalars(query.order_by(User.id.asc())).all())


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    updates = payload.model_dump(exclude_unset=True)

    target_role = updates.get("role", user.role)
    target_is_active = updates.get("is_active", user.is_active)
    _ensure_not_last_active_admin(db, user, target_role, target_is_active)

    if "email" in updates and updates["email"] is not None:
        normalized_email = updates["email"].strip().lower()
        duplicate = db.scalar(
            select(User).where(
                User.email == normalized_email,
                User.id != user_id,
            )
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )
        user.email = normalized_email

    if "password" in updates and updates["password"] is not None:
        user.password_hash = hash_password(updates.pop("password"))

    if "full_name" in updates and updates["full_name"] is not None:
        user.full_name = updates["full_name"].strip()
        updates.pop("full_name")

    updates.pop("email", None)
    for field_name, value in updates.items():
        setattr(user, field_name, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> Response:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    _ensure_not_last_active_admin(db, user, user.role, False)
    user.is_active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

