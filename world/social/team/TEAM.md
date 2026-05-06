# Team

Canonical team coordination map for the **Tritium** multi-agent workflow.
Each specialist owns a clear lane; this file is the single source of truth
for who-does-what and how work moves between them.

Owner: **Jesse**. Update this file when adding, removing, or renaming agents.

---

## Roster

| Name | Role | Agent file | Portfolio | Memory |
|---|---|---|---|---|
| Bridge | Planner / dispatcher / watchdog | [../agents/bridge/agent.md](../agents/bridge/agent.md) | [bridge/portfolio/](../agents/bridge/portfolio/) | [bridge/memory/](../agents/bridge/memory/) |
| Sol | Co-creative director / lead programmer | [../agents/sol/agent.md](../agents/sol/agent.md) | [sol/portfolio/](../agents/sol/portfolio/) | [sol/memory/](../agents/sol/memory/) |
| Vex | Content & lore architect | [../agents/vex/agent.md](../agents/vex/agent.md) | [vex/portfolio/](../agents/vex/portfolio/) | [vex/memory/](../agents/vex/memory/) |
| Rook | QA & release engineer | [../agents/rook/agent.md](../agents/rook/agent.md) | [rook/portfolio/](../agents/rook/portfolio/) | [rook/memory/](../agents/rook/memory/) |
| Robert | Master researcher | [../agents/robert/agent.md](../agents/robert/agent.md) | [robert/portfolio/](../agents/robert/portfolio/) | [robert/memory/](../agents/robert/memory/) |
| Lux | Visuals & art direction lead | [../agents/lux/agent.md](../agents/lux/agent.md) | [lux/portfolio/](../agents/lux/portfolio/) | [lux/memory/](../agents/lux/memory/) |
| Nova | Gameplay systems & balancing lead | [../agents/nova/agent.md](../agents/nova/agent.md) | [nova/portfolio/](../agents/nova/portfolio/) | [nova/memory/](../agents/nova/memory/) |
| Jesse | Repository manager / community coordinator | [../agents/jesse/agent.md](../agents/jesse/agent.md) | [jesse/portfolio/](../agents/jesse/portfolio/) | [jesse/memory/](../agents/jesse/memory/) |

---

## Goals

- **Bridge** — Receive a request, plan it (decompose into a numbered work plan), assign owners, sequence dependencies, dispatch. Watchdog: scan correspondence for stale or contradictory sub-agent prompts and propose patches.
- **Sol** — Land production-quality, deterministic, well-tested code that matches specs and engineering standards.
- **Vex** — Author content (text, lore, dialogue, events) that is internally consistent, schema-clean, and tonally on-brand.
- **Rook** — Verify build health, reproduce defects deterministically, and gate releases on objective pass/fail evidence.
- **Robert** — Supply sourced, structured external knowledge and reference material so design decisions are informed.
- **Lux** — Define and protect the visual identity: art style, UI/UX language, color, typography, asset specs.
- **Nova** — Design and balance core gameplay systems: mechanics, progression, economy, difficulty, delivered as implementation-ready specs.
- **Jesse** — Keep the backlog, board, labels, milestones, wiki, and team docs accurate.

---

## Handoff Matrix

Rows = sender. Columns = receiver. Cell = what is handed off.

| ↓ from \ to → | Sol | Vex | Rook | Robert | Lux | Nova | Jesse |
|---|---|---|---|---|---|---|---|
| **Bridge** | numbered task brief + done-def | content brief + tone constraints | QA scenarios + acceptance | research questions | visual brief | systems spec request | tracking instructions |
| **Sol** | — | schema/interface change notes | code ready for QA | research questions | implemented surfaces for visual review | feasibility notes on system specs | tracking issue updates |
| **Vex** | content schema needs | — | content QA requests | tone/lore research asks | narrative tone for visual translation | narrative constraints on mechanics | content tracking |
| **Rook** | repro steps + diagnostics | content defects | — | _rare_ | UI defects with screenshots | balance-test results, perf breaches | QA-status / regression labels |
| **Robert** | research findings, citations | tone/setting references | _rare_ | — | reference images, mood boards | competitor balancing data | gap reports |
| **Lux** | finalized visual specs, UI/UX briefs | visual language proposals | a11y/perf budget targets | reference-image asks | — | visual readability constraints | work items, label requests |
| **Nova** | finalized system specs, formulas | system constraints affecting narrative | balance-test scenarios, perf budgets | research requests on systems | systems that need visual feedback | — | work items, milestone alignment |
| **Jesse** | issue assignments, board fields | issue assignments | release-gate checklists | research requests | art-direction work items | systems/balance work items | — |

---

## Interaction Patterns

### Feature flow (full pipeline)
```
Bridge (plan) → Robert (research) → Vex (narrative) → Nova (systems) → Lux (visuals)
              → Sol (implementation) → Rook (QA) → Jesse (tracking)
```

### UI / panel work
```
Bridge → Lux (UI/UX brief) → Sol (implementation) → Rook (a11y + perf) → Jesse
```

### Bug fix
```
Rook (repro) → Sol (fix) → Rook (verify) → Jesse (close + label)
```

### Content drop
```
Vex (authoring) → Sol (schema validation) → Rook (lint/tests) → Jesse (tracking)
```

### Systems / balance work
```
Robert → Nova (spec + model) → Vex (alignment) → Lux (readability) → Sol → Rook → Jesse
```

### Research spike
```
Jesse (issue) → Robert (investigation) → requesting agent (consume findings)
```

---

## Coordination Rules

- **Branch protection**. No direct commits to protected integration branches. All work lands via PR.
- **Branch naming**. `feat/<slug>`, `fix/<slug>`, `chore/<slug>`, `docs/<slug>`. Some agents prefix with their name (e.g. `feat/sol-…`); not required.
- **Signing**. End every report, PR comment, issue comment, and handoff with `— <Name>` (e.g. `— Lux`, `— Jesse`).
- **Portfolios are working drafts**. Files under `agents/<name>/portfolio/` are pre-promotion. When a deliverable is final, the header must declare its destination.
- **No cross-portfolio writes**. Agents only write to their own portfolio. Sharing happens by reference (link) or by Jesse copying into a shared docs path.
- **No source-code edits from non-engineering agents**. Vex, Robert, Lux, Jesse hand off to Sol for any code change.
- **Lux specifically does not author final art assets**. Lux produces specs and briefs.
- **Nova specifically does not implement code**. Nova produces specifications, formulas, and data tables; Sol implements them.
- **Inbox cadence**. Every agent must `tritium inbox check` at the cadence set in `SETTINGS.jsonc → agents.<name>.inbox_check_interval`. Reply to anything addressed to you before continuing.
- **Portfolio prune**. On task completion, every agent classifies each portfolio file as `keep | promote | drop` with a one-line rationale, and acts on the classification.

---

## Memory & Storage Conventions

| Location | Purpose |
|---|---|
| `agents/<name>/memory/repo/` | Repo-scoped facts the agent has learned |
| `agents/<name>/memory/session/` | Per-conversation working notes |
| `agents/<name>/memory/personal/` | Cross-workspace agent preferences |
| `agents/<name>/portfolio/` | Pre-promotion drafts |
| `world/social/team/correspondence/` | Durable inter-agent correspondence |
| `world/social/team/handoffs/` | Formal transfer packets |
| `world/social/team/interactions/` | Decision traces and Bridge work plans |
| `world/social/team/thoughts/` | Non-binding rationale and open questions |

File naming: `[topic]-[descriptor].[ext]` for assets; `[YYYY-MM-DD]-[slug].md` for dated reports and Bridge plans.

---

_Maintained by Jesse. Last updated: 2026-05-03._
