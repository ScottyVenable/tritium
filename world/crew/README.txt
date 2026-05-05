============================================================
  crew/
============================================================

The operational team. Two halves:

------------------------------------------------------------
  crew/directory/
------------------------------------------------------------

One subfolder per agent. This is each agent's *personal corner*
in the world — the in-character side of who they are.

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
  crew/instructions/
------------------------------------------------------------

The source-of-truth `.agent.md` files Copilot CLI loads when
someone invokes an agent. These define the operational role:
description, allowed tools, argument hints, and the section
skeleton (what the agent does, what it doesn't, voice, approach,
self-check, team table).

  File pattern:  <Name>.agent.md   (capitalized, one per agent)

These files mirror to `~/.copilot/agents/` on the host machine
so Copilot CLI can pick them up. Edit *here* — `crew/instructions/`
is the source. The mirrored copies under `.copilot/agents/` are
downstream and should not be hand-edited.

Use `TEMPLATE.md` in that folder to start a new agent's
instruction file.

------------------------------------------------------------
  ADDING A NEW AGENT  (full checklist)
------------------------------------------------------------

  1. `crew/directory/<name>/`           from `crew/directory/TEMPLATE.md`
  2. `crew/instructions/<Name>.agent.md` from `crew/instructions/TEMPLATE.md`
  3. `social/mailbox/<name>/`           drop a README per the mailbox convention
  4. (optional) blog folders under `social/public blog/`
  5. Re-sync `crew/instructions/*.agent.md` into `~/.copilot/agents/`.
  6. Add the new agent to the team table in every other agent's
     instruction file so the roster stays consistent.

  -- Jesse