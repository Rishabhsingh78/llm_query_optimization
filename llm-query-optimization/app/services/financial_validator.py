import re


def validate_financial_values(answer: str, summaries: list) -> bool:
    """
    Validate numeric financial values mentioned by the LLM
    against authoritative customer summary data.

    Returns True when all numeric values in the answer that
    correspond to known financial/order metrics are consistent.
    """

    if not answer:
        return False

    # Collect authoritative numeric values from DB summaries.
    expected_numbers = set()

    for summary in summaries:
        for key in (
            "orders",
            "invoice_total",
            "payment_total",
            "outstanding",
            "cancelled_orders",
            "pending_orders",
            "processing_orders",
        ):
            value = summary.get(key)

            if value is None:
                continue

            try:
                expected_numbers.add(float(value))
            except (TypeError, ValueError):
                continue

    # Extract actual numeric values from LLM response.
    # This avoids empty matches such as "".
    numbers = re.findall(
        r"(?<![\w.])\d[\d,]*(?:\.\d+)?",
        answer,
    )

    normalized_numbers = set()

    for number in numbers:
        if not number:
            continue

        cleaned = number.replace(",", "").strip()

        if not cleaned:
            continue

        try:
            normalized_numbers.add(float(cleaned))
        except ValueError:
            continue

    # Only validate numbers that appear in the LLM response.
    # If the response contains no numbers, don't reject it solely
    # because it is qualitative.
    if not normalized_numbers:
        return True

    # Every numeric value returned by the LLM must exist in
    # the authoritative DB-derived values.
    for number in normalized_numbers:
        if number not in expected_numbers:
            return False

    return True