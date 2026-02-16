import ollama
from config.settings import MODEL_NAME


def generate(character, conversation, user_input):
    messages = []

    # System message (persona)
    messages.append({
        "role": "system",
        "content": character
    })

    # Past conversation
    for role, content in conversation:
        if role.lower() == "user":
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "assistant", "content": content})

    # Current user message
    messages.append({"role": "user", "content": user_input})

    response = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        options={
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.2
        }
    )

    return response["message"]["content"]

