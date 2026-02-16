from database.db import get_conn
from database.chats import create_chat

def get_or_create_user(user):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT active_chat_id FROM telegram_users WHERE telegram_user_id = %s;",
        (user.id,)
    )

    row = cur.fetchone()

    if row:
        cur.close()
        conn.close()
        return row[0]

    chat_id = create_chat("Default Chat")

    cur.execute(
        """
        INSERT INTO telegram_users
        (telegram_user_id, username, first_name, active_chat_id)
        VALUES (%s, %s, %s, %s);
        """,
        (user.id, user.username, user.first_name, chat_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    return chat_id

