from database.db import get_conn
from database.chats import create_chat as db_create_chat
from database.chats import delete_chat as db_delete_chat
from database.chats import get_chats


# ---------- LOCAL CLI SESSION ----------
_local_active_chat = None


# ---------- LOCAL CLI FUNCTIONS ----------

def create_new_chat_local(title="New Chat"):
    global _local_active_chat
    chat_id = db_create_chat(title)
    _local_active_chat = chat_id
    return chat_id


def switch_chat_local(chat_id):
    global _local_active_chat
    _local_active_chat = chat_id


def get_active_chat_local():
    return _local_active_chat


# ---------- TELEGRAM FUNCTIONS ----------

def create_new_chat_telegram(user_id, title="New Chat"):
    chat_id = db_create_chat(title)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE telegram_users
        SET active_chat_id = %s
        WHERE telegram_user_id = %s;
        """,
        (chat_id, user_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    return chat_id


def get_active_chat_telegram(user_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT active_chat_id FROM telegram_users WHERE telegram_user_id = %s;",
        (user_id,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row[0] if row else None


def switch_chat_telegram(user_id, chat_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE telegram_users
        SET active_chat_id = %s
        WHERE telegram_user_id = %s;
        """,
        (chat_id, user_id)
    )

    conn.commit()
    cur.close()
    conn.close()


def delete_chat(chat_id):
    db_delete_chat(chat_id)


def get_all_chats():
    return get_chats()

