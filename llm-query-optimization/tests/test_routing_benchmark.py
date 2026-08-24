from app.services.intent_router import route_question


QUESTIONS = [
    (
        "What is the outstanding amount for Sharma Traders?",
        "OUTSTANDING_AMOUNT",
        "DETERMINISTIC",
    ),
    (
        "How many orders does Sharma Traders have?",
        "ORDER_COUNT",
        "DETERMINISTIC",
    ),
    (
        "What is the total invoice amount for Sharma Traders?",
        "INVOICE_TOTAL",
        "DETERMINISTIC",
    ),
    (
        "What is the total payment amount for Sharma Traders?",
        "PAYMENT_TOTAL",
        "DETERMINISTIC",
    ),
    (
        "How many cancelled orders are there for Sharma Traders?",
        "CANCELLED_ORDER_COUNT",
        "DETERMINISTIC",
    ),
    (
        "How many pending orders are there for Sharma Traders?",
        "PENDING_ORDER_COUNT",
        "DETERMINISTIC",
    ),
    (
        "How many processing orders are there for Sharma Traders?",
        "PROCESSING_ORDER_COUNT",
        "DETERMINISTIC",
    ),
    (
        "What is the outstanding amount for Gupta Enterprises?",
        "OUTSTANDING_AMOUNT",
        "DETERMINISTIC",
    ),
    (
        "How many orders does Gupta Enterprises have?",
        "ORDER_COUNT",
        "DETERMINISTIC",
    ),
    (
        "What is the total invoice amount for Gupta Enterprises?",
        "INVOICE_TOTAL",
        "DETERMINISTIC",
    ),
    (
        "What is the total payment amount for Gupta Enterprises?",
        "PAYMENT_TOTAL",
        "DETERMINISTIC",
    ),
    (
        "Compare Sharma Traders and Gupta Enterprises.",
        "COMPLEX",
        "SIMPLE",
    ),
    (
        "What is the difference between Sharma Traders and Gupta Enterprises?",
        "COMPLEX",
        "SIMPLE",
    ),
    (
        "Compare the payment recovery of Sharma Traders and Gupta Enterprises.",
        "COMPLEX",
        "SIMPLE",
    ),
    (
        "Which customer has the higher outstanding amount?",
        "OUTSTANDING_COMPARISON",
        "DETERMINISTIC",
    ),
    (
        "Why is Sharma Traders' outstanding higher?",
        "COMPLEX",
        "HARD",
    ),
    (
        "What business risks does Sharma Traders have?",
        "COMPLEX",
        "HARD",
    ),
    (
        "What should we do about Sharma Traders?",
        "COMPLEX",
        "HARD",
    ),
    (
        "What is Sharma Traders' profit margin?",
        "UNSUPPORTED",
        "DETERMINISTIC",
    ),
    (
        "What is the average delivery time for Sharma Traders?",
        "UNSUPPORTED",
        "DETERMINISTIC",
    ),
    (
        "Which order was placed most recently by Sharma Traders?",
        "UNSUPPORTED",
        "DETERMINISTIC",
    ),
    (
        "Explain the financial situation of Sharma Traders using the available data.",
        "COMPLEX",
        "HARD",
    ),
]


def test_routing_benchmark():
    correct = 0

    print("\n" + "=" * 70)
    print("ROUTING BENCHMARK")
    print("=" * 70)

    for question, expected_intent, expected_complexity in QUESTIONS:

        result = route_question(question)

        intent_correct = result.intent == expected_intent
        complexity_correct = result.complexity == expected_complexity

        is_correct = (
            intent_correct
            and complexity_correct
        )

        if is_correct:
            correct += 1

        print("\nQuestion:", question)
        print(
            "Expected:",
            expected_intent,
            expected_complexity,
        )
        print(
            "Actual:",
            result.intent,
            result.complexity,
        )
        print(
            "Confidence:",
            result.confidence,
        )
        print(
            "Correct:",
            is_correct,
        )

    accuracy = (
        correct / len(QUESTIONS)
    ) * 100

    print("\n" + "=" * 70)
    print(
        f"Routing accuracy: "
        f"{correct}/{len(QUESTIONS)} "
        f"({accuracy:.2f}%)"
    )
    print("=" * 70)

    assert correct == len(QUESTIONS)