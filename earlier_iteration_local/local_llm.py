import ollama

MODEL_NAME = "qwen3:8b"  # or llama3:8b

def generate(prompt: str) -> str:
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.9}
    )

    return response["message"]["content"].strip()

