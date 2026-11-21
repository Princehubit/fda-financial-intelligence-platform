
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Notification, NotificationPreference


def get_or_create_preferences(
    db: Session,
    user_id: int,
) -> NotificationPreference:
    preferences = db.scalar(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
    )

    if preferences is None:
        preferences = NotificationPreference(user_id=user_id)
        db.add(preferences)
        db.flush()

    return preferences


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    category: str = "general",
    link: str | None = None,
) -> Notification | None:
    preferences = db.scalar(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
    )

    if preferences is not None and not preferences.in_app_enabled:
        return None

    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        category=category,
        link=link,
        is_read=False,
    )

    db.add(notification)
    db.flush()

    return notification
