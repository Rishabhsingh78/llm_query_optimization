from app.db import SessionLocal
import tiktoken

from app.services.data_service import (
    get_customer_data,
    format_data_for_llm,
)


TENANT_ID = 3
CUSTOMER = "Sharma Traders"


db = SessionLocal()

try:
    data = get_customer_data(
        db,
        TENANT_ID,
        CUSTOMER,
    )

    formatted_data = format_data_for_llm(data)

    print("Customer:", CUSTOMER)

    print("Orders:", len(data["orders"]))
    print("Invoices:", len(data["invoices"]))
    print("Payments:", len(data["payments"]))
    print("Messages:", len(data["messages"]))

    print("\nFormatted characters:", len(formatted_data))

    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = len(encoding.encode(formatted_data))

    print("Formatted tokens:", tokens)

finally:
    db.close()