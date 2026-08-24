import pytest

from app.services.tenant_limiter import (
    TenantLimiter,
    TenantLimitExceeded,
)


def test_tenant_request_limit():
    limiter = TenantLimiter()

    limiter.MAX_REQUESTS_PER_HOUR = 2

    limiter.check_request(tenant_id=1)
    limiter.check_request(tenant_id=1)

    with pytest.raises(TenantLimitExceeded):
        limiter.check_request(tenant_id=1)


def test_llm_request_limit():
    limiter = TenantLimiter()

    limiter.MAX_LLM_REQUESTS_PER_HOUR = 2

    limiter.check_llm_request(
        tenant_id=1,
        estimated_tokens=100,
    )

    limiter.check_llm_request(
        tenant_id=1,
        estimated_tokens=100,
    )

    with pytest.raises(TenantLimitExceeded):
        limiter.check_llm_request(
            tenant_id=1,
            estimated_tokens=100,
        )


def test_llm_token_budget_limit():
    limiter = TenantLimiter()

    limiter.MAX_LLM_TOKENS_PER_HOUR = 200

    limiter.check_llm_request(
        tenant_id=1,
        estimated_tokens=100,
    )

    limiter.check_llm_request(
        tenant_id=1,
        estimated_tokens=100,
    )

    with pytest.raises(TenantLimitExceeded):
        limiter.check_llm_request(
            tenant_id=1,
            estimated_tokens=1,
        )


def test_tenant_isolation():
    limiter = TenantLimiter()

    limiter.MAX_REQUESTS_PER_HOUR = 1

    limiter.check_request(
        tenant_id=1,
    )

    # Tenant 2 must have its own quota.
    limiter.check_request(
        tenant_id=2,
    )

    with pytest.raises(TenantLimitExceeded):
        limiter.check_request(
            tenant_id=1,
        )


def test_llm_usage_is_tracked():
    limiter = TenantLimiter()

    limiter.check_llm_request(
        tenant_id=1,
        estimated_tokens=500,
    )

    usage = limiter.get_usage(
        tenant_id=1,
    )

    assert usage["llm_requests"] == 1
    assert usage["llm_tokens"] == 500