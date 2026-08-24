import time
from typing import Optional

import tiktoken
from openai import OpenAI

from app.config import OPENROUTER_API_KEY


# ============================================================
# OpenRouter client
# ============================================================

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


# ============================================================
# Models
# ============================================================

FAST_MODEL = "google/gemini-3.7-flash"
STRONG_MODEL = "google/gemini-3.1-pro-preview"


def get_model_for_complexity(complexity: str) -> str:
    if complexity == "SIMPLE":
        return FAST_MODEL

    return STRONG_MODEL


# ============================================================
# Tokenizer
# ============================================================

encoding = tiktoken.get_encoding("cl100k_base")


# ============================================================
# Pricing
# ============================================================

MODEL_PRICING = {
    FAST_MODEL: {
        "input_per_million": 0.375,
        "output_per_million": 1.875,
    },
    STRONG_MODEL: {
        "input_per_million": 2.0,
        "output_per_million": 12.0,
    },
}


def calculate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:

    pricing = MODEL_PRICING.get(model)

    if pricing is None:
        return 0.0

    input_cost = (
        prompt_tokens / 1_000_000
    ) * pricing["input_per_million"]

    output_cost = (
        completion_tokens / 1_000_000
    ) * pricing["output_per_million"]

    return round(
        input_cost + output_cost,
        10,
    )


# ============================================================
# LLM configuration
# ============================================================

MAX_OUTPUT_TOKENS = {
    FAST_MODEL: 300,
    STRONG_MODEL: 400,
}

LLM_TIMEOUT_SECONDS = 15

MAX_LLM_RETRIES = 1

RETRY_DELAY_SECONDS = 0.5


# ============================================================
# Last LLM usage
# ============================================================

LAST_LLM_USAGE = {}


# ============================================================
# LLM call
# ============================================================

def ask_llm(
    prompt: str,
    model: str,
) -> Optional[str]:

    global LAST_LLM_USAGE

    LAST_LLM_USAGE = {}

    response = None

    for attempt in range(
        MAX_LLM_RETRIES + 1
    ):

        try:

            print(
                f"Calling LLM: model={model}, "
                f"attempt={attempt + 1}"
            )

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a business data assistant. "
                            "Answer only from the provided data. "
                            "Do not invent facts. "
                            "Be concise and accurate."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0,
                max_tokens=MAX_OUTPUT_TOKENS.get(
                    model,
                    400,
                ),
                timeout=LLM_TIMEOUT_SECONDS,
            )

            # Successful request
            break

        except Exception as exc:

            error_text = str(exc).lower()

            print(
                f"LLM request failed: {exc}"
            )

            # ==================================================
            # Permanent failures
            # ==================================================
            #
            # 402 means credits/budget issue.
            # Retrying will not solve it.
            #
            # ==================================================

            if (
                "402" in error_text
                or "credits" in error_text
                or "insufficient" in error_text
                or "in_flight_budget" in error_text
            ):

                print(
                    "Permanent LLM failure. "
                    "Not retrying."
                )

                LAST_LLM_USAGE = {}

                return None

            # ==================================================
            # Retry temporary failures
            # ==================================================

            if attempt < MAX_LLM_RETRIES:

                print(
                    "Temporary LLM failure. "
                    f"Retrying in "
                    f"{RETRY_DELAY_SECONDS}s..."
                )

                time.sleep(
                    RETRY_DELAY_SECONDS
                )

                continue

            # ==================================================
            # All attempts failed
            # ==================================================

            print(
                "LLM request failed after "
                "all retry attempts."
            )

            LAST_LLM_USAGE = {}

            return None

    # ========================================================
    # Safety check
    # ========================================================

    if response is None:
        return None

    if not response.choices:
        print(
            "LLM returned no choices."
        )

        return None

    message = response.choices[0].message

    if message is None:
        return None

    answer = message.content

    if not answer:
        print(
            "LLM returned an empty response."
        )

        return None

    # ============================================================
    # TOKEN + COST TRACKING
    # ============================================================

    usage = response.usage

    prompt_tokens = (
        getattr(
            usage,
            "prompt_tokens",
            0,
        )
        or 0
    )

    completion_tokens = (
        getattr(
            usage,
            "completion_tokens",
            0,
        )
        or 0
    )

    total_tokens = (
        getattr(
            usage,
            "total_tokens",
            0,
        )
        or (
            prompt_tokens
            + completion_tokens
        )
    )

    # OpenRouter may provide actual cost.
    cost_usd = getattr(
        usage,
        "cost",
        None,
    )

    # Fallback to local calculation.
    if cost_usd is None:

        cost_usd = calculate_cost(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    cost_usd = float(
        cost_usd or 0.0
    )

    LAST_LLM_USAGE = {
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cost_usd": cost_usd,
    }

    print(
        "Model:",
        model,
    )

    print(
        "Prompt tokens:",
        prompt_tokens,
    )

    print(
        "Completion tokens:",
        completion_tokens,
    )

    print(
        "Total tokens:",
        total_tokens,
    )

    print(
        "Actual/estimated cost USD:",
        cost_usd,
    )

    return answer


# ============================================================
# LLM with customer data
# ============================================================

def ask_with_data(
    question: str,
    data: str,
    complexity: str,
) -> Optional[str]:

    model = get_model_for_complexity(
        complexity
    )

    prompt = f"""
Answer using only the DATA below.

Rules:
- Do not invent facts.
- Treat the provided numbers as authoritative.
- Keep numerical values accurate.
- Simple calculations are allowed.
- Do not invent causes or unsupported facts.
- If the data is insufficient, say:
"The provided data does not contain enough information to answer that."
- Keep the answer concise.
- Answer in at most 150 words.
- Complete the answer.
- Do not stop mid-sentence.

DATA:
{data}

QUESTION:
{question}

Answer directly.
"""

    return ask_llm(
        prompt=prompt,
        model=model,
    )