import random

from app.db import SessionLocal
from app.models.models import Tenant, Order, Invoice, Payment, Message


CUSTOMERS = [
    "Sharma Traders",
    "Gupta Enterprises",
    "Agarwal Stores",
    "Verma Industries",
    "Singh & Sons",
    "Patel Wholesale",
    "Kumar Traders",
    "Mehta Distributors",
    "Jain Enterprises",
    "Mishra Supplies",
]

ORDER_STATUSES = ["pending", "processing", "completed", "stuck", "cancelled"]


def seed():
    db = SessionLocal()

    try:
        # Start fresh every time
        db.query(Message).delete()
        db.query(Payment).delete()
        db.query(Invoice).delete()
        db.query(Order).delete()
        db.query(Tenant).delete()
        db.commit()

        tenants = [
            Tenant(name="Tenant A"),
            Tenant(name="Tenant B"),
        ]

        db.add_all(tenants)
        db.commit()

        for tenant in tenants:
            invoices = []
            payments = []
            orders = []
            messages = []

            # 2,000 orders
            for i in range(2000):
                customer = random.choice(CUSTOMERS)

                orders.append(
                    Order(
                        tenant_id=tenant.id,
                        customer_name=customer,
                        status=random.choice(ORDER_STATUSES),
                        amount=random.randint(1000, 100000),
                    )
                )

            # 1,500 invoices
            for i in range(1500):
                customer = random.choice(CUSTOMERS)
                invoice_number = f"INV-{tenant.id}-{i + 1}"

                invoices.append(
                    Invoice(
                        tenant_id=tenant.id,
                        customer_name=customer,
                        invoice_number=invoice_number,
                        amount=random.randint(5000, 200000),
                    )
                )

            # 2,500 payments
            for i in range(2500):
                customer = random.choice(CUSTOMERS)
                invoice_number = f"INV-{tenant.id}-{random.randint(1, 1500)}"

                payments.append(
                    Payment(
                        tenant_id=tenant.id,
                        customer_name=customer,
                        invoice_number=invoice_number,
                        amount=random.randint(1000, 100000),
                    )
                )

            # 1,000 messages
            for i in range(1000):
                customer = random.choice(CUSTOMERS)

                messages.append(
                    Message(
                        tenant_id=tenant.id,
                        customer_name=customer,
                        content=f"Message {i + 1} from {customer}",
                    )
                )

            db.add_all(orders)
            db.add_all(invoices)
            db.add_all(payments)
            db.add_all(messages)

            db.commit()

            print(f"Seeded {tenant.name}")

        print("Seeding completed successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()