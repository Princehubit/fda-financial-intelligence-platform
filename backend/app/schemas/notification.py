
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    message: str
    category: str
    link: str | None
    is_read: bool
    created_at: datetime


class UnreadCountResponse(BaseModel):
    unread_count: int


class NotificationPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email_enabled: bool
    in_app_enabled: bool
    transaction_alerts: bool
    fraud_alerts: bool
    security_alerts: bool
    updated_at: datetime


class NotificationPreferenceUpdate(BaseModel):
    email_enabled: bool | None = None
    in_app_enabled: bool | None = None
    transaction_alerts: bool | None = None
    fraud_alerts: bool | None = None
    security_alerts: bool | None = None
