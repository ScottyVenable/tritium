"""Load agent personas from the world tree.

Prefers `<agent>/workbook/system-prompt.md` (Vex's tighter system prompts).
Falls back to `<agent>/PERSONALITY.txt` with the leading `<!-- seed -->`
HTML-comment markers stripped.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from .config import Config

_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

# Canonical team-facts file lives alongside the agent directories at the
# top of the agents tree. This is the SINGLE source of truth for who
# exists in the world; the bridge reads it ONCE per process and prepends
# it to every system prompt.
_TEAM_FACTS_FILENAME = "TEAM_FACTS.md"
_TEAM_FACTS_CACHE: str | None = None

_log = logging.getLogger("tritium_bridge.personas")


def _strip_seed_markers(text: str) -> str:
    # Strip any HTML-style seed comments anywhere; the seed lives at the top.
    cleaned = _HTML_COMMENT.sub("", text)
    return cleaned.strip()


def persona_path(cfg: Config, agent: str) -> tuple[Path, str]:
    """Return (path, source) for the persona file used. source in {'workbook','personality'}."""
    base = cfg.agent_dir(agent)
    sp = base / "workbook" / "system-prompt.md"
    if sp.is_file():
        return sp, "workbook"
    pers = base / "PERSONALITY.txt"
    return pers, "personality"


def load_persona(cfg: Config, agent: str) -> str:
    path, _ = persona_path(cfg, agent)
    if not path.is_file():
        raise FileNotFoundError(f"No persona file for agent '{agent}' at {path}")
    raw = path.read_text(encoding="utf-8", errors="replace")
    return _strip_seed_markers(raw)


def load_all(cfg: Config) -> dict[str, str]:
    out = {}
    for a in cfg.schedule_agents:
        out[a] = load_persona(cfg, a)
    return out


def load_team_facts(cfg: Config) -> str:
    """Load canonical TEAM_FACTS.md once per process and cache it.

    Returns empty string and logs a warning if the file is missing — the
    bridge keeps working but will not be grounded.
    """
    global _TEAM_FACTS_CACHE
    if _TEAM_FACTS_CACHE is not None:
        return _TEAM_FACTS_CACHE
    path = cfg.agents_root / _TEAM_FACTS_FILENAME
    if not path.is_file():
        _log.warning("TEAM_FACTS missing at %s; system prompts will be ungrounded", path)
        _TEAM_FACTS_CACHE = ""
        return _TEAM_FACTS_CACHE
    try:
        _TEAM_FACTS_CACHE = path.read_text(encoding="utf-8", errors="replace").strip()
    except Exception as e:
        _log.warning("TEAM_FACTS unreadable at %s: %s", path, e)
        _TEAM_FACTS_CACHE = ""
    return _TEAM_FACTS_CACHE


def system_prompt_for(cfg: Config, agent: str, world_context: str = "") -> str:
    """Assemble the full system prompt: facts -> recent world -> persona+frame.

    Order matters. The model sees:
      1. TEAM_FACTS  (hard rules / canonical roster)
      2. Recent activity in the world  (grounding from journals, board, mailbox)
      3. Per-agent persona + operating frame  (voice)
    """
    persona = load_persona(cfg, agent)
    frame = (
        f"You are {agent}, a member of the Tritium team. Project: {cfg.project_name}.\n"
        "You are speaking through the Tritium Bridge service while Scotty is asleep.\n"
        "Stay strictly in character. Keep outputs short, useful, and honest.\n"
        "Never claim to have run code or accessed systems you cannot reach from here.\n"
        "Do not invent project facts you have not been told.\n"
    )
    persona_block = frame + "\n---\n" + persona

    facts = load_team_facts(cfg)
    world = (world_context or "").strip()

    # Defensive budget-trim. Drop world sections from the bottom up if needed.
    from .worldcontext import trim_for_prompt_budget
    facts, world, persona_block, dropped = trim_for_prompt_budget(facts, world, persona_block)
    if dropped:
        _log.info("prompt trimmed: dropped sections=%s", ",".join(dropped))

    parts: list[str] = []
    if facts:
        parts.append(facts)
    if world:
        parts.append(
            "# Recent activity in the world (read this before generating)\n\n" + world
        )
    parts.append(persona_block)
    return "\n\n---\n\n".join(parts)
