# pyrefly: ignore [missing-import]

from app.services.inancial_validator import validate_financial_values
from app.services.cache_service import set_customer_summary_cache
import time

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.services.cache_service import (
    get_customer_summary_cache,
    set_customer_summary_cache,
)

from app.db import (
    Base,
    SessionLocal,
    engine,
    test_connection,
)

from app.llm.client import ask_with_data

from app.services.analytics_service import (
    format_comparison,
    format_payment_recovery,
    format_customer_summary
)
from app.services.data_service import (
    extract_customer_name,
    extract_customer_names,
    get_all_tenant_data,
    get_outstanding_amount,
)

from app.services.intent_router import (
    detect_intent,
    detect_complexity,
)

from app.services.query_handlers import (
    get_order_count,
    get_total_invoice_amount,
    get_total_payment_amount,
    get_cancelled_order_count,
    get_pending_order_count,
    get_processing_order_count,
    get_customer_summary,
)


app = FastAPI(title="LLM Query Optimization")


# ============================================================
# Startup
# ============================================================

@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


# ============================================================
# Health
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

    print()
    print("START TIME : >>>>>>>>>>>>>>>>>>>>.")

    question = request.question.strip()

    # ========================================================
    # 1. Identify customer + intent
    # ========================================================

    customer_name = extract_customer_name(
        question
    )

    intent = detect_intent(
        question
    )

    print("Customer:", customer_name)
    print("Intent:", intent)

    # ========================================================
    # 2. Deterministic queries
    # ========================================================
    #
    # These queries do NOT need an LLM.
    #
    # SQL is responsible for exact calculations.
    #
    # This gives us:
    #
    # - better accuracy
    # - lower latency
    # - lower LLM cost
    #
    # ========================================================

    # --------------------------------------------------------
    # Outstanding amount
    # --------------------------------------------------------

    if (
        intent == "OUTSTANDING_AMOUNT"
        and customer_name
    ):
        outstanding = get_outstanding_amount(
            db,
            tenant_id,
            customer_name,
        )

        total_time = (
            time.perf_counter() - start
        )

        print(
            "Outstanding:",
            outstanding,
        )

        print(
            f"Total time: {total_time:.4f}s"
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
                "db": round(total_time, 4),
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
        result = get_order_count(
            db,
            tenant_id,
            customer_name,
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
                "db": round(total_time, 4),
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
        result = get_total_invoice_amount(
            db,
            tenant_id,
            customer_name,
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
                "db": round(total_time, 4),
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
        result = get_total_payment_amount(
            db,
            tenant_id,
            customer_name,
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
                "db": round(total_time, 4),
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
        result = get_cancelled_order_count(
            db,
            tenant_id,
            customer_name,
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
                "db": round(total_time, 4),
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
        result = get_pending_order_count(
            db,
            tenant_id,
            customer_name,
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
                "db": round(total_time, 4),
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
        result = get_processing_order_count(
            db,
            tenant_id,
            customer_name,
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
                "db": round(total_time, 4),
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

    print(
        "Customers:",
        customer_names,
    )

    # --------------------------------------------------------
    # 3A. We know which customers are relevant
    # --------------------------------------------------------

    if customer_names:

        summaries = []

        for customer in customer_names:

            summary = get_customer_summary_cache(
                tenant_id,
                customer,
            )

            if summary is not None:

                print(
                    f"Cache HIT: {customer}"
                )

            else:

                print(
                    f"Cache MISS: {customer}"
                )

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

        # Convert structured summaries
        # into compact LLM context.
        formatted_data = "\n".join(
            str(summary)
            for summary in summaries
        )

    # --------------------------------------------------------
    # 3B. We don't know the customer
    # --------------------------------------------------------

    else:

        # IMPORTANT:
        #
        # Do NOT send the complete tenant database
        # to the LLM.
        #
        # This was the original performance problem.
        #
        # Instead, safely refuse / ask for clarification.
        #

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
            "timing": {
                "db": 0,
                "format": 0,
                "llm": 0,
                "total": round(total_time, 4),
            },
        }

    # ========================================================
    # 4. DB / context timing
    # ========================================================

    db_time = (
        time.perf_counter() - start
    )

    print(
        "DB TIME:",
        db_time,
    )

    print(
        "Formatted characters:",
        len(formatted_data),
    )

    # ========================================================
    # 5. Complexity routing
    # ========================================================

    complexity = detect_complexity(
        question
    )

    print(
        "Complexity:",
        complexity,
    )

    # ========================================================
    # 6. LLM
    # ========================================================

    llm_start = time.perf_counter()
    # 6. Deterministic analytics

    question_lower = question.lower()

    if len(summaries) == 2 and "payment recovery" in question_lower:
        answer = format_payment_recovery(
            summaries[0],
            summaries[1],
        )

        total_time = time.perf_counter() - start

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

    if len(summaries) == 2 and (
        "compare" in question_lower
        or "difference" in question_lower
    ):
        answer = format_comparison(
            summaries[0],
            summaries[1],
        )

        total_time = time.perf_counter() - start

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
    

    if len(summaries) == 1 and (
    "summarize" in question.lower()
    or "summary" in question.lower()
):
        answer = format_customer_summary(summaries[0])

        total_time = time.perf_counter() - start

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
    # 6. Deterministic reasoning
    # ========================================================

    question_lower = question.lower()

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
            f"{summary['customer']} has an outstanding balance of "
            f"₹{summary['outstanding']:,}. "
            f"This is because the invoice total is "
            f"₹{summary['invoice_total']:,}, while the payment total is "
            f"₹{summary['payment_total']:,}. "
            f"The outstanding amount is the difference between "
            f"invoice total and payment total."
        )

        total_time = time.perf_counter() - start

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
            f"Based on the provided data, {summary['customer']} "
            f"has the following business risks:\n"
            f"- {summary['cancelled_orders']} cancelled orders\n"
            f"- {summary['pending_orders']} pending orders\n"
            f"- {summary['processing_orders']} processing orders\n"
            f"- An outstanding balance of "
            f"₹{summary['outstanding']:,}"
        )

        total_time = time.perf_counter() - start

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
    # 7. LLM

        # --------------------------------------------------------
    # What should we do about the customer?
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
                f"Prioritize collection of the outstanding "
                f"₹{summary['outstanding']:,}."
            )

        if summary["pending_orders"] > 0:
            recommendations.append(
                f"Review the {summary['pending_orders']} pending orders "
                f"and follow up on delayed orders."
            )

        if summary["processing_orders"] > 0:
            recommendations.append(
                f"Monitor the {summary['processing_orders']} processing "
                f"orders to ensure they are completed."
            )

        if summary["cancelled_orders"] > 0:
            recommendations.append(
                f"Review the {summary['cancelled_orders']} cancelled orders "
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
                f"No immediate action is indicated by the "
                f"available data for {summary['customer']}."
            )

        total_time = time.perf_counter() - start

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
        
    llm_start = time.perf_counter()

    answer = ask_with_data(
        question,
        formatted_data,
        complexity,
    )

    llm_time = (
        time.perf_counter() - llm_start
    )

    is_valid = validate_financial_values(
        answer,
        summaries,
    )
    print("Financial validation:", is_valid)

    if not is_valid:
        total_time = (
            time.perf_counter() - start
        )

        return {
            "answer": (
                "I couldn't safely verify the financial figures "
                "in the generated response."
            ),
            "source": "validation_failed",
            "intent": intent,
            "customers": customer_names,
            "timing": {
                "db": round(db_time, 2),
                "format": 0,
                "llm": round(llm_time, 2),
                "total": round(total_time, 2),
            },
        }

    # ========================================================
    # 7. Total timing
    # ========================================================

    total_time = (
        time.perf_counter() - start
    )

    print(
        f"DB time: {db_time:.2f}s"
    )

    print(
        f"LLM time: {llm_time:.2f}s"
    )

    print(
        f"Total time: {total_time:.2f}s"
    )

    # ========================================================
    # 8. Response
    # ========================================================

    return {
        "answer": answer,
        "source": "llm",
        "intent": intent,
        "complexity": complexity,
        "customers": customer_names,
        "timing": {
            "db": round(db_time, 2),
            "format": 0,
            "llm": round(llm_time, 2),
            "total": round(total_time, 2),
        },
    }