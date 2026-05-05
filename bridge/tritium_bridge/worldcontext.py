"""Per-tick recent-world context loader.

Builds a short "what's been happening" string that gets injected into every
agent's system prompt between TEAM_FACTS and the per-agent persona. The goal
is grounding: the model sees fresh facts about who said/did what before it
generates, so it stops hallucinating teammate names or events.

Sources (most recent first):
  1. Last 3 journal entries across the 5 real agents.
  2. Last 5 message-board posts (morning-briefing files skipped).
  3. Last 3 mailbox items addressed to the acting agent.
  4. Last 2 entries from the acting agent's own work memories.

Total budget is roughly 1200 tokens (~4800 chars). If the assembled prompt
would exceed PROMPT_HARD_BUDGET, sections drop in this order:
memories -> mailbox -> message-board -> journals.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

from .config import Config

log = logging.getLogger("tritium_bridge.worldcontext")

# --- budgets (chars; chars/4 ~ tokens) ---
TOTAL_CHAR_BUDGET = 4800
SECTION_BUDGETS = {
    "journals": 2200,
    "message_board": 1500,
    "mailbox": 700,
    "memories": 400,
}
# Hard ceiling for the full assembled prompt; if exceeded we drop sections.
PROMPT_HARD_BUDGET_CHARS = 24000  # ~6000 tokens

REAL_AGENTS = ["Bridge", "Sol", "Jesse", "Vex", "Rook"]

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_DATE_FROM_NAME = re.compile(r"(\d{4}-\d{2}-\d{2})")
_BLANKS = re.compile(r"\n{3,}")


def _read_text(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        log.warning("skip unreadable file %s: %s", p, e)
        return None


def _sanitize(text: str) -> str:
    text = _THINK.sub("", text)
    # collapse blank-line runs and trim
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines).strip()


def _date_from_name(p: Path) -> str:
    m = _DATE_FROM_NAME.search(p.name)
    return m.group(1) if m else ""


def _truncate(s: str, limit: int) -> str:
    if len(s) <= limit:
        return s
    return s[: max(0, limit - 12)].rstrip() + "\n[...trunc]"


# ---------- section builders ----------

def _journals_section(cfg: Config) -> str:
    candidates: list[tuple[str, str, Path]] = []  # (date, agent, path)
    for agent in REAL_AGENTS:
        jdir = cfg.agent_dir(agent) / "journal"
        if not jdir.is_dir():
            continue
        for p in jdir.iterdir():
            if not p.is_file() or p.suffix.lower() != ".txt":
                continue
            d = _date_from_name(p)
            if d:
                candidates.append((d, agent, p))
    # newest first by date then by filename for tie-break
    candidates.sort(key=lambda t: (t[0], t[2].name), reverse=True)
    picks = candidates[:3]
    if not picks:
        return ""

    parts: list[str] = []
    per_entry = max(300, SECTION_BUDGETS["journals"] // max(1, len(picks)))
    for d, agent, p in picks:
        raw = _read_text(p)
        if raw is None:
            continue
        body = _sanitize(raw)
        body = _truncate(body, per_entry)
        parts.append(f"[{agent} journal, {d}]\n{body}")
    return "\n\n".join(parts).strip()


def _message_board_section(cfg: Config) -> str:
    mdir = cfg.social_hub / "message board"
    if not mdir.is_dir():
        return ""
    files: list[Path] = []
    for p in mdir.iterdir():
        if not p.is_file() or p.suffix.lower() != ".md":
            continue
        if "morning-briefing" in p.name.lower():
            continue
        files.append(p)
    files.sort(key=lambda x: (_date_from_name(x), x.name), reverse=True)
    picks = files[:5]
    if not picks:
        return ""
    parts: list[str] = []
    per_entry = max(150, SECTION_BUDGETS["message_board"] // max(1, len(picks)))
    for p in picks:
        raw = _read_text(p)
        if raw is None:
            continue
        body = _truncate(_sanitize(raw), per_entry)
        d = _date_from_name(p) or ""
        head = f"[message board, {d}]" if d else "[message board]"
        parts.append(f"{head}\n{body}")
    return "\n\n".join(parts).strip()


def _mailbox_section(cfg: Config, agent: str) -> str:
    mdir = cfg.social_hub / "mailbox" / agent.lower()
    if not mdir.is_dir():
        return ""
    files = [p for p in mdir.iterdir() if p.is_file() and p.suffix.lower() in (".md", ".txt")]
    if not files:
        return ""
    files.sort(key=lambda x: (_date_from_name(x), x.name), reverse=True)
    picks = files[:3]
    parts: list[str] = []
    per_entry = max(150, SECTION_BUDGETS["mailbox"] // max(1, len(picks)))
    for p in picks:
        raw = _read_text(p)
        if raw is None:
            continue
        body = _sanitize(raw)
        # try to pull a "from" hint from filename like 2026-05-05--bridge-...
        sender = "unknown"
        m = re.match(r"\d{4}-\d{2}-\d{2}--([a-zA-Z]+)", p.name)
        if m:
            sender = m.group(1).lower()
        d = _date_from_name(p) or ""
        head = f"[mailbox, from {sender}, {d}]" if d else f"[mailbox, from {sender}]"
        parts.append(f"{head}\n{_truncate(body, per_entry)}")
    return "\n\n".join(parts).strip()


def _memories_section(cfg: Config, agent: str) -> str:
    mdir = cfg.agent_dir(agent) / "memories" / "work"
    if not mdir.is_dir():
        return ""
    files = [p for p in mdir.iterdir() if p.is_file() and p.suffix.lower() == ".txt"]
    if not files:
        return ""
    files.sort(key=lambda x: (_date_from_name(x), x.name), reverse=True)
    picks = files[:2]
    parts: list[str] = []
    per_entry = max(120, SECTION_BUDGETS["memories"] // max(1, len(picks)))
    for p in picks:
        raw = _read_text(p)
        if raw is None:
            continue
        body = _truncate(_sanitize(raw), per_entry)
        d = _date_from_name(p) or ""
        head = f"[your memory, {d}]" if d else "[your memory]"
        parts.append(f"{head}\n{body}")
    return "\n\n".join(parts).strip()


# ---------- public ----------

def build_recent_world(cfg: Config, agent: str) -> str:
    """Return assembled recent-world string. Empty string if nothing to inject."""
    sections: dict[str, str] = {
        "journals": _journals_section(cfg),
        "message_board": _message_board_section(cfg),
        "mailbox": _mailbox_section(cfg, agent),
        "memories": _memories_section(cfg, agent),
    }
    # Trim each section to its per-section budget too, defensively.
    for k, v in list(sections.items()):
        if v and len(v) > SECTION_BUDGETS[k]:
            sections[k] = _truncate(v, SECTION_BUDGETS[k])

    return _assemble(sections)


def _assemble(sections: dict[str, str]) -> str:
    headings = {
        "journals": "## Recent journal entries",
        "message_board": "## Recent message-board posts",
        "mailbox": "## Recent mailbox for you",
        "memories": "## Your recent work memories",
    }
    order = ["journals", "message_board", "mailbox", "memories"]
    blocks: list[str] = []
    for key in order:
        body = sections.get(key, "").strip()
        if not body:
            continue  # omit header entirely if empty
        blocks.append(f"{headings[key]}\n\n{body}")
    out = "\n\n".join(blocks).strip()
    if len(out) > TOTAL_CHAR_BUDGET:
        out = _truncate(out, TOTAL_CHAR_BUDGET)
    return out


def trim_for_prompt_budget(facts: str, world: str, persona: str) -> tuple[str, str, str, list[str]]:
    """If total assembled prompt exceeds hard budget, drop sections from world.

    Drop order: memories -> mailbox -> message-board -> journals (requirement).
    Returns (facts, world, persona, dropped_section_names).
    """
    dropped: list[str] = []
    total = len(facts) + len(world) + len(persona)
    if total <= PROMPT_HARD_BUDGET_CHARS:
        return facts, world, persona, dropped

    # Re-parse world by section headers and strip from the bottom of the drop order.
    drop_order = [
        ("## Your recent work memories", "memories"),
        ("## Recent mailbox for you", "mailbox"),
        ("## Recent message-board posts", "message_board"),
        ("## Recent journal entries", "journals"),
    ]
    cur = world
    for header, label in drop_order:
        if header in cur:
            idx = cur.index(header)
            cur = cur[:idx].rstrip()
            dropped.append(label)
        if len(facts) + len(cur) + len(persona) <= PROMPT_HARD_BUDGET_CHARS:
            return facts, cur, persona, dropped
    return facts, cur, persona, dropped
