def compute_risk(emotions: dict, llm_data: dict, streak_factor=1.0):
    sadness = emotions.get("sadness", 0)
    fear = emotions.get("fear", 0)
    anger = emotions.get("anger", 0)
    joy = emotions.get("joy", 0)

    emotion_component = (
        sadness * 5 +
        fear * 3 +
        anger * 2 -
        joy * 2
    )

    hopelessness_component = llm_data["hopelessness_level"] * 1.5
    intent_component = llm_data["risk_level"] * 2

    risk_score = emotion_component + hopelessness_component + intent_component
    risk_score *= streak_factor

    return round(risk_score, 2)

