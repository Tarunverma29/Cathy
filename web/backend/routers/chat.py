"""
web/backend/routers/chat.py

Fixes:
- Loads persona file dynamically based on user's persona_mbti + persona_mode + gender
- Falls back to personas/cathy.txt if no persona configured or file not found
- WebSocket now reads persona_mbti/persona_mode from JWT on each connection
"""

import sys, os, json, traceback
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from web.backend.auth_utils import get_current_user, decode_token
from web.backend.db import (
    create_web_chat,
    get_user_chats,
    get_recent_web_messages,
    save_web_message,
    log_web_emotional_state,
)
from database.db import get_conn

from mental.classifier import classify_emotions
from mental.reasoning import analyze_psychology
from mental.risk_engine import compute_risk
from mental.responder import build_crisis_response

import ollama
from config.settings import MODEL_NAME

router = APIRouter()

# ── Persona name map ─────────────────────────────────────────────────────────
# Maps MBTI type → (female_name, male_name)
PERSONA_NAMES = {
    'INFP': ('lily',   'eli'),
    'ENFP': ('nova',   'finn'),
    'INFJ': ('sera',   'aaron'),
    'ENFJ': ('maya',   'theo'),
    'ISFP': ('zoe',    'kai'),
    'ESFP': ('mia',    'rex'),
    'ISFJ': ('rose',   'sam'),
    'ESFJ': ('cathy',  'marcus'),
    'INTP': ('nora',   'leo'),
    'ENTP': ('quinn',  'jace'),
    'INTJ': ('vera',   'cole'),
    'ENTJ': ('ava',    'zane'),
    'ISTP': ('rena',   'rhys'),
    'ESTP': ('skye',   'dex'),
    'ISTJ': ('claire', 'grant'),
    'ESTJ': ('dana',   'brett'),
}

# Default fallback character
_DEFAULT_CHARACTER = None

def _load_default():
    global _DEFAULT_CHARACTER
    if _DEFAULT_CHARACTER is None:
        with open("personas/cathy.txt", "r", encoding="utf-8") as f:
            _DEFAULT_CHARACTER = f.read()
    return _DEFAULT_CHARACTER


def load_character(persona_mbti: str | None, persona_mode: str | None, gender: str | None) -> str:
    """
    Load the correct persona .txt file.
    persona_mode: 'romantic' | 'neutral'
    gender: user's gender → determines which persona gender to use
    """
    if not persona_mbti:
        return _load_default()

    mbti = persona_mbti.upper()
    if mbti not in PERSONA_NAMES:
        return _load_default()

    female_name, male_name = PERSONA_NAMES[mbti]

    # Persona gender is opposite of user's gender
    # (male user → female persona, female user → male persona)
    if gender and gender.lower() == 'female':
        persona_gender = 'male'
        name = male_name
    else:
        persona_gender = 'female'
        name = female_name

    # Try to find the file: personas/{gender}/{mode}/{name}.txt
    mode_folder = 'girlfriend' if (persona_mode or '').lower() == 'romantic' else 'neutral'

    candidate_paths = [
        f"personas/{persona_gender}/{mode_folder}/{name}.txt",
        f"personas/{persona_gender}/{mode_folder}/{mbti.lower()}.txt",
        f"personas/{name}.txt",
        f"personas/{mbti.lower()}.txt",
        "personas/cathy.txt",
    ]

    for path in candidate_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

    return _load_default()


# ── REST: Chat Management ────────────────────────────────────────────────────

class NewChatRequest(BaseModel):
    title: str = "New Chat"


@router.post("/chats")
def new_chat(body: NewChatRequest, user=Depends(get_current_user)):
    user_id = int(user["sub"])
    chat_id = create_web_chat(user_id, body.title)
    return {"chat_id": chat_id, "title": body.title}


@router.get("/chats")
def list_chats(user=Depends(get_current_user)):
    user_id = int(user["sub"])
    chats = get_user_chats(user_id)
    return [
        {"id": c[0], "title": c[1], "created_at": c[2].isoformat()}
        for c in chats
    ]


@router.get("/chats/{chat_id}/messages")
def get_messages(chat_id: int, user=Depends(get_current_user)):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT user_id FROM web_chats WHERE id = %s;", (chat_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row or row[0] != int(user["sub"]):
        raise HTTPException(status_code=403, detail="Access denied")

    messages = get_recent_web_messages(chat_id, limit=50)
    return [{"role": r, "content": c} for r, c in messages]


@router.delete("/chats/{chat_id}")
def delete_chat(chat_id: int, user=Depends(get_current_user)):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        "DELETE FROM web_chats WHERE id = %s AND user_id = %s;",
        (chat_id, int(user["sub"]))
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"deleted": True}


# ── WebSocket: Streaming Chat ────────────────────────────────────────────────

def _build_messages(character: str, conversation: list, user_input: str):
    messages = [{"role": "system", "content": character}]
    for role, content in conversation:
        messages.append({
            "role": "user" if role.lower() == "user" else "assistant",
            "content": content,
        })
    messages.append({"role": "user", "content": user_input})
    return messages


@router.websocket("/ws/{chat_id}")
async def chat_ws(websocket: WebSocket, chat_id: int):
    await websocket.accept()

    # ── Authenticate ────────────────────────────────────────────────────────
    try:
        auth_msg = await websocket.receive_text()
        data     = json.loads(auth_msg)
        token    = data.get("token", "")
        user     = decode_token(token)
        user_id  = int(user["sub"])
    except Exception as e:
        print(f"WS auth failed: {e}")
        await websocket.send_json({"type": "error", "content": "Unauthorized"})
        await websocket.close()
        return

    # ── Verify chat ownership ────────────────────────────────────────────────
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT user_id FROM web_chats WHERE id = %s;", (chat_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row or row[0] != user_id:
        await websocket.send_json({"type": "error", "content": "Access denied"})
        await websocket.close()
        return

    # ── Load persona from user's JWT ─────────────────────────────────────────
    CHARACTER = load_character(
        persona_mbti=user.get("persona_mbti"),
        persona_mode=user.get("persona_mode"),
        gender=user.get("gender"),
    )

    await websocket.send_json({"type": "ready"})
    print(f"WS ready: user={user_id} chat={chat_id} persona={user.get('persona_mbti','default')}")

    try:
        while True:
            raw        = await websocket.receive_text()
            data       = json.loads(raw)
            user_input = data.get("message", "").strip()

            if not user_input:
                continue

            print(f"WS message: user={user_id} input={user_input[:60]!r}")

            try:
                # Save user message
                save_web_message(chat_id, "user", user_input)

                # ── Mental Health Pipeline ──────────────────────────────────
                emotions   = classify_emotions(user_input)
                llm_data   = analyze_psychology(user_input)
                risk_score = compute_risk(emotions, llm_data, 1.0)

                log_web_emotional_state(user_id, chat_id, emotions, llm_data, risk_score)

                # ── Critical Risk ───────────────────────────────────────────
                if risk_score >= 15:
                    reply = build_crisis_response(
                        user_input, emotions, llm_data, risk_score, use_llm=True
                    )
                    save_web_message(chat_id, "assistant", reply)
                    await websocket.send_json({"type": "message", "content": reply})
                    continue

                # ── High risk check-in before streaming ─────────────────────
                if risk_score >= 10:
                    check_in = build_crisis_response(
                        user_input, emotions, llm_data, risk_score, use_llm=False
                    )
                    await websocket.send_json({"type": "checkin", "content": check_in})

                # ── Stream Ollama reply ─────────────────────────────────────
                conversation  = get_recent_web_messages(chat_id, limit=10)
                messages_list = _build_messages(CHARACTER, conversation, user_input)

                full_reply = ""
                await websocket.send_json({"type": "stream_start"})

                for chunk in ollama.chat(
                    model=MODEL_NAME,
                    messages=messages_list,
                    stream=True,
                    options={"temperature": 0.7, "top_p": 0.9, "repeat_penalty": 1.2},
                ):
                    token_text = chunk["message"]["content"]
                    if token_text:
                        full_reply += token_text
                        await websocket.send_json({"type": "stream", "content": token_text})

                await websocket.send_json({"type": "stream_end"})
                print(f"WS stream done: {len(full_reply)} chars")

                # ── Moderate risk check-in after reply ──────────────────────
                if 6 <= risk_score < 10:
                    check_in = build_crisis_response(
                        user_input, emotions, llm_data, risk_score, use_llm=False
                    )
                    full_reply += f"\n\n…{check_in}"
                    await websocket.send_json({"type": "checkin", "content": f"…{check_in}"})

                save_web_message(chat_id, "assistant", full_reply)

            except Exception as e:
                print(f"WS pipeline error:\n{traceback.format_exc()}")
                await websocket.send_json({
                    "type": "error",
                    "content": f"Something went wrong: {str(e)}"
                })
                await websocket.send_json({"type": "stream_end"})

    except WebSocketDisconnect:
        print(f"WS disconnected: user={user_id} chat={chat_id}")
