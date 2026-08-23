# from sqlalchemy import func
# from sqlalchemy.orm import Session

# from app.models.models import Order, Invoice, Payment


# def get_outstanding_amount(
#     db: Session,
#     tenant_id: int,
#     customer_name: str,
# ):
#     total_invoices = (
#         db.query(func.coalesce(func.sum(Invoice.amount), 0))
#         .filter(
#             Invoice.tenant_id == tenant_id,
#             Invoice.customer_name == customer_name,
#         )
#         .scalar()
#     )

#     total_payments = (
#         db.query(func.coalesce(func.sum(Payment.amount), 0))
#         .filter(
#             Payment.tenant_id == tenant_id,
#             Payment.customer_name == customer_name,
#         )
#         .scalar()
#     )

#     return total_invoices - total_payments


# def get_order_count(
#     db: Session,
#     tenant_id: int,
#     customer_name=None,
# ):
#     query = db.query(func.count(Order.id)).filter(
#         Order.tenant_id == tenant_id
#     )

#     if customer_name:
#         query = query.filter(
#             Order.customer_name == customer_name
#         )

#     return query.scalar()


# def get_cancelled_order_count(
#     db: Session,
#     tenant_id: int,
#     customer_name=None,
# ):
#     query = db.query(func.count(Order.id)).filter(
#         Order.tenant_id == tenant_id,
#         Order.status == "cancelled",
#     )

#     if customer_name:
#         query = query.filter(
#             Order.customer_name == customer_name
#         )

#     return query.scalar()


# def get_pending_order_count(
#     db: Session,
#     tenant_id: int,
#     customer_name=None,
# ):
#     query = db.query(func.count(Order.id)).filter(
#         Order.tenant_id == tenant_id,
#         Order.status == "pending",
#     )

#     if customer_name:
#         query = query.filter(
#             Order.customer_name == customer_name
#         )

#     return query.scalar()


# def get_processing_order_count(
#     db: Session,
#     tenant_id: int,
#     customer_name=None,
# ):
#     query = db.query(func.count(Order.id)).filter(
#         Order.tenant_id == tenant_id,
#         Order.status == "processing",
#     )

#     if customer_name:
#         query = query.filter(
#             Order.customer_name == customer_name
#         )

#     return query.scalar()


# def get_total_invoice_amount(
#     db: Session,
#     tenant_id: int,
#     customer_name=None,
# ):
#     query = db.query(
#         func.coalesce(func.sum(Invoice.amount), 0)
#     ).filter(
#         Invoice.tenant_id == tenant_id
#     )

#     if customer_name:
#         query = query.filter(
#             Invoice.customer_name == customer_name
#         )

#     return query.scalar()


# def get_total_payment_amount(
#     db: Session,
#     tenant_id: int,
#     customer_name=None,
# ):
#     query = db.query(
#         func.coalesce(func.sum(Payment.amount), 0)
#     ).filter(
#         Payment.tenant_id == tenant_id
#     )

#     if customer_name:
#         query = query.filter(
#             Payment.customer_name == customer_name
#         )

#     return query.scalar()



from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.models import Order, Invoice, Payment

from app.models.models import Order, Invoice


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
    order_count = get_order_count(
        db,
        tenant_id,
        customer_name,
    )

    invoice_total = get_total_invoice_amount(
        db,
        tenant_id,
        customer_name,
    )

    payment_total = get_total_payment_amount(
        db,
        tenant_id,
        customer_name,
    )

    cancelled = get_cancelled_order_count(
        db,
        tenant_id,
        customer_name,
    )

    pending = get_pending_order_count(
        db,
        tenant_id,
        customer_name,
    )

    processing = get_processing_order_count(
        db,
        tenant_id,
        customer_name,
    )

    # Financial truth is calculated by the application,
    # never by the LLM.
    outstanding = invoice_total - payment_total

    return {
        "customer": customer_name,

        # Operational facts
        "orders": order_count,
        "cancelled_orders": cancelled,
        "pending_orders": pending,
        "processing_orders": processing,

        # Authoritative financial facts
        "invoice_total": invoice_total,
        "payment_total": payment_total,
        "outstanding": outstanding,
    }

