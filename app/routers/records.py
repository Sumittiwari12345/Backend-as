from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_roles
from ..models import FinancialRecord, RecordType, User, UserRole
from ..schemas import (
    FinancialRecordCreate,
    FinancialRecordListResponse,
    FinancialRecordResponse,
    FinancialRecordUpdate,
)

router = APIRouter(prefix="/records", tags=["Financial Records"])


def _build_record_clauses(
    start_date: date | None,
    end_date: date | None,
    category: str | None,
    record_type: RecordType | None,
    min_amount: Decimal | None,
    max_amount: Decimal | None,
) -> list:
    clauses = [FinancialRecord.is_deleted.is_(False)]

    if start_date is not None:
        clauses.append(FinancialRecord.record_date >= start_date)
    if end_date is not None:
        clauses.append(FinancialRecord.record_date <= end_date)
    if category is not None:
        clauses.append(func.lower(FinancialRecord.category) == category.strip().lower())
    if record_type is not None:
        clauses.append(FinancialRecord.type == record_type)
    if min_amount is not None:
        clauses.append(FinancialRecord.amount >= min_amount)
    if max_amount is not None:
        clauses.append(FinancialRecord.amount <= max_amount)

    return clauses


@router.post("", response_model=FinancialRecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(
    payload: FinancialRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
) -> FinancialRecord:
    record = FinancialRecord(
        amount=payload.amount,
        type=payload.type,
        category=payload.category.strip(),
        record_date=payload.record_date,
        notes=payload.notes,
        created_by_id=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=FinancialRecordListResponse)
def list_records(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    category: str | None = Query(default=None, min_length=2, max_length=80),
    record_type: RecordType | None = Query(default=None, alias="type"),
    min_amount: Decimal | None = Query(default=None, ge=0),
    max_amount: Decimal | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.analyst, UserRole.admin)),
) -> FinancialRecordListResponse:
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date.",
        )
    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_amount cannot be greater than max_amount.",
        )

    filters = _build_record_clauses(start_date, end_date, category, record_type, min_amount, max_amount)

    total = db.scalar(select(func.count(FinancialRecord.id)).where(*filters)) or 0
    offset = (page - 1) * page_size
    items = db.scalars(
        select(FinancialRecord)
        .where(*filters)
        .order_by(FinancialRecord.record_date.desc(), FinancialRecord.id.desc())
        .offset(offset)
        .limit(page_size)
    ).all()

    return FinancialRecordListResponse(
        items=list(items),
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{record_id}", response_model=FinancialRecordResponse)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.analyst, UserRole.admin)),
) -> FinancialRecord:
    record = db.scalar(
        select(FinancialRecord).where(
            FinancialRecord.id == record_id,
            FinancialRecord.is_deleted.is_(False),
        )
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial record not found.",
        )
    return record


@router.patch("/{record_id}", response_model=FinancialRecordResponse)
def update_record(
    record_id: int,
    payload: FinancialRecordUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> FinancialRecord:
    record = db.scalar(
        select(FinancialRecord).where(
            FinancialRecord.id == record_id,
            FinancialRecord.is_deleted.is_(False),
        )
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial record not found.",
        )

    updates = payload.model_dump(exclude_unset=True)
    if "category" in updates and updates["category"] is not None:
        updates["category"] = updates["category"].strip()

    for field_name, value in updates.items():
        setattr(record, field_name, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> Response:
    record = db.scalar(
        select(FinancialRecord).where(
            FinancialRecord.id == record_id,
            FinancialRecord.is_deleted.is_(False),
        )
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial record not found.",
        )

    record.is_deleted = True
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

