import json

import redis


redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True,
)


SUMMARY_TTL = 300  # 5 minutes


def get_customer_summary_cache(
    tenant_id: int,
    customer_name: str,
):
    key = (
        f"customer_summary:"
        f"{tenant_id}:"
        f"{customer_name.lower()}"
    )

    cached = redis_client.get(key)

    if cached is None:
        print(f"CACHE MISS: {customer_name}")
        return None

    print(f"CACHE HIT: {customer_name}")

    return json.loads(cached)

def set_customer_summary_cache(
    tenant_id: int,
    customer_name: str,
    summary: dict,
):
    key = (
        f"customer_summary:"
        f"{tenant_id}:"
        f"{customer_name.lower()}"
    )

    redis_client.setex(
        key,
        SUMMARY_TTL,
        json.dumps(summary),
    )

    print(f"CACHE SET: {customer_name}")


def invalidate_customer_summary_cache(
    tenant_id: int,
    customer_name: str,
):
    key = (
        f"customer_summary:"
        f"{tenant_id}:"
        f"{customer_name.lower()}"
    )

    redis_client.delete(key)