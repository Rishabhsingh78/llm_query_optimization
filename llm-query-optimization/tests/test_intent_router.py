from app.services.intent_router import route_question


def test_outstanding_is_deterministic():
    result = route_question(
        "What is the outstanding amount for Sharma Traders?"
    )

    assert result.intent == "OUTSTANDING_AMOUNT"
    assert result.complexity == "DETERMINISTIC"
    assert result.confidence >= 0.99


def test_order_count_is_deterministic():
    result = route_question(
        "How many orders does Sharma Traders have?"
    )

    assert result.intent == "ORDER_COUNT"
    assert result.complexity == "DETERMINISTIC"
    assert result.confidence >= 0.99


def test_invoice_total_is_deterministic():
    result = route_question(
        "What is the total invoice amount for Sharma Traders?"
    )

    assert result.intent == "INVOICE_TOTAL"
    assert result.complexity == "DETERMINISTIC"


def test_payment_total_is_deterministic():
    result = route_question(
        "What is the total payment amount for Sharma Traders?"
    )

    assert result.intent == "PAYMENT_TOTAL"
    assert result.complexity == "DETERMINISTIC"


def test_business_risk_is_hard():
    result = route_question(
        "What business risks does Sharma Traders have?"
    )

    assert result.intent == "COMPLEX"
    assert result.complexity == "HARD"
    assert result.confidence >= 0.80


def test_financial_explanation_is_hard():
    result = route_question(
        "Explain the financial situation of Sharma Traders."
    )

    assert result.intent == "COMPLEX"
    assert result.complexity == "HARD"


def test_profit_margin_is_unsupported():
    result = route_question(
        "What is Sharma Traders' profit margin?"
    )

    assert result.intent == "UNSUPPORTED"
    assert result.confidence >= 0.99


def test_delivery_time_is_unsupported():
    result = route_question(
        "What is the average delivery time for Sharma Traders?"
    )

    assert result.intent == "UNSUPPORTED"


def test_latest_order_is_unsupported():
    result = route_question(
        "Which order was placed most recently by Sharma Traders?"
    )

    assert result.intent == "UNSUPPORTED"


def test_unknown_question_is_conservative():
    result = route_question(
        "Tell me something about Sharma Traders."
    )

    assert result.intent == "COMPLEX"
    assert result.complexity == "HARD"
    assert result.confidence <= 0.80