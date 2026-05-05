"""On-demand world-tree readers exposed to the model as tool calls.

These functions are invoked when the LLM emits a `tool_calls` field in a
response. Each returns a plain string capped at ~1500 chars so an over-eager
model can't blow the context window. All paths are derived from the live
``Config`` (i.e. the source-of-truth ``WORLD_ROOT``).

Design rules:
- Pure reads. Never write to disk.
- Defensive: missing files return a short "no data" message, not an
  exception, so the model can keep going.
- Bracketed folder names (``[1] -- social hub --`` etc.) are part of the
  on-disk layout. We use ``pathlib.Path`` joins, not glob, since brackets
  collide with glob syntax.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Callable, Optional

from .config import Config

log = logging.getLogger("tritium_bridge.tools")

# Per-call output cap. Keep tight; the world-context injector already
# carries the bulk weight for grounding.
RESULT_CHAR_CAP = 1500
TRUNCATION_SUFFIX = "\n...[truncated]"

_DATE_FROM_NAME = re.compile(r"(\d{4}-\d{2}-\d{2})")
_THINK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _cap(text: str) -> str:
    """Truncate to RESULT_CHAR_CAP gracefully."""
    if text is None:
        return ""
    if len(text) <= RESULT_CHAR_CAP:
        return text
    head = text[: RESULT_CHAR_CAP - len(TRUNCATION_SUFFIX)].rstrip()
    return head + TRUNCATION_SUFFIX


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""
    except Exception as e:
        log.warning("tool read failed for %s: %s", path, e)
        return ""


def _strip_think(text: str) -> str:
    return _THINK.sub("", text).strip()


def _date_from_name(p: Path) -> str:
    m = _DATE_FROM_NAME.search(p.name)
    return m.group(1) if m else ""


# ---------- tool implementations ----------

def read_team_facts(cfg: Config) -> str:
    """Return the canonical TEAM_FACTS.md."""
    p = cfg.agents_root / "TEAM_FACTS.md"
    text = _read(p)
    return _cap(text) if text else "TEAM_FACTS.md not found."


def read_personality(cfg: Config, agent_name: str) -> str:
    """Return the agent's personality / system prompt."""
    base = cfg.agent_dir(agent_name)
    candidates = [
        base / "workbook" / "system-prompt.md",
        base / "PERSONALITY.txt",
    ]
    for c in candidates:
        if c.is_file():
            text = _strip_think(_read(c))
            return _cap(text)
    return f"No personality file for agent '{agent_name}'."


def read_recent_journals(cfg: Config, agent_name: Optional[str] = None,
                         days: int = 3) -> str:
    """Return the most-recent journal entries, capped to roughly ``days`` files.

    If ``agent_name`` is None, scans all real teammates and merges newest-first.
    """
    real = ["Bridge", "Sol", "Jesse", "Vex", "Rook"]
    targets = [agent_name] if agent_name else real
    candidates: list[tuple[str, str, Path]] = []  # (date, agent, path)
    for a in targets:
        jdir = cfg.agent_dir(a) / "journal"
        if not jdir.is_dir():
            continue
        for p in jdir.iterdir():
            if p.is_file() and p.suffix.lower() == ".txt":
                d = _date_from_name(p)
                if d:
                    candidates.append((d, a, p))
    candidates.sort(key=lambda t: (t[0], t[2].name), reverse=True)
    picks = candidates[: max(1, days)]
    if not picks:
        who = agent_name or "any agent"
        return f"No recent journals for {who}."
    parts: list[str] = []
    for d, a, p in picks:
        body = _strip_think(_read(p))
        parts.append(f"[{a} journal, {d}]\n{body}")
    return _cap("\n\n".join(parts).strip())


def read_message_board(cfg: Config, limit: int = 5) -> str:
    """Return the most-recent message-board files (excluding morning briefings)."""
    mdir = cfg.social_hub / "message board"
    if not mdir.is_dir():
        return "Message board directory not found."
    files = [
        p for p in mdir.iterdir()
        if p.is_file() and p.suffix.lower() == ".md"
        and "morning-briefing" not in p.name.lower()
    ]
    files.sort(key=lambda x: (_date_from_name(x), x.name), reverse=True)
    picks = files[: max(1, limit)]
    if not picks:
        return "No message-board posts found."
    parts: list[str] = []
    for p in picks:
        d = _date_from_name(p) or ""
        head = f"[message board, {d}]" if d else f"[message board, {p.name}]"
        parts.append(f"{head}\n{_strip_think(_read(p))}")
    return _cap("\n\n".join(parts).strip())


def read_mailbox(cfg: Config, agent_name: str) -> str:
    """Return recent mailbox messages addressed to ``agent_name``."""
    mdir = cfg.social_hub / "mailbox" / agent_name.lower()
    if not mdir.is_dir():
        return f"No mailbox for agent '{agent_name}'."
    files = [p for p in mdir.iterdir()
             if p.is_file() and p.suffix.lower() in (".md", ".txt")]
    files.sort(key=lambda x: (_date_from_name(x), x.name), reverse=True)
    picks = files[:3]
    if not picks:
        return f"No mailbox items for '{agent_name}'."
    parts: list[str] = []
    for p in picks:
        d = _date_from_name(p) or ""
        head = f"[mailbox, {d}, {p.name}]"
        parts.append(f"{head}\n{_strip_think(_read(p))}")
    return _cap("\n\n".join(parts).strip())


def read_blog_posts(cfg: Config, limit: int = 3) -> str:
    """Return recent posts from the public blog."""
    bdir = cfg.social_hub / "public blog"
    if not bdir.is_dir():
        return "Public blog directory not found."
    files = [p for p in bdir.iterdir()
             if p.is_file() and p.suffix.lower() in (".md", ".txt")]
    files.sort(key=lambda x: (_date_from_name(x), x.name), reverse=True)
    picks = files[: max(1, limit)]
    if not picks:
        return "No blog posts found."
    parts: list[str] = []
    for p in picks:
        d = _date_from_name(p) or ""
        head = f"[blog, {d}, {p.name}]"
        parts.append(f"{head}\n{_strip_think(_read(p))}")
    return _cap("\n\n".join(parts).strip())


# ---------- OpenAI-format tool schema ----------

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_team_facts",
            "description": (
                "Read the canonical TEAM_FACTS.md listing every real teammate "
                "and in-world character. Use this to confirm a teammate's "
                "name or role before mentioning them."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_personality",
            "description": (
                "Read another teammate's personality / system prompt so you "
                "can speak about them accurately. Pass the short name "
                "(Bridge, Sol, Jesse, Vex, Rook)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string",
                                    "description": "Short agent name."}
                },
                "required": ["agent_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_recent_journals",
            "description": (
                "Read the most recent journal entries. If agent_name is "
                "omitted, returns the newest entries across all teammates."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string"},
                    "days": {"type": "integer", "default": 3},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_message_board",
            "description": "Read recent shared message-board posts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 5}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_mailbox",
            "description": "Read recent mailbox items addressed to an agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string"}
                },
                "required": ["agent_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_blog_posts",
            "description": "Read recent posts from the public blog.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 3}
                },
                "required": [],
            },
        },
    },
]


# ---------- dispatcher ----------

def _bind(cfg: Config) -> dict[str, Callable[..., str]]:
    return {
        "read_team_facts": lambda **kw: read_team_facts(cfg, **kw),
        "read_personality": lambda **kw: read_personality(cfg, **kw),
        "read_recent_journals": lambda **kw: read_recent_journals(cfg, **kw),
        "read_message_board": lambda **kw: read_message_board(cfg, **kw),
        "read_mailbox": lambda **kw: read_mailbox(cfg, **kw),
        "read_blog_posts": lambda **kw: read_blog_posts(cfg, **kw),
    }


def execute_tool_call(cfg: Config, name: str, arguments_json: str) -> str:
    """Run a tool by name. Returns a human-readable string (cap-respected)."""
    handlers = _bind(cfg)
    fn = handlers.get(name)
    if fn is None:
        return f"[tool error] unknown tool: {name}"
    try:
        args = json.loads(arguments_json) if arguments_json else {}
    except json.JSONDecodeError as e:
        return f"[tool error] bad arguments JSON: {e}"
    if not isinstance(args, dict):
        return "[tool error] arguments must be a JSON object"
    try:
        out = fn(**args)
    except TypeError as e:
        return f"[tool error] {name}: {e}"
    except Exception as e:
        log.exception("tool %s failed", name)
        return f"[tool error] {name}: {e}"
    return _cap(out if isinstance(out, str) else str(out))
