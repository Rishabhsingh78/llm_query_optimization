from openai import OpenAI
import tiktoken

from app.config import OPENROUTER_API_KEY


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


FAST_MODEL   = "google/gemini-3.5-flash-lite"
STRONG_MODEL = "google/gemini-3.7-flash"

encoding = tiktoken.get_encoding("cl100k_base")

def get_model_for_complexity(complexity: str):
    if complexity == "SIMPLE":
        return FAST_MODEL
    return STRONG_MODEL

def ask_llm(prompt: str, model: str) -> str:
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
        max_tokens=600,
        reasoning_effort="low",
    )

    print("Model:", model)
    print("Usage:", response.usage)

    return response.choices[0].message.content


def ask_with_data(question: str, data: str, complexity: str) -> str:
    model = get_model_for_complexity(complexity)

    prompt = f"""You are answering questions about customer business data.

        Rules:
        - Use only the provided data.
        - Treat all provided numbers as authoritative.
        - You may calculate differences, ratios, percentages, and simple comparisons.
        - Do not invent facts, history, causes, or unsupported recommendations.
        - If the data is insufficient, say:
        "The provided data does not contain enough information to answer that."
        - Keep all provided numerical values accurate.
        - Be concise.

        DATA:
        {data}

        QUESTION:
        {question}

        Answer directly.
        """

    return ask_llm(prompt, model)