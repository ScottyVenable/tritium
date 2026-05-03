# Bridge — Proposed Prompt Edits

Bridge writes patch proposals for sub-agent prompts here when its watchdog
duty detects drift (stale instructions, contradictions, under-scope, repeated
clarification questions on the same topic).

## File pattern

`<YYYY-MM-DD>-<agent>-<slug>.md`

## Required sections

- **Subject agent** (which agent's prompt is being patched).
- **Symptom** (the observation that triggered the proposal, with citations from `team/correspondence/` or `team/interactions/`).
- **Proposed patch** (unified diff against the current `agent.md`, or before/after snippet).
- **Risk** (what this change could break).
- **Status** — `proposed | approved | applied | rejected`.

Bridge **never applies its own proposals**. The user reviews and either approves or rejects each one. On approval, the change is applied via Sol or Jesse depending on the file path.

— Bridge
