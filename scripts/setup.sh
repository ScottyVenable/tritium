#!/usr/bin/env bash
# Tritium OS v4.1 -- setup.sh
# Idempotent bootstrapper for Tritium OS on Linux/macOS/Termux.
# Run: bash scripts/setup.sh [--dry-run] [--quiet]

set -euo pipefail

VERSION="4.1"
DRY=0; QUIET=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY=1 ;;
        --quiet)   QUIET=1 ;;
    esac
done

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
TRITIUM_HOME="${TRITIUM_HOME:-$HOME/.tritium-os}"
BIN_DIR="$TRITIUM_HOME/bin"
STATE_DIR="$TRITIUM_HOME/state"
KEYS_DIR="$TRITIUM_HOME/keys"
LEDGER_DIR="$TRITIUM_HOME/ledger"

_log() { [ "$QUIET" -eq 0 ] && printf '%s\n' "$1" || true; }
_run() { [ "$DRY" -eq 0 ] && "$@" || printf '  [dry] %s\n' "$*"; }

_log ""
_log "+--- Tritium OS v${VERSION} Setup ---"
_log "  Repo       : $REPO_ROOT"
_log "  Home       : $TRITIUM_HOME"
_log "  Bin dir    : $BIN_DIR"

# Stage 1: Directories
_log ""
_log "[1] Directories"
for d in "$BIN_DIR" "$STATE_DIR" "$KEYS_DIR" "$LEDGER_DIR"; do
    if [ ! -d "$d" ]; then
        _log "  mkdir $d"; _run mkdir -p "$d"
    else
        _log "  exists $d"
    fi
done

# Stage 2: System dependencies
_log ""
_log "[2] System dependencies"
if command -v pkg >/dev/null 2>&1; then
    _log "  Termux detected"
    _run pkg install -y python git openssh 2>/dev/null || true
elif command -v apt-get >/dev/null 2>&1; then
    _run apt-get install -y python3 python3-pip git 2>/dev/null || true
fi
if command -v pip3 >/dev/null 2>&1; then
    _run pip3 install --quiet cryptography 2>&1 | tail -1
elif command -v pip >/dev/null 2>&1; then
    _run pip install --quiet cryptography 2>&1 | tail -1
fi

# Stage 3: Python bridge dependencies
_log ""
_log "[3] Python bridge"
if [ -f "$REPO_ROOT/requirements.txt" ]; then
    _run pip3 install --quiet -r "$REPO_ROOT/requirements.txt" 2>&1 | tail -1
    _log "  requirements.txt installed"
else
    _log "  no requirements.txt found"
fi

# Stage 4: Core scripts (v4.0)
_log ""
_log "[4] Core scripts"
for name in install.sh install.ps1 new-agent.sh new-agent.ps1 package.sh package.ps1 verify.sh verify.ps1; do
    src="$HERE/$name"; dst="$BIN_DIR/$name"
    if [ -f "$src" ]; then
        _run cp "$src" "$dst"
        _log "  cp $name"
    fi
done

# Stage 5: v4.1 tools
_log ""
_log "[5] v4.1 tools"
V41_SCRIPTS="tritium-crypt tritium-open tritium-close tritium-cp tritium-doctor tier-auto tritium-id tritium-authorize"
for name in $V41_SCRIPTS; do
    src="$HERE/$name"; dst="$BIN_DIR/$name"
    if [ -f "$src" ]; then
        _run cp "$src" "$dst"
        _run chmod +x "$dst"
        _log "  installed $name"
    else
        _log "  [skip] $name not found"
    fi
done

# Stage 6: Vault & Registry init
_log ""
_log "[6] Vault + Registry"
[ -d "$REPO_ROOT/world_vault" ] || _run mkdir -p "$REPO_ROOT/world_vault"
[ -d "$REPO_ROOT/registry" ]    || _run mkdir -p "$REPO_ROOT/registry"
if [ -f "$HERE/tritium-crypt" ]; then
    _run python3 "$HERE/tritium-crypt" init
fi

# Stage 7: Ledger DB (inline Python to avoid heredoc quoting conflict)
_log ""
_log "[7] Ledger"
if command -v python3 >/dev/null 2>&1; then
    LEDGER_DB="$LEDGER_DIR/ledger.db"
    python3 "$REPO_ROOT/scripts/setup-ledger.py" "$LEDGER_DB"
fi

_log ""
_log "+--- Setup complete (v${VERSION}) ---"
_log "  Run: tritium-doctor   -- verify all components"
_log "  Run: tritium-cp       -- view system status"
_log "  Run: tier-auto status -- check active tier"
