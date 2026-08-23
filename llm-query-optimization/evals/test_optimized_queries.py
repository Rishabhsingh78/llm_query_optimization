import requests


TENANT_ID = 3
URL = f"http://127.0.0.1:8000/tenant/{TENANT_ID}/query"


QUESTIONS = [
    "What is the outstanding amount for Sharma Traders?",
    "How many orders does Sharma Traders have?",
    "Compare Sharma Traders and Gupta Enterprises.",
]


for question in QUESTIONS:
    print("\n" + "=" * 60)
    print("Question:", question)

    response = requests.post(
        URL,
        json={"question": question},
    )

    print("Status:", response.status_code)
    print("Response:", response.json())