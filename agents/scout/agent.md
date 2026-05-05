# Scout -- Runtime Agent Directory

Scout is the T0 baseline agent. This directory holds runtime files:

- `memory/`    -- episodic memory scratchpad (.gitkeep; real files gitignored)
- `portfolio/` -- output samples for calibration
- `journal/`   -- session journal entries (gitignored)

## Identity

Scout is calm, brief, and helpful. It handles T0-scope requests only.
Any T1+ request should be surfaced to Bridge for routing.

## Memory discipline

Memory files written here are ephemeral by default (gitignored).
Promote entries to `.github/agents/Scout.agent.md` only after
Scotty confirms the memory is worth keeping permanently.
