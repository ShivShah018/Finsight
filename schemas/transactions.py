from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date


class TransactionCreate(BaseModel):
    category_id: int
    amount: float = Field(gt=0)
    type: str
    description: Optional[str] = None
    currency: str = "INR"
    transaction_date: date
    is_bill: bool = False

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v = v.lower()
        if v not in ("income", "expense"):
            raise ValueError("Type must be 'income' or 'expense'")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = v.upper()
        if v not in ("INR", "USD", "NPR"):
            raise ValueError("Currency must be INR, USD, or NPR")
        return v


class TransactionUpdate(BaseModel):
    category_id: Optional[int] = None
    amount: Optional[float] = Field(default=None, gt=0)
    type: Optional[str] = None
    description: Optional[str] = None
    currency: Optional[str] = None
    transaction_date: Optional[date] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.lower()
            if v not in ("income", "expense"):
                raise ValueError("Type must be 'income' or 'expense'")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.upper()
            if v not in ("INR", "USD", "NPR"):
                raise ValueError("Currency must be INR, USD, or NPR")
        return v


class TransactionResponse(BaseModel):
    id: int
    category_id: int
    category_name: str
    amount: float
    type: str
    description: Optional[str] = None
    transaction_date: date
    currency: str = "INR"


class TransactionListResponse(BaseModel):
    transactions: list[TransactionResponse]
    total: int
