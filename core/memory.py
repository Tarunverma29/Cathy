from database.db import get_conn
from core.embeddings import get_embedding

def add_memory(chat_id: int, text: str):
    embedding = get_embedding(text)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO memories (chat_id, content, embedding)
        VALUES (%s, %s, %s);
        """,
        (chat_id, text, embedding)
    )

    conn.commit()
    cur.close()
    conn.close()


def get_relevant_memories(chat_id: int, query: str, limit=5):
    query_embedding = get_embedding(query)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT content
        FROM memories
        WHERE chat_id = %s
        ORDER BY embedding <-> %s::vector
        LIMIT %s;
        """,
        (chat_id, query_embedding, limit)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [r[0] for r in rows]

