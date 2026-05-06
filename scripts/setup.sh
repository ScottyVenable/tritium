#!/usr/bin/env bash
# scripts/setup.sh -- DEPRECATED.
# Kept as a thin wrapper for muscle memory and external docs.
# Use scripts/install.sh going forward.
echo "scripts/setup.sh is deprecated -- calling install.sh instead"
exec "$(dirname "$0")/install.sh" "$@"
