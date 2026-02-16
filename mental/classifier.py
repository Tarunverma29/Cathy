from transformers import pipeline

_emotion_model = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=None
)

def classify_emotions(text: str):
    results = _emotion_model(text)[0]

    return {r["label"]: float(r["score"]) for r in results}

