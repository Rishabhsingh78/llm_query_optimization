import time
from dataclasses import dataclass
from threading import Lock


@dataclass
class TenantUsage:
    window_start: float
    request_count: int = 0
    llm_request_count: int = 0
    llm_tokens: int = 0


class TenantLimitExceeded(Exception):
    pass


class TenantLimiter:
    """
    In-memory tenant limiter.

    Production:
    - Redis should be used instead of in-memory state.
    - Limits should be shared across application instances.
    """

    WINDOW_SECONDS = 60 * 60

    MAX_REQUESTS_PER_HOUR = 400
    MAX_LLM_REQUESTS_PER_HOUR = 100
    MAX_LLM_TOKENS_PER_HOUR = 100_000

    def __init__(self):
        self._usage = {}
        self._lock = Lock()

    def _get_usage(self, tenant_id: int) -> TenantUsage:
        now = time.time()

        usage = self._usage.get(tenant_id)

        if usage is None:
            usage = TenantUsage(
                window_start=now,
            )
            self._usage[tenant_id] = usage
            return usage

        if now - usage.window_start >= self.WINDOW_SECONDS:
            usage = TenantUsage(
                window_start=now,
            )
            self._usage[tenant_id] = usage

        return usage

    def check_request(self, tenant_id: int):
        with self._lock:
            usage = self._get_usage(tenant_id)

            if usage.request_count >= self.MAX_REQUESTS_PER_HOUR:
                raise TenantLimitExceeded(
                    "Tenant request limit exceeded."
                )

            usage.request_count += 1

    def check_llm_request(
        self,
        tenant_id: int,
        estimated_tokens: int = 0,
    ):
        with self._lock:
            usage = self._get_usage(tenant_id)

            if (
                usage.llm_request_count
                >= self.MAX_LLM_REQUESTS_PER_HOUR
            ):
                raise TenantLimitExceeded(
                    "Tenant LLM request limit exceeded."
                )

            if (
                usage.llm_tokens + estimated_tokens
                > self.MAX_LLM_TOKENS_PER_HOUR
            ):
                raise TenantLimitExceeded(
                    "Tenant LLM token budget exceeded."
                )

            usage.llm_request_count += 1
            usage.llm_tokens += estimated_tokens

    def get_usage(self, tenant_id: int):
        with self._lock:
            usage = self._get_usage(tenant_id)

            return {
                "requests": usage.request_count,
                "llm_requests": usage.llm_request_count,
                "llm_tokens": usage.llm_tokens,
                "window_seconds": self.WINDOW_SECONDS,
            }


tenant_limiter = TenantLimiter()