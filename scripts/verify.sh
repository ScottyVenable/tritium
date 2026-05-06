#!/usr/bin/env bash
# Smoke-test the Tritium runtime.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/.." && pwd)"

cd "$root/core/runtime/server"
if [[ ! -d node_modules ]]; then
  echo "[tritium] installing runtime deps…"
  npm install --no-audit --no-fund
fi
node src/verify.js
