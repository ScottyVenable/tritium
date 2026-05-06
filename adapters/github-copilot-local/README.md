# Adapter: GitHub Copilot (local, VS Code)

Drop-in `.github/` directory for **VS Code GitHub Copilot custom agents** running locally.

## Install

```bash
bash ../../scripts/install.sh --target /path/to/repo --adapter github-copilot-local
```

This copies `.github/agents/`, `.github/team/`, `.github/portfolios/`, `.github/copilot-instructions.md`, and `.github/TEAM.md` into the target repo. Existing files are preserved with a `.bak` suffix.

## How it works

VS Code Copilot reads `.github/copilot-instructions.md` as the default agent personality, and `.github/agents/<Name>.agent.md` files when you `@mention` a custom agent. We map Tritium agents 1:1 onto Copilot custom agents.

## Files

- `.github/copilot-instructions.md` — minimal Bridge-as-default routing prompt.
- `.github/agents/<Name>.agent.md` — one per Tritium agent (Bridge, Sol, Vex, Rook, Robert, Lux, Nova, Jesse).
- `.github/TEAM.md` — handoff matrix.
- `.github/portfolios/<name>/README.md` — pre-promotion drafts location.
- `.github/team/{correspondence,handoffs,interactions,thoughts}/README.md` — team docs.

## Live coordination

For the IM/email bus and dashboard, also run the Tritium runtime separately:

```bash
cd /path/to/tritium/core/runtime/server && npm i && npm start
# dashboard at http://localhost:7330
```

Each agent's prompt instructs them to call `tritium inbox check` at their configured `inbox_check_interval`.
