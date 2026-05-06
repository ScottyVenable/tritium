#!/usr/bin/env bash
# Build the Tritium pre-release zip + SHA-256 checksum.
#
# Output: dist/tritium-v<VERSION>.zip and dist/tritium-v<VERSION>.zip.sha256

set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/.." && pwd)"
cd "$root"

VERSION="$(grep -oE '"version"\s*:\s*"[^"]+"' runtime/server/package.json | head -1 | sed 's/.*"version"\s*:\s*"//;s/"$//')"
[[ -z "$VERSION" ]] && VERSION="0.1.0"

dist="$root/dist"
mkdir -p "$dist"
out="$dist/tritium-v${VERSION}.zip"
rm -f "$out" "$out.sha256"

# Exclude: dist/, node_modules/, .tritium*/ runtime caches, *.bak.
( cd "$root/.." && zip -r "$out" "$(basename "$root")" \
    -x "$(basename "$root")/dist/*" \
    -x "$(basename "$root")/node_modules/*" \
    -x "$(basename "$root")/*/node_modules/*" \
    -x "$(basename "$root")/*/*/node_modules/*" \
    -x "$(basename "$root")/.tritium*/*" \
    -x "$(basename "$root")/**/.tritium*/*" \
    -x "$(basename "$root")/**/*.bak" \
    >/dev/null )

if command -v sha256sum >/dev/null; then
  ( cd "$dist" && sha256sum "$(basename "$out")" > "$(basename "$out").sha256" )
elif command -v shasum >/dev/null; then
  ( cd "$dist" && shasum -a 256 "$(basename "$out")" > "$(basename "$out").sha256" )
else
  echo "warning: no sha256sum/shasum found; skipping checksum" >&2
fi

ls -lh "$out" "$out.sha256" 2>/dev/null || ls -lh "$out"
