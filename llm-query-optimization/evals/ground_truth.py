from sqlalchemy import func

from app.db import SessionLocal
from app.models.models import Order, Invoice, Payment


def get_customer_metrics(
    tenant_id: int,
    customer_name: str,
):
    db = SessionLocal()

    try:
        orders = (
            db.query(func.count(Order.id))
            .filter(
                Order.tenant_id == tenant_id,
                Order.customer_name == customer_name,
            )
            .scalar()
            or 0
        )

        cancelled_orders = (
            db.query(func.count(Order.id))
            .filter(
                Order.tenant_id == tenant_id,
                Order.customer_name == customer_name,
                Order.status == "cancelled",
            )
            .scalar()
            or 0
        )

        pending_orders = (
            db.query(func.count(Order.id))
            .filter(
                Order.tenant_id == tenant_id,
                Order.customer_name == customer_name,
                Order.status == "pending",
            )
            .scalar()
            or 0
        )

        processing_orders = (
            db.query(func.count(Order.id))
            .filter(
                Order.tenant_id == tenant_id,
                Order.customer_name == customer_name,
                Order.status == "processing",
            )
            .scalar()
            or 0
        )

        invoice_total = (
            db.query(
                func.coalesce(func.sum(Invoice.amount), 0)
            )
            .filter(
                Invoice.tenant_id == tenant_id,
                Invoice.customer_name == customer_name,
            )
            .scalar()
            or 0
        )

        payment_total = (
            db.query(
                func.coalesce(func.sum(Payment.amount), 0)
            )
            .filter(
                Payment.tenant_id == tenant_id,
                Payment.customer_name == customer_name,
            )
            .scalar()
            or 0
        )

        outstanding = invoice_total - payment_total

        recovery_rate = (
            (payment_total / invoice_total) * 100
            if invoice_total
            else 0
        )

        return {
            "customer": customer_name,
            "orders": orders,
            "cancelled_orders": cancelled_orders,
            "pending_orders": pending_orders,
            "processing_orders": processing_orders,
            "invoice_total": invoice_total,
            "payment_total": payment_total,
            "outstanding": outstanding,
            "payment_recovery": round(recovery_rate, 2),
        }

    finally:
        db.close()


def get_customer_names(tenant_id: int):
    db = SessionLocal()

    try:
        rows = (
            db.query(Order.customer_name)
            .filter(Order.tenant_id == tenant_id)
            .distinct()
            .all()
        )

        return sorted(row[0] for row in rows)

    finally:
        db.close()


def get_comparison(
    tenant_id: int,
    customer_a: str,
    customer_b: str,
):
    return {
        customer_a: get_customer_metrics(
            tenant_id,
            customer_a,
        ),
        customer_b: get_customer_metrics(
            tenant_id,
            customer_b,
        ),
    }


def get_expected_outstanding(
    tenant_id: int,
    customer_name: str,
):
    return get_customer_metrics(
        tenant_id,
        customer_name,
    )["outstanding"]


if __name__ == "__main__":
    tenant_id = 3

    print("Customers:")
    for customer in get_customer_names(tenant_id):
        print(customer)

    print()

    print(
        "Sharma Traders:",
        get_customer_metrics(
            tenant_id,
            "Sharma Traders",
        ),
    )

    print()

    print(
        "Gupta Enterprises:",
        get_customer_metrics(
            tenant_id,
            "Gupta Enterprises",
        ),
    )