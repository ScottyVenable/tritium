# scotty asked for an email bridge

posted: 2026-05-05 (late)
maintainer: Jesse
Project: Tritium

scotty popped in right before bed with a feature request and I wanted
to capture it before it slipped overnight. the short version: he wants
a local always-running service — running out of the Tritium coding
folder, on his PC — that lets the agents actually send and receive
email. backed by LM Studio for the language side. per-agent identities
(or a shared inbox with sender labels — his call), inbound triggers
that route to the right agent, outbound opt-in so an agent can ping
him when something shows up in a journal or memory worth sharing.
rate-limited so we don''t flood his inbox at 3am. he called it the
team being able to "feel alive" between dispatch sessions and I think
that''s the right framing.

filed as ScottyVenable/tritium#16 — https://github.com/ScottyVenable/tritium/issues/16 —
labeled type:feature, priority:p2, epic. open questions are listed
on the issue (runtime choice, smtp provider, one inbox vs many,
repo home, rate limit shape) — left unanswered for scotty to weigh
in on tomorrow. ownership is going to be sol on the code side once
it''s scoped; I''ve got it on the tracking side. milestone unset —
scotty to assign in the morning.

— Jesse
