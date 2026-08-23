import json
import requests

from evals.ground_truth import get_outstanding


TENANT_ID = 3

URL = f"http://127.0.0.1:8000/tenant/{TENANT_ID}/query"


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


# IMPORTANT:
# Abhi sirf 1 question run karenge.
# API credits/time waste nahi karna.
QUESTIONS = QUESTIONS[:1]


results = []


for question in QUESTIONS:

    print(f"\nQuestion: {question}")

    response = requests.post(
        URL,
        json={
            "question": question
        },
    )

    print("Status:", response.status_code)

    if response.status_code != 200:
        print("Error:", response.text)
        continue

    result = response.json()

    llm_answer = result["answer"]

    print("LLM Answer:", llm_answer)

    # Ground truth for our current test question
    ground_truth = get_outstanding(
        TENANT_ID,
        "Sharma Traders",
    )

    print("Ground Truth:", ground_truth)

    # Simple correctness check for now
    normalized_answer = (
        llm_answer
        .replace(",", "")
        .replace("₹", "")
        .replace(" ", "")
    )

    correct = str(ground_truth) in normalized_answer

    print("Correct:", correct)

    results.append(
        {
            "question": question,
            "llm_answer": llm_answer,
            "ground_truth": ground_truth,
            "correct": correct,
            "timing": result.get("timing"),
        }
    )


# Save results
with open("results/baseline.json", "w") as file:
    json.dump(
        results,
        file,
        indent=2,
        ensure_ascii=False,
    )


print("\n----------------------------")
print("Baseline evaluation complete")
print("----------------------------")
print(f"Results saved: results/baseline.json")