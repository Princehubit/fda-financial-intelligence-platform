
import logging

import jwt
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from jwt.exceptions import InvalidTokenError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.db.database import SessionLocal, get_db
from app.db.models import Notification, NotificationPreference, User
from app.schemas.notification import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification_manager import notification_manager
from app.services.notification_service import get_or_create_preferences


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"],
)


@router.get(
    "/",
    response_model=list[NotificationResponse],
)
def get_notifications(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notifications = db.scalars(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    ).all()

    return list(notifications)


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    )

    return {"unread_count": count or 0}


@router.patch("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    notification.is_read = True
    db.commit()

    return {"message": "Notification marked as read"}


@router.patch("/read-all")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notifications = db.scalars(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    ).all()

    for notification in notifications:
        notification.is_read = True

    db.commit()

    return {
        "message": "All notifications marked as read",
        "updated_count": len(notifications),
    }


@router.get(
    "/preferences",
    response_model=NotificationPreferenceResponse,
)
def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preferences = get_or_create_preferences(
        db,
        current_user.id,
    )

    db.commit()
    db.refresh(preferences)

    return preferences


@router.patch(
    "/preferences",
    response_model=NotificationPreferenceResponse,
)
def update_notification_preferences(
    preference_data: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preferences = get_or_create_preferences(
        db,
        current_user.id,
    )

    updates = preference_data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        if value is not None:
            setattr(preferences, field, value)

    db.commit()
    db.refresh(preferences)

    return preferences


# --------------------------------------------------
# REAL-TIME NOTIFICATION WEBSOCKET
# --------------------------------------------------

@router.websocket("/ws")
async def notification_websocket(websocket: WebSocket):
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    user_id = None
    connected = False

    try:
        settings = get_settings()

        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        subject = payload.get("sub")

        if (
            not isinstance(subject, str)
            or not subject.isdecimal()
            or not 1 <= len(subject) <= 10
        ):
            await websocket.close(code=1008)
            return

        user_id = int(subject)

        if not 1 <= user_id <= 2147483647:
            await websocket.close(code=1008)
            return

        user = db.get(User, user_id)

        if user is None:
            await websocket.close(code=1008)
            return

        await notification_manager.connect(
            user_id,
            websocket,
        )
        connected = True

        logger.info(
            "WebSocket connected for user %s",
            user_id,
        )

        try:
            while True:
                # Receive keep-alive messages and detect disconnects.
                await websocket.receive_text()

        except WebSocketDisconnect:
            logger.info(
                "WebSocket disconnected for user %s",
                user_id,
            )

    except InvalidTokenError:
        await websocket.close(code=1008)

    except Exception:
        logger.exception(
            "Notification WebSocket connection failed."
        )

        try:
            await websocket.close(code=1011)
        except Exception:
            pass

    finally:
        if connected and user_id is not None:
            await notification_manager.disconnect(
                user_id,
                websocket,
            )

        db.close()
