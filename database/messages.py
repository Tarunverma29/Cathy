from .db import get_conn


def get_recent_messages(chat_id, limit=6):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT role, content
        FROM messages
        WHERE chat_id = %s
        ORDER BY created_at DESC
        LIMIT %s;
    """, (chat_id, limit))

    rows = cur.fetchall()
    conn.close()

    # Reverse so oldest first
    rows.reverse()

    return [(row[0], row[1]) for row in rows]


def save_message(chat_id, role, content):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO messages (chat_id, role, content)
        VALUES (%s, %s, %s);
    """, (chat_id, role, content))

    conn.commit()
    conn.close()

