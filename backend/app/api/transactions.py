from fastapi import APIRouter, Depends, HTTPException, status
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
