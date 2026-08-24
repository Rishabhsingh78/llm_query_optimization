from app.services.cache_service import (
    set_customer_summary_cache,
    get_customer_summary_cache,
)

from app.services.cache_invalidator import (
    invalidate_after_payment_change,
    invalidate_after_invoice_change,
    invalidate_after_order_change,
)


def test_payment_change_invalidates_cache():
    tenant_id = 3
    customer = "Sharma Traders"

    summary = {
        "customer": customer,
        "invoice_total": 100000,
        "payment_total": 70000,
        "outstanding": 30000,
    }

    set_customer_summary_cache(
        tenant_id,
        customer,
        summary,
    )

    assert get_customer_summary_cache(
        tenant_id,
        customer,
    ) is not None

    invalidate_after_payment_change(
        tenant_id,
        customer,
    )

    assert get_customer_summary_cache(
        tenant_id,
        customer,
    ) is None


def test_invoice_change_invalidates_cache():
    tenant_id = 3
    customer = "Sharma Traders"

    set_customer_summary_cache(
        tenant_id,
        customer,
        {
            "outstanding": 30000,
        },
    )

    invalidate_after_invoice_change(
        tenant_id,
        customer,
    )

    assert get_customer_summary_cache(
        tenant_id,
        customer,
    ) is None


def test_order_change_invalidates_cache():
    tenant_id = 3
    customer = "Sharma Traders"

    set_customer_summary_cache(
        tenant_id,
        customer,
        {
            "orders": 100,
        },
    )

    invalidate_after_order_change(
        tenant_id,
        customer,
    )

    assert get_customer_summary_cache(
        tenant_id,
        customer,
    ) is None


# ADD THIS AT THE END
def test_cache_isolated_between_tenants():
    customer = "Sharma Traders"

    set_customer_summary_cache(
        3,
        customer,
        {
            "outstanding": 100000,
        },
    )

    set_customer_summary_cache(
        4,
        customer,
        {
            "outstanding": 500000,
        },
    )

    invalidate_after_payment_change(
        3,
        customer,
    )

    assert (
        get_customer_summary_cache(
            3,
            customer,
        )
        is None
    )

    assert (
        get_customer_summary_cache(
            4,
            customer,
        )
        == {
            "outstanding": 500000,
        }
    )