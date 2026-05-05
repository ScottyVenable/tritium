# Bug reproduction — standard template

Fill out top to bottom. If a section is "unknown" or "n/a", say
so explicitly; do not delete it. Empty sections look like the
information was never gathered, and that is a different problem.

A repro is not finished until someone else can follow it cold.

---

## Header

- **Title:** one line. Symptom first, not hypothesis.
- **Severity:** P0 / P1 / P2 / P3. Pick one.
  - P0 = blocking, data-loss, or app does not start.
  - P1 = milestone blocker, no acceptable workaround.
  - P2 = normal fix, has a workaround.
  - P3 = backlog, cosmetic or rare.
- **Reporter:** name.
- **Date / time observed:** ISO local.
- **Build / commit:** SHA, branch, version string from `--version`
  if available.
- **OS / runtime:** Windows build, .NET runtime version.
- **Related issues / PRs:** numbers only.

## Process state at failure

- Did the process start?
- Did it stay alive? For how long? (PID + lifetime in seconds.)
- Was MainWindowHandle non-zero at any point?
- Was the tray icon registered?
- Exit code, if captured.

## Reproduction steps

Numbered. Each step is one observable action. No "configure
normally". No "do the usual setup". If a step depends on state,
say what state.

  1. ...
  2. ...
  3. ...

Expected: what should happen at the last step.
Actual:   what happens instead.

Reproducibility: always / intermittent (N of M tries) / once.

## Logs

- Path to the relevant log file.
- Last 10 lines or the failure window, whichever is smaller.
  Quote verbatim. Do not paraphrase log lines.

## Event log

- Source, Event ID, timestamp.
- Full exception type and message.
- Stack frames named, in order, with file:line where the runtime
  provides them. The runtime usually provides them; if it does
  not, say so.

## Top hypothesis

One paragraph. State the most likely cause and why. If you have
two competing hypotheses, list both, but rank them.

## Suspected file:line

  - `path\to\file.cs:NN` — what you think happens here.
  - `path\to\other.xaml.cs:NN` — what you think happens here.

If you cannot point to a file:line, say "unknown" and explain
what additional information would let you point to one. Do not
guess.

## Workaround (if any)

Steps a user can take right now to avoid the bug. "None known"
is a valid answer.

## Escalation

- Owner (who fixes): Sol / Vex / unknown.
- Routing: PR target, mailbox note path if filed, issue number
  if filed.
- Blocking what: list of milestones / features blocked. "Nothing"
  is a valid answer.

## Verification plan after fix

How will I know the fix worked. Specific commands or specific
checklist items, not vibes.

  - [ ] ...
  - [ ] ...

---

— Rook
