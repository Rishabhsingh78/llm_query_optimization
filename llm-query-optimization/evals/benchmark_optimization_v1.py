import json
import time
import requests


URL = "http://127.0.0.1:8000/tenant/3/query"

QUESTIONS = [
    "What is the outstanding amount for Sharma Traders?",
    "How many orders does Sharma Traders have?",
    "What is the total invoice amount for Sharma Traders?",
    "What is the total payment amount for Sharma Traders?",
    "How many cancelled orders are there for Sharma Traders?",
    "How many pending orders are there for Sharma Traders?",
    "How many processing orders are there for Sharma Traders?",
    "Compare Sharma Traders and Gupta Enterprises.",
    "Summarize Sharma Traders.",
    "What is the difference between Sharma Traders and Gupta Enterprises?",
    "Why is Sharma Traders' outstanding higher?",
    "What business risks does Sharma Traders have?",
    "What should we do about Sharma Traders?",
    "Compare the payment recovery of Sharma Traders and Gupta Enterprises.",
]


results = []


for question in QUESTIONS:

    start = time.perf_counter()

    response = requests.post(
        URL,
        json={
            "question": question,
        },
    )

    elapsed = time.perf_counter() - start

    result = {
        "question": question,
        "status": response.status_code,
        "client_latency": round(elapsed, 4),
        "response": response.json(),
    }

    results.append(result)

    print("\n" + "=" * 70)
    print("Question:", question)
    print("Latency:", round(elapsed, 4), "seconds")
    print("Response:", response.json())


with open(
    "results/optimized_benchmark.json",
    "w",
) as f:
    json.dump(
        results,
        f,
        indent=2,
    )


print("\n")
print("=" * 70)
print("Benchmark complete")
print("Results saved to results/optimized_benchmark.json")