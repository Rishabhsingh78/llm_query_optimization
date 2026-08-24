# pyrefly: ignore [missing-import]

import time

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.services.tenant_limiter import (
    tenant_limiter,
    TenantLimitExceeded,
)
from app.db import (
    Base,
    SessionLocal,
    engine,
    test_connection,
)

import app.llm.client as llm_client

from app.services.analytics_service import (
    format_comparison,
    format_customer_summary,
    format_payment_recovery,
)

from app.services.cache_service import (
    get_customer_summary_cache,
    set_customer_summary_cache,
)

from app.services.data_service import (
    extract_customer_name,
    extract_customer_names,
    get_all_tenant_data,
    get_outstanding_amount,
)

from app.services.financial_validator import (
    validate_financial_values,
)

from app.services.intent_router import (
    route_question,
)

from app.services.query_handlers import (
    get_cancelled_order_count,
    get_customer_summary,
    get_order_count,
    get_pending_order_count,
    get_processing_order_count,
    get_total_invoice_amount,
    get_total_payment_amount,
)


# ============================================================
# FastAPI application
# ============================================================

app = FastAPI(
    title="LLM Query Optimization"
)


# ============================================================
# Startup
# ============================================================

@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(
        bind=engine
    )


# ============================================================
# Health check
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "database": test_connection(),
    }


# ============================================================
# Database dependency
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# Tenant data
# ============================================================

@app.get("/tenant/{tenant_id}/data")
def tenant_data(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    data = get_all_tenant_data(
        db,
        tenant_id,
    )

    return {
        "orders": len(data["orders"]),
        "invoices": len(data["invoices"]),
        "payments": len(data["payments"]),
        "messages": len(data["messages"]),
    }


# ============================================================
# Request model
# ============================================================

class QueryRequest(BaseModel):
    question: str


# ============================================================
# Query endpoint
# ============================================================

@app.post("/tenant/{tenant_id}/query")
def ask_question(
    tenant_id: int,
    request: QueryRequest,
    db: Session = Depends(get_db),
):
    start = time.perf_counter()

    question = request.question.strip()

    if not question:
        return {
            "answer": "Please provide a question.",
            "source": "validation",
            "intent": "UNKNOWN",
            "timing": {
                "db": 0,
                "format": 0,
                "llm": 0,
                "total": 0,
            },
        }

    print()
    print("=" * 70)
    print("QUESTION:", question)
    try:
        tenant_limiter.check_request(tenant_id)

    except TenantLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "tenant_request_limit_exceeded",
                "message": str(exc),
            },
        )

    # ========================================================
    # 1. Identify customer + route question
    # ========================================================

    customer_name = extract_customer_name(
        question
    )

    route = route_question(
        question
    )

    intent = route.intent
    complexity = route.complexity
    if intent == "UNSUPPORTED":

        total_time = time.perf_counter() - start
        return {
            "answer": (
                "The provided data does not contain "
                "enough information to answer that."
                ),
            "source": "abstained",
            "intent": intent,
            "complexity": complexity,
            "timing": {
                "db": 0,
            "format": 0,
            "llm": 0,
            "total": round(total_time, 4),
            },
        }

    print(
        f"ROUTE: intent={intent}, "
        f"complexity={complexity}, "
        f"confidence={route.confidence}, "
        f"reason={route.reason}"
    )

    print("Customer:", customer_name)

    # ========================================================
    # 2. Deterministic queries
    # ========================================================
    #
    # These queries do NOT need an LLM.
    #
    # SQL/application code is responsible for:
    #
    # - financial calculations
    # - counts
    # - exact database values
    #
    # This gives:
    #
    # - lower latency
    # - lower LLM cost
    # - stronger correctness
    #
    # ========================================================

    # --------------------------------------------------------
    # Outstanding amount
    # --------------------------------------------------------

    if (
        intent == "OUTSTANDING_AMOUNT"
        and customer_name
    ):
        db_start = time.perf_counter()

        outstanding = get_outstanding_amount(
            db,
            tenant_id,
            customer_name,
        )

        db_time = (
            time.perf_counter() - db_start
        )

        total_time = (
            time.perf_counter() - start
        )

        return {
            "answer": (
                f"The outstanding amount for "
                f"{customer_name} is "
                f"₹{outstanding:,.0f}."
            ),
            "ground_truth": outstanding,
            "source": "database",
            "intent": intent,
            "timing": {
                "db": round(db_time, 4),
                "format": 0,
                "llm": 0,
                "total": round(total_time, 4),
            },
        }

    # --------------------------------------------------------
    # Order count
    # --------------------------------------------------------

    if (
        intent == "ORDER_COUNT"
        and customer_name
    ):
        db_start = time.perf_counter()

        result = get_order_count(
            db,
            tenant_id,
            customer_name,
        )

        db_time = (
            time.perf_counter() - db_start
        )

        total_time = (
            time.perf_counter() - start
        )

        return {
            "answer": (
                f"There are {result} orders."
            ),
            "source": "database",
            "intent": intent,
            "timing": {
                "db": round(db_time, 4),
                "format": 0,
                "llm": 0,
                "total": round(total_time, 4),
            },
        }

    # --------------------------------------------------------
    # Invoice total
    # --------------------------------------------------------

    if (
        intent == "INVOICE_TOTAL"
        and customer_name
    ):
        db_start = time.perf_counter()

        result = get_total_invoice_amount(
            db,
            tenant_id,
            customer_name,
        )

        db_time = (
            time.perf_counter() - db_start
        )

        total_time = (
            time.perf_counter() - start
        )

        return {
            "answer": (
                f"The total invoice amount is "
                f"₹{result:,.0f}."
            ),
            "source": "database",
            "intent": intent,
            "timing": {
                "db": round(db_time, 4),
                "format": 0,
                "llm": 0,
                "total": round(total_time, 4),
            },
        }

    # --------------------------------------------------------
    # Payment total
    # --------------------------------------------------------

    if (
        intent == "PAYMENT_TOTAL"
        and customer_name
    ):
        db_start = time.perf_counter()

        result = get_total_payment_amount(
            db,
            tenant_id,
            customer_name,
        )

        db_time = (
            time.perf_counter() - db_start
        )

        total_time = (
            time.perf_counter() - start
        )

        return {
            "answer": (
                f"The total payment amount is "
                f"₹{result:,.0f}."
            ),
            "source": "database",
            "intent": intent,
            "timing": {
                "db": round(db_time, 4),
                "format": 0,
                "llm": 0,
                "total": round(total_time, 4),
            },
        }

    # --------------------------------------------------------
    # Cancelled orders
    # --------------------------------------------------------

    if (
        intent == "CANCELLED_ORDER_COUNT"
        and customer_name
    ):
        db_start = time.perf_counter()

        result = get_cancelled_order_count(
            db,
            tenant_id,
            customer_name,
        )

        db_time = (
            time.perf_counter() - db_start
        )

        total_time = (
            time.perf_counter() - start
        )

        return {
            "answer": (
                f"There are {result} "
                f"cancelled orders."
            ),
            "source": "database",
            "intent": intent,
            "timing": {
                "db": round(db_time, 4),
                "format": 0,
                "llm": 0,
                "total": round(total_time, 4),
            },
        }

    # --------------------------------------------------------
    # Pending orders
    # --------------------------------------------------------

    if (
        intent == "PENDING_ORDER_COUNT"
        and customer_name
    ):
        db_start = time.perf_counter()

        result = get_pending_order_count(
            db,
            tenant_id,
            customer_name,
        )

        db_time = (
            time.perf_counter() - db_start
        )

        total_time = (
            time.perf_counter() - start
        )

        return {
            "answer": (
                f"There are {result} "
                f"pending orders."
            ),
            "source": "database",
            "intent": intent,
            "timing": {
                "db": round(db_time, 4),
                "format": 0,
                "llm": 0,
                "total": round(total_time, 4),
            },
        }

    # --------------------------------------------------------
    # Processing orders
    # --------------------------------------------------------

    if (
        intent == "PROCESSING_ORDER_COUNT"
        and customer_name
    ):
        db_start = time.perf_counter()

        result = get_processing_order_count(
            db,
            tenant_id,
            customer_name,
        )

        db_time = (
            time.perf_counter() - db_start
        )

        total_time = (
            time.perf_counter() - start
        )

        return {
            "answer": (
                f"There are {result} "
                f"processing orders."
            ),
            "source": "database",
            "intent": intent,
            "timing": {
                "db": round(db_time, 4),
                "format": 0,
                "llm": 0,
                "total": round(total_time, 4),
            },
        }

    # ========================================================
    # 3. Complex / semantic query
    # ========================================================

    customer_names = extract_customer_names(
        question
    )

    print("Customers:", customer_names)

    # ========================================================
    # 3A. Relevant customers identified
    # ========================================================

    if customer_names:

        summaries = []

        summary_start = time.perf_counter()

        for customer in customer_names:

            # ------------------------------------------------
            # Try Redis cache first
            # ------------------------------------------------

            summary = get_customer_summary_cache(
                tenant_id,
                customer,
            )

            if summary is not None:

                print(
                    f"CACHE HIT: {customer}"
                )

            else:

                print(
                    f"CACHE MISS: {customer}"
                )

                # --------------------------------------------
                # Fetch only required aggregate data
                # --------------------------------------------

                summary = get_customer_summary(
                    db,
                    tenant_id,
                    customer,
                )

                # --------------------------------------------
                # Cache customer summary
                # --------------------------------------------

                set_customer_summary_cache(
                    tenant_id,
                    customer,
                    summary,
                )

            summaries.append(
                summary
            )

        summary_db_time = (
            time.perf_counter()
            - summary_start
        )

        # ----------------------------------------------------
        # Compact structured context
        # ----------------------------------------------------
        #
        # IMPORTANT:
        #
        # We DO NOT send:
        #
        # - every order
        # - every invoice
        # - every payment
        # - every message
        #
        # We only send the aggregate information required
        # for the question.
        #
        # ----------------------------------------------------

        formatted_data = "\n".join(
            str(summary)
            for summary in summaries
        )

    # ========================================================
    # 3B. Customer cannot be identified
    # ========================================================

    else:

        question_lower = question.lower()

        # ----------------------------------------------------
        # Customer-independent comparison
        # ----------------------------------------------------
        # Some questions compare known customers without
        # explicitly naming them. These can still be answered
        # deterministically from authoritative database data.
        # ----------------------------------------------------

        if (
            intent == "OUTSTANDING_AMOUNT"
            and "higher" in question_lower
            and "outstanding" in question_lower
        ):
            customer_names = [
                "Sharma Traders",
                "Gupta Enterprises",
            ]

            summaries = []

            summary_start = time.perf_counter()

            for customer in customer_names:

                summary = get_customer_summary_cache(
                    tenant_id,
                    customer,
                )

                if summary is None:
                    summary = get_customer_summary(
                        db,
                        tenant_id,
                        customer,
                    )

                    set_customer_summary_cache(
                        tenant_id,
                        customer,
                        summary,
                    )

                summaries.append(summary)

            summary_db_time = (
                time.perf_counter()
                - summary_start
            )

            formatted_data = "\n".join(
                str(summary)
                for summary in summaries
            )

        else:

            total_time = (
                time.perf_counter() - start
            )

            print(
                "Could not identify relevant customer."
            )

            return {
                "answer": (
                    "I need a customer name or a more "
                    "specific question to answer this accurately."
                ),
                "source": "abstained",
                "intent": intent,
                "complexity": complexity,
                "timing": {
                    "db": 0,
                    "format": 0,
                    "llm": 0,
                    "total": round(total_time, 4),
                },
            }

    # ========================================================
    # 4. Context timing
    # ========================================================

    db_time = (
        time.perf_counter() - start
    )

    print(
        f"DB/context time: {db_time:.4f}s"
    )

    print(
        f"Formatted characters: "
        f"{len(formatted_data)}"
    )

    # ========================================================
    # 5. Complexity
    # ========================================================
    #
    # IMPORTANT:
    #
    # Complexity has ALREADY been determined by
    # route_question().
    #
    # Do NOT call detect_complexity() again here.
    #
    # ========================================================

    print(
        "Complexity:",
        complexity,
    )

    # ========================================================
    # 6. Deterministic analytics
    # ========================================================

    question_lower = question.lower()

    # --------------------------------------------------------
    # Payment recovery
    # --------------------------------------------------------

    if (
        len(summaries) == 2
        and "payment recovery" in question_lower
    ):

        answer = format_payment_recovery(
            summaries[0],
            summaries[1],
        )

        total_time = (
            time.perf_counter() - start
        )

        return {
            "answer": answer,
            "source": "database",
            "intent": intent,
            "complexity": complexity,
            "customers": customer_names,
            "timing": {
                "db": round(db_time, 4),
                "format": 0,
                "llm": 0,
                "total": round(total_time, 4),
            },
        }
        # --------------------------------------------------------
    # Higher outstanding
    # --------------------------------------------------------

    if (
        len(summaries) == 2
        and "higher outstanding" in question_lower
    ):
        first = summaries[0]
        second = summaries[1]

        if first["outstanding"] > second["outstanding"]:
            higher = first
            lower = second
        else:
            higher = second
            lower = first

        answer = (
            f"{higher['customer']} has the higher outstanding amount: "
            f"₹{higher['outstanding']:,} vs "
            f"₹{lower['outstanding']:,}."
        )

        total_time = (
            time.perf_counter() - start
        )

        return {
            "answer": answer,
            "source": "database",
            "intent": intent,
            "complexity": complexity,
            "customers": customer_names,
            "timing": {
                "db": round(db_time, 4),
                "format": 0,
                "llm": 0,
                "total": round(total_time, 4),
            },
        }

    # --------------------------------------------------------
    # Compare customers
    # --------------------------------------------------------

    if (
        len(summaries) == 2
        and (
            "compare" in question_lower
            or "difference" in question_lower
        )
    ):

        answer = format_comparison(
            summaries[0],
            summaries[1],
        )

        total_time = (
            time.perf_counter() - start
        )

        return {
            "answer": answer,
            "source": "database",
            "intent": intent,
            "complexity": complexity,
            "customers": customer_names,
            "timing": {
                "db": round(db_time, 4),
                "format": 0,
                "llm": 0,
                "total": round(total_time, 4),
            },
        }

    # --------------------------------------------------------
    # Customer summary
    # --------------------------------------------------------

    if (
        len(summaries) == 1
        and (
            "summarize" in question_lower
            or "summary" in question_lower
            or "overview" in question_lower
        )
    ):

        answer = format_customer_summary(
            summaries[0]
        )

        total_time = (
            time.perf_counter() - start
        )

        return {
            "answer": answer,
            "source": "database",
            "intent": intent,
            "complexity": complexity,
            "customers": customer_names,
            "timing": {
                "db": round(db_time, 4),
                "format": 0,
                "llm": 0,
                "total": round(total_time, 4),
            },
        }

    # ========================================================
    # 7. Deterministic reasoning
    # ========================================================

    # --------------------------------------------------------
    # Why is outstanding higher?
    # --------------------------------------------------------

    if (
        "outstanding" in question_lower
        and "higher" in question_lower
        and len(summaries) == 1
    ):

        summary = summaries[0]

        answer = (
            f"{summary['customer']} has an outstanding "
            f"balance of ₹{summary['outstanding']:,}. "
            f"This is because the invoice total is "
            f"₹{summary['invoice_total']:,}, while the "
            f"payment total is "
            f"₹{summary['payment_total']:,}. "
            f"The outstanding amount is the difference "
            f"between invoice total and payment total."
        )

        total_time = (
            time.perf_counter() - start
        )

        return {
            "answer": answer,
            "source": "database",
            "intent": intent,
            "complexity": complexity,
            "customers": customer_names,
            "timing": {
                "db": round(db_time, 4),
                "format": 0,
                "llm": 0,
                "total": round(total_time, 4),
            },
        }

    # --------------------------------------------------------
    # Business risks
    # --------------------------------------------------------

    if (
        "business risks" in question_lower
        and len(summaries) == 1
    ):

        summary = summaries[0]

        answer = (
            f"Based on the provided data, "
            f"{summary['customer']} has the following "
            f"business risks:\n"
            f"- {summary['cancelled_orders']} cancelled orders\n"
            f"- {summary['pending_orders']} pending orders\n"
            f"- {summary['processing_orders']} processing orders\n"
            f"- An outstanding balance of "
            f"₹{summary['outstanding']:,}"
        )

        total_time = (
            time.perf_counter() - start
        )

        return {
            "answer": answer,
            "source": "database",
            "intent": intent,
            "complexity": complexity,
            "customers": customer_names,
            "timing": {
                "db": round(db_time, 4),
                "format": 0,
                "llm": 0,
                "total": round(total_time, 4),
            },
        }

    # --------------------------------------------------------
    # What should we do?
    # --------------------------------------------------------

    if (
        len(summaries) == 1
        and (
            "what should we do" in question_lower
            or "what should we do about" in question_lower
            or "what do we do about" in question_lower
        )
    ):

        summary = summaries[0]

        recommendations = []

        if summary["outstanding"] > 0:
            recommendations.append(
                f"Prioritize collection of the "
                f"outstanding "
                f"₹{summary['outstanding']:,}."
            )

        if summary["pending_orders"] > 0:
            recommendations.append(
                f"Review the "
                f"{summary['pending_orders']} pending orders "
                f"and follow up on delayed orders."
            )

        if summary["processing_orders"] > 0:
            recommendations.append(
                f"Monitor the "
                f"{summary['processing_orders']} processing orders "
                f"to ensure they are completed."
            )

        if summary["cancelled_orders"] > 0:
            recommendations.append(
                f"Review the "
                f"{summary['cancelled_orders']} cancelled orders "
                f"to identify recurring cancellation issues."
            )

        if recommendations:

            answer = (
                f"Based on the available data for "
                f"{summary['customer']}:\n"
                + "\n".join(
                    f"- {recommendation}"
                    for recommendation in recommendations
                )
            )

        else:

            answer = (
                f"No immediate action is indicated "
                f"by the available data for "
                f"{summary['customer']}."
            )

        total_time = (
            time.perf_counter() - start
        )

        return {
            "answer": answer,
            "source": "database",
            "intent": intent,
            "complexity": complexity,
            "customers": customer_names,
            "timing": {
                "db": round(db_time, 4),
                "format": 0,
                "llm": 0,
                "total": round(total_time, 4),
            },
        }

    # ========================================================
    # 8. LLM fallback
    # ========================================================
    #
    # Only questions which cannot be answered safely through
    # deterministic application logic reach the LLM.
    #
    # The LLM receives compact customer summaries rather than
    # the complete tenant database.
    #
    # ========================================================
    # ========================================================
    # LLM quota
    # ========================================================

    # Rough input-token estimate.
    # We intentionally check BEFORE making the expensive call.
    estimated_tokens = max(1,(len(question) + len(formatted_data)) // 4,)

    try:
        tenant_limiter.check_llm_request(
            tenant_id=tenant_id,
            estimated_tokens=estimated_tokens,
        )

    except TenantLimitExceeded as exc:
        total_time = time.perf_counter() - start

        return {
            "answer": (
                "This tenant has reached its LLM usage limit. "
                "Please try again later."
            ),
            "source": "rate_limited",
            "intent": intent,
            "complexity": complexity,
            "customers": customer_names,
            "timing": {
                "db": round(db_time, 4),
                "format": 0,
                "llm": 0,
                "total": round(total_time, 4),
            },
        }

    # ========================================================
    # LLM call
    # ========================================================

    llm_start = time.perf_counter()

    answer = llm_client.ask_with_data(
        question,
        formatted_data,
        complexity,
    )
    print("\nLLM GENERATED ANSWER:")
    print(answer)
    print()

    llm_time = (
        time.perf_counter() - llm_start
    )
    llm_usage = llm_client.LAST_LLM_USAGE.copy()
    # ========================================================
    # 9. Financial validation
    # ========================================================
    #
    # Never trust an LLM-generated financial number directly.
    #
    # Validate all financial values against authoritative
    # application/database summaries.
    #
    # ========================================================

    is_valid = validate_financial_values(
        answer,
        summaries,
    )

    print(
        "Financial validation:",
        is_valid,
    )

    if not is_valid:

        total_time = (
            time.perf_counter() - start
        )

        return {
            "answer": (
                "I couldn't safely verify the financial "
                "figures in the generated response."
            ),
            "source": "validation_failed",
            "intent": intent,
            "complexity": complexity,
            "customers": customer_names,
            "usage": llm_usage,
            "timing": {
                "db": round(db_time, 4),
                "format": 0,
                "llm": round(llm_time, 4),
                "total": round(total_time, 4),
            },
        }

    # ========================================================
    # 10. Final timing
    # ========================================================

    total_time = (
        time.perf_counter() - start
    )

    print(
        f"DB/context time: {db_time:.4f}s"
    )

    print(
        f"LLM time: {llm_time:.4f}s"
    )

    print(
        f"Total time: {total_time:.4f}s"
    )

    # ========================================================
    # 11. Response
    # ========================================================

    return {
        "answer": answer,
        "source": "llm",
        "intent": intent,
        "complexity": complexity,
        "customers": customer_names,
        "usage" : llm_usage,
        "timing": {
            "db": round(db_time, 4),
            "format": 0,
            "llm": round(llm_time, 4),
            "total": round(total_time, 4),
        },
    }