# Changelog

All notable changes to Tritium are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [SemVer](https://semver.org).

## [0.1.0] — 2026-05-03

### Added
- Initial pre-release of the Tritium multi-agent workflow package.
- Eight-agent canonical roster: Bridge, Sol, Vex, Rook, Robert, Lux, Nova, Jesse.
- Bridge upgraded from pure router to **planner + router + watchdog**:
  - Planning section in `agents/bridge/agent.md` (decompose → write plan to `team/interactions/<date>-<slug>.md` → assign owners → dispatch).
  - Watchdog duty: scans recent correspondence/interactions and proposes prompt patches to `agents/bridge/proposed-prompt-edits/`.
- Real-time inter-agent **chat layer** (`runtime/server/`):
  - SQLite (better-sqlite3) message bus with tables `agents`, `im_messages`, `email`, `threads`, `read_receipts`, `settings`.
  - REST + WebSocket API.
  - Two channels: IM (short, threaded) and Email (long, structured, attachments).
- **Local dashboard** (`runtime/dashboard/`):
  - Static SPA, dark minimalist theme, responsive ≥360px.
  - Routes: `/im`, `/email`, `/agents`, `/settings`, `/timeline`.
  - WebSocket-driven live IM stream; compose IM and email as `@you`.
  - No external CDN — all assets local.
- **`tritium` CLI** (`runtime/cli/`):
  - `tritium serve` — start server + dashboard.
  - `tritium inbox check [--agent <name>]` — list unread IMs and emails.
  - `tritium send-im --from <a> --to <b> --body "..."`
  - `tritium send-email --from <a> --to <b> --subject "..." --body "..." [--attach <path>]`
  - `tritium run-agent <name> --task "..."` (stub for adapter dispatch).
- **JSON Schemas** (`runtime/schemas/`) for IM, email, settings, handoffs.
- **Master settings file** (`SETTINGS.example.jsonc`) with per-agent stats: `independence`, `verbosity`, `inbox_check_interval`, `memory_write_quota`, `portfolio_size_limit`, `model_preference`, `temperature`, `enabled`. Globals: `default_model`, `dashboard_port`, `db_path`, `auto_archive_after_days`, `premium_budget_hint`.
- **Adapters**:
  - `adapters/github-copilot-local/` — drop-in `.github/` for VS Code Copilot.
  - `adapters/github-copilot-remote/` — `.github/` workflows + templates + CODEOWNERS for the synced repo.
  - `adapters/claude-cli/` — `CLAUDE.md` + per-agent prompts + slash commands.
  - `adapters/gemini-cli/` — `GEMINI.md` + tool config + per-agent prompts.
  - `adapters/openai-lmstudio/` — Node script that wires agents to any OpenAI-compatible endpoint, defaults to `dryRun: true`.
- **Memory + portfolio discipline**: each agent has `memory/{repo,session,personal}/` and `portfolio/`, with standardized `MEMORY.md` and `PORTFOLIO.md` headers and a `portfolio prune` step required at task completion.
- **Scripts**: `install.{sh,ps1}`, `package.{sh,ps1}`, `verify.{sh,ps1}`, `new-agent.{sh,ps1}`.
- **Docs**: architecture, usage-vscode-copilot, usage-claude-cli, usage-gemini-cli, usage-api-openai-lmstudio, settings-reference, adding-a-new-agent, troubleshooting.

### Notes
- Agent prompts in this release are derived from the public Political Ascent `TEAM.md`, `copilot-instructions.md`, and shared custom-instruction context. Each agent owner should review their own `agent.md` before production use.
- Adapters ship with `dryRun: true`. No paid API calls are made by default.
- No AI provider keys are bundled.
- Tunnel-mode (remote dashboard access via tailscale/cloudflared) is documented in `docs/troubleshooting.md` but not shipped.

## [Unreleased]

- Editable settings panel in dashboard (round-trips to `SETTINGS.jsonc`).
- First-class adapter for OpenAI Assistants API and Anthropic Messages API native (no proxy).
- Multi-repo aware Bridge planner.
