# Vex — Memory

This directory holds Vex's persistent notes. It has three scopes:

| Scope | Path | Retention |
|---|---|---|
| Repo | `memory/repo/` | Long-lived facts about this codebase. Survives across sessions. |
| Session | `memory/session/` | Notes for the current task. Cleared at task completion. |
| Personal | `memory/personal/` | Cross-workspace preferences for Vex. Survives across repos. |

## Write rules

- One file per topic. Filename: `<topic>.md` for repo/personal; `<YYYY-MM-DD>-<slug>.md` for session.
- Keep entries factual and specific. Cite the source (file path, conversation, URL) when known.
- Respect `memory_write_quota` from `SETTINGS.jsonc`. Consolidate before writing new files.

## Prune rules

- At task completion, classify every `memory/session/` file as `promote-to-repo | drop`.
- Quarterly, Vex reviews `memory/repo/` and removes anything contradicted, obsolete, or redundant.

— Vex
