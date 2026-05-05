"""Watch the social-hub inbox for newly-saved Scotty messages.

Lightweight pull-based scan; no watchdog dependency. The mailer drops .eml
files into `<world>/[1] -- social hub --/inbox-from-scotty/`. This module
returns any unprocessed files (those without a sibling `.processed` marker).
"""
from __future__ import annotations

from email import message_from_bytes
from pathlib import Path

from .config import Config


def inbox_dir(cfg: Config) -> Path:
    return cfg.social_hub / "inbox-from-scotty"


def list_pending(cfg: Config) -> list[Path]:
    d = inbox_dir(cfg)
    if not d.is_dir():
        return []
    out = []
    for p in sorted(d.glob("*.eml")):
        if not p.with_suffix(p.suffix + ".processed").exists():
            out.append(p)
    return out


def parse_route(path: Path, default_agent: str = "Bridge") -> tuple[str, str, str]:
    """Return (agent, subject, body). Subject of `to:<agent>` routes the message."""
    raw = path.read_bytes()
    msg = message_from_bytes(raw)
    subject = msg.get("Subject", "")
    agent = default_agent
    low = subject.lower()
    if "to:" in low:
        # naive parse: take token after 'to:' up to whitespace or ']'
        idx = low.index("to:") + 3
        rest = low[idx:]
        token = ""
        for ch in rest:
            if ch.isalpha():
                token += ch
            else:
                break
        if token:
            agent = token.capitalize()

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body = part.get_content()
                except Exception:
                    body = part.get_payload(decode=True).decode("utf-8", "replace")
                break
    else:
        try:
            body = msg.get_content()
        except Exception:
            body = (msg.get_payload(decode=True) or b"").decode("utf-8", "replace")
    return agent, subject, body


def mark_processed(path: Path) -> None:
    marker = path.with_suffix(path.suffix + ".processed")
    marker.write_text("processed\n", encoding="utf-8")
