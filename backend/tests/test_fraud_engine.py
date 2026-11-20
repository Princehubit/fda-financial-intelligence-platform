from decimal import Decimal

from app.ml.fraud_engine import analyze_transaction


def test_low_risk_transaction():
    result = analyze_transaction(
        amount=Decimal("1000"),
        transaction_type="purchase",
        merchant_category="groceries",
        location="Bhubaneswar",
        device="Android",
    )

    assert result["risk_score"] == 0
    assert result["risk_level"] == "Low"
    assert result["status"] == "approved"


def test_medium_risk_transaction():
    result = analyze_transaction(
        amount=Decimal("10000"),
        transaction_type="transfer",
        merchant_category="electronics",
        location="Bhubaneswar",
        device="Android",
    )

    assert result["risk_score"] == 40
    assert result["risk_level"] == "Medium"
    assert result["status"] == "review"


def test_critical_risk_transaction():
    result = analyze_transaction(
        amount=Decimal("100000"),
        transaction_type="transfer",
        merchant_category="electronics",
        location=None,
        device=None,
    )

    assert result["risk_score"] == 85
    assert result["risk_level"] == "Critical"
    assert result["status"] == "flagged"
