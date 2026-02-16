from local_db import get_conn
from local_embed import embed_text


def add_memory(chat_id: int, content: str, importance: int = 1):
    embedding = embed_text(content)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO memories (chat_id, content, importance, embedding)
        VALUES (%s, %s, %s, %s)
        """,
        (chat_id, content, importance, embedding)
    )

    conn.commit()
    cur.close()
    conn.close()


def get_relevant_memories(chat_id: int, query: str, limit: int = 5):
    query_embedding = embed_text(query)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT content
        FROM memories
        WHERE chat_id = %s
        ORDER BY embedding <-> %s::vector
        LIMIT %s
        """,
        (chat_id, query_embedding, limit)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [row[0] for row in rows]

