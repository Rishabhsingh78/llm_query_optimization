from app.db import SessionLocal
from app.services.query_handlers import get_customer_summary


TENANT_ID = 3

CUSTOMERS = [
    "Sharma Traders",
    "Gupta Enterprises",
]


db = SessionLocal()

try:
    summaries = []

    for customer in CUSTOMERS:
        summary = get_customer_summary(
            db,
            TENANT_ID,
            customer,
        )

        summaries.append(summary)

    print("\nComparison Summaries:")

    for summary in summaries:
        print(summary)

finally:
    db.close()