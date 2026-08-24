from openai import OpenAI
import tiktoken
LAST_LLM_USAGE = {}
from app.config import OPENROUTER_API_KEY, GEMINI_API_KEY


# client = OpenAI(
#     base_url="https://openrouter.ai/api/v1",
#     api_key=OPENROUTER_API_KEY,
# )

from app.config import GEMINI_API_KEY


client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
FAST_MODEL = "gemini-3.7-flash"
STRONG_MODEL = "gemini-3.7-flash"

encoding = tiktoken.get_encoding("cl100k_base")

def get_model_for_complexity(complexity: str):
    if complexity == "SIMPLE":
        return FAST_MODEL
    return STRONG_MODEL

def ask_llm(prompt: str, model: str) -> str:
    global LAST_LLM_USAGE

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

    usage = response.usage

    LAST_LLM_USAGE = {
        "model": model,
        "prompt_tokens": usage.prompt_tokens or 0,
        "completion_tokens": usage.completion_tokens or 0,
        "total_tokens": usage.total_tokens or 0,
        "cost_usd": 0.0,
    }

    print("Model:", model)
    print("Usage:", usage)

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