
from datetime import datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class TransactionCreate(BaseModel):
    transaction_id: str = Field(
        min_length=1,
        max_length=100,
    )

    amount: Decimal = Field(
        gt=0,
        max_digits=15,
        decimal_places=2,
    )

    transaction_type: str = Field(
        min_length=1,
        max_length=50,
    )

    merchant_category: str = Field(
        min_length=1,
        max_length=100,
    )

    location: str | None = Field(
        default=None,
        max_length=255,
    )

    device: str | None = Field(
        default=None,
        max_length=100,
    )

    transaction_date: datetime

    @field_validator(
        "transaction_id",
        "transaction_type",
        "merchant_category",
    )
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field cannot be empty or whitespace")
        return value


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    transaction_id: str
    amount: Decimal
    transaction_type: str
    merchant_category: str
    location: str | None
    device: str | None
    transaction_date: datetime
    status: str
    fraud_probability: Decimal | None
    risk_score: Decimal | None
    risk_level: str | None
    created_at: datetime
