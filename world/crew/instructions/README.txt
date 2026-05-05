============================================================
  [3b] (agents) instruction files
============================================================

This is the source of truth for every agent's operational
instructions — the `.agent.md` files Copilot CLI loads at
runtime to know who an agent is, what tools they can use,
and how they're supposed to work.

------------------------------------------------------------
  WHAT LIVES HERE
------------------------------------------------------------

  <Name>.agent.md     one file per agent (Bridge, Sol, Jesse,
                      Vex, Rook, ...). Capitalized. Frontmatter
                      on top, role description below.
  TEMPLATE.md         start new agent files from this. Copy,
                      rename to `<Name>.agent.md`, fill it in.

------------------------------------------------------------
  HOW THESE GET USED
------------------------------------------------------------

Copilot CLI reads agent instructions from `~/.copilot/agents/`
on the host. Files in this folder are mirrored *into* that
directory — either by a sync script, by the new-folder
template machinery, or by hand.

  Edit the file HERE.
  Mirror it to `~/.copilot/agents/`.
  Don't edit the mirror.

If you find yourself fixing something in `~/.copilot/agents/`
directly, stop, port the fix back here, and re-sync. Otherwise
the next mirror will overwrite your change.

------------------------------------------------------------
  FRONTMATTER CONTRACT
------------------------------------------------------------

Every agent file opens with YAML frontmatter:

  ---
  description: >-
    Use when: <one-liner triggers and scope>.
    <One sentence stating who this agent is.>
    Trigger phrases: <comma-separated list>.
  name: <Name>
  tools:
    - read
    - edit
    - search
    - execute
    - todo
    - agent
    - browser
    - web
  argument-hint: >-
    <What the user should describe when invoking this agent.>
  ---

Match the existing files (Sol.agent.md, Bridge.agent.md, etc.)
for section structure: identity paragraph, "What X does",
"What X does NOT do", voice, approach, self-check, team table.

  -- Jesse