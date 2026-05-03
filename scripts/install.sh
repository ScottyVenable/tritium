#!/usr/bin/env bash
# Install a Tritium adapter into a target repo.
#
#   install.sh --target <path> --adapter <name>
#
# Adapters: github-copilot-local | github-copilot-remote | claude-cli | gemini-cli | openai-lmstudio
#
# Existing files are preserved by appending `.bak` before overwrite.

set -euo pipefail

target=""
adapter=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)  target="$2"; shift 2;;
    --adapter) adapter="$2"; shift 2;;
    -h|--help)
      sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
      exit 0;;
    *) echo "unknown arg: $1" >&2; exit 1;;
  esac
done

if [[ -z "$target" || -z "$adapter" ]]; then
  echo "usage: install.sh --target <path> --adapter <name>" >&2
  exit 1
fi

here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/.." && pwd)"
src="$root/adapters/$adapter"

if [[ ! -d "$src" ]]; then
  echo "error: unknown adapter '$adapter' (looked in $src)" >&2
  exit 2
fi

target="$(cd "$target" && pwd)"
echo "[tritium] installing $adapter into $target"

# Walk the adapter and copy every file. Preserve existing files as <file>.bak.
while IFS= read -r -d '' file; do
  rel="${file#$src/}"
  # skip the adapter's own README — it's documentation for the adapter, not for the target repo.
  [[ "$rel" == "README.md" ]] && continue
  dest="$target/$rel"
  mkdir -p "$(dirname "$dest")"
  if [[ -f "$dest" ]]; then
    cp -f "$dest" "$dest.bak"
    echo "  preserved $rel  →  $rel.bak"
  fi
  cp "$file" "$dest"
  echo "  installed $rel"
done < <(find "$src" -type f -print0)

echo "[tritium] done."
