from app.services.intent_router import detect_complexity, detect_intent

questions = [
    "What is the outstanding amount for Sharma Traders?",
    "How many orders are there?",
    "Compare Sharma Traders and Gupta Enterprises.",
    "Summarize Sharma Traders.",
    "What is the difference between Sharma and Gupta?",
    "Why is Sharma Traders' outstanding higher?",
    "What business risks does Sharma Traders have?",
    "What should we do about Sharma Traders?",
]


for question in questions:
    intent = detect_intent(question)

    complexity = None

    if intent == "COMPLEX":
        complexity = detect_complexity(question)

    print("\nQuestion:", question)
    print("Intent:", intent)
    print("Complexity:", complexity)