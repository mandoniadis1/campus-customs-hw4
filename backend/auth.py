"""Accounts, login and sessions for Campus Customs.

Passwords are stored only as salted PBKDF2-HMAC-SHA256 hashes:
    pbkdf2_sha256$<iterations>$<salt>$<hex digest>
The seed database uses an older format without the iteration count
(pbkdf2_sha256$<salt>$<hex digest>, 120,000 iterations). Those still verify and are
upgraded to the current format the next time that user logs in.

Logging in creates a random session token sent to the browser as an HttpOnly cookie.
Only a SHA-256 hash of the token is stored (sessions table).
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
import time
from contextlib import closing
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from pydantic import BaseModel, field_validator

from catalog import DB_PATH

HASH_ITERATIONS = 600_000  # OWASP-recommended minimum for PBKDF2-HMAC-SHA256
LEGACY_ITERATIONS = 120_000  # seed database format
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
SESSION_COOKIE = "cc_session"
SESSION_DAYS = 7
MAX_FAILED_LOGINS = 5  # per email + IP, within LOCKOUT_SECONDS
LOCKOUT_SECONDS = 15 * 60
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

router = APIRouter(prefix="/api/auth", tags=["auth"])


# --- password hashing -------------------------------------------------------


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), HASH_ITERATIONS).hex()
    return f"pbkdf2_sha256${HASH_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if parts[0] != "pbkdf2_sha256" or len(parts) not in (3, 4):
        return False
    if len(parts) == 4:
        iterations, salt, digest = int(parts[1]), parts[2], parts[3]
    else:
        iterations, salt, digest = LEGACY_ITERATIONS, parts[1], parts[2]
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
    return hmac.compare_digest(candidate, digest)


def needs_upgrade(stored: str) -> bool:
    parts = stored.split("$")
    return len(parts) != 4 or int(parts[1]) < HASH_ITERATIONS


# Checked when the email doesn't exist, so failed logins take the same time either way.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


# --- database ---------------------------------------------------------------


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_tables() -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS sessions (
                   token_hash TEXT PRIMARY KEY,
                   user_id INTEGER NOT NULL REFERENCES users(id),
                   created_at TEXT NOT NULL DEFAULT (datetime('now')),
                   expires_at TEXT NOT NULL
               )"""
        )


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# --- API models ---------------------------------------------------------------


class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    created_at: str


class RegisterIn(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    confirm_password: str

    @field_validator("first_name", "last_name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = v.strip()
        if not 1 <= len(v) <= 60:
            raise ValueError("must be 1-60 characters")
        return v

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v) or len(v) > 254:
            raise ValueError("enter a valid email address")
        return v

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        if not MIN_PASSWORD_LENGTH <= len(v) <= MAX_PASSWORD_LENGTH:
            raise ValueError(f"must be {MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH} characters")
        return v


class LoginIn(BaseModel):
    email: str
    password: str


def _user_out(row: sqlite3.Row) -> UserOut:
    first, last = row["first_name"], row["last_name"]
    if not first:  # older rows may only have the combined name
        first, _, last = row["name"].partition(" ")
    return UserOut(id=row["id"], first_name=first, last_name=last or "", email=row["email"], created_at=row["created_at"])


def _start_session(response: Response, user_id: int) -> None:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(UTC) + timedelta(days=SESSION_DAYS)
    with closing(connect()) as conn, conn:
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (_token_hash(token), user_id, expires.strftime("%Y-%m-%d %H:%M:%S")),
        )
    response.set_cookie(
        SESSION_COOKIE, token, max_age=SESSION_DAYS * 86400, httponly=True, samesite="lax",
        secure=False,  # set True when served over HTTPS
    )


def current_user(token: str | None) -> UserOut | None:
    if not token:
        return None
    with closing(connect()) as conn:
        row = conn.execute(
            """SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id
               WHERE s.token_hash = ? AND s.expires_at > datetime('now')""",
            (_token_hash(token),),
        ).fetchone()
    return _user_out(row) if row else None


# Failed-login counter (in memory; resets when the server restarts).
_failures: dict[str, list[float]] = {}


def _recent_failures(key: str) -> list[float]:
    now = time.time()
    _failures[key] = [t for t in _failures.get(key, []) if now - t < LOCKOUT_SECONDS]
    return _failures[key]


# --- routes -------------------------------------------------------------------


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: RegisterIn, response: Response) -> UserOut:
    if body.password != body.confirm_password:
        raise HTTPException(422, "Passwords don't match.")
    with closing(connect()) as conn, conn:
        if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (body.email,)).fetchone():
            raise HTTPException(409, "An account with this email already exists.")
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
            (f"{body.first_name} {body.last_name}", body.email, hash_password(body.password), body.first_name, body.last_name),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    _start_session(response, row["id"])
    return _user_out(row)


@router.post("/login", response_model=UserOut)
def login(body: LoginIn, request: Request, response: Response) -> UserOut:
    email = body.email.strip().lower()
    key = f"{email}|{request.client.host if request.client else ''}"
    if len(_recent_failures(key)) >= MAX_FAILED_LOGINS:
        raise HTTPException(429, "Too many failed attempts. Please wait 15 minutes and try again.")
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
    ok = verify_password(body.password, row["password_hash"] if row else _DUMMY_HASH) and row is not None
    if not ok:
        _failures[key].append(time.time())
        raise HTTPException(401, "Incorrect email or password.")
    _failures.pop(key, None)
    if needs_upgrade(row["password_hash"]):
        with closing(connect()) as conn, conn:
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(body.password), row["id"]))
    _start_session(response, row["id"])
    return _user_out(row)


@router.post("/logout", status_code=204)
def logout(response: Response, cc_session: str | None = Cookie(default=None)) -> Response:
    if cc_session:
        with closing(connect()) as conn, conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(cc_session),))
    response.delete_cookie(SESSION_COOKIE)
    response.status_code = 204
    return response


@router.get("/me", response_model=UserOut | None)
def me(cc_session: str | None = Cookie(default=None)) -> UserOut | None:
    return current_user(cc_session)
