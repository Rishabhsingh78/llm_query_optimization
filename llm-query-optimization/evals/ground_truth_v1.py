from sqlalchemy import func

from app.db import SessionLocal
from app.models.models import Invoice, Payment


def get_outstanding(tenant_id: int, customer_name: str):
    db = SessionLocal()

    try:
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

    finally:
        db.close()


if __name__ == "__main__":
    result = get_outstanding(3, "Sharma Traders")
    print("Ground truth:", result)