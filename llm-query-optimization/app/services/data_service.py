from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import Order, Invoice, Payment, Message


def get_all_tenant_data(db: Session, tenant_id: int):
    return {
        "orders": db.query(Order).filter(
            Order.tenant_id == tenant_id
        ).all(),

        "invoices": db.query(Invoice).filter(
            Invoice.tenant_id == tenant_id
        ).all(),

        "payments": db.query(Payment).filter(
            Payment.tenant_id == tenant_id
        ).all(),

        "messages": db.query(Message).filter(
            Message.tenant_id == tenant_id
        ).all(),
    }


def format_data_for_llm(data):
    lines = []

    for order in data["orders"]:
        lines.append(
            f"Order: id={order.id}, customer={order.customer_name}, "
            f"status={order.status}, amount={order.amount}"
        )

    for invoice in data["invoices"]:
        lines.append(
            f"Invoice: id={invoice.id}, customer={invoice.customer_name}, "
            f"invoice_number={invoice.invoice_number}, amount={invoice.amount}"
        )

    for payment in data["payments"]:
        lines.append(
            f"Payment: id={payment.id}, customer={payment.customer_name}, "
            f"invoice_number={payment.invoice_number}, amount={payment.amount}"
        )

    for message in data["messages"]:
        lines.append(
            f"Message: id={message.id}, customer={message.customer_name}, "
            f"content={message.content}"
        )

    return "\n".join(lines)


def get_customer_data(
    db: Session,
    tenant_id: int,
    customer_name: str,
):
    return {
        "orders": db.query(Order).filter(
            Order.tenant_id == tenant_id,
            Order.customer_name == customer_name,
        ).all(),

        "invoices": db.query(Invoice).filter(
            Invoice.tenant_id == tenant_id,
            Invoice.customer_name == customer_name,
        ).all(),

        "payments": db.query(Payment).filter(
            Payment.tenant_id == tenant_id,
            Payment.customer_name == customer_name,
        ).all(),

        "messages": db.query(Message).filter(
            Message.tenant_id == tenant_id,
            Message.customer_name == customer_name,
        ).all(),
    }

def extract_customer_name(question: str):
    customers = [
        "Sharma Traders",
        "Gupta Enterprises",
    ]

    question_lower = question.lower()

    for customer in customers:
        if customer.lower() in question_lower:
            return customer

    return None

def get_outstanding_amount(
    db: Session,
    tenant_id: int,
    customer_name: str,
):
    total_invoices = (
        db.query(func.coalesce(func.sum(Invoice.amount), 0))
        .filter(
            Invoice.tenant_id == tenant_id,
            Invoice.customer_name == customer_name,
        )
        .scalar()
    )

    total_payments = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(
            Payment.tenant_id == tenant_id,
            Payment.customer_name == customer_name,
        )
        .scalar()
    )

    return total_invoices - total_payments


def extract_customer_names(question: str):
    customers = [
        "Sharma Traders",
        "Gupta Enterprises",
    ]

    question_lower = question.lower()

    return [
        customer
        for customer in customers
        if customer.lower() in question_lower
    ]