
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from app.models.models import Order, Invoice, Payment

def get_order_count(
    db: Session,
    tenant_id: int,
    customer_name=None,
):
    query = db.query(func.count(Order.id)).filter(
        Order.tenant_id == tenant_id
    )

    if customer_name:
        query = query.filter(
            Order.customer_name == customer_name
        )

    return query.scalar()


def get_total_invoice_amount(
    db: Session,
    tenant_id: int,
    customer_name=None,
):
    query = db.query(
        func.coalesce(func.sum(Invoice.amount), 0)
    ).filter(
        Invoice.tenant_id == tenant_id
    )

    if customer_name:
        query = query.filter(
            Invoice.customer_name == customer_name
        )

    return query.scalar()

def get_total_payment_amount(
    db: Session,
    tenant_id: int,
    customer_name=None,
):
    query = db.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(
        Payment.tenant_id == tenant_id
    )

    if customer_name:
        query = query.filter(
            Payment.customer_name == customer_name
        )

    return query.scalar()


def get_cancelled_order_count(
    db: Session,
    tenant_id: int,
    customer_name=None,
):
    query = db.query(func.count(Order.id)).filter(
        Order.tenant_id == tenant_id,
        Order.status == "cancelled",
    )

    if customer_name:
        query = query.filter(
            Order.customer_name == customer_name
        )

    return query.scalar()


def get_pending_order_count(
    db: Session,
    tenant_id: int,
    customer_name=None,
):
    query = db.query(func.count(Order.id)).filter(
        Order.tenant_id == tenant_id,
        Order.status == "pending",
    )

    if customer_name:
        query = query.filter(
            Order.customer_name == customer_name
        )

    return query.scalar()


def get_processing_order_count(
    db: Session,
    tenant_id: int,
    customer_name=None,
):
    query = db.query(func.count(Order.id)).filter(
        Order.tenant_id == tenant_id,
        Order.status == "processing",
    )

    if customer_name:
        query = query.filter(
            Order.customer_name == customer_name
        )

    return query.scalar()


def get_customer_summary(
    db: Session,
    tenant_id: int,
    customer_name: str,
):
    order_stats = (
        db.query(
            func.count(Order.id).label("orders"),
            func.sum(
                case(
                    (Order.status == "cancelled", 1),
                    else_=0,
                )
            ).label("cancelled_orders"),
            func.sum(
                case(
                    (Order.status == "pending", 1),
                    else_=0,
                )
            ).label("pending_orders"),
            func.sum(
                case(
                    (Order.status == "processing", 1),
                    else_=0,
                )
            ).label("processing_orders"),
        )
        .filter(
            Order.tenant_id == tenant_id,
            Order.customer_name == customer_name,
        )
        .one()
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
    )

    # Financial truth is calculated by application code.
    outstanding = invoice_total - payment_total

    return {
        "customer": customer_name,
        "orders": order_stats.orders or 0,
        "cancelled_orders": order_stats.cancelled_orders or 0,
        "pending_orders": order_stats.pending_orders or 0,
        "processing_orders": order_stats.processing_orders or 0,
        "invoice_total": invoice_total,
        "payment_total": payment_total,
        "outstanding": outstanding,
    }