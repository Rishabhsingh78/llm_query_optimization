import json

import redis


redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True,
)


SUMMARY_TTL = 300


def _normalize_customer_name(customer_name: str) -> str:
    return " ".join(
        customer_name.lower().strip().split()
    )


def _cache_key(
    tenant_id: int,
    customer_name: str,
) -> str:
    normalized_name = _normalize_customer_name(
        customer_name
    )

    return (
        f"customer_summary:"
        f"{tenant_id}:"
        f"{normalized_name}"
    )


def get_customer_summary_cache(
    tenant_id: int,
    customer_name: str,
):
    key = _cache_key(
        tenant_id,
        customer_name,
    )

    cached = redis_client.get(key)

    if cached is None:
        print(
            f"CACHE MISS: "
            f"tenant={tenant_id}, "
            f"customer={customer_name}"
        )
        return None

    print(
        f"CACHE HIT: "
        f"tenant={tenant_id}, "
        f"customer={customer_name}"
    )

    return json.loads(cached)


def set_customer_summary_cache(
    tenant_id: int,
    customer_name: str,
    summary: dict,
):
    key = _cache_key(
        tenant_id,
        customer_name,
    )

    redis_client.setex(
        key,
        SUMMARY_TTL,
        json.dumps(summary),
    )

    print(
        f"CACHE SET: "
        f"tenant={tenant_id}, "
        f"customer={customer_name}"
    )


def invalidate_customer_summary_cache(
    tenant_id: int,
    customer_name: str,
):
    key = _cache_key(
        tenant_id,
        customer_name,
    )

    deleted = redis_client.delete(key)

    print(
        f"CACHE INVALIDATE: "
        f"tenant={tenant_id}, "
        f"customer={customer_name}, "
        f"deleted={deleted}"
    )

    return deleted > 0