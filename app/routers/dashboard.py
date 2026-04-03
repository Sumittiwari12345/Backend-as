from datetime import date
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_roles
from ..models import FinancialRecord, RecordType, User, UserRole
from ..schemas import CategoryTotal, DashboardSummaryResponse, TrendPoint

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _to_decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _build_dashboard_clauses(start_date: date | None, end_date: date | None) -> list:
    clauses = [FinancialRecord.is_deleted.is_(False)]
    if start_date is not None:
        clauses.append(FinancialRecord.record_date >= start_date)
    if end_date is not None:
        clauses.append(FinancialRecord.record_date <= end_date)
    return clauses


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_summary(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    recent_limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.viewer, UserRole.analyst, UserRole.admin)),
) -> DashboardSummaryResponse:
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date.",
        )

    filters = _build_dashboard_clauses(start_date, end_date)

    income_expr = func.coalesce(
        func.sum(
            case(
                (FinancialRecord.type == RecordType.income, FinancialRecord.amount),
                else_=0,
            )
        ),
        0,
    )
    expense_expr = func.coalesce(
        func.sum(
            case(
                (FinancialRecord.type == RecordType.expense, FinancialRecord.amount),
                else_=0,
            )
        ),
        0,
    )

    totals_row = db.execute(
        select(
            income_expr.label("total_income"),
            expense_expr.label("total_expense"),
        ).where(*filters)
    ).one()
    total_income = _to_decimal(totals_row.total_income)
    total_expense = _to_decimal(totals_row.total_expense)

    category_rows = db.execute(
        select(
            FinancialRecord.category.label("category"),
            income_expr.label("income"),
            expense_expr.label("expense"),
        )
        .where(*filters)
        .group_by(FinancialRecord.category)
        .order_by(FinancialRecord.category.asc())
    ).all()

    category_totals = [
        CategoryTotal(
            category=row.category,
            income=_to_decimal(row.income),
            expense=_to_decimal(row.expense),
            net=_to_decimal(row.income) - _to_decimal(row.expense),
        )
        for row in category_rows
    ]

    recent_activity = list(
        db.scalars(
            select(FinancialRecord)
            .where(*filters)
            .order_by(FinancialRecord.record_date.desc(), FinancialRecord.id.desc())
            .limit(recent_limit)
        ).all()
    )

    return DashboardSummaryResponse(
        total_income=total_income,
        total_expense=total_expense,
        net_balance=total_income - total_expense,
        category_totals=category_totals,
        recent_activity=recent_activity,
    )


@router.get("/trends", response_model=list[TrendPoint])
def get_trends(
    period: Literal["monthly", "weekly"] = Query(default="monthly"),
    points: int = Query(default=6, ge=1, le=52),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.viewer, UserRole.analyst, UserRole.admin)),
) -> list[TrendPoint]:
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date.",
        )

    filters = _build_dashboard_clauses(start_date, end_date)
    sqlite_period_expr = (
        func.strftime("%Y-%m", FinancialRecord.record_date)
        if period == "monthly"
        else func.strftime("%Y-W%W", FinancialRecord.record_date)
    )

    income_expr = func.coalesce(
        func.sum(
            case(
                (FinancialRecord.type == RecordType.income, FinancialRecord.amount),
                else_=0,
            )
        ),
        0,
    )
    expense_expr = func.coalesce(
        func.sum(
            case(
                (FinancialRecord.type == RecordType.expense, FinancialRecord.amount),
                else_=0,
            )
        ),
        0,
    )

    rows = db.execute(
        select(
            sqlite_period_expr.label("period"),
            income_expr.label("income"),
            expense_expr.label("expense"),
        )
        .where(*filters)
        .group_by(sqlite_period_expr)
        .order_by(sqlite_period_expr.desc())
        .limit(points)
    ).all()

    trend_points = [
        TrendPoint(
            period=row.period,
            income=_to_decimal(row.income),
            expense=_to_decimal(row.expense),
            net=_to_decimal(row.income) - _to_decimal(row.expense),
        )
        for row in rows
    ]
    trend_points.reverse()
    return trend_points

