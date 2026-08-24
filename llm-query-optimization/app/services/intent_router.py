from app.services import query_handlers
from dataclasses import dataclass


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

    # Semantic questions must not be treated
    # as deterministic financial queries.
    if any(keyword in q for keyword in SEMANTIC_KEYWORDS):
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
    q = question.lower().strip()

    if any(keyword in q for keyword in SEMANTIC_KEYWORDS):
        return "HARD"

    if any(keyword in q for keyword in SIMPLE_ANALYTICS_KEYWORDS):
        return "SIMPLE"

    return "HARD"


def route_question(question: str) -> RouteDecision:
    """
    Decide how the query should be handled.

    The router is deliberately conservative:
    when confidence is low, we classify the query as HARD
    instead of sending it through an unsafe deterministic path.
    """
    q = question.lower().strip()

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

    intent = detect_intent(q)
    complexity = detect_complexity(q)

    # ---------------------------------------------------------
    # UNSUPPORTED / ABSTAIN PATH (NO DB QUERIES)
    # ---------------------------------------------------------

    if detect_unsupported_query(question):
        return RouteDecision(
            intent="COMPLEX",
            complexity="HARD",
            confidence=0.99,
            reason="Unsupported query – no database access.",
        )

    # ---------------------------------------------------------
    # High-confidence deterministic financial queries
    # ---------------------------------------------------------

    if intent in FINANCIAL_INTENTS:
        return RouteDecision(
            intent=intent,
            complexity="DETERMINISTIC",
            confidence=0.99,
            reason="Exact financial intent matched.",
        )

    # ---------------------------------------------------------
    # High-confidence deterministic operational queries
    # ---------------------------------------------------------

    operational_intents = {
        "ORDER_COUNT",
        "CANCELLED_ORDER_COUNT",
        "PENDING_ORDER_COUNT",
        "PROCESSING_ORDER_COUNT",
    }

    if intent in operational_intents:
        return RouteDecision(
            intent=intent,
            complexity="DETERMINISTIC",
            confidence=0.99,
            reason="Exact operational intent matched.",
        )

    # ---------------------------------------------------------
    # Semantic questions
    # ---------------------------------------------------------

    if complexity == "HARD":
        return RouteDecision(
            intent="COMPLEX",
            complexity="HARD",
            confidence=0.80,
            reason="Semantic/reasoning query detected.",
        )

    # ---------------------------------------------------------
    # Simple analytics
    # ---------------------------------------------------------

    if complexity == "SIMPLE":
        return RouteDecision(
            intent="COMPLEX",
            complexity="SIMPLE",
            confidence=0.90,
            reason="Simple analytical query detected.",
        )

    # ---------------------------------------------------------
    # Conservative fallback
    # ---------------------------------------------------------

    return RouteDecision(
        intent="COMPLEX",
        complexity="HARD",
        confidence=0.50,
        reason="Unable to confidently classify query.",
    )


def is_financial_intent(intent: str) -> bool:
    return intent in FINANCIAL_INTENTS


def detect_unsupported_query(question: str) -> bool:
    q = question.lower().strip()

    return any(
        keyword in q
        for keyword in UNSUPPORTED_KEYWORDS
    )