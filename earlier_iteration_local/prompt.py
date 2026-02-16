def build_prompt(character, memories, conversation, user_input):
    memory_block = "\n".join(f"- {m}" for m in memories)

    convo_block = ""
    for role, msg in conversation:
        convo_block += f"{role}: {msg}\n"

    return f"""
SYSTEM:
{character}

MEMORY:
{memory_block}

CONVERSATION:
{convo_block}

USER:
{user_input}
""".strip()

