# Tritium

**A portable, local-first multi-agent workflow coordination layer.**

[![Version](https://img.shields.io/badge/version-v0.1.0-blue?style=flat-square)](https://github.com/ScottyVenable/tritium/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/status-pre--release-orange?style=flat-square)](https://github.com/ScottyVenable/tritium)

---

## What is Tritium?

Tritium is a portable, self-contained multi-agent workflow coordination layer you can drop into any repository or CLI environment. It ships an eight-role AI crew (Bridge, Sol, Vex, Rook, Robert, Lux, Nova, Jesse), a local SQLite message bus, a live dashboard at `localhost:7330`, a CLI, and drop-in adapters for VS Code Copilot, Claude CLI, Gemini CLI, and any OpenAI-compatible API. No cloud dependency required — everything runs on your machine.

---

## The Crew

| Agent | Role | Specialty |
|---|---|---|
| **Bridge** | Planner · Dispatcher · Watchdog | Decomposes requests, routes work to specialists, audits sub-agent prompts |
| **Sol** | Lead Programmer | Implementation, architecture, automation, CI/CD |
| **Vex** | Content Architect | Narrative text, content tables, authored documentation |
| **Rook** | QA & Release Engineer | Build verification, reproduction cases, release gates |
| **Robert** | Master Researcher | External knowledge, references, gap analysis |
| **Lux** | Visuals & Art Direction | Style guides, UI/UX briefs, asset specifications |
| **Nova** | Gameplay Systems | Mechanics design, progression curves, balance formulas |
| **Jesse** | Repository Manager | Issues, project boards, milestones, labels, wiki |

---

## What's in the Box

```
tritium/
├── agents/                 # Runtime/technical layer — role definitions, system prompts, memory schema, portfolio
│   ├── bridge/
│   ├── sol/
│   ├── vex/
│   ├── rook/
│   ├── robert/
│   ├── lux/
│   ├── nova/
│   └── jesse/
├── adapters/               # Drop-in integrations
│   ├── github-copilot-local/
│   ├── github-copilot-remote/
│   ├── claude-cli/
│   ├── gemini-cli/
│   └── openai-lmstudio/
├── core/runtime/                # Node/TS server · dashboard SPA · CLI · JSON schemas
├── core/heartbeat/              # Python service — keeps the world alive between sessions
├── world/                  # Living world layer — crew journals, personalities, mailbox, locations
├── team/                   # Roster · handoff matrix · correspondence · decision traces
├── docs/                   # Architecture · usage guides · settings reference · troubleshooting
├── scripts/                # install · package · verify · scaffold-new-agent
├── SETTINGS.example.jsonc  # Master tunables — copy to SETTINGS.jsonc and edit
├── CHANGELOG.md
└── LICENSE
```

---

## Quickstart

### 1. Install an adapter into your repo

| Environment | Shell | Command |
|---|---|---|
| VS Code GitHub Copilot (local) | bash | `bash scripts/install.sh --target /path/to/repo --adapter github-copilot-local` |
| VS Code GitHub Copilot (remote) | bash | `bash scripts/install.sh --target /path/to/repo --adapter github-copilot-remote` |
| Claude CLI | bash | `bash scripts/install.sh --target /path/to/repo --adapter claude-cli` |
| Gemini CLI | bash | `bash scripts/install.sh --target /path/to/repo --adapter gemini-cli` |
| OpenAI / LM Studio | bash | `cd adapters/openai-lmstudio && npm i && npm run start` |
| Any of the above | PowerShell | Replace `scripts/install.sh` with `scripts\install.ps1` |

### 2. Start the live coordination layer

```bash
cd core/runtime/server
npm install
npm start
# Dashboard: http://localhost:7330
```

---

## Live Coordination Layer

Tritium ships a local-first real-time coordination layer with no external dependencies:

| Component | Description |
|---|---|
| **SQLite message bus** | Persistent store for IM threads, email, read receipts, agent registry |
| **REST + WebSocket API** | Live message delivery; all dashboard routes are WebSocket-driven |
| **IM channel** | Short, threaded messages between agents and `@you` |
| **Email channel** | Long-form structured messages with optional attachments |
| **Dashboard** | Dark SPA at `http://localhost:7330` — routes: `/im` · `/email` · `/agents` · `/settings` · `/timeline` |
| **`tritium` CLI** | `serve` · `inbox check` · `send-im` · `send-email` · `run-agent` |

---

## Master Settings

Copy `SETTINGS.example.jsonc` to `SETTINGS.jsonc` and edit. Override path with `--settings /path/to/SETTINGS.jsonc`.

<details>
<summary>Show condensed example</summary>

```jsonc
{
  "global": {
    "default_model": "claude-sonnet-4.5",  // inherited by all agents unless overridden
    "dashboard_port": 7330,
    "db_path": "./.tritium/tritium.db",
    "auto_archive_after_days": 30,
    "premium_budget_hint": "medium",       // "low" | "medium" | "high" | "unlimited"
    "dryRun": true                         // flip to false when ready to spend tokens
  },
  "agents": {
    "bridge": {
      "independence": 7,    // 0–10: how autonomously the agent operates
      "verbosity": 3,       // 0–5: output length budget
      "inbox_check_interval": 1,
      "memory_write_quota": 20,
      "portfolio_size_limit": 50,
      "model_preference": null, // null = inherit global.default_model
      "temperature": 0.2,
      "enabled": true
    }
    // ... one block per agent; see SETTINGS.example.jsonc for the full set
  }
}
```

</details>

See [docs/settings-reference.md](docs/settings-reference.md) for every key and its effect.

---

## Documentation

| Document | Description |
|---|---|
| [docs/architecture.md](docs/architecture.md) | System design, component diagram, data flow |
| [docs/settings-reference.md](docs/settings-reference.md) | Every setting key, type, default, and effect |
| [docs/usage-vscode-copilot.md](docs/usage-vscode-copilot.md) | VS Code Copilot adapter walkthrough |
| [docs/usage-claude-cli.md](docs/usage-claude-cli.md) | Claude CLI adapter walkthrough |
| [docs/usage-gemini-cli.md](docs/usage-gemini-cli.md) | Gemini CLI adapter walkthrough |
| [docs/usage-api-openai-lmstudio.md](docs/usage-api-openai-lmstudio.md) | OpenAI / LM Studio adapter walkthrough |
| [docs/adding-a-new-agent.md](docs/adding-a-new-agent.md) | How to scaffold and register a new agent |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common issues and fixes |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

---

## License

MIT — see [LICENSE](LICENSE).

See [world/social/team/TEAM.md](world/social/team/TEAM.md) for the full handoff matrix and interaction patterns.

## Live coordination layer

Tritium ships a small Node/SQLite **message bus** so agents can chat and email each other while working:

- **IM** — short, threaded, expected-soon replies. Real-time WebSocket stream.
- **Email** — longer, structured, supports attachments (file paths or inline blobs).
- **Dashboard** — local SPA at `http://localhost:7330` to watch the IM stream, browse the inbox, send messages as `@you`, and edit settings live.

See [docs/architecture.md](docs/architecture.md) for the data model and [docs/settings-reference.md](docs/settings-reference.md) for tunables.

## Master settings

`SETTINGS.example.jsonc` is the single source of tunables. Copy to `SETTINGS.jsonc` and edit:

```jsonc
{
  "global": {
    "default_model": "claude-sonnet-4.5",
    "dashboard_port": 7330,
    "db_path": "./.tritium/tritium.db"
  },
  "agents": {
    "bridge": { "independence": 7, "verbosity": 3, "inbox_check_interval": 1, "enabled": true },
    "sol":    { "independence": 6, "verbosity": 4, "inbox_check_interval": 2, "enabled": true }
    // ...
  }
}
```

Higher `independence` = fewer clarification questions back to you. See [docs/settings-reference.md](docs/settings-reference.md) for every key.

## Scaling up

Add a new agent in one command:

```bash
bash scripts/new-agent.sh <name> "<role-description>"
```

This scaffolds `agents/<name>/`, registers it in `world/social/team/TEAM.md`, adds a settings stub, and prepares prompts for each adapter.

## Pre-release

Build the zip + SHA-256:

```bash
bash scripts/package.sh
# → dist/tritium-v0.1.0.zip
# → dist/tritium-v0.1.0.zip.sha256
```

Smoke-test the runtime:

```bash
bash scripts/verify.sh
```

## Roadmap

See [CHANGELOG.md](CHANGELOG.md). The dashboard ships read-write for IM/email and read-only for `SETTINGS.jsonc` reflection in v0.1; the editable settings panel and tunnel-mode documentation land in v0.2.

— Tritium Team


## The Team & Their World

Tritium is built by a named team of agents — Bridge, Sol, Jesse, Vex, and
Rook — working under Scotty as Creative Director. Their living world (journals,
memories, mailbox, locations) is snapshotted in [world/](world/README.md).
That folder is a backup of the team's shared space; it is not required to
run the runtime.
