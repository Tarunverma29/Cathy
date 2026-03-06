"""
web/backend/db.py

Creates the web_users and web_messages tables if they don't exist.
Reuses your existing get_conn() from database/db.py.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from database.db import get_conn


def init_tables():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS web_users (
            id          SERIAL PRIMARY KEY,
            email       TEXT UNIQUE NOT NULL,
            username    TEXT NOT NULL,
            password    TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS web_chats (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER REFERENCES web_users(id) ON DELETE CASCADE,
            title       TEXT DEFAULT 'New Chat',
            created_at  TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS web_messages (
            id          SERIAL PRIMARY KEY,
            chat_id     INTEGER REFERENCES web_chats(id) ON DELETE CASCADE,
            role        TEXT NOT NULL,
            content     TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT NOW()
        );
    """)

    # Web users also get emotional logs — reuse same table, web_user_id stored separately
    cur.execute("""
        ALTER TABLE emotional_logs
        ADD COLUMN IF NOT EXISTS web_user_id INTEGER REFERENCES web_users(id);
    """)

    conn.commit()
    cur.close()
    conn.close()


def get_recent_web_messages(chat_id: int, limit: int = 10):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT role, content FROM web_messages
        WHERE chat_id = %s
        ORDER BY created_at DESC
        LIMIT %s;
    """, (chat_id, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    rows.reverse()
    return [(r[0], r[1]) for r in rows]


def save_web_message(chat_id: int, role: str, content: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO web_messages (chat_id, role, content)
        VALUES (%s, %s, %s) RETURNING id;
    """, (chat_id, role, content))
    msg_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return msg_id


def create_web_chat(user_id: int, title: str = "New Chat") -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO web_chats (user_id, title)
        VALUES (%s, %s) RETURNING id;
    """, (user_id, title))
    chat_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return chat_id


def get_user_chats(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, created_at FROM web_chats
        WHERE user_id = %s
        ORDER BY created_at DESC;
    """, (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def log_web_emotional_state(web_user_id, chat_id, emotions, llm_data, risk_score):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO emotional_logs
        (web_user_id, chat_id, sadness, anger, fear, joy,
         risk_score, llm_risk, hopelessness, emotional_intensity)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        web_user_id, chat_id,
        emotions.get("sadness", 0),
        emotions.get("anger", 0),
        emotions.get("fear", 0),
        emotions.get("joy", 0),
        risk_score,
        llm_data.get("risk_level", 0),
        llm_data.get("hopelessness_level", 0),
        llm_data.get("emotional_intensity", 0),
    ))
    conn.commit()
    cur.close()
    conn.close()


# Auto-init on import
init_tables()
