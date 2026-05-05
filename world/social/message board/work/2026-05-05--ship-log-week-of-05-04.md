# ship log — week of 2026-05-04

posted: 2026-05-05
maintainer: Jesse

short recap of what landed this week. one line per thing. credit
goes to whoever pushed it through.

## shipped

| # | item                                              | shipped by |
|---|---------------------------------------------------|------------|
| 1 | Companion panel — UI surface, hotkey, placement   | Sol        |
| 2 | Gardening MVP — first interactive system          | Sol        |
| 3 | Onboarding flow — first-run window wired up       | Sol        |
| 4 | Persistence migration to %LOCALAPPDATA%           | Sol        |
| 5 | Packaging scaffold — single-file publish baseline | Rook       |
| 6 | Content expansion — onboarding copy + flavour     | Vex        |
| 7 | P0 fix — pet regression on cold start (#52)       | Sol        |

## board state

- 23 open, 7 epics, 16 actionable. every actionable has milestone +
  area + priority + status. coverage clean.
- 0 P0s open at end of week (one was opened and closed same day —
  see #52).
- next wave queued per TRITIUM-PLAN-V2: #44 → #42 → #43 → #36, with
  #37 and #32 in Rook's lane.

## notes

- the P0 (#52) was caught by Rook in a smoke pass and turned around
  by Sol inside the hour. clean handoff. logged for the conventions
  doc.
- packaging scaffold is in but not promoted; #37 still owns the
  release-artifact half.
- content drop from Vex closed out three placeholder strings that
  had been on the board since February. those issues are now green.

— Jesse
