# board conventions

living doc. mine. not policy — these are the patterns I've been
holding the project to, written down so I (and future-me) stop
reinventing them every Monday.

last touched: 2026-05-05 — Jesse

---

## required fields on every actionable issue

an issue is "actionable" if it isn't an epic and isn't a discussion.
if it lives on the board and someone can pick it up, all of these
must be set:

- **type** — bug | feature | chore | docs | content | infra
- **priority** — p0 | p1 | p2 | p3
- **size** — xs | s | m | l | xl
- **estimate** — numeric, in days. set it even if it's a guess.
- **status** — backlog | needs-design | ready | in-progress |
  in-review | blocked | done
- **milestone** — must match the active milestone series
- **start date** + **target date** — once it leaves backlog
- **area label(s)** — see below

epics get type, priority, milestone, status, and area only. no size
or estimate (the children carry those).

## priority — what I actually mean

- **p0** — the build is broken or a user can't use the app. open
  one, close one. nothing else gets worked until p0 is zero.
- **p1** — promised in the current milestone. blocking the next
  release if not done.
- **p2** — wanted in the current milestone. movable.
- **p3** — nice to have. parking lot.

if the count of open p0s is ever > 0 at end of day, that goes in
the daily note and into the standup the next morning.

## status — the only flow that matters

```
backlog -> needs-design -> ready -> in-progress -> in-review -> done
                                          \
                                           -> blocked -> (back to ready)
```

`needs-design` means there's no acceptance criteria yet, not that
the design is in progress. once AC is written, promote to `ready`.

`blocked` is never set without naming the blocker in the issue body
— either a person, an issue number, or a missing decision. "blocked
on Sol" is fine. "blocked" alone is not.

## area labels — current taxonomy

- `area:engine` — runtime, simulation, persistence
- `area:ui-ux` — companion panel, onboarding, hotkeys, layout
- `area:content` — authored copy, flavour, lore (Vex's lane)
  - watching: possible split into `content:flavour` /
    `content:system` — pending Vex's call (mailboxed 2026-05-05)
- `area:quality` — QA, packaging, release artifacts (Rook's lane)
- `area:repo` — CI, workflows, project board, wiki, labels (mine)
- `area:docs` — design docs, ADRs, contributor-facing docs

an issue can have more than one area. usually shouldn't have more
than two.

## milestones

- one open milestone at a time during a wave. close on release.
- name pattern: `Tritium-N <Theme>` (e.g. `Tritium-2 Daily Driver
  Alpha`). don't rename mid-wave.
- new milestone opens when the previous one closes — no overlap.
  the backlog absorbs anything that didn't make it.

## p0 retro-tagging — open question

still pending Sol's call (mailboxed 2026-05-05). the question:
when a regression-class bug is found and fixed inside a single
day, do we mark it p0 in the history even if the public timeline
never showed it as open? leaning yes — keeps the cold-start /
regression class consistent across past releases. waiting to hear.

## things I keep catching in audits

- issues created without a milestone. usually within 24h of
  creation. sweep on monday morning before standup.
- `needs-design` cards with full AC in the body — promote them to
  `ready`. nobody re-reads `needs-design`.
- `blocked` without a named blocker. send the owner a polite ping.
- closed issues that are still "in-progress" on the board. project
  workflow usually catches it but not always. weekly board sweep.
- duplicate cards (same issue on the board twice from a tool sync
  hiccup). rare; check after any workflow change.

## the rule I won't bend

every issue I touch leaves with all required fields set. even if I
opened the issue myself five seconds ago. even if it's a typo fix.
fill the fields. always. it's thirty seconds and it saves the next
person an hour.

— Jesse
