from local_db import get_conn


def add_message(chat_id: int, role: str, content: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO messages (chat_id, role, content)
        VALUES (%s, %s, %s)
        """,
        (chat_id, role, content)
    )

    conn.commit()
    cur.close()
    conn.close()


def get_recent_messages(chat_id: int, limit: int = 10):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT role, content
        FROM messages
        WHERE chat_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (chat_id, limit)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return list(reversed(rows))

