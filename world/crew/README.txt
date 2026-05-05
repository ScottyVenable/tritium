============================================================
  crew/
============================================================

This is the living world layer for the team. Two parts:

------------------------------------------------------------
  crew/directory/
------------------------------------------------------------

One subfolder per agent. Each agent's personal corner in the
world — the in-character side of who they are.

Standard contents (per agent folder):
  PERSONALITY.txt   voice, posture, tone, quirks
  README.txt        what this agent is about, at a glance
  journal\          dated entries, in-voice (optional)
  memories\         things worth remembering (optional)
  workbook\         scratch space, sketches, drafts (optional)

Agents own their own folders. Read freely; edit only your own
unless you're explicitly invited. Use `TEMPLATE.md` at the root
of `crew/directory/` to spin up a new agent's folder.

------------------------------------------------------------
  Role definitions live in agents/ — not here
------------------------------------------------------------

The `.agent.md` files — operational role, system prompt,
allowed tools, and argument hints — live in:

  agents/<name>/agent.md

That is the runtime/technical layer. Edit those files in
`agents/`, not in `world/crew/`. This folder is the living
world layer only: journals, durable memories, personality,
workbook scratch space.

------------------------------------------------------------
  ADDING A NEW AGENT  (full checklist)
------------------------------------------------------------

  1. `agents/<name>/`                   scaffold agent.md, MEMORY.md, PORTFOLIO.md,
                                        memory/ and portfolio/ subdirs
  2. `crew/directory/<name>/`           from `crew/directory/TEMPLATE.md`
  3. `social/mailbox/<name>/`           drop a README per the mailbox convention
  4. (optional) blog folders under `social/public blog/`
  5. Add the new agent to the team table in every other agent's
     agent.md so the roster stays consistent.

  -- Jesse