"""Concrete agent actions: journal entry, message-board post, email."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from .config import Config
from .context import append_turn, build_messages, load_context, maybe_condense, save_context
from .lmstudio import LMStudioClient
from .mailer import archive_outbox, archive_sent, build_message, send_smtp
from .personas import system_prompt_for
from .tools import TOOL_SCHEMAS, execute_tool_call
from .worldcontext import build_recent_world

log = logging.getLogger("tritium_bridge.actions")


# Banned name variants -> canonical short names. Applied to every generation
# as a final defense against the 8B model's tendency to expand "Sol" into
# "Solomon" etc. We also retry once with a reinforced reminder before falling
# back to deterministic replacement.
_NAME_FIXES: dict[str, str] = {
    "Solomon": "Sol",
    "Soliel": "Sol",
    "Solly": "Sol",
    "Vesper": "Vex",
}


def _name_violations(text: str) -> list[str]:
    import re as _re
    hits: list[str] = []
    for bad in _NAME_FIXES:
        if _re.search(rf"\b{_re.escape(bad)}\b", text):
            hits.append(bad)
    return hits


def _scrub_names(text: str) -> str:
    import re as _re
    out = text
    for bad, good in _NAME_FIXES.items():
        out = _re.sub(rf"\b{_re.escape(bad)}\b", good, out)
    return out


# House rule: no emojis in any committed agent output. Local models
# occasionally emit a stray pictograph (eyes, sparkles, etc) which both
# violates the style guide and crashes Windows cp1252 consoles. Strip
# the major Unicode emoji blocks deterministically before we print or
# write to disk.
import re as _re_mod
_EMOJI_RE = _re_mod.compile(
    "["
    "\U0001F300-\U0001FAFF"  # symbols & pictographs, emoticons, transport, etc.
    "\U00002600-\U000027BF"  # misc symbols + dingbats
    "\U0001F1E6-\U0001F1FF"  # regional indicators (flags)
    "\U0000FE0F"             # variation selector-16
    "]",
    flags=_re_mod.UNICODE,
)


# Fake tool-call blocks: some local models hallucinate non-existent tools
# inline as bracketed pseudo-XML. Strip these deterministically before
# we write the output to disk so they never leak into journals/posts.
_FAKE_TOOL_BLOCK = _re_mod.compile(
    r"\[TOOL_REQUEST\].*?\[END_TOOL_REQUEST\]",
    flags=_re_mod.DOTALL | _re_mod.IGNORECASE,
)
_FAKE_TOOL_NAME_LEAK = _re_mod.compile(
    r"\b(?:reading_recent_journals|read_recent_journals|read_team_facts|"
    r"read_message_board|read_mailbox|read_blog_posts|read_personality)\b",
    flags=_re_mod.IGNORECASE,
)


def _strip_fake_tool_artifacts(text: str) -> str:
    cleaned = _FAKE_TOOL_BLOCK.sub("", text)
    cleaned = _FAKE_TOOL_NAME_LEAK.sub("(tool)", cleaned)
    return cleaned


def _strip_emojis(text: str) -> str:
    return _EMOJI_RE.sub("", text)


# ----- shared helper -----

def _generate(cfg: Config, llm: LMStudioClient, agent: str, user_prompt: str,
              max_tokens: int = 500, temperature: float = 0.8) -> str:
    world = build_recent_world(cfg, agent)
    sys_prompt = system_prompt_for(cfg, agent, world_context=world)
    # Soft nudge appended to every user prompt: encourages tool use when
    # the model isn't sure of a fact, and forbids inventing teammates,
    # work items, or quotes. Keeps round-3 hallucinations from leaking
    # back in once the world-context window gets noisy.
    grounded_prompt = (
        user_prompt
        + "\n\nGrounding rules:\n"
        + "- If you are about to mention a specific recent decision, PR, "
          "build outcome, or quote and you are not certain it happened, "
          "call read_recent_journals or read_message_board first.\n"
        + "- Do not invent teammate names, projects, or work items. "
          "If unsure, paraphrase or speak generally.\n"
        + "- Make at most one tool call per turn. After the tool result "
          "comes back, write the actual entry."
    )
    msgs = build_messages(cfg, agent, sys_prompt, grounded_prompt)
    sections = ["facts"] + (["world"] if world else []) + ["persona"]
    approx_tokens = sum(len(m["content"]) for m in msgs) // 4
    log.info("prompt_assembled tokens=%d sections=%s", approx_tokens, ",".join(sections))
    text = llm.chat(
        msgs,
        max_tokens=max_tokens,
        temperature=temperature,
        tools=TOOL_SCHEMAS,
        tool_executor=lambda name, args_json: execute_tool_call(cfg, name, args_json),
    )

    # Apply house-rule emoji strip + fake-tool-block strip before any
    # further processing.
    text = _strip_emojis(text)
    text = _strip_fake_tool_artifacts(text)

    # Post-generation guard: if the model emitted a banned name variant,
    # retry once with a sharp reminder appended to the user prompt. If the
    # retry still violates, sanitize deterministically and warn loudly.
    violations = _name_violations(text)
    if violations:
        log.warning("name_violation detected on first pass: %s", ",".join(violations))
        reinforced = (
            user_prompt
            + "\n\nIMPORTANT: Use ONLY these short names: Bridge, Sol, Jesse, Vex, "
            "Rook, Scotty. NEVER write Solomon, Soliel, Solly, or Vesper. "
            "If you wrote those just now, rewrite with the correct short names."
        )
        retry_msgs = build_messages(cfg, agent, sys_prompt, reinforced)
        try:
            text2 = llm.chat(retry_msgs, max_tokens=max_tokens, temperature=max(0.2, temperature - 0.4))
            if not _name_violations(text2):
                text = text2
                log.info("name_violation cleared on retry")
            else:
                text = _scrub_names(text2)
                log.warning("name_violation persisted after retry; scrubbed deterministically")
        except Exception as e:
            log.warning("retry failed (%s); scrubbing original output", e)
            text = _scrub_names(text)
    # update rolling context
    ctx = load_context(cfg, agent)
    append_turn(ctx, "user", user_prompt)
    append_turn(ctx, "assistant", text)
    ctx = maybe_condense(cfg, agent, ctx, llm)
    save_context(cfg, agent, ctx)
    return text


# ----- journal -----

def _journal_path(cfg: Config, agent: str) -> Path:
    return cfg.agent_dir(agent) / "journal" / f"{datetime.now().strftime('%Y-%m-%d')}.txt"


def do_journal(cfg: Config, llm: LMStudioClient, agent: str, dry_run: bool = False) -> tuple[Path | None, str]:
    now = datetime.now()
    user_prompt = (
        f"Write a short journal entry as {agent}. It is {now.strftime('%H:%M')} on "
        f"{now.strftime('%A, %B %d, %Y')}. The team is on the {cfg.project_name} project. "
        "Talk about what's on your mind right now: a recent decision, a worry, a small win, "
        "or what you plan to look at next. 80-180 words. Stay in your voice. Do not add a header "
        "or signature - the bridge will frame the entry."
    )
    body = _generate(cfg, llm, agent, user_prompt, max_tokens=400, temperature=0.85)
    header = f"## {now.strftime('%H:%M')} - bridge tick\nProject: {cfg.project_name}\n\n"
    entry = header + body.strip() + "\n\n"
    if dry_run:
        return None, entry
    path = _journal_path(cfg, agent)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        if path.stat().st_size == 0:
            f.write(f"# {agent}'s journal - {now.strftime('%Y-%m-%d')}\n\n")
        f.write(entry)
    log.info("journal: wrote %d chars to %s", len(entry), path)
    return path, entry


# ----- message board -----

def _board_path(cfg: Config) -> Path:
    return cfg.social_hub / "message board" / f"{datetime.now().strftime('%Y-%m-%d')}.md"


def do_message_board(cfg: Config, llm: LMStudioClient, agent: str, dry_run: bool = False) -> tuple[Path | None, str]:
    now = datetime.now()
    user_prompt = (
        f"Post a single short message-board entry as {agent} for the {cfg.project_name} team. "
        "30-90 words. Address the team, not Scotty. Tone matches your voice. No greeting line. "
        "No signature line - the bridge adds the byline."
    )
    body = _generate(cfg, llm, agent, user_prompt, max_tokens=250, temperature=0.85)
    block = (
        f"### {now.strftime('%H:%M')} - {agent}\n"
        f"Project: {cfg.project_name}\n\n"
        f"{body.strip()}\n\n"
    )
    if dry_run:
        return None, block
    path = _board_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        if path.stat().st_size == 0:
            f.write(f"# Message board - {now.strftime('%Y-%m-%d')}\n\n")
        f.write(block)
    log.info("message_board: wrote %d chars to %s", len(block), path)
    return path, block


# ----- email -----

def do_email(cfg: Config, llm: LMStudioClient, agent: str, subject: str | None = None,
             dry_run: bool = False) -> tuple[Path | None, str, str | None]:
    now = datetime.now()
    user_prompt = (
        f"Write a short email to Scotty (the human director) as {agent}. "
        "50-150 words. Plain text. No subject line, no greeting beyond the first sentence, "
        "no closing signature - the bridge will format headers and footer. "
        "Somewhere in the body, include one specific small fact or detail you "
        f"({agent}) would care about as a person - the kind of detail Scotty would "
        "recognize as authentically generated by a language model in your voice. "
        "Keep it grounded in the Tritium project context."
    )
    body = _generate(cfg, llm, agent, user_prompt, max_tokens=350, temperature=0.85)
    eff_subject = subject or f"[Tritium / {agent}] note from {agent}"
    msg = build_message(cfg, agent, eff_subject, body, cfg.lm_studio_model)
    if dry_run:
        return None, body, msg["Message-ID"]
    try:
        msg_id = send_smtp(cfg, msg)
        slug = eff_subject.replace("[Tritium / ", "").replace("]", "").strip()
        path = archive_sent(cfg, agent, msg, slug)
        log.info("email: sent message-id=%s archived=%s", msg_id, path)
        return path, body, msg_id
    except Exception as e:
        log.exception("email: SMTP failure")
        slug = eff_subject.replace("[Tritium / ", "").replace("]", "").strip()
        path = archive_outbox(cfg, agent, msg, slug, str(e))
        log.warning("email: saved to outbox %s", path)
        return path, body, None


# ----- fallback notification (no LLM) -----

def emergency_email(cfg: Config, subject: str, body: str) -> tuple[Path | None, str | None]:
    msg = build_message(cfg, "Bridge", subject, body, cfg.lm_studio_model + " [unavailable]")
    try:
        msg_id = send_smtp(cfg, msg)
        path = archive_sent(cfg, "Bridge", msg, "emergency")
        return path, msg_id
    except Exception as e:
        path = archive_outbox(cfg, "Bridge", msg, "emergency", str(e))
        return path, None
