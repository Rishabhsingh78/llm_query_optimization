import json
import statistics
import time

import requests

from evals.ground_truth import get_customer_metrics


TENANT_ID = 3

URL = (
    f"http://127.0.0.1:8000/"
    f"tenant/{TENANT_ID}/query"
)


QUESTIONS = [
    "What is the outstanding amount for Sharma Traders?",
    "What is the outstanding amount for Gupta Enterprises?",
    "How many orders are stuck?",
    "How many orders are completed?",
    "What is the total invoice amount?",
    "What is the total payment amount?",
    "How many invoices does Sharma Traders have?",
    "How many payments does Sharma Traders have?",
    "What is the total order value?",
    "Which customer has the most orders?",
    "Which customer has the highest invoice amount?",
    "Which customer has the highest payment amount?",
    "How many cancelled orders are there?",
    "How many pending orders are there?",
    "How many processing orders are there?",
    "How many messages are there for Sharma Traders?",
    "Compare Sharma Traders and Gupta Enterprises.",
    "What are the stuck orders for Sharma Traders?",
    "What is the total order value for Sharma Traders?",
    "What is the outstanding amount for a customer that does not exist?",
]


def percentile(values, percentile_value):
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


def extract_numbers(text):
    if not text:
        return []

    import re

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
            pass

    return numbers


def contains_number(text, expected):
    numbers = extract_numbers(text)

    if isinstance(expected, float):
        return any(
            abs(number - expected) < 0.01
            for number in numbers
        )

    return expected in numbers


def contains_abstention(text):
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
        "does not contain enough information",
    ]

    return any(
        phrase in text
        for phrase in phrases
    )


def expected_result(question):
    """
    Ground truth is derived directly from Postgres.

    This function deliberately avoids asking the LLM
    what the correct answer should be.
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

    if "outstanding amount for sharma" in question_lower:
        return {
            "type": "numeric",
            "value": sharma["outstanding"],
        }

    if "outstanding amount for gupta" in question_lower:
        return {
            "type": "numeric",
            "value": gupta["outstanding"],
        }

    if (
        "how many orders"
        in question_lower
        and "sharma"
        in question_lower
    ):
        return {
            "type": "numeric",
            "value": sharma["orders"],
        }

    if "total invoice amount" in question_lower:
        return {
            "type": "numeric",
            "value": (
                sharma["invoice_total"]
                if "sharma" in question_lower
                else (
                    sharma["invoice_total"]
                    + gupta["invoice_total"]
                )
            ),
        }

    if "total payment amount" in question_lower:
        return {
            "type": "numeric",
            "value": (
                sharma["payment_total"]
                if "sharma" in question_lower
                else (
                    sharma["payment_total"]
                    + gupta["payment_total"]
                )
            ),
        }

    if "cancelled orders" in question_lower:
        return {
            "type": "numeric",
            "value": (
                sharma["cancelled_orders"]
                + gupta["cancelled_orders"]
            ),
        }

    if "pending orders" in question_lower:
        return {
            "type": "numeric",
            "value": (
                sharma["pending_orders"]
                + gupta["pending_orders"]
            ),
        }

    if "processing orders" in question_lower:
        return {
            "type": "numeric",
            "value": (
                sharma["processing_orders"]
                + gupta["processing_orders"]
            ),
        }

    if "compare sharma" in question_lower:
        return {
            "type": "comparison",
            "customers": [
                "Sharma Traders",
                "Gupta Enterprises",
            ],
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

    if (
        "customer that does not exist"
        in question_lower
    ):
        return {
            "type": "abstain",
        }

    # These questions depend on fields that are not
    # represented by the current ground-truth implementation.
    return {
        "type": "unverified",
    }


def check_result(question, answer):
    expected = expected_result(question)

    if expected["type"] == "numeric":
        return contains_number(
            answer,
            expected["value"],
        )

    if expected["type"] == "comparison":
        for customer in expected["customers"]:
            if customer.lower() not in answer.lower():
                return False

        for value in expected["values"]:
            if not contains_number(answer, value):
                return False

        return True

    if expected["type"] == "abstain":
        return contains_abstention(answer)

    # We explicitly do not mark unsupported evaluations
    # as correct just because the answer looks plausible.
    return None


results = []

latencies = []

correct_count = 0
evaluated_count = 0
successful_requests = 0


for question in QUESTIONS:

    print("\n" + "=" * 70)
    print("Question:", question)

    start = time.perf_counter()

    try:
        response = requests.post(
            URL,
            json={
                "question": question,
            },
            timeout=60,
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        latencies.append(elapsed)

        print(
            "Latency:",
            round(elapsed, 4),
            "seconds",
        )

        if response.status_code != 200:
            print(
                "Status:",
                response.status_code,
            )

            print(
                "Error:",
                response.text,
            )

            results.append(
                {
                    "question": question,
                    "status": response.status_code,
                    "client_latency": round(
                        elapsed,
                        4,
                    ),
                    "correct": False,
                    "evaluation": "request_failed",
                }
            )

            continue

        successful_requests += 1

        body = response.json()

        answer = body.get(
            "answer",
            "",
        )

        expected = expected_result(
            question
        )

        correct = check_result(
            question,
            answer,
        )

        if correct is not None:
            evaluated_count += 1

            if correct:
                correct_count += 1

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
            {
                "question": question,
                "status": response.status_code,
                "client_latency": round(
                    elapsed,
                    4,
                ),
                "answer": answer,
                "expected": expected,
                "correct": correct,
                "timing": body.get(
                    "timing"
                ),
            }
        )

    except Exception as exc:

        elapsed = (
            time.perf_counter()
            - start
        )

        print(
            "Request failed:",
            exc,
        )

        results.append(
            {
                "question": question,
                "status": None,
                "client_latency": round(
                    elapsed,
                    4,
                ),
                "correct": False,
                "error": str(exc),
            }
        )


average_latency = (
    statistics.mean(latencies)
    if latencies
    else 0
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
    correct_count
    / evaluated_count
    * 100
    if evaluated_count
    else 0
)

success_rate = (
    successful_requests
    / len(QUESTIONS)
    * 100
    if QUESTIONS
    else 0
)


summary = {
    "questions": len(QUESTIONS),
    "successful_requests": successful_requests,
    "success_rate_percent": round(
        success_rate,
        2,
    ),
    "evaluated_questions": evaluated_count,
    "correct_answers": correct_count,
    "accuracy_percent": round(
        accuracy,
        2,
    ),
    "latency_seconds": {
        "average": round(
            average_latency,
            4,
        ),
        "p50": round(
            p50_latency,
            4,
        ),
        "p95": round(
            p95_latency,
            4,
        ),
    },
}


output = {
    "summary": summary,
    "results": results,
}


with open(
    "results/baseline.json",
    "w",
) as file:

    json.dump(
        output,
        file,
        indent=2,
        ensure_ascii=False,
    )


print("\n")
print("=" * 70)
print("BASELINE EVALUATION COMPLETE")
print("=" * 70)

print(
    f"Questions: {len(QUESTIONS)}"
)

print(
    f"Successful requests: "
    f"{successful_requests}"
)

print(
    f"Success rate: "
    f"{success_rate:.2f}%"
)

print(
    f"Evaluated questions: "
    f"{evaluated_count}"
)

print(
    f"Correct answers: "
    f"{correct_count}"
)

print(
    f"Accuracy: "
    f"{accuracy:.2f}%"
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

print(
    "\nResults saved to "
    "results/baseline.json"
)