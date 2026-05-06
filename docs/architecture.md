# Architecture

Tritium is a coordination layer over a small, local-first runtime.

## Components

```
┌─────────────────────────────────────────────────────────────┐
│  Adapters (Copilot / Claude / Gemini / OpenAI / LM Studio)  │
│         ↑                                                   │
│         │  read agents/<name>/{agent.md, prompts/system.md} │
│         │  honor SETTINGS.jsonc                             │
│         ↓                                                   │
│  Tritium runtime                                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Node HTTP server (built-in `http`, no framework)   │    │
│  │  - REST API at /api/*                               │    │
│  │  - WebSocket at /ws (live IM broadcast)             │    │
│  │  - Static dashboard at /                            │    │
│  └────────────────────┬────────────────────────────────┘    │
│                       │                                     │
│                       ▼                                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  SQLite (better-sqlite3, WAL mode)                  │    │
│  │  agents · threads · im_messages · email             │    │
│  │  email_attachments · read_receipts · settings_cache │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Data flow

1. User launches `tritium serve`. The runtime opens (or migrates) the SQLite db, seeds the agent table from `SETTINGS.jsonc`, and listens on `localhost:<dashboard_port>` (7330 by default).
2. The user opens an agent in their adapter of choice. The adapter loads `agents/<name>/prompts/system.md` and `agents/<name>/agent.md` as the system prompt.
3. As the agent works, it calls `tritium inbox check --agent <name>` at the cadence in `SETTINGS.jsonc`. The CLI hits the runtime's REST API.
4. When the agent emits a structured IM block (e.g. `[[IM to=vex]]…[[/IM]]`), the OpenAI adapter forwards it to `POST /api/im`. Other adapters can do the same via shell tool calls.
5. The dashboard subscribes to the `/ws` WebSocket and re-renders on every `im` / `email` event.

## Why Node + SQLite + vanilla SPA

- **Zero install pain**: `npm install` once, `node` runs anywhere.
- **One file = one user's full state**: SQLite is a portable, durable single-file store.
- **No framework lock-in**: vanilla ES modules in the dashboard mean you can edit it without a build step.
- **Local-only by default**: bound to `127.0.0.1`. Nothing leaves your machine unless you tunnel.

## Schemas

JSON Schema documents are in `runtime/schemas/`:

- `im.json` — IM message envelope.
- `email.json` — email envelope (with attachments).
- `settings.json` — `SETTINGS.jsonc` shape.
- `handoff.json` — handoff packet (used by `world/social/team/handoffs/`).

## Security baseline

- API surface is bound to `127.0.0.1` only.
- Static assets are served with `cache-control: no-store` to avoid stale dashboards.
- Path traversal blocked by `safeStaticPath`.
- IM and email bodies are length-capped (32 KB and 200 KB respectively).
- The dashboard never uses `innerHTML` for user-controlled data — all DOM is built via `document.createTextNode` / safe `el()` helper.
- No AI provider keys are stored in the repo or zip. Adapters read keys from environment only, and default to `dryRun: true`.
