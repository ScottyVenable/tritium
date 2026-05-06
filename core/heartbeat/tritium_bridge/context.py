"""Per-agent rolling context. Stored as JSON inside each agent's workbook."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .config import Config

MAX_TURNS = 10
CONDENSE_TARGET_TOKENS = 200
PROMPT_TOKEN_BUDGET = 6000  # ~ rough char/4 estimate


def _ctx_path(cfg: Config, agent: str) -> Path:
    return cfg.agent_dir(agent) / "workbook" / ".context.json"


def load_context(cfg: Config, agent: str) -> dict:
    p = _ctx_path(cfg, agent)
    if not p.is_file():
        return {"summary": "", "turns": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"summary": "", "turns": []}


def save_context(cfg: Config, agent: str, ctx: dict) -> None:
    p = _ctx_path(cfg, agent)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding="utf-8")


def append_turn(ctx: dict, role: str, content: str) -> None:
    ctx.setdefault("turns", []).append({
        "role": role,
        "content": content,
        "ts": datetime.now(timezone.utc).isoformat(),
    })


def maybe_condense(cfg, agent: str, ctx: dict, llm) -> dict:
    """If turn count exceeds MAX_TURNS, summarize the older half into ctx['summary']."""
    turns = ctx.get("turns", [])
    if len(turns) <= MAX_TURNS:
        return ctx
    keep = turns[-MAX_TURNS:]
    older = turns[:-MAX_TURNS]
    older_text = "\n".join(f"[{t['role']}] {t['content']}" for t in older)
    prior_summary = ctx.get("summary", "")
    prompt = (
        "Summarize the following prior context for the agent named "
        f"{agent} in roughly {CONDENSE_TARGET_TOKENS} tokens. Preserve "
        "relationships, recent decisions, and any open commitments.\n\n"
        f"PRIOR_SUMMARY:\n{prior_summary}\n\nNEW_TURNS:\n{older_text}"
    )
    try:
        from .lmstudio import ChatMessage  # local import to avoid cycle
        new_summary = llm.chat(
            [ChatMessage("system", "You produce terse, faithful summaries."),
             ChatMessage("user", prompt)],
            max_tokens=400, temperature=0.2,
        )
    except Exception:
        # If summarization fails, just drop the older turns rather than crash.
        new_summary = prior_summary
    ctx["summary"] = new_summary
    ctx["turns"] = keep
    return ctx


def build_messages(cfg, agent: str, system_prompt: str, user_prompt: str) -> list[dict]:
    """Assemble the message list for an LLM call, capped at PROMPT_TOKEN_BUDGET."""
    ctx = load_context(cfg, agent)
    msgs: list[dict] = [{"role": "system", "content": system_prompt}]
    if ctx.get("summary"):
        msgs.append({"role": "system", "content": "Prior context summary:\n" + ctx["summary"]})
    for t in ctx.get("turns", []):
        msgs.append({"role": t["role"], "content": t["content"]})
    msgs.append({"role": "user", "content": user_prompt})

    # Crude budget enforcement: chars/4 ~ tokens.
    while True:
        total = sum(len(m["content"]) for m in msgs) // 4
        if total <= PROMPT_TOKEN_BUDGET or len(msgs) <= 3:
            break
        # drop the oldest non-system turn
        for i, m in enumerate(msgs):
            if m["role"] != "system":
                msgs.pop(i)
                break
    return msgs
