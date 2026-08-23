from app.db import SessionLocal
from app.services.query_handlers import (
    get_order_count,
    get_total_invoice_amount,
    get_total_payment_amount,
    get_cancelled_order_count,
    get_pending_order_count,
    get_processing_order_count,
    get_customer_summary
)


TENANT_ID = 3
CUSTOMER = "Sharma Traders"


db = SessionLocal()

try:
    order_count = get_order_count(
        db,
        TENANT_ID,
        CUSTOMER,
    )

    invoice_total = get_total_invoice_amount(
        db,
        TENANT_ID,
        CUSTOMER,
    )
    payment_total = get_total_payment_amount(
        db,
        TENANT_ID,
        CUSTOMER,
    )
    cancelled = get_cancelled_order_count(
        db,
        TENANT_ID,
        CUSTOMER,
    )

    pending = get_pending_order_count(
        db,
        TENANT_ID,
        CUSTOMER,
    )

    processing = get_processing_order_count(
        db,
        TENANT_ID,
        CUSTOMER,
    )
    summary = get_customer_summary(
    db,
    TENANT_ID,
    CUSTOMER,
    )

    print("\nCustomer Summary:")
    print(summary)

    print("Customer:", CUSTOMER)
    print("Order count:", order_count)
    print("Invoice total:", invoice_total)
    print("Payment total:", payment_total)
    print("Cancelled orders:", cancelled)
    print("Pending orders:", pending)
    print("Processing orders:", processing)

finally:
    db.close()