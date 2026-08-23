# def detect_intent(question: str) -> str:
#     q = question.lower()

#     if "outstanding" in q:
#         return "OUTSTANDING_AMOUNT"

#     if "cancelled" in q and "order" in q:
#         return "CANCELLED_ORDER_COUNT"

#     if "pending" in q and "order" in q:
#         return "PENDING_ORDER_COUNT"

#     if "processing" in q and "order" in q:
#         return "PROCESSING_ORDER_COUNT"

#     if "how many" in q and "order" in q:
#         return "ORDER_COUNT"

#     if "total invoice" in q or "invoice amount" in q:
#         return "INVOICE_TOTAL"

#     if "total payment" in q or "payment amount" in q:
#         return "PAYMENT_TOTAL"

#     return "COMPLEX"


def detect_intent(question: str) -> str:
    q = question.lower()

    # Semantic / reasoning questions must go to LLM.
    semantic_keywords = [
        "why",
        "reason",
        "explain",
        "risk",
        "recommend",
        "recommendation",
        "predict",
        "likely",
        "cause",
        "causing",
        "should we",
        "what should",
    ]

    is_semantic = any(
        keyword in q
        for keyword in semantic_keywords
    )

    if is_semantic:
        return "COMPLEX"

    if "outstanding" in q:
        return "OUTSTANDING_AMOUNT"

    if "cancelled" in q and "order" in q:
        return "CANCELLED_ORDER_COUNT"

    if "pending" in q and "order" in q:
        return "PENDING_ORDER_COUNT"

    if "processing" in q and "order" in q:
        return "PROCESSING_ORDER_COUNT"

    if "how many" in q and "order" in q:
        return "ORDER_COUNT"

    if "total invoice" in q or "invoice amount" in q:
        return "INVOICE_TOTAL"

    if "total payment" in q or "payment amount" in q:
        return "PAYMENT_TOTAL"

    return "COMPLEX"


def detect_complexity(question: str) -> str:
    q = question.lower()

    hard_keywords = [
        "why",
        "reason",
        "risk",
        "explain",
        "recommend",
        "recommendation",
        "predict",
        "likely",
        "cause",
        "causing",
        "should we",
        "what should",
    ]

    if any(
        keyword in q
        for keyword in hard_keywords
    ):
        return "HARD"

    simple_keywords = [
        "compare",
        "comparison",
        "difference",
        "summary",
        "summarize",
        "overview",
    ]

    if any(
        keyword in q
        for keyword in simple_keywords
    ):
        return "SIMPLE"

    return "HARD"