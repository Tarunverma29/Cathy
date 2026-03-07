import re
import json
import ollama
from config.settings import MODEL_NAME

SYSTEM_PROMPT = """
You are a psychological state analyzer.

Analyze the user's message and return ONLY valid JSON in this format:

{
  "mood_state": "short description",
  "risk_level": 0-10,
  "hopelessness_level": 0-10,
  "emotional_intensity": 0-10,
  "requires_attention": true/false
}

Return ONLY the JSON object. No explanation, no markdown, no other text.
"""

def analyze_psychology(message: str):
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ],
        options={
            "temperature": 0.2
        }
    )

    content = response["message"]["content"]

    # Strip <think>...</think> blocks that qwen3 and similar models emit
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

    # Extract JSON object if wrapped in markdown code fences
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        content = match.group(0)

    try:
        return json.loads(content)
    except Exception:
        return {
            "mood_state": "unknown",
            "risk_level": 0,
            "hopelessness_level": 0,
            "emotional_intensity": 0,
            "requires_attention": False
        }
