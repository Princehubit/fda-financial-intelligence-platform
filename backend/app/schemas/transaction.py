from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TransactionCreate(BaseModel):
    transaction_id: str
    amount: Decimal
    transaction_type: str
    merchant_category: str
    location: str | None = None
    device: str | None = None
    transaction_date: datetime


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
