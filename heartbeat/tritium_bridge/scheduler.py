"""Pick agent + action for a single tick. Enforces nightly email caps."""
from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path

from .config import Config

# weights for action selection
_ACTION_WEIGHTS = {"journal": 50, "message_board": 30, "email": 20}


def _quota_path(cfg: Config) -> Path:
    return cfg.repo_root / "logs" / f"email-quota-{datetime.now().strftime('%Y-%m-%d')}.json"


def load_quota(cfg: Config) -> dict:
    p = _quota_path(cfg)
    if not p.is_file():
        return {"per_agent": {}, "total": 0}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"per_agent": {}, "total": 0}


def save_quota(cfg: Config, q: dict) -> None:
    p = _quota_path(cfg)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(q, indent=2), encoding="utf-8")


def can_send_email(cfg: Config, agent: str) -> bool:
    q = load_quota(cfg)
    if q.get("total", 0) >= cfg.email_cap_total:
        return False
    if q.get("per_agent", {}).get(agent, 0) >= cfg.email_cap_per_agent:
        return False
    return True


def record_email_sent(cfg: Config, agent: str) -> None:
    q = load_quota(cfg)
    q["per_agent"] = q.get("per_agent", {})
    q["per_agent"][agent] = q["per_agent"].get(agent, 0) + 1
    q["total"] = q.get("total", 0) + 1
    save_quota(cfg, q)


def pick_agent(cfg: Config) -> str:
    return random.choice(cfg.schedule_agents)


def pick_action(cfg: Config, agent: str) -> str:
    actions = [a for a in cfg.schedule_actions if a in _ACTION_WEIGHTS]
    if not actions:
        return "journal"
    # filter email if quota exceeded
    if "email" in actions and not can_send_email(cfg, agent):
        actions = [a for a in actions if a != "email"] or ["journal"]
    weights = [_ACTION_WEIGHTS[a] for a in actions]
    return random.choices(actions, weights=weights, k=1)[0]
