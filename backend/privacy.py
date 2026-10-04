"""Privacy and safety guards for the chatbot (Problem 9).

- redact_sensitive()  — removes card numbers, SSNs, phone numbers, street addresses, passwords and other
                        people's email addresses from shopper text BEFORE it reaches the model or the database
- reply_problems()    — flags a reply that asks the shopper for personal data, contains an email address
                        that isn't the shopper's own, or contains a web link (checked by the agent's output validator)
- clean_label()       — makes page text sent by the browser (e.g. a results title from the URL) safe to put
                        in the agent's instructions
- RateLimiter         — caps how many chat messages one shopper (or one IP for guests) can send per minute

The agent may only know the logged-in shopper's first name, last name and email.
"""

from __future__ import annotations

import re
import time
from collections import defaultdict, deque

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CARD_CANDIDATE_RE = re.compile(r"\b\d(?:[ -]?\d){12,18}\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
ADDRESS_RE = re.compile(
    r"\b\d{1,6}\s+(?:[A-Z][a-z]+\s){1,4}(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Ln|Lane|Dr|Drive|Ct|Court|Way|Pl|Place|Ter|Terrace)\b\.?",
)
URL_RE = re.compile(r"\bhttps?://|\bwww\.\S+|\b[\w-]+\.(?:com|net|org|io|co|ly|xyz)(?:/\S*)?\b", re.IGNORECASE)
PASSWORD_RE = re.compile(r"\b(password|passcode|pin)\s*(?:is|:|=)\s*\S+", re.IGNORECASE)

PERSONAL_DATA_WORDS = (
    r"(home |mailing |shipping |street )?address|phone( number)?|cell|birthday|date of birth|age|"
    r"card( number)?|credit card|cvv|password|social security|ssn|student id|net ?id|dorm|room number|location"
)
ASKS_FOR_DATA_RE = re.compile(rf"\byour\b[^?]{{0,40}}\b(?:{PERSONAL_DATA_WORDS})\b", re.IGNORECASE)


def _luhn_ok(digits: str) -> bool:
    total, parity = 0, len(digits) % 2
    for i, ch in enumerate(digits):
        d = int(ch)
        if i % 2 == parity:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


def redact_sensitive(text: str, own_email: str | None = None) -> tuple[str, list[str]]:
    """Return (cleaned text, kinds removed). The shopper's own email (if logged in) is kept."""
    found: list[str] = []

    def sub(pattern: re.Pattern, label: str, text: str, keep=lambda m: False) -> str:
        def repl(m: re.Match) -> str:
            if keep(m):
                return m.group(0)
            found.append(label)
            return f"[{label} removed]"

        return pattern.sub(repl, text)

    text = sub(PASSWORD_RE, "password", text)
    text = sub(
        CARD_CANDIDATE_RE, "card number", text,
        keep=lambda m: not _luhn_ok(re.sub(r"\D", "", m.group(0))),
    )
    text = sub(SSN_RE, "ID number", text)
    text = sub(PHONE_RE, "phone number", text)
    text = sub(ADDRESS_RE, "address", text)
    own = (own_email or "").lower()
    text = sub(EMAIL_RE, "email", text, keep=lambda m: m.group(0).lower() == own)
    return text, sorted(set(found))


def reply_problems(reply: str, own_email: str | None) -> list[str]:
    """Reasons a reply must be rewritten (empty list = fine)."""
    problems = []
    for question in re.findall(r"[^.!?\n]*\?", reply):
        if ASKS_FOR_DATA_RE.search(question):
            problems.append(
                "it asks the shopper for personal information. Only ask about products, sizes, colors or budget; "
                "never ask for addresses, phone numbers, birthdays, payment details, IDs or passwords"
            )
            break
    own = (own_email or "").lower()
    if any(e.lower() != own for e in EMAIL_RE.findall(reply)):
        problems.append("it contains an email address that isn't the shopper's own")
    if URL_RE.search(reply):  # Problem 12: no outside links (phishing / off-site risk); cards link to our pages
        problems.append("it contains a web link. Never include URLs; product cards already link to our own pages")
    return problems


def clean_label(text: str | None, limit: int = 80) -> str:
    """Browser-supplied text for the instructions: one line, no markup/quotes, short."""
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text or "")
    text = re.sub(r"[`\"<>{}\[\]#*]", "", text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


class RateLimiter:
    """Sliding-window limit per key (customer id or guest IP). In memory; resets on restart."""

    def __init__(self, max_requests: int, per_seconds: float):
        self.max, self.window = max_requests, per_seconds
        self._hits: defaultdict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window:
            hits.popleft()
        if len(hits) >= self.max:
            return False
        hits.append(now)
        return True
