from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator

from .models import RecordType, UserRole


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("*", when_used="json", check_fields=False)
    def serialize_decimal_values(self, value):
        if isinstance(value, Decimal):
            return float(value)
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.viewer
    is_active: bool = True

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        has_letter = any(character.isalpha() for character in value)
        has_digit = any(character.isdigit() for character in value)
        if not (has_letter and has_digit):
            raise ValueError("Password must include at least one letter and one number.")
        return value


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str | None) -> str | None:
        if value is None:
            return value
        has_letter = any(character.isalpha() for character in value)
        has_digit = any(character.isdigit() for character in value)
        if not (has_letter and has_digit):
            raise ValueError("Password must include at least one letter and one number.")
        return value


class UserResponse(APIModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FinancialRecordCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    type: RecordType
    category: str = Field(min_length=2, max_length=80)
    record_date: date
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Category cannot be blank.")
        return normalized


class FinancialRecordUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    type: RecordType | None = None
    category: str | None = Field(default=None, min_length=2, max_length=80)
    record_date: date | None = None
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Category cannot be blank.")
        return normalized


class FinancialRecordResponse(APIModel):
    id: int
    amount: Decimal
    type: RecordType
    category: str
    record_date: date
    notes: str | None
    created_by_id: int
    created_at: datetime
    updated_at: datetime


class FinancialRecordListResponse(APIModel):
    items: list[FinancialRecordResponse]
    total: int
    page: int
    page_size: int


class CategoryTotal(APIModel):
    category: str
    income: Decimal
    expense: Decimal
    net: Decimal


class DashboardSummaryResponse(APIModel):
    total_income: Decimal
    total_expense: Decimal
    net_balance: Decimal
    category_totals: list[CategoryTotal]
    recent_activity: list[FinancialRecordResponse]


class TrendPoint(APIModel):
    period: str
    income: Decimal
    expense: Decimal
    net: Decimal
