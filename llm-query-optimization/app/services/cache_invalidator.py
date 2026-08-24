from app.services.cache_service import (
    invalidate_customer_summary_cache,
)


def invalidate_after_payment_change(
    tenant_id: int,
    customer_name: str,
):
    """
    Payment changes directly affect:
    - payment_total
    - outstanding
    - payment recovery
    """

    return invalidate_customer_summary_cache(
        tenant_id=tenant_id,
        customer_name=customer_name,
    )


def invalidate_after_invoice_change(
    tenant_id: int,
    customer_name: str,
):
    """
    Invoice changes directly affect:
    - invoice_total
    - outstanding
    - payment recovery
    """

    return invalidate_customer_summary_cache(
        tenant_id=tenant_id,
        customer_name=customer_name,
    )


def invalidate_after_order_change(
    tenant_id: int,
    customer_name: str,
):
    """
    Order changes affect:
    - order count
    - cancelled orders
    - pending orders
    - processing orders
    """

    return invalidate_customer_summary_cache(
        tenant_id=tenant_id,
        customer_name=customer_name,
    )