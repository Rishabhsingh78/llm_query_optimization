from app.services.financial_validator import (
    validate_financial_values,
)


SHARMA_SUMMARY = {
    "orders": 199,
    "invoice_total": 16751325,
    "payment_total": 13960983,
    "outstanding": 2790342,
    "cancelled_orders": 41,
    "pending_orders": 42,
    "processing_orders": 36,
}


def test_valid_financial_values():
    answer = """
    Sharma Traders has an invoice total of 16,751,325,
    payments of 13,960,983, and an outstanding balance
    of 2,790,342.
    """

    assert validate_financial_values(
        answer,
        [SHARMA_SUMMARY],
    ) is True


def test_valid_payment_recovery_percentage():
    answer = """
    Sharma Traders has recovered approximately 83.34%
    of the invoiced amount.
    """

    assert validate_financial_values(
        answer,
        [SHARMA_SUMMARY],
    ) is True


def test_valid_outstanding_percentage():
    answer = """
    Approximately 16.66% of the invoice amount remains
    outstanding.
    """

    assert validate_financial_values(
        answer,
        [SHARMA_SUMMARY],
    ) is True


def test_wrong_outstanding_is_rejected():
    answer = """
    Sharma Traders has an outstanding balance of 3000000.
    """

    assert validate_financial_values(
        answer,
        [SHARMA_SUMMARY],
    ) is False


def test_wrong_payment_recovery_is_rejected():
    answer = """
    Sharma Traders has recovered 90% of the invoiced amount.
    """

    assert validate_financial_values(
        answer,
        [SHARMA_SUMMARY],
    ) is False


def test_hallucinated_number_is_rejected():
    answer = """
    Sharma Traders has 500 orders and an outstanding balance
    of 2,790,342.
    """

    assert validate_financial_values(
        answer,
        [SHARMA_SUMMARY],
    ) is False


def test_qualitative_answer_is_allowed():
    answer = """
    Sharma Traders appears to have a significant outstanding
    balance and should prioritize collections.
    """

    assert validate_financial_values(
        answer,
        [SHARMA_SUMMARY],
    ) is True


def test_empty_answer_is_rejected():
    assert validate_financial_values(
        "",
        [SHARMA_SUMMARY],
    ) is False


def test_empty_summary_is_rejected():
    answer = "The outstanding balance is 2,790,342."

    assert validate_financial_values(
        answer,
        [],
    ) is False


def test_valid_order_counts():
    answer = """
    Sharma Traders has 199 orders, including 41 cancelled,
    42 pending, and 36 processing.
    """

    assert validate_financial_values(
        answer,
        [SHARMA_SUMMARY],
    ) is True