from app.llm.client import ask_llm

print("Calling LLM...")

answer = ask_llm("Hey how are you today?")

print("Response:", answer)
print("Done")