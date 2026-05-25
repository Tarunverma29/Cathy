"""
web/backend/routers/auth.py

Fixes:
- SELECT now fetches all 8 columns (including gender, mbti, persona_mbti, persona_mode)
- PATCH /profile endpoint added for post-login profile updates
- _make_token() helper includes all fields
- VALID_MBTI validation set
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
from database.db import get_conn
from web.backend.auth_utils import (
    hash_password, verify_password, create_access_token, get_current_user
)

router = APIRouter()

VALID_MBTI = {
    'INFP','ENFP','INFJ','ENFJ','ISFP','ESFP','ISFJ','ESFJ',
    'INTP','ENTP','INTJ','ENTJ','ISTP','ESTP','ISTJ','ESTJ',
}

# ── Pydantic models ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email:        str
    username:     str
    password:     str
    gender:       Optional[str] = None   # 'male' | 'female'
    mbti:         Optional[str] = None
    persona_mbti: Optional[str] = None
    persona_mode: Optional[str] = None   # 'romantic' | 'neutral'


class LoginRequest(BaseModel):
    email:    str
    password: str


class ProfileUpdateRequest(BaseModel):
    mbti:         Optional[str] = None
    persona_mbti: Optional[str] = None
    persona_mode: Optional[str] = None


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_token(user_id, email, username, gender, mbti, persona_mbti, persona_mode):
    return create_access_token({
        "sub":          str(user_id),
        "email":        email,
        "username":     username,
        "gender":       gender,
        "mbti":         mbti,
        "persona_mbti": persona_mbti,
        "persona_mode": persona_mode,
    })


def get_user_by_email(email: str):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        """
        SELECT id, email, username, password, gender, mbti, persona_mbti, persona_mode
        FROM web_users WHERE email = %s;
        """,
        (email,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/register")
def register(body: RegisterRequest):
    if get_user_by_email(body.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validate optional MBTI fields
    if body.mbti and body.mbti.upper() not in VALID_MBTI:
        raise HTTPException(status_code=400, detail=f"Invalid MBTI type: {body.mbti}")
    if body.persona_mbti and body.persona_mbti.upper() not in VALID_MBTI:
        raise HTTPException(status_code=400, detail=f"Invalid persona MBTI: {body.persona_mbti}")

    hashed = hash_password(body.password)

    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        """
        INSERT INTO web_users (email, username, password, gender, mbti, persona_mbti, persona_mode)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """,
        (
            body.email, body.username, hashed,
            body.gender,
            body.mbti.upper()         if body.mbti         else None,
            body.persona_mbti.upper() if body.persona_mbti else None,
            body.persona_mode,
        )
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    token = _make_token(
        user_id, body.email, body.username,
        body.gender, body.mbti, body.persona_mbti, body.persona_mode
    )
    return {"access_token": token, "token_type": "bearer", "username": body.username}


@router.post("/login")
def login(body: LoginRequest):
    row = get_user_by_email(body.email)

    if not row or not verify_password(body.password, row[3]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id, email, username, _, gender, mbti, persona_mbti, persona_mode = row

    token = _make_token(user_id, email, username, gender, mbti, persona_mbti, persona_mode)
    return {"access_token": token, "token_type": "bearer", "username": username}


@router.patch("/profile")
def update_profile(body: ProfileUpdateRequest, user=Depends(get_current_user)):
    user_id = int(user["sub"])

    # Validate
    if body.mbti and body.mbti.upper() not in VALID_MBTI:
        raise HTTPException(status_code=400, detail=f"Invalid MBTI type: {body.mbti}")
    if body.persona_mbti and body.persona_mbti.upper() not in VALID_MBTI:
        raise HTTPException(status_code=400, detail=f"Invalid persona MBTI: {body.persona_mbti}")

    # Build SET clause dynamically (only update provided fields)
    updates = {}
    if body.mbti         is not None: updates["mbti"]         = body.mbti.upper()
    if body.persona_mbti is not None: updates["persona_mbti"] = body.persona_mbti.upper()
    if body.persona_mode is not None: updates["persona_mode"] = body.persona_mode

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clause = ", ".join(f"{k} = %s" for k in updates)
    values     = list(updates.values()) + [user_id]

    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        f"""
        UPDATE web_users SET {set_clause} WHERE id = %s
        RETURNING id, email, username, gender, mbti, persona_mbti, persona_mode;
        """,
        values
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    user_id, email, username, gender, mbti, persona_mbti, persona_mode = row
    new_token = _make_token(user_id, email, username, gender, mbti, persona_mbti, persona_mode)
    return {"access_token": new_token, "token_type": "bearer"}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return user
