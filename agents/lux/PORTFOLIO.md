# Lux — Portfolio

Working drafts and pre-promotion artifacts. Files here are **not canonical**.
When a draft is ready, Lux (or Jesse) promotes it to the appropriate
canonical location (see `team/TEAM.md`).

## Conventions

- Filename: `<topic>-<descriptor>.<ext>` for assets; `<YYYY-MM-DD>-<slug>.md` for dated reports.
- Every draft starts with a header: **Audience**, **Status** (`draft | review | promoted | archived`), **Destination** (where it will live when promoted), **Updated** (date).
- Images and binaries go under `portfolio/images/` (or `portfolio/assets/`).

## Portfolio prune (required at task completion)

For each file in `portfolio/`, Lux marks it:

- `keep` — still in flight, will be touched again soon.
- `promote` — final; move to canonical destination.
- `drop` — superseded, abandoned, or no longer relevant.

Write the prune log as `portfolio/_prune-<YYYY-MM-DD>.md` with one line per file. Then act on the classifications.

If `portfolio_size_limit` (from `SETTINGS.jsonc`) is exceeded, prune before adding new files.

— Lux
