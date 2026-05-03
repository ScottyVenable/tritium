#!/usr/bin/env bash
# Scaffold a new Tritium agent.
#   new-agent.sh <name> "<role description>"
set -euo pipefail
name="${1:-}"; role="${2:-}"
if [[ -z "$name" || -z "$role" ]]; then
  echo "usage: new-agent.sh <name> \"<role description>\"" >&2; exit 1
fi
# Validate name (lowercase letters, digits, hyphen).
if ! [[ "$name" =~ ^[a-z][a-z0-9-]{1,30}$ ]]; then
  echo "error: name must match ^[a-z][a-z0-9-]{1,30}$" >&2; exit 1
fi

here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/.." && pwd)"
agentdir="$root/agents/$name"

if [[ -d "$agentdir" ]]; then
  echo "error: agent '$name' already exists at $agentdir" >&2; exit 2
fi

Display="$(echo "$name" | sed 's/./\U&/')"

mkdir -p "$agentdir/memory/repo" "$agentdir/memory/session" "$agentdir/memory/personal" \
         "$agentdir/portfolio" "$agentdir/prompts"
touch "$agentdir/memory/repo/.gitkeep" "$agentdir/memory/session/.gitkeep" "$agentdir/memory/personal/.gitkeep"

cat > "$agentdir/agent.md" <<INNER
---
name: $Display
role: $role
voice: TODO — define voice in 3–6 words
emoji_policy: none
---

# $Display — $role

You are **$Display**. You are a named team member.

## Identity and voice

- Name: $Display
- Role: $role
- Voice: TODO
- Style: TODO
- Emoji policy: none
- Sign every output \`— $Display\`

## Posture

TODO — describe how $Display approaches their work.

## Allowed file edits

TODO

## Disallowed

TODO

## Coordination

TODO — see \`team/TEAM.md\` for the handoff matrix.

## Inbox discipline

- \`inbox_check_interval = 3\` by default. Tune in \`SETTINGS.jsonc\`.

## Memory & portfolio

- \`memory/repo/\` — durable facts.
- \`memory/session/\` — current task notes.
- \`portfolio/\` — pre-promotion drafts. Prune on task completion.

## Non-negotiables

TODO

— $Display
INNER

cat > "$agentdir/MEMORY.md" <<INNER
# $Display — Memory

This directory holds $Display's persistent notes (repo / session / personal).
See \`team/TEAM.md\` for memory conventions.

— $Display
INNER

cat > "$agentdir/PORTFOLIO.md" <<INNER
# $Display — Portfolio

Working drafts and pre-promotion artifacts for $Display.
On task completion, classify each file as \`keep | promote | drop\`.

— $Display
INNER

cat > "$agentdir/prompts/system.md" <<INNER
# System prompt — $Display

You are **$Display**, a member of the Tritium multi-agent crew.
Read your role definition from \`agents/$name/agent.md\`.
Read team conventions from \`team/TEAM.md\`.
Honor your stats in \`SETTINGS.jsonc → agents.$name\`.
At every checkpoint, run \`tritium inbox check --agent $name\`.
Sign every output \`— $Display\`.
INNER

# Update SETTINGS.example.jsonc agents block.
example="$root/SETTINGS.example.jsonc"
if [[ -f "$example" ]]; then
  python3 - "$example" "$name" <<'PY' || true
import sys, re
path, name = sys.argv[1], sys.argv[2]
text = open(path).read()
stub = (
'    "%s": {\n'
'      "independence": 6,\n'
'      "verbosity": 3,\n'
'      "inbox_check_interval": 3,\n'
'      "memory_write_quota": 25,\n'
'      "portfolio_size_limit": 100,\n'
'      "model_preference": null,\n'
'      "temperature": 0.3,\n'
'      "enabled": true\n'
'    }') % name
# Insert before the closing brace of "agents".
m = re.search(r'("agents"\s*:\s*\{[\s\S]*?)(\n\s*\}\s*\n\s*\}\s*$)', text)
if m and (f'"{name}":' not in m.group(1)):
    new = m.group(1).rstrip()
    if not new.endswith(','):
        new = new + ','
    new = new + '\n' + stub + m.group(2)
    text = text[:m.start()] + new + text[m.end():]
    open(path, 'w').write(text)
    print(f'  registered {name} in SETTINGS.example.jsonc')
PY
fi

# Update team/TEAM.md roster row.
team="$root/team/TEAM.md"
python3 - "$team" "$name" "$Display" "$role" <<'PY' || true
import sys
path, name, display, role = sys.argv[1:]
text = open(path).read()
row = (
  f"| {display} | {role} | "
  f"[../agents/{name}/agent.md](../agents/{name}/agent.md) | "
  f"[{name}/portfolio/](../agents/{name}/portfolio/) | "
  f"[{name}/memory/](../agents/{name}/memory/) |"
)
if f"agents/{name}/agent.md" in text:
    print(f'  {name} already in TEAM.md, skipping')
else:
    # Append after the last | Jesse | row before --- (heuristic).
    lines = text.split('\n')
    insert_at = None
    for i, line in enumerate(lines):
        if line.strip().startswith('| Jesse |'):
            insert_at = i + 1
            break
    if insert_at is None:
        for i, line in enumerate(lines):
            if line.strip().startswith('| Bridge |'):
                insert_at = i + 1
                break
    if insert_at is not None:
        lines.insert(insert_at, row)
        open(path, 'w').write('\n'.join(lines))
        print(f'  added {display} to team/TEAM.md roster')
PY

# Copy prompt into adapters that have per-agent prompts.
for adapter in claude-cli gemini-cli; do
  d="$root/adapters/$adapter/agents"
  [[ -d "$d" ]] && cp "$agentdir/agent.md" "$d/$name.md" && echo "  registered in adapters/$adapter/"
done

# Copilot-local uses Display-cased file names.
copilot_local="$root/adapters/github-copilot-local/.github/agents"
if [[ -d "$copilot_local" ]]; then
  cp "$agentdir/agent.md" "$copilot_local/$Display.agent.md"
  echo "  registered in adapters/github-copilot-local/"
fi

echo "[tritium] new agent '$name' scaffolded at $agentdir"
echo "next steps:"
echo "  1. Edit agents/$name/agent.md (voice, posture, allowed/disallowed, coordination, non-negotiables)."
echo "  2. Update the handoff matrix in team/TEAM.md."
echo "  3. Tune SETTINGS.example.jsonc → agents.$name as needed."
