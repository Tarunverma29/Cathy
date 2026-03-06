"""
mental/responder.py

Generates diverse, context-sensitive crisis and elevated-risk responses
instead of a single hardcoded message.
"""

import random
import ollama
from config.settings import MODEL_NAME


# ── Tiered response pools ───────────────────────────────────────────────────

_TIER_CRITICAL = [   # risk >= 15  (immediate danger signal)
    (
        "Hey… I need to stop and check on you for a second. "
        "What you're carrying right now sounds really heavy. "
        "Are you safe where you are?"
    ),
    (
        "I can hear how much pain is in your words right now. "
        "You matter — not just to me, but to people around you. "
        "If you're having thoughts of hurting yourself, please reach out to a crisis line. "
        "In India you can call iCall: 9152987821. I'm here too."
    ),
    (
        "Something you said is making me genuinely worried about you. "
        "I'm not going anywhere, but I need to ask — are you okay? "
        "Like, actually okay?"
    ),
    (
        "This feels like one of those moments where I really want to make sure "
        "you're not alone with all of this. Can you tell me what's going on?"
    ),
    (
        "You don't have to hold this by yourself. Whatever you're feeling right now — "
        "it's real, and it makes sense that it's overwhelming. "
        "Is there someone near you, or can we talk through it together?"
    ),
]

_TIER_HIGH = [   # 10 <= risk < 15  (elevated distress)
    "You seem like you're going through something really tough. "
    "I'm not going to pretend that's nothing. Want to talk about what's actually happening?",

    "I notice something's off with you today. "
    "You don't have to summarise it — just start wherever feels easiest.",

    "Okay, I'm paying attention. What's going on with you?",

    "You're allowed to not be okay. What's weighing on you right now?",

    "Something's clearly hitting hard. I'm not rushing you — take your time.",
]

_TIER_MODERATE = [   # 6 <= risk < 10  (noticeable distress)
    "You sound like you're carrying something today. Everything alright?",
    "Hey — you seem a bit off. Want to talk about it or just vent?",
    "I'm here. What's going on?",
    "Feels like today's been rough. What happened?",
]


# ── Emotion-specific add-ons ────────────────────────────────────────────────

def _emotion_note(emotions: dict) -> str:
    """Return a short empathetic line tailored to the dominant emotion."""
    if not emotions:
        return ""

    dominant = max(emotions, key=emotions.get)
    score = emotions[dominant]

    if score < 0.35:
        return ""

    notes = {
        "sadness": [
            "It sounds like there's a real sadness underneath this.",
            "There's a lot of heaviness in what you're sharing.",
        ],
        "anger": [
            "I can feel how frustrated and angry you are — that's valid.",
            "Your anger makes sense. Something isn't right and you know it.",
        ],
        "fear": [
            "It sounds like you're scared, and that fear is real.",
            "Fear that intense can feel completely suffocating. I get it.",
        ],
        "disgust": [
            "Something has really gotten under your skin.",
            "That kind of disgust usually means something important was violated.",
        ],
        "surprise": [
            "It sounds like something hit you out of nowhere.",
        ],
        "joy": [],   # no add-on for joy
    }

    pool = notes.get(dominant, [])
    return random.choice(pool) if pool else ""


# ── LLM-generated response for critical tier ───────────────────────────────

def _llm_crisis_response(user_input: str, emotions: dict, llm_data: dict) -> str:
    """
    Ask the LLM to write an empathetic, non-prescriptive check-in message.
    Falls back to a canned response on failure.
    """
    dominant_emotion = max(emotions, key=emotions.get) if emotions else "distress"
    mood = llm_data.get("mood_state", "unknown")

    system = (
        "You are a compassionate mental health companion. "
        "The user is in significant emotional distress. "
        "Write ONE short (2-4 sentence) human response that: "
        "1) Acknowledges their pain without minimising it. "
        "2) Gently checks if they are safe. "
        "3) Encourages them to keep talking or seek help. "
        "Do NOT use clinical language. Do NOT list hotlines unless it feels natural. "
        "Sound like a caring friend, not a helpline script. "
        f"The user's dominant emotion is: {dominant_emotion}. Mood state: {mood}."
    )

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_input},
            ],
            options={"temperature": 0.75, "top_p": 0.9},
        )
        return response["message"]["content"].strip()
    except Exception:
        return random.choice(_TIER_CRITICAL)


# ── Public API ──────────────────────────────────────────────────────────────

def build_crisis_response(
    user_input: str,
    emotions: dict,
    llm_data: dict,
    risk_score: float,
    use_llm: bool = True,
) -> str:
    """
    Return a context-aware, varied response for elevated risk situations.

    risk_score >= 15  → critical tier  (LLM-generated or canned)
    10 <= score < 15  → high tier
    6  <= score < 10  → moderate tier
    """

    emotion_note = _emotion_note(emotions)

    if risk_score >= 15:
        if use_llm:
            base = _llm_crisis_response(user_input, emotions, llm_data)
        else:
            base = random.choice(_TIER_CRITICAL)

    elif risk_score >= 10:
        base = random.choice(_TIER_HIGH)

    else:
        base = random.choice(_TIER_MODERATE)

    # Stitch emotion note on if we have one and it's not already in the LLM reply
    if emotion_note and emotion_note.lower()[:20] not in base.lower():
        return f"{emotion_note} {base}".strip()

    return base
