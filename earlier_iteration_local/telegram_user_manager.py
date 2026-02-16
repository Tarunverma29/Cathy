from local_db import get_conn
from local_chat_manager import create_chat
from datetime import datetime


def get_or_create_user(telegram_user):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT active_chat_id FROM telegram_users WHERE telegram_user_id = %s;",
        (telegram_user.id,)
    )

    row = cur.fetchone()

    if row:
        cur.execute(
            "UPDATE telegram_users SET last_seen = %s WHERE telegram_user_id = %s;",
            (datetime.now(), telegram_user.id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return row[0]

    # Create new user + default chat
    chat_id = create_chat("Default Chat")

    cur.execute(
        """
        INSERT INTO telegram_users
        (telegram_user_id, username, first_name, active_chat_id)
        VALUES (%s, %s, %s, %s);
        """,
        (
            telegram_user.id,
            telegram_user.username,
            telegram_user.first_name,
            chat_id
        )
    )

    cur.execute(
        """
        INSERT INTO telegram_user_chats (telegram_user_id, chat_id)
        VALUES (%s, %s);
        """,
        (telegram_user.id, chat_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    return chat_id


def get_user_chats(telegram_user_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT c.id, c.title
        FROM chats c
        JOIN telegram_user_chats tuc
        ON c.id = tuc.chat_id
        WHERE tuc.telegram_user_id = %s
        ORDER BY c.created_at DESC;
        """,
        (telegram_user_id,)
    )

    chats = cur.fetchall()
    cur.close()
    conn.close()
    return chats


def set_active_chat(telegram_user_id, chat_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE telegram_users
        SET active_chat_id = %s
        WHERE telegram_user_id = %s;
        """,
        (chat_id, telegram_user_id)
    )

    conn.commit()
    cur.close()
    conn.close()


def create_user_chat(telegram_user_id, title):
    chat_id = create_chat(title)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO telegram_user_chats (telegram_user_id, chat_id)
        VALUES (%s, %s);
        """,
        (telegram_user_id, chat_id)
    )

    cur.execute(
        """
        UPDATE telegram_users
        SET active_chat_id = %s
        WHERE telegram_user_id = %s;
        """,
        (chat_id, telegram_user_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    return chat_id

