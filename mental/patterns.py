from database.db import get_conn

def get_recent_risk(user_id, limit=10):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT risk_score
        FROM emotional_logs
        WHERE telegram_user_id = %s
        ORDER BY created_at DESC
        LIMIT %s;
    """, (user_id, limit))

    rows = cur.fetchall()
    conn.close()

    return [r[0] for r in rows]


def detect_streak(user_id):
    recent = get_recent_risk(user_id)

    if len(recent) < 5:
        return 1.0

    high_count = sum(1 for r in recent if r > 10)

    if high_count >= 5:
        return 1.5
    elif high_count >= 3:
        return 1.2

    return 1.0

