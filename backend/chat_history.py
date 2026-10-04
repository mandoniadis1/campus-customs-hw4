"""Saved chats for logged-in customers (Problem 8), stored in the chat_messages table.

chat_messages already existed in the seed database (id, user_id, role, content, products_json, created_at).
Two nullable columns are added on startup:
    context_json — unused since Problem 9 (page context is not stored: we keep nothing about the
                   shopper beyond their messages, name and email)
    page_json    — on assistant messages: the PageUpdate (results page) that reply opened
Guests are never saved. Product cards are rebuilt from the catalogue on reload, so old chats
show today's prices and stock rather than stale copies.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing

from catalog import DB_PATH
from models import ChatHistoryMessage, ChatResponse, ChatTurn, PageUpdate
from tools import product_cards

MODEL_HISTORY = 20  # earlier messages replayed to the model on each turn
PANEL_HISTORY = 100  # messages reloaded into the chat panel


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_chat_tables() -> None:
    with closing(_connect()) as conn, conn:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(chat_messages)")}
        for col in ("context_json", "page_json"):
            if col not in cols:
                conn.execute(f"ALTER TABLE chat_messages ADD COLUMN {col} TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages(user_id, id)")


def _rows(user_id: int, limit: int) -> list[sqlite3.Row]:
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
        ).fetchall()
    return rows[::-1]  # oldest first


def model_history(user_id: int) -> list[ChatTurn]:
    """The customer's recent messages, for the agent's message history."""
    return [
        ChatTurn(role=r["role"], content=r["content"][:4000])
        for r in _rows(user_id, MODEL_HISTORY)
        if r["role"] in ("user", "assistant")
    ]


def _product_ids(products_json: str | None) -> list[str]:
    try:
        items = json.loads(products_json or "[]")
    except json.JSONDecodeError:
        return []
    return [p["product_id"] for p in items if isinstance(p, dict) and p.get("product_id")]


def load_history(user_id: int) -> list[ChatHistoryMessage]:
    """The customer's saved chat, oldest first, with product cards rebuilt from the catalogue."""
    out: list[ChatHistoryMessage] = []
    for r in _rows(user_id, PANEL_HISTORY):
        if r["role"] not in ("user", "assistant"):
            continue
        page = None
        if r["page_json"]:
            try:
                page = PageUpdate.model_validate_json(r["page_json"])
            except ValueError:
                page = None
        out.append(
            ChatHistoryMessage(
                role=r["role"], content=r["content"], products=product_cards(_product_ids(r["products_json"])),
                page=page, created_at=r["created_at"],
            )
        )
    return out


def save_exchange(user_id: int, message: str, reply: ChatResponse) -> None:
    """Save one shopper message (already redacted by privacy.py) and the assistant's reply, in one transaction."""
    with closing(_connect()) as conn, conn:
        conn.execute("INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)", (user_id, message))
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json, page_json) VALUES (?, 'assistant', ?, ?, ?)",
            (
                user_id,
                reply.reply,
                json.dumps([p.model_dump() for p in reply.products]),
                reply.page.model_dump_json() if reply.page else None,
            ),
        )


def clear_history(user_id: int) -> int:
    with closing(_connect()) as conn, conn:
        return conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,)).rowcount
