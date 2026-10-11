from decimal import Decimal


def analyze_transaction(
    amount: Decimal,
    transaction_type: str,
    merchant_category: str,
    location: str | None,
    device: str | None,
) -> dict:
    risk_score = 0.0
    reasons = []

    amount_value = float(amount)

    if amount_value >= 100000:
        risk_score += 35
        reasons.append("Very high transaction amount")
    elif amount_value >= 50000:
        risk_score += 25
        reasons.append("High transaction amount")
    elif amount_value >= 10000:
        risk_score += 10
        reasons.append("Elevated transaction amount")

    high_risk_categories = {
        "electronics",
        "jewelry",
        "cryptocurrency",
        "gaming",
    }

    if merchant_category.lower() in high_risk_categories:
        risk_score += 15
        reasons.append("Higher-risk merchant category")

    if transaction_type.lower() in {"international", "transfer", "cash_withdrawal"}:
        risk_score += 15
        reasons.append("Higher-risk transaction type")

    if not location:
        risk_score += 10
        reasons.append("Transaction location unavailable")

    if not device:
        risk_score += 10
        reasons.append("Device information unavailable")

    risk_score = min(risk_score, 100.0)

    fraud_probability = risk_score / 100.0

    if risk_score >= 80:
        risk_level = "Critical"
        status = "flagged"
    elif risk_score >= 60:
        risk_level = "High"
        status = "flagged"
    elif risk_score >= 30:
        risk_level = "Medium"
        status = "review"
    else:
        risk_level = "Low"
        status = "approved"

    return {
        "fraud_probability": round(fraud_probability, 4),
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "status": status,
        "reasons": reasons,
    }
