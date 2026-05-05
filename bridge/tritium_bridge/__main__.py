"""Bridge CLI entrypoint.

Usage:
    python -m tritium_bridge --check
    python -m tritium_bridge --tick [--agent NAME] [--action KIND] [--subject S] [--dry-run]
    python -m tritium_bridge --imap-watch
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from . import actions as A
from .config import load as load_config
from .lmstudio import LMStudioClient
from .mailer import poll_imap
from .personas import persona_path, load_persona
from .scheduler import pick_action, pick_agent, record_email_sent


def _setup_logging(repo_root: Path) -> None:
    log_dir = repo_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    handlers = [
        logging.FileHandler(log_dir / "bridge.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
        handlers=handlers,
    )


def cmd_check(cfg) -> int:
    log = logging.getLogger("check")
    ok = True
    log.info("PASS: env loaded (smtp=%s imap=%s lm=%s)", cfg.smtp_host, cfg.imap_host, cfg.lm_studio_url)

    if not cfg.world_root.is_dir():
        log.error("FAIL: WORLD_ROOT does not exist: %s", cfg.world_root)
        ok = False
    else:
        log.info("PASS: world_root exists: %s", cfg.world_root)

    if not cfg.agents_root.is_dir():
        log.error("FAIL: agents root missing: %s", cfg.agents_root)
        ok = False
    else:
        log.info("PASS: agents root: %s", cfg.agents_root)

    for a in cfg.schedule_agents:
        try:
            p, src = persona_path(cfg, a)
            text = load_persona(cfg, a)
            log.info("PASS: persona %s (%s, %d chars) -> %s", a, src, len(text), p)
        except Exception as e:
            log.error("FAIL: persona %s: %s", a, e)
            ok = False

    try:
        with LMStudioClient(cfg) as llm:
            models = llm.list_models()
            if cfg.lm_studio_model not in models:
                log.warning("WARN: configured model '%s' not in /v1/models list (will JIT load): %s",
                            cfg.lm_studio_model, models[:5])
            else:
                log.info("PASS: LM Studio reachable, model '%s' present", cfg.lm_studio_model)
    except Exception as e:
        log.error("FAIL: LM Studio unreachable: %s", e)
        ok = False

    return 0 if ok else 1


def cmd_tick(cfg, args) -> int:
    log = logging.getLogger("tick")

    # 1. IMAP poll first (best-effort)
    try:
        saved = poll_imap(cfg)
        if saved:
            log.info("imap: saved %d new messages", len(saved))
    except Exception as e:
        log.warning("imap poll failed (non-fatal): %s", e)

    # 2. choose agent + action
    agent = args.agent or pick_agent(cfg)
    if agent not in cfg.schedule_agents:
        log.error("agent '%s' not in SCHEDULE_AGENTS=%s", agent, cfg.schedule_agents)
        return 2
    action = args.action or pick_action(cfg, agent)
    log.info("tick: agent=%s action=%s dry_run=%s", agent, action, args.dry_run)

    # 3. ensure LM Studio reachable; if not, send fallback alert and exit
    try:
        llm = LMStudioClient(cfg)
        if not llm.ping():
            raise RuntimeError("LM Studio ping failed")
    except Exception as e:
        log.error("LM Studio offline: %s", e)
        if not args.dry_run:
            body = (
                "Bridge tried to wake the team and could not reach the local "
                f"LM Studio server at {cfg.lm_studio_url}.\n\n"
                f"Error: {e}\n\n"
                "Please bring LM Studio back up (load model "
                f"'{cfg.lm_studio_model}') and the scheduled task will pick "
                "up on the next tick.\n"
            )
            path, mid = A.emergency_email(
                cfg,
                "[Tritium / Bridge] LM Studio offline - bridge needs your help",
                body,
            )
            log.error("fallback email path=%s message-id=%s", path, mid)
        return 3

    try:
        if action == "journal":
            path, text = A.do_journal(cfg, llm, agent, dry_run=args.dry_run)
            print(text)
            log.info("journal -> %s", path)
        elif action == "message_board":
            path, text = A.do_message_board(cfg, llm, agent, dry_run=args.dry_run)
            print(text)
            log.info("message_board -> %s", path)
        elif action == "email":
            path, text, msg_id = A.do_email(cfg, llm, agent, subject=args.subject, dry_run=args.dry_run)
            print(text)
            log.info("email -> path=%s message-id=%s", path, msg_id)
            if msg_id and not args.dry_run:
                record_email_sent(cfg, agent)
        else:
            log.error("unknown action: %s", action)
            return 2
    finally:
        llm.close()
    return 0


def cmd_imap_watch(cfg) -> int:
    log = logging.getLogger("imap")
    log.info("imap-watch: polling every 60s. Ctrl+C to stop.")
    while True:
        try:
            saved = poll_imap(cfg)
            if saved:
                log.info("saved %d", len(saved))
        except Exception as e:
            log.warning("poll error: %s", e)
        time.sleep(60)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tritium-bridge")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--tick", action="store_true")
    mode.add_argument("--imap-watch", action="store_true")

    p.add_argument("--agent")
    p.add_argument("--action", choices=["journal", "message_board", "email"])
    p.add_argument("--subject")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    cfg = load_config()
    _setup_logging(cfg.repo_root)

    if args.check:
        return cmd_check(cfg)
    if args.tick:
        return cmd_tick(cfg, args)
    if args.imap_watch:
        return cmd_imap_watch(cfg)
    return 1


if __name__ == "__main__":
    sys.exit(main())
