import json
import re
import statistics
import time

import requests

from evals.ground_truth import get_customer_metrics


# ================================================================
# Configuration
# ================================================================

TENANT_ID = 3

URL = (
    f"http://127.0.0.1:8000"
    f"/tenant/{TENANT_ID}/query"
)


# ================================================================
# Benchmark questions
# ================================================================

QUESTIONS = [
    # ------------------------------------------------------------
    # Deterministic lookups - Sharma Traders
    # ------------------------------------------------------------

    "What is the outstanding amount for Sharma Traders?",
    "How many orders does Sharma Traders have?",
    "What is the total invoice amount for Sharma Traders?",
    "What is the total payment amount for Sharma Traders?",
    "How many cancelled orders are there for Sharma Traders?",
    "How many pending orders are there for Sharma Traders?",
    "How many processing orders are there for Sharma Traders?",

    # ------------------------------------------------------------
    # Deterministic lookups - Gupta Enterprises
    # ------------------------------------------------------------

    "What is the outstanding amount for Gupta Enterprises?",
    "How many orders does Gupta Enterprises have?",
    "What is the total invoice amount for Gupta Enterprises?",
    "What is the total payment amount for Gupta Enterprises?",

    # ------------------------------------------------------------
    # Multi-customer queries
    # ------------------------------------------------------------

    "Compare Sharma Traders and Gupta Enterprises.",
    "What is the difference between Sharma Traders and Gupta Enterprises?",
    "Compare the payment recovery of Sharma Traders and Gupta Enterprises.",
    "Which customer has the higher outstanding amount?",

    # ------------------------------------------------------------
    # Reasoning / business questions
    # ------------------------------------------------------------

    "Why is Sharma Traders' outstanding higher?",
    "What business risks does Sharma Traders have?",
    "What should we do about Sharma Traders?",

    # ------------------------------------------------------------
    # Intentionally unsupported questions
    # ------------------------------------------------------------

    "What is Sharma Traders' profit margin?",
    "What is the average delivery time for Sharma Traders?",
    "Which order was placed most recently by Sharma Traders?",
    # Genuine LLM fallback
    # ------------------------------------------------------------

    "Explain the financial situation of Sharma Traders using the available data.",
    "What patterns do you see in Sharma Traders' business?",
    "Based on the available data, give me an assessment of Sharma Traders.",
    "What factors indicate that Sharma Traders may be a collection risk?",
    "What insights can you derive about Sharma Traders from the available data?",
]


# ================================================================
# LLM statistics
# ================================================================

llm_calls = 0
total_llm_cost = 0.0

total_prompt_tokens = 0
total_completion_tokens = 0
total_tokens = 0


# ================================================================
# Utility functions
# ================================================================

def extract_numbers(text):
    """
    Extract numeric values from an answer.

    Examples:
        ₹2,790,342 -> 2790342
        41 cancelled -> 41
        83.34% -> 83.34
    """

    if not text:
        return []

    matches = re.findall(
        r"[-+]?\d[\d,]*(?:\.\d+)?",
        text,
    )

    numbers = []

    for value in matches:
        value = value.replace(",", "")

        try:
            if "." in value:
                numbers.append(float(value))
            else:
                numbers.append(int(value))

        except ValueError:
            continue

    return numbers


def contains_number(text, expected):
    """
    Check whether the expected number exists in the answer.
    """

    numbers = extract_numbers(text)

    if isinstance(expected, float):
        return any(
            abs(number - expected) < 0.01
            for number in numbers
        )

    return any(
        number == expected
        for number in numbers
    )


def contains_abstention(text):
    """
    Detect whether the system explicitly says
    that the question cannot be answered safely.
    """

    if not text:
        return False

    text = text.lower()

    phrases = [
        "cannot determine",
        "can't determine",
        "cannot answer",
        "can't answer",
        "not enough information",
        "insufficient information",
        "not available",
        "unavailable",
        "cannot be determined",
        "can't be determined",
        "do not have enough",
        "don't have enough",
        "not provided",
        "not present in the data",
        "does not contain enough information",
        "couldn't safely verify",
        "could not safely verify",
        "need a customer name",
        "more specific question",
    ]

    return any(
        phrase in text
        for phrase in phrases
    )


def percentile(values, percentile_value):
    """
    Calculate percentile using linear interpolation.
    """

    if not values:
        return 0.0

    values = sorted(values)

    if len(values) == 1:
        return values[0]

    rank = (
        percentile_value / 100
    ) * (len(values) - 1)

    lower = int(rank)

    upper = min(
        lower + 1,
        len(values) - 1,
    )

    weight = rank - lower

    return (
        values[lower]
        + weight
        * (
            values[upper]
            - values[lower]
        )
    )


# ================================================================
# Ground truth
# ================================================================

def expected_result(question):
    """
    Build expected results from the database.

    No business numbers are hardcoded.
    """

    question_lower = question.lower()

    sharma = get_customer_metrics(
        TENANT_ID,
        "Sharma Traders",
    )

    gupta = get_customer_metrics(
        TENANT_ID,
        "Gupta Enterprises",
    )

    # Genuine LLM fallback
    # ------------------------------------------------------------

    llm_questions = (
        "explain the financial situation",
        "what patterns do you see",
        "give me an assessment",
        "what factors indicate",
        "what insights can you derive",
    )

    if any(
        phrase in question_lower
        for phrase in llm_questions
    ):
        return {
            "type": "llm_reasoning",
        }

    # ------------------------------------------------------------
    # Sharma Traders
    # ------------------------------------------------------------

    if "outstanding amount for sharma" in question_lower:
        return {
            "type": "numeric",
            "value": sharma["outstanding"],
        }

    if "how many orders does sharma" in question_lower:
        return {
            "type": "numeric",
            "value": sharma["orders"],
        }

    if "total invoice amount for sharma" in question_lower:
        return {
            "type": "numeric",
            "value": sharma["invoice_total"],
        }

    if "total payment amount for sharma" in question_lower:
        return {
            "type": "numeric",
            "value": sharma["payment_total"],
        }

    if (
        "cancelled orders" in question_lower
        and "sharma" in question_lower
    ):
        return {
            "type": "numeric",
            "value": sharma["cancelled_orders"],
        }

    if (
        "pending orders" in question_lower
        and "sharma" in question_lower
    ):
        return {
            "type": "numeric",
            "value": sharma["pending_orders"],
        }

    if (
        "processing orders" in question_lower
        and "sharma" in question_lower
    ):
        return {
            "type": "numeric",
            "value": sharma["processing_orders"],
        }

    # ------------------------------------------------------------
    # Gupta Enterprises
    # ------------------------------------------------------------

    if "outstanding amount for gupta" in question_lower:
        return {
            "type": "numeric",
            "value": gupta["outstanding"],
        }

    if "how many orders does gupta" in question_lower:
        return {
            "type": "numeric",
            "value": gupta["orders"],
        }

    if "total invoice amount for gupta" in question_lower:
        return {
            "type": "numeric",
            "value": gupta["invoice_total"],
        }

    if "total payment amount for gupta" in question_lower:
        return {
            "type": "numeric",
            "value": gupta["payment_total"],
        }

    # ------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------

    if (
        "compare sharma traders and gupta enterprises"
        in question_lower
        or
        "difference between sharma traders and gupta enterprises"
        in question_lower
    ):
        return {
            "type": "comparison",
            "values": [
                sharma["orders"],
                gupta["orders"],
                sharma["invoice_total"],
                gupta["invoice_total"],
                sharma["payment_total"],
                gupta["payment_total"],
                sharma["outstanding"],
                gupta["outstanding"],
            ],
        }

    # ------------------------------------------------------------
    # Payment recovery comparison
    # ------------------------------------------------------------

    if "compare the payment recovery" in question_lower:
        return {
            "type": "comparison",
            "values": [
                sharma["payment_recovery"],
                gupta["payment_recovery"],
            ],
        }

    # ------------------------------------------------------------
    # Higher outstanding
    # ------------------------------------------------------------

    if "which customer has the higher outstanding" in question_lower:
        return {
            "type": "numeric",
            "value": max(
                sharma["outstanding"],
                gupta["outstanding"],
            ),
        }

    # ------------------------------------------------------------
    # Why outstanding is higher
    # ------------------------------------------------------------

    if "why is sharma traders' outstanding higher" in question_lower:
        return {
            "type": "numeric",
            "value": sharma["outstanding"],
        }

    # ------------------------------------------------------------
    # Business risks
    # ------------------------------------------------------------

    if "what business risks does sharma traders have" in question_lower:
        return {
            "type": "numeric",
            "value": sharma["outstanding"],
        }

    # ------------------------------------------------------------
    # Recommendation
    # ------------------------------------------------------------

    if "what should we do about sharma traders" in question_lower:
        return {
            "type": "numeric",
            "value": sharma["outstanding"],
        }

    # ------------------------------------------------------------
    # Unsupported questions
    # ------------------------------------------------------------

    if (
        "profit margin" in question_lower
        or "average delivery time" in question_lower
        or "most recently" in question_lower
    ):
        return {
            "type": "abstain",
        }

    # ------------------------------------------------------------
    # Unknown / unverified
    # ------------------------------------------------------------

    return {
        "type": "unverified",
    }


# ================================================================
# Evaluate answer
# ================================================================

def evaluate_answer(answer, expected):
    """
    Evaluate the API answer against expected result.
    """

    if not answer:
        return False

    expected_type = expected.get("type")

    # ------------------------------------------------------------
    # Numeric
    # ------------------------------------------------------------

    if expected_type == "numeric":
        return contains_number(
            answer,
            expected["value"],
        )

    # ------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------

    if expected_type == "comparison":
        expected_values = expected.get(
            "values",
            [],
        )

        actual_numbers = extract_numbers(
            answer
        )

        for expected_value in expected_values:

            if isinstance(
                expected_value,
                float,
            ):
                found = any(
                    abs(
                        number
                        - expected_value
                    ) < 0.01
                    for number in actual_numbers
                )

            else:
                found = any(
                    number == expected_value
                    for number in actual_numbers
                )

            if not found:
                return False

        return True

    # ------------------------------------------------------------
    # Abstention
    # ------------------------------------------------------------

    if expected_type == "abstain":
        return contains_abstention(answer)

    # ------------------------------------------------------------
    # Safe abstention
    # ------------------------------------------------------------

    if expected_type == "safe_abstention":
        return contains_abstention(answer)

    # ------------------------------------------------------------
    # LLM reasoning
    # ------------------------------------------------------------

    if expected_type == "llm_reasoning":

        if contains_abstention(answer):
            return False

        if not answer.strip():
            return False

        # LLM should provide a meaningful response.
        # Very short responses usually indicate
        # truncation / validation failure.
        if len(answer.strip()) < 50:
            return False

        return True

# ================================================================
# Main benchmark
# ================================================================

def main():

    global llm_calls
    global total_llm_cost
    global total_prompt_tokens
    global total_completion_tokens
    global total_tokens

    results = []

    latencies = []

    successful_requests = 0
    evaluated_questions = 0
    correct_answers = 0

    print("=" * 70)
    print("OPTIMIZED BENCHMARK")
    print("=" * 70)

    for question in QUESTIONS:

        print()
        print("=" * 70)
        print(
            f"Question: {question}"
        )

        start = time.perf_counter()

        benchmark_result = {
            "question": question,
            "status": None,
            "answer": None,
            "expected": None,
            "correct": None,
            "client_latency": None,
            "usage": {},
        }

        try:

            response = requests.post(
                URL,
                json={
                    "question": question,
                },
                timeout=120,
            )

            latency = (
                time.perf_counter()
                - start
            )

            latencies.append(
                latency
            )

            benchmark_result[
                "client_latency"
            ] = round(
                latency,
                4,
            )

            benchmark_result[
                "status"
            ] = response.status_code

            successful_requests += (
                response.status_code == 200
            )

            if response.status_code != 200:

                benchmark_result[
                    "correct"
                ] = False

                benchmark_result[
                    "error"
                ] = response.text

                print(
                    f"Latency: {latency:.4f} seconds"
                )

                print(
                    "HTTP Error:",
                    response.status_code,
                )

                results.append(
                    benchmark_result
                )

                continue

            result = response.json()

            answer = result.get(
                "answer",
                "",
            )

            usage = (
                result.get("usage")
                or {}
            )

            benchmark_result[
                "answer"
            ] = answer

            benchmark_result[
                "usage"
            ] = usage

            # ----------------------------------------------------
            # Collect LLM usage from API response
            # ----------------------------------------------------

            if usage.get("model"):

                llm_calls += 1

                total_llm_cost += float(
                    usage.get(
                        "cost_usd"
                    )
                    or 0
                )

                total_prompt_tokens += int(
                    usage.get(
                        "prompt_tokens"
                    )
                    or 0
                )

                total_completion_tokens += int(
                    usage.get(
                        "completion_tokens"
                    )
                    or 0
                )

                total_tokens += int(
                    usage.get(
                        "total_tokens"
                    )
                    or 0
                )

            # ----------------------------------------------------
            # Expected result
            # ----------------------------------------------------

            expected = expected_result(
                question
            )

            benchmark_result[
                "expected"
            ] = expected

            correct = evaluate_answer(
                answer,
                expected,
            )

            benchmark_result[
                "correct"
            ] = correct

            # ----------------------------------------------------
            # Metrics
            # ----------------------------------------------------

            if correct is not None:

                evaluated_questions += 1

                if correct:
                    correct_answers += 1

            # ----------------------------------------------------
            # Console output
            # ----------------------------------------------------

            print(
                f"Latency: {latency:.4f} seconds"
            )

            print(
                "Answer:",
                answer,
            )

            print(
                "Expected:",
                expected,
            )

            print(
                "Correct:",
                correct,
            )

            results.append(
                benchmark_result
            )

        except Exception as exc:

            latency = (
                time.perf_counter()
                - start
            )

            benchmark_result[
                "client_latency"
            ] = round(
                latency,
                4,
            )

            benchmark_result[
                "correct"
            ] = False

            benchmark_result[
                "error"
            ] = str(exc)

            print(
                f"Latency: {latency:.4f} seconds"
            )

            print(
                "Error:",
                str(exc),
            )

            results.append(
                benchmark_result
            )

    # ============================================================
    # Final statistics
    # ============================================================

    average_latency = (
        statistics.mean(latencies)
        if latencies
        else 0.0
    )

    p50_latency = percentile(
        latencies,
        50,
    )

    p95_latency = percentile(
        latencies,
        95,
    )

    accuracy = (
        (
            correct_answers
            / evaluated_questions
        )
        * 100
        if evaluated_questions
        else 0.0
    )

    average_cost_per_query = (
        total_llm_cost
        / len(QUESTIONS)
        if QUESTIONS
        else 0.0
    )

    average_cost_per_llm_query = (
        total_llm_cost
        / llm_calls
        if llm_calls
        else 0.0
    )

    # ============================================================
    # Benchmark summary
    # ============================================================

    summary = {
        "questions": len(QUESTIONS),
        "successful_requests": successful_requests,
        "evaluated_questions": evaluated_questions,
        "correct_answers": correct_answers,
        "accuracy": round(
            accuracy,
            2,
        ),
        "average_latency": round(
            average_latency,
            4,
        ),
        "p50_latency": round(
            p50_latency,
            4,
        ),
        "p95_latency": round(
            p95_latency,
            4,
        ),
        "llm_calls": llm_calls,
        "total_llm_cost_usd": total_llm_cost,
        "average_cost_per_query_usd": (
            average_cost_per_query
        ),
        "average_cost_per_llm_query_usd": (
            average_cost_per_llm_query
        ),
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": (
            total_completion_tokens
        ),
        "total_tokens": total_tokens,
    }

    # ============================================================
    # Save results
    # ============================================================

    output = {
        "summary": summary,
        "results": results,
    }

    with open(
        "results/optimized_benchmark.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # ============================================================
    # Print final benchmark
    # ============================================================

    print()
    print("=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)

    print(
        f"Questions: {len(QUESTIONS)}"
    )

    print(
        f"Successful requests: "
        f"{successful_requests}"
    )

    print(
        f"Evaluated questions: "
        f"{evaluated_questions}"
    )

    print(
        f"Correct answers: "
        f"{correct_answers}/"
        f"{evaluated_questions}"
    )

    print(
        f"Accuracy: {accuracy:.2f}%"
    )

    print(
        f"Average latency: "
        f"{average_latency:.4f}s"
    )

    print(
        f"P50 latency: "
        f"{p50_latency:.4f}s"
    )

    print(
        f"P95 latency: "
        f"{p95_latency:.4f}s"
    )

    print()

    print(
        f"LLM calls: {llm_calls}"
    )

    print(
        f"Total LLM cost: "
        f"${total_llm_cost:.8f}"
    )

    print(
        f"Average cost/query: "
        f"${average_cost_per_query:.8f}"
    )

    print(
        f"Average cost/LLM query: "
        f"${average_cost_per_llm_query:.8f}"
    )

    print(
        f"Prompt tokens: "
        f"{total_prompt_tokens}"
    )

    print(
        f"Completion tokens: "
        f"{total_completion_tokens}"
    )

    print(
        f"Total tokens: "
        f"{total_tokens}"
    )

    print()
    print(
        "Results saved to "
        "results/optimized_benchmark.json"
    )


if __name__ == "__main__":
    main()