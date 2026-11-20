
import pytest
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.transaction import TransactionCreate


def valid_transaction(**overrides):
    data = {
        "transaction_id": "TXN-TEST-001",
        "amount": "2499.99",
        "transaction_type": "purchase",
        "merchant_category": "electronics",
        "location": "Bhubaneswar",
        "device": "Test-Device",
        "transaction_date": "2026-11-21T10:30:00",
    }

    data.update(overrides)
    return data


def test_valid_transaction_data():
    transaction = TransactionCreate(**valid_transaction())

    assert transaction.transaction_id == "TXN-TEST-001"
    assert transaction.amount == Decimal("2499.99")


@pytest.mark.parametrize(
    "amount",
    ["0", "-1", "-100.50"],
)
def test_non_positive_amount_is_rejected(amount):
    with pytest.raises(ValidationError):
        TransactionCreate(**valid_transaction(amount=amount))


def test_amount_with_too_many_decimal_places_is_rejected():
    with pytest.raises(ValidationError):
        TransactionCreate(
            **valid_transaction(amount="10.999")
        )


def test_amount_exceeding_database_precision_is_rejected():
    with pytest.raises(ValidationError):
        TransactionCreate(
            **valid_transaction(amount="10000000000000.00")
        )


@pytest.mark.parametrize(
    "transaction_id",
    ["", " "],
)
def test_empty_transaction_id_is_rejected(transaction_id):
    with pytest.raises(ValidationError):
        TransactionCreate(
            **valid_transaction(transaction_id=transaction_id)
        )


def test_transaction_id_exceeding_database_length_is_rejected():
    with pytest.raises(ValidationError):
        TransactionCreate(
            **valid_transaction(transaction_id="T" * 101)
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("transaction_type", ""),
        ("merchant_category", ""),
    ],
)
def test_empty_required_categories_are_rejected(field, value):
    with pytest.raises(ValidationError):
        TransactionCreate(
            **valid_transaction(**{field: value})
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("transaction_type", "T" * 51),
        ("merchant_category", "M" * 101),
        ("location", "L" * 256),
        ("device", "D" * 101),
    ],
)
def test_fields_exceeding_database_lengths_are_rejected(field, value):
    with pytest.raises(ValidationError):
        TransactionCreate(
            **valid_transaction(**{field: value})
        )


def test_optional_location_and_device_can_be_none():
    transaction = TransactionCreate(
        **valid_transaction(location=None, device=None)
    )

    assert transaction.location is None
    assert transaction.device is None


def test_transaction_date_is_parsed():
    transaction = TransactionCreate(**valid_transaction())

    assert isinstance(transaction.transaction_date, datetime)
