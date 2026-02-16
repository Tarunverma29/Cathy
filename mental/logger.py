from database.db import get_conn

def log_emotional_state(user_id, chat_id, emotions, llm_data, risk_score):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO emotional_logs
        (
            telegram_user_id,
            chat_id,
            sadness,
            anger,
            fear,
            joy,
            risk_score,
            llm_risk,
            hopelessness,
            emotional_intensity
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        user_id,
        chat_id,
        emotions.get("sadness", 0),
        emotions.get("anger", 0),
        emotions.get("fear", 0),
        emotions.get("joy", 0),
        risk_score,
        llm_data["risk_level"],
        llm_data["hopelessness_level"],
        llm_data["emotional_intensity"]
    ))

    conn.commit()
    conn.close()

