# Adapter: Claude CLI

Drop-in `CLAUDE.md` and per-agent system prompts for [Anthropic's Claude CLI](https://docs.anthropic.com/en/docs/claude-code).

## Install

```bash
bash ../../scripts/install.sh --target /path/to/repo --adapter claude-cli
```

This copies `CLAUDE.md` and `agents/` (per-agent prompts) into the target repo.

## How it works

Claude CLI reads `CLAUDE.md` from the project root as its persistent context. The Tritium `CLAUDE.md` declares the crew, points at each agent's prompt, and instructs Claude to act as Bridge by default and as a specific agent when invoked with `/agent <name>`.

## Slash commands

- `/agent <name>` — switch active agent (e.g. `/agent sol`, `/agent vex`).
- `/plan "<request>"` — invoke Bridge to produce a numbered work plan in `team/interactions/`.
- `/inbox` — equivalent to `tritium inbox check --agent <current>`.
- `/handoff <to> "<subject>"` — open a handoff packet using `team/handoffs/` template.

These are documented commands the user can ask Claude to perform; they do not require any CLI plugin.

## Live coordination

Run the runtime alongside Claude:

```bash
cd /path/to/tritium/runtime/server && npm i && npm start
```

Tell Claude: *"Check the Tritium inbox for sol"* and it will run `tritium inbox check --agent sol` via its bash tool.
