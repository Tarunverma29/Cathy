from database.db import get_conn

def create_chat(title: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO chats (title) VALUES (%s) RETURNING id;",
        (title,)
    )

    chat_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return chat_id


def delete_chat(chat_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM chats WHERE id = %s;", (chat_id,))
    conn.commit()

    cur.close()
    conn.close()


def get_chats():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, title FROM chats ORDER BY created_at DESC;")
    chats = cur.fetchall()

    cur.close()
    conn.close()

    return chats

