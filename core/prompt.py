def build_prompt(character, memories, conversation, user_input):
    prompt = f"{character}\n\n"

    if memories:
        prompt += "Relevant Memories:\n"
        for m in memories:
            prompt += f"- {m}\n"
        prompt += "\n"

    if conversation:
        prompt += "Recent Conversation:\n"
        for role, content in conversation:
            prompt += f"{role}: {content}\n"
        prompt += "\n"

    prompt += f"User: {user_input}\nAssistant:"

    return prompt

