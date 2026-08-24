from dataclasses import dataclass

from app.services import query_handlers, data_service


@dataclass(frozen=True)
class RouteDecision:
    intent: str
    complexity: str
    confidence: float
    reason: str


SEMANTIC_KEYWORDS = (
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
)

SIMPLE_ANALYTICS_KEYWORDS = (
    "compare",
    "comparison",
    "difference",
    "summary",
    "summarize",
    "overview",
)

FINANCIAL_INTENTS = {
    "OUTSTANDING_AMOUNT",
    "INVOICE_TOTAL",
    "PAYMENT_TOTAL",
}

OPERATIONAL_INTENTS = {
    "ORDER_COUNT",
    "CANCELLED_ORDER_COUNT",
    "PENDING_ORDER_COUNT",
    "PROCESSING_ORDER_COUNT",
}

UNSUPPORTED_KEYWORDS = (
    "profit margin",
    "profit",
    "delivery time",
    "delivery duration",
    "most recently",
    "latest order",
    "recent order",
    "placed most recently",
)


def detect_intent(question: str) -> str:
    q = question.lower().strip()

    # ---------------------------------------------------------
    # Semantic questions must be classified before checking
    # financial keywords.
    #
    # Example:
    # "Why is Sharma Traders' outstanding higher?"
    #
    # This is a reasoning question, not a simple outstanding
    # lookup.
    # ---------------------------------------------------------
    if any(
        keyword in q
        for keyword in SEMANTIC_KEYWORDS
    ):
        return "COMPLEX"

    # ---------------------------------------------------------
    # Outstanding
    # ---------------------------------------------------------
    if "outstanding" in q:
        return "OUTSTANDING_AMOUNT"

    # ---------------------------------------------------------
    # Order status counts
    # ---------------------------------------------------------
    if "cancelled" in q and "order" in q:
        return "CANCELLED_ORDER_COUNT"

    if "pending" in q and "order" in q:
        return "PENDING_ORDER_COUNT"

    if "processing" in q and "order" in q:
        return "PROCESSING_ORDER_COUNT"

    # ---------------------------------------------------------
    # Total order count
    # ---------------------------------------------------------
    if "how many" in q and "order" in q:
        return "ORDER_COUNT"

    # ---------------------------------------------------------
    # Invoice total
    # ---------------------------------------------------------
    if (
        "total invoice" in q
        or "invoice amount" in q
    ):
        return "INVOICE_TOTAL"

    # ---------------------------------------------------------
    # Payment total
    # ---------------------------------------------------------
    if (
        "total payment" in q
        or "payment amount" in q
    ):
        return "PAYMENT_TOTAL"

    return "COMPLEX"


def detect_complexity(question: str) -> str:
    q = question.lower().strip()

    # Semantic/reasoning questions are hard.
    if any(
        keyword in q
        for keyword in SEMANTIC_KEYWORDS
    ):
        return "HARD"

    # Simple analytical questions can be handled by
    # deterministic application logic.
    if any(
        keyword in q
        for keyword in SIMPLE_ANALYTICS_KEYWORDS
    ):
        return "SIMPLE"

    return "HARD"


def is_multi_customer_outstanding_query(
    question: str,
) -> bool:
    """
    Detect questions that compare outstanding amounts
    across multiple customers.

    Example:
        "Which customer has the higher outstanding amount?"

    These queries should be handled deterministically
    from database summaries instead of being sent to
    the LLM.
    """

    q = question.lower().strip()

    if "outstanding" not in q:
        return False

    comparison_keywords = (
        "higher",
        "lower",
        "highest",
        "lowest",
        "compare",
        "comparison",
        "difference",
        "more",
        "less",
    )

    if not any(
        keyword in q
        for keyword in comparison_keywords
    ):
        return False

    # Try to detect customers mentioned explicitly.
    customer_names = (
        data_service.extract_customer_names(question)
    )

    # If two or more customers are explicitly present,
    # this is definitely a multi-customer query.
    if len(customer_names) >= 2:
        return True

    # Some questions compare customers without explicitly
    # mentioning their names.
    #
    # Example:
    # "Which customer has the higher outstanding amount?"
    #
    # The application knows the customer universe from the
    # seeded dataset, so this is treated as a deterministic
    # comparison query.
    implicit_comparison_patterns = (
        "which customer has the higher outstanding",
        "which customer has the lower outstanding",
        "which customer has the highest outstanding",
        "which customer has the lowest outstanding",
        "which customer has more outstanding",
        "which customer has less outstanding",
    )

    return any(
        pattern in q
        for pattern in implicit_comparison_patterns
    )


def route_question(question: str) -> RouteDecision:
    """
    Decide how the query should be handled.

    Routing strategy:

    1. Unsupported queries -> immediate abstention.
    2. Deterministic financial queries -> database.
    3. Deterministic operational queries -> database.
    4. Multi-customer outstanding comparisons -> deterministic
       database analytics.
    5. Simple analytics -> deterministic application logic.
    6. Semantic/reasoning queries -> LLM.
    7. Unknown queries -> conservative HARD route.

    The router does not use an LLM itself.
    """

    q = question.lower().strip()

    # =========================================================
    # 1. UNSUPPORTED
    # =========================================================

    if detect_unsupported_query(q):
        return RouteDecision(
            intent="UNSUPPORTED",
            complexity="DETERMINISTIC",
            confidence=0.99,
            reason=(
                "Requested information is not "
                "represented in the available schema."
            ),
        )
    if is_multi_customer_outstanding_query(question):
        return RouteDecision(
            intent="OUTSTANDING_COMPARISON",
            complexity="DETERMINISTIC",
            confidence=0.99,
            reason=(
                "Outstanding comparison can be "
                "computed from authoritative database summaries."
            ),
        )


    
    # =========================================================
    # 2. Multi-customer outstanding comparison
    # =========================================================
    #
    # Important:
    #
    # "Which customer has the higher outstanding amount?"
    #
    # must NOT be treated as a single-customer outstanding
    # lookup.
    #
    # It is a deterministic comparison over DB summaries.
    # =========================================================

    if is_multi_customer_outstanding_query(question):
        return RouteDecision(
            intent="OUTSTANDING_COMPARISON",
            complexity="DETERMINISTIC",
            confidence=0.99,
            reason=(
                "Multi-customer outstanding comparison "
                "can be computed directly from database "
                "summaries."
            ),
        )

    # =========================================================
    # 3. Detect normal intent
    # =========================================================

    intent = detect_intent(q)
    complexity = detect_complexity(q)

    # =========================================================
    # 4. Deterministic financial queries
    # =========================================================

    if intent in FINANCIAL_INTENTS:
        return RouteDecision(
            intent=intent,
            complexity="DETERMINISTIC",
            confidence=0.99,
            reason="Exact financial intent matched.",
        )

    # =========================================================
    # 5. Deterministic operational queries
    # =========================================================

    if intent in OPERATIONAL_INTENTS:
        return RouteDecision(
            intent=intent,
            complexity="DETERMINISTIC",
            confidence=0.99,
            reason="Exact operational intent matched.",
        )

    # =========================================================
    # 6. Semantic / reasoning questions
    # =========================================================

    if complexity == "HARD":
        return RouteDecision(
            intent="COMPLEX",
            complexity="HARD",
            confidence=0.80,
            reason="Semantic/reasoning query detected.",
        )

    # =========================================================
    # 7. Simple analytics
    # =========================================================

    if complexity == "SIMPLE":
        return RouteDecision(
            intent="COMPLEX",
            complexity="SIMPLE",
            confidence=0.90,
            reason="Simple analytical query detected.",
        )

    # =========================================================
    # 8. Conservative fallback
    # =========================================================

    return RouteDecision(
        intent="COMPLEX",
        complexity="HARD",
        confidence=0.50,
        reason="Unable to confidently classify query.",
    )


def is_financial_intent(intent: str) -> bool:
    return intent in FINANCIAL_INTENTS


def is_multi_customer_outstanding_query(
    question: str,
) -> bool:
    """
    Detect outstanding comparison queries.

    Examples:
        "Which customer has the higher outstanding amount?"
        "Compare Sharma Traders and Gupta Enterprises outstanding"
    """

    q = question.lower().strip()

    if "outstanding" not in q:
        return False

    comparison_keywords = (
        "higher",
        "lower",
        "highest",
        "lowest",
        "compare",
        "comparison",
        "difference",
        "more",
        "less",
    )

    if not any(
        keyword in q
        for keyword in comparison_keywords
    ):
        return False

    # Explicit customer names.
    customer_names = (
        data_service.extract_customer_names(question)
    )

    if len(customer_names) >= 2:
        return True

    # Implicit comparison.
    # Example:
    # "Which customer has the higher outstanding amount?"
    implicit_comparison_phrases = (
        "which customer",
        "which customers",
        "customer has",
        "customer with",
    )

    return any(
        phrase in q
        for phrase in implicit_comparison_phrases
    )

def detect_unsupported_query(question: str) -> bool:
    q = question.lower().strip()

    return any(
        keyword in q
        for keyword in UNSUPPORTED_KEYWORDS
    )

