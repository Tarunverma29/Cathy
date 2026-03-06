"""
web/backend/routers/auth.py
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from database.db import get_conn
from web.backend.auth_utils import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def get_user_by_email(email: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, username, password FROM web_users WHERE email = %s;",
        (email,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


@router.post("/register")
def register(body: RegisterRequest):
    if get_user_by_email(body.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(body.password)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO web_users (email, username, password) VALUES (%s, %s, %s) RETURNING id;",
        (body.email, body.username, hashed)
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    token = create_access_token({
        "sub": str(user_id),
        "email": body.email,
        "username": body.username
    })
    return {"access_token": token, "token_type": "bearer", "username": body.username}


@router.post("/login")
def login(body: LoginRequest):
    row = get_user_by_email(body.email)

    if not row or not verify_password(body.password, row[3]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id, email, username, _ = row
    token = create_access_token({
        "sub": str(user_id),
        "email": email,
        "username": username
    })
    return {"access_token": token, "token_type": "bearer", "username": username}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return user
