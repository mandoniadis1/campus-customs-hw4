"""Append-only audit trail of agent-loop activity (Problem 12): hw4/output/audit_trail.json.

The file is one JSON list that is NEVER wiped. Each write takes an exclusive file lock, reads the list,
appends one entry and atomically replaces the file, so parallel chats can't corrupt it and a crash
mid-write can't truncate it. Entries hold short summaries only (≤ 200–300 chars), never full prompts,
names, emails or anything redacted by privacy.py.
"""

from __future__ import annotations

import asyncio
import fcntl
import json
import os
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic_core import to_jsonable_python

from models import AuditEntry

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
# AUDIT_TRAIL_PATH can point tests at a scratch file so they don't add to the real trail.
AUDIT_PATH = Path(os.getenv("AUDIT_TRAIL_PATH", OUTPUT_DIR / "audit_trail.json"))
LOCK_PATH = AUDIT_PATH.with_suffix(".lock")


def short(value: Any, limit: int = 300) -> str:
    """One-line, length-capped summary. Pydantic tool results become readable JSON, not Python reprs."""
    text = value if isinstance(value, str) else json.dumps(to_jsonable_python(value), ensure_ascii=False, default=str)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


class AuditTrail:
    """One per shopper message. `await trail.log("tool_call", tool=..., args=...)`."""

    def __init__(self, shopper: str):
        self.run_id = f"{datetime.now(UTC):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:6]}"
        self.shopper = shopper
        self.started = time.perf_counter()
        self.step = 0

    async def log(self, event: str, **fields: Any) -> None:
        self.step += 1
        entry = AuditEntry(
            run_id=self.run_id,
            step=self.step,
            timestamp=datetime.now(UTC).isoformat(timespec="milliseconds"),
            elapsed_s=round(time.perf_counter() - self.started, 2),
            event=event,
            shopper=self.shopper,
            **fields,
        )
        await asyncio.to_thread(_append, entry)


def _append(entry: AuditEntry) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK_PATH, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        entries = json.loads(AUDIT_PATH.read_text()) if AUDIT_PATH.exists() and AUDIT_PATH.stat().st_size else []
        entries.append(entry.model_dump(exclude_none=True))
        tmp = AUDIT_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n")
        os.replace(tmp, AUDIT_PATH)
