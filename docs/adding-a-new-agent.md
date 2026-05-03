# Adding a new agent

```bash
bash scripts/new-agent.sh <name> "<role description>"
```

This script:

1. Creates `agents/<name>/` with `agent.md`, `MEMORY.md`, `PORTFOLIO.md`, `prompts/system.md`, `memory/{repo,session,personal}/`, and `portfolio/`.
2. Adds a default-stats stub to `SETTINGS.example.jsonc`.
3. Adds a row to `team/TEAM.md`'s roster table (handoff matrix is *not* auto-populated — you fill in the cells once the agent's lane is settled).
4. Copies the agent's `agent.md` into each adapter's per-agent prompt directory.

After running, you should:

- Edit `agents/<name>/agent.md` to specify the agent's voice, posture, allowed/disallowed file edits, coordination, and non-negotiables.
- Tune `SETTINGS.example.jsonc → agents.<name>` (defaults are reasonable; adjust `independence` and `inbox_check_interval` to match the agent's role).
- Update the handoff matrix in `team/TEAM.md`.
- Notify Bridge so the watchdog tracks the new agent.

## Naming conventions

- Agent name is one word, lower-case in code (`vex`), Title-Case in display (`Vex`).
- Avoid ambiguity with existing agents: don't add a "Sage" if you have a "Sol".
- Single-syllable, evocative names age well.
