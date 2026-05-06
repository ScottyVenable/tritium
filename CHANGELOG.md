# Changelog

All notable changes to this project will be documented in this file.
Format: Keep a Changelog (https://keepachangelog.com/en/1.0.0/).
Versioning: Semantic Versioning (https://semver.org/).

## [Unreleased]

### Changed
- **Repo reorganization (Phase A of unification plan).** Top-level layout flattened to reduce nesting:
  - `core/runtime/` → `runtime/` (Node/TS server, dashboard SPA, CLI, schemas now live at root).
  - `mobile-environment/` → `scripts/mobile/` (Termux/Android helpers grouped under `scripts/`).
  - All internal references in scripts (`scripts/package.sh`, `scripts/verify.sh`), docs (`docs/architecture.md`, `docs/troubleshooting.md`, `docs/usage-*.md`), and `README.md` updated to the new paths.
  - `core/heartbeat/` → `runtime/heartbeat/` (live service alongside the Node server).
  - `core/registry/` → `data/registry/` (data, not code).
  - Empty `core/` directory removed; references in `AGENTS.md`, `README.md`, and `docs/` updated.
  - Top-level after Phase A: `adapters/`, `agents/`, `data/`, `docs/`, `runtime/`, `scripts/`, `world/`, plus root files.

### Removed
- `world/crew/instructions/` — held `.agent.md` files that duplicated `agents/<name>/agent.md`. Under Option B, `agents/` is the sole core/runtime/technical layer and `world/crew/` is the living world layer. Diff confirmed no unique content in `world/crew/instructions/`; those copies carried encoding artifacts (`ΓÇö`/`ΓåÆ`) already fixed in `agents/`.

### Changed
- `world/crew/README.txt` — removed `instructions/` section; updated "ADDING A NEW AGENT" checklist to point to `agents/<name>/`; added explicit note that runtime definitions live in `agents/`, not here.
- `world/crew/directory/TEMPLATE.md` — updated cross-reference from `world/crew/instructions/<Name>.agent.md` to `agents/<name>/agent.md`.
- `README.md` — clarified `agents/` and `world/` component descriptions to reflect the two-layer split (core/runtime/technical vs living world).

## [4.1.0]-- 2026-01-02 -- Omni-Refactor

### Added
- `scripts/tritium-crypt` -- AES-256-GCM vault with X25519/HKDF key wrapping and Ed25519 signing.
- `scripts/tritium-open` -- shield-checked vault payload opener.
- `scripts/tritium-close` -- re-seal with 3-pass mirror shred and snap-back logging.
- `scripts/tier-auto` -- four-tier agent manager with automatic T0 snap-back.
- `scripts/tritium-cp` -- Python ASCII control panel dashboard.
- `scripts/tritium-doctor` -- 11-point diagnostic suite; exits non-zero on FAIL.
- `scripts/tritium-id` -- runtime identity printer.
- `scripts/tritium-authorize` -- shield token renewal.
- `scripts/setup.sh` -- idempotent v4.0+v4.1 bootstrapper (Termux/Linux).
- `scripts/setup-ledger.py` -- ledger schema helper (called by setup.sh).
- `core/registry/models.json` -- authoritative tier/model registry for all agents.
- `core/registry/credits.ledger` -- append-only AI credit monitoring.
- `world/vault/manifest.json` -- encrypted payload manifest.
- `bridge/tritium_bridge/ledger.py` -- SQLite ledger facade (log_event, remember, recall, summary).
- `data/ledger.schema.sql` -- SQLite ledger schema.
- `mobile-environment/configs/bashrc.sh` -- Termux shell integration with aliases and shield check.
- `.github/agents/` -- agent spec .md files for Bridge, Scout, Sol, Jesse, Vex, Rook.
- `agents/scout/` -- Scout runtime directory with MEMORY.md and subdirs.
- `AGENTS.md` -- authoritative agent roster.
- `docs/SECURITY-tritium-crypt.md` -- Rook's crypto vault specification.
- `docs/ARCHITECTURE-v4.md` -- v4.0 Genesis architecture document.
- `docs/ARCHITECTURE-v4.1.md` -- v4.1 Omni-Refactor architecture document.
- Bridge Team Lead role: Rule 0 Scout pre-dispatch before any routing decision.
- Tier snap-back: all T1+ sessions return to T0 Scout via `tier-auto snap`.

### Changed
- `scripts/tritium-doctor` replaced stub with 11-point diagnostic implementation.
- Bridge role updated from "Dispatcher" to "Team Lead" with Scout pre-dispatch.

### Security
- Vault boundary: `.tritium_mirror/`, `*.x25519`, `*.ed25519`, `*.pem` gitignored.
- AES-256-GCM + X25519/HKDF key wrapping; never silently degrades.
- Ed25519 manifest signing; open refuses on signature mismatch.

## [4.0.0] -- 2026-01-01 -- Genesis

### Added
- Initial Tritium OS multi-agent runtime foundation.
- `bridge/tritium_bridge/` Python package: personas, context, LM Studio, actions, filedrop, scheduler, worldcontext.
- `scripts/install.sh` / `install.ps1` -- dependency installer.
- `scripts/verify.sh` / `verify.ps1` -- environment verifier.
- `scripts/new-agent.sh` / `new-agent.ps1` -- agent scaffold generator.
- `scripts/package.sh` / `package.ps1` -- release packager.
- Six named agents: Bridge, Scout, Sol, Jesse, Vex, Rook.

## [Unreleased]

### Changed
- Renamed `bridge/` Python service folder to `core/heartbeat/` to remove naming collision with the Bridge agent.
- Renamed `world/` subfolders: dropped Windows Explorer bracket convention throughout.
  - `[1] -- social hub --` → `social/`
  - `[2] -- locations --` → `locations/`
  - `[3] -- agents --` → `crew/`
  - `[4]_bridge_` → `bridge-workspace/`
  - `crew/[3a] (agents) directory` → `crew/directory/`
  - `crew/[3b] (agents) instruction files` → `crew/instructions/`
- Updated `.gitignore` path for bridge-workspace `.env`.
- Updated internal references in `world/README.md`, `world/crew/README.txt`, `world/crew/directory/TEMPLATE.md`, `world/social/README.txt`, and root `README.md`.
- Root `README.md` tree now documents `core/heartbeat/` and `world/`.

### Removed
- `world/[ more folders can be created ]` — empty PowerToys NewPlus placeholder.
- `world/README.txt` — duplicate of `world/README.md`.

## [0.1.0] — 2026-05-03

### Added
- Initial pre-release of the Tritium multi-agent workflow package.
- Eight-agent canonical roster: Bridge, Sol, Vex, Rook, Robert, Lux, Nova, Jesse.
- Bridge upgraded from pure router to **planner + router + watchdog**:
  - Planning section in `agents/bridge/agent.md` (decompose → write plan to `world/social/team/interactions/<date>-<slug>.md` → assign owners → dispatch).
  - Watchdog duty: scans recent correspondence/interactions and proposes prompt patches to `agents/bridge/proposed-prompt-edits/`.
- Real-time inter-agent **chat layer** (`core/runtime/server/`):
  - SQLite (better-sqlite3) message bus with tables `agents`, `im_messages`, `email`, `threads`, `read_receipts`, `settings`.
  - REST + WebSocket API.
  - Two channels: IM (short, threaded) and Email (long, structured, attachments).
- **Local dashboard** (`core/runtime/dashboard/`):
  - Static SPA, dark minimalist theme, responsive ≥360px.
  - Routes: `/im`, `/email`, `/agents`, `/settings`, `/timeline`.
  - WebSocket-driven live IM stream; compose IM and email as `@you`.
  - No external CDN — all assets local.
- **`tritium` CLI** (`core/runtime/cli/`):
  - `tritium serve` — start server + dashboard.
  - `tritium inbox check [--agent <name>]` — list unread IMs and emails.
  - `tritium send-im --from <a> --to <b> --body "..."`
  - `tritium send-email --from <a> --to <b> --subject "..." --body "..." [--attach <path>]`
  - `tritium run-agent <name> --task "..."` (stub for adapter dispatch).
- **JSON Schemas** (`core/runtime/schemas/`) for IM, email, settings, handoffs.
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
