# Settings reference

Tritium reads `SETTINGS.jsonc` from the package root. If absent, falls back to `SETTINGS.example.jsonc`. Override the path via `--settings <path>`.

## `global`

| Key | Type | Default | Effect |
|---|---|---|---|
| `default_model` | string | `claude-sonnet-4.5` | Model used when an agent has no `model_preference`. |
| `dashboard_port` | int (1024–65535) | `7330` | Port for the runtime server, REST API, WebSocket, and dashboard. |
| `db_path` | string | `./.tritium/tritium.db` | SQLite database path. Created on first run. |
| `auto_archive_after_days` | int ≥0 | `30` | Read IMs older than this are moved into a compressed archive. `0` = never. |
| `premium_budget_hint` | enum | `medium` | `low` \| `medium` \| `high` \| `unlimited`. Soft hint to all agents about premium-API budget. Lower budgets bias agents toward higher independence and lower verbosity. |
| `dryRun` | bool | `true` | When true, adapters refuse to make outbound API calls and print what they would have sent. |
| `proposed_prompt_edits_dir` | string | `./agents/bridge/proposed-prompt-edits` | Where Bridge writes watchdog proposals. |

## `agents.<name>`

| Stat | Range / Type | Default | Effect |
|---|---|---|---|
| `independence` | 0–10 | 6 | How autonomously the agent operates. Higher = fewer clarification questions. **Bridge respects this when deciding whether to ask the user vs. document a decision and proceed.** |
| `verbosity` | 0–5 | 3 | Output length budget. 0 = terse bullet, 5 = thorough essay. |
| `inbox_check_interval` | int ≥1 | 3 | How often (in tool calls / checkpoints) the agent must `tritium inbox check`. 1 = every step. |
| `memory_write_quota` | int ≥0 | 25 | Max memory writes per task. Prevents memory bloat. |
| `portfolio_size_limit` | int ≥0 | 100 | Max files in agent's portfolio before a prune is required. |
| `model_preference` | string \| null | null | Override `global.default_model` for this agent. |
| `temperature` | 0.0–1.5 | 0.3 | Sampling temperature. Lower for engineering, higher for creative. |
| `enabled` | bool | true | If false, Bridge will not dispatch to this agent. |

## Adding a new agent

```bash
bash scripts/new-agent.sh <name> "<role description>"
```

This scaffolds `agents/<name>/`, registers in `world/social/team/TEAM.md`, and inserts a default settings stub.

## Independence levels in detail

| Independence | Behavior |
|---|---|
| 0–3 | Ask before every routing decision and option choice. Verbose check-ins. |
| 4–5 | Ask on conflicts or genuinely ambiguous scope. |
| 6 | **Default for most agents.** Decide on small choices, ask on big ones. |
| 7–8 | Decide and proceed for most cases. Document the decision in the plan or PR. |
| 9–10 | Maximum autonomy. Escalate only when the step requires user-only context (credentials, taste, business priority). |
