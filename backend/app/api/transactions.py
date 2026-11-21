
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import Transaction, User
from app.ml.fraud_engine import analyze_transaction
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
)
from app.services.email_service import send_notification_email
from app.services.notification_manager import notification_manager
from app.services.notification_service import (
    create_notification,
    get_or_create_preferences,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/transactions",
    tags=["Transactions"],
)


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    transaction_data: TransactionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing_transaction = db.scalar(
        select(Transaction).where(
            Transaction.transaction_id == transaction_data.transaction_id
        )
    )

    if existing_transaction:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transaction ID already exists",
        )

    analysis = analyze_transaction(
        amount=transaction_data.amount,
        transaction_type=transaction_data.transaction_type,
        merchant_category=transaction_data.merchant_category,
        location=transaction_data.location,
        device=transaction_data.device,
    )

    transaction = Transaction(
        user_id=current_user.id,
        transaction_id=transaction_data.transaction_id,
        amount=transaction_data.amount,
        transaction_type=transaction_data.transaction_type,
        merchant_category=transaction_data.merchant_category,
        location=transaction_data.location,
        device=transaction_data.device,
        transaction_date=transaction_data.transaction_date,
        status=analysis["status"],
        fraud_probability=analysis["fraud_probability"],
        risk_score=analysis["risk_score"],
        risk_level=analysis["risk_level"],
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    risk_level = str(analysis["risk_level"]).strip().lower()
    is_fraud_alert = risk_level in {"high", "critical"}

    category = "fraud" if is_fraud_alert else "transaction"

    if is_fraud_alert:
        title = "Fraud Risk Alert"
        message = (
            f"Transaction {transaction.transaction_id} has been "
            f"flagged with {analysis['risk_level']} risk. "
            f"Risk score: {analysis['risk_score']}."
        )
    else:
        title = "Transaction Update"
        message = (
            f"Your transaction {transaction.transaction_id} "
            f"was recorded successfully. "
            f"Status: {transaction.status}."
        )

    try:
        preferences = get_or_create_preferences(
            db,
            current_user.id,
        )

        category_enabled = (
            preferences.fraud_alerts
            if is_fraud_alert
            else preferences.transaction_alerts
        )

        created_notification = None

        if category_enabled and preferences.in_app_enabled:
            created_notification = create_notification(
                db=db,
                user_id=current_user.id,
                title=title,
                message=message,
                category=category,
                link="/",
            )

        db.commit()

        # Deliver the saved notification to connected browsers.
        if created_notification is not None:
            db.refresh(created_notification)

            notification_payload = {
                "id": created_notification.id,
                "title": created_notification.title,
                "message": created_notification.message,
                "category": created_notification.category,
                "link": created_notification.link,
                "is_read": created_notification.is_read,
                "created_at": created_notification.created_at.isoformat(),
            }

            background_tasks.add_task(
                notification_manager.send_to_user,
                current_user.id,
                notification_payload,
            )

        # Attempt email delivery separately.
        if category_enabled and preferences.email_enabled:
            try:
                send_notification_email(
                    to_email=current_user.email,
                    subject=title,
                    body=message,
                )
            except Exception:
                logger.exception(
                    "Unexpected notification email error."
                )

    except Exception:
        db.rollback()
        logger.exception(
            "Notification processing failed for transaction %s.",
            transaction.transaction_id,
        )

    return transaction


@router.get(
    "/",
    response_model=list[TransactionResponse],
)
def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transactions = db.scalars(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
    ).all()

    return list(transactions)


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transaction = db.scalar(
        select(Transaction).where(
            Transaction.transaction_id == transaction_id,
            Transaction.user_id == current_user.id,
        )
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return transaction


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transaction = db.scalar(
        select(Transaction).where(
            Transaction.transaction_id == transaction_id,
            Transaction.user_id == current_user.id,
        )
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    db.delete(transaction)
    db.commit()
