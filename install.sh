#!/usr/bin/env bash
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │  Tritium OS — one-file installer                                           │
# │                                                                             │
# │  Usage (from repo root):                                                   │
# │    bash install.sh                                                          │
# │    bash install.sh --install-deps   # auto-install missing system deps      │
# │    bash install.sh --dry-run        # show actions without applying         │
# │    bash install.sh --force          # overwrite existing installations      │
# │    bash install.sh --quiet          # suppress non-essential output         │
# │                                                                             │
# │  Supports: Linux (apt/dnf/pacman), macOS (brew), Termux, Ubuntu/proot     │
# │            Windows users: run install.ps1 instead.                         │
# └─────────────────────────────────────────────────────────────────────────────┘

set -euo pipefail

# ─── Flags ──────────────────────────────────────────────────────────────────
DRY=0; QUIET=0; FORCE=0; INSTALL_DEPS=0

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)      DRY=1 ;;
    --quiet|-q)     QUIET=1 ;;
    --force)        FORCE=1 ;;
    --install-deps) INSTALL_DEPS=1 ;;
    -h|--help)
      sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//' | sed 's/[│┌└─]//g'
      exit 0
      ;;
    # Forward any extra flags to scripts/install.sh only.
    *) break ;;
  esac
  shift
done

# ─── Helpers ────────────────────────────────────────────────────────────────
BOLD=$'\033[1m'; RESET=$'\033[0m'; CYAN=$'\033[36m'; DIM=$'\033[2m'
_log()  { [ "$QUIET" -eq 0 ] && printf '%s\n' "$1" || true; }
_warn() { printf '\033[1;33m⚠\033[0m  %s\n' "$1" >&2; }
_ok()   { printf '\033[1;32m✔\033[0m  %s\n' "$1"; }
_err()  { printf '\033[1;31m✖\033[0m  %s\n' "$1" >&2; }
_run()  { if [ "$DRY" -eq 1 ]; then printf "  ${DIM}[dry] %s${RESET}\n" "$*"; else "$@"; fi; }
_h()    { [ "$QUIET" -eq 0 ] && printf '\n%s\n' "${BOLD}$1${RESET}" || true; }

# ─── Banner ─────────────────────────────────────────────────────────────────
if [ "$QUIET" -eq 0 ]; then
  printf '\033[1;36m'
  echo '  _____     _ _   _                 ___  ____'
  echo ' |_   _| __(_) |_(_)_   _ _ __ ___ / _ \/ ___|'
  echo '   | || '"'"'__| | __| | | | | '"'"'_ ` _ \ | | \___ \'
  echo '   | || |  | | |_| | |_| | | | | | | |_| |___) |'
  echo '   |_||_|  |_|\__|_|\__,_|_| |_| |_|\___/|____/'
  printf '\033[0m'
  echo '  Tritium OS — one-file installer'
  echo
fi

# ─── Paths ──────────────────────────────────────────────────────────────────
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$HERE"
SERVER_DIR="$REPO_ROOT/runtime/server"
CLI_SCRIPT="$REPO_ROOT/runtime/cli/tritium.js"
TRITIUM_HOME="${TRITIUM_HOME:-$HOME/.tritium-os}"

# ─── Platform detection ─────────────────────────────────────────────────────
PLATFORM="unknown"
PKG_INSTALLER=""
IS_TERMUX=0
IS_PROOT_UBUNTU=0

# Termux: $PREFIX is set and /data/data/com.termux exists (or $PREFIX contains it)
if [ -n "${PREFIX:-}" ] && echo "${PREFIX:-}" | grep -q "com.termux"; then
  PLATFORM="Termux"
  PKG_INSTALLER="pkg"
  IS_TERMUX=1
elif command -v pkg >/dev/null 2>&1 && [ -d "/data/data/com.termux" ]; then
  PLATFORM="Termux"
  PKG_INSTALLER="pkg"
  IS_TERMUX=1
else
  case "$(uname -s 2>/dev/null)" in
    Linux*)
      PLATFORM="Linux"
      # Detect Ubuntu/Debian proot under Termux
      if [ -f /etc/os-release ] && grep -qi ubuntu /etc/os-release 2>/dev/null; then
        # Check if we're inside a proot (heuristic: /proc/1/cmdline contains proot or we lack /dev/pts)
        if [ -f /proc/1/cmdline ] && cat /proc/1/cmdline 2>/dev/null | tr '\0' ' ' | grep -qi proot; then
          IS_PROOT_UBUNTU=1
          _log "  Detected: Ubuntu proot (under Termux)"
        fi
      fi
      if command -v apt-get >/dev/null 2>&1; then
        PKG_INSTALLER="apt"
      elif command -v dnf >/dev/null 2>&1; then
        PKG_INSTALLER="dnf"
      elif command -v pacman >/dev/null 2>&1; then
        PKG_INSTALLER="pacman"
      fi
      ;;
    Darwin*)
      PLATFORM="macOS"
      PKG_INSTALLER="brew"
      ;;
  esac
fi

_log "  Platform    : $PLATFORM"
_log "  Repo root   : $REPO_ROOT"
_log "  Tritium home: $TRITIUM_HOME"
[ "$DRY" -eq 1 ] && _log "  Mode        : DRY-RUN"
_log ""

# ─── Step 1: System requirements ────────────────────────────────────────────
_h "[1/4] Checking system requirements"

check_node() {
  if ! command -v node >/dev/null 2>&1; then return 1; fi
  local ver; ver="$(node --version 2>/dev/null | sed 's/^v//')"
  local major; major="$(printf '%s' "$ver" | awk -F. '{print $1+0}')"
  [ "$major" -ge 20 ]
}

NODE_OK=0; NPM_OK=0; GIT_OK=0
check_node && NODE_OK=1
command -v npm  >/dev/null 2>&1 && NPM_OK=1
command -v git  >/dev/null 2>&1 && GIT_OK=1

# ── Auto-install missing deps ───────────────────────────────────────────────
if [ "$INSTALL_DEPS" -eq 1 ] && [ -n "$PKG_INSTALLER" ]; then
  _log "  --install-deps requested (pkg manager: $PKG_INSTALLER)"

  case "$PKG_INSTALLER" in
    apt)
      if [ "$NODE_OK" -eq 0 ]; then
        _log "  Installing Node 20 via NodeSource…"
        if _run bash -c "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -" 2>/dev/null; then
          _run apt-get install -y nodejs || true
        else
          _run apt-get install -y nodejs npm || true
        fi
        check_node && NODE_OK=1
      fi
      # Build tools for better-sqlite3 (required on Ubuntu/Debian/proot)
      _log "  Ensuring build-essential + python3 (needed for better-sqlite3)…"
      _run apt-get install -y build-essential python3 python3-pip libsqlite3-dev 2>/dev/null || true
      [ "$GIT_OK" -eq 0 ] && { _run apt-get install -y git || true; command -v git >/dev/null 2>&1 && GIT_OK=1; }
      ;;
    dnf)
      if [ "$NODE_OK" -eq 0 ]; then
        _run dnf module enable nodejs:20 -y 2>/dev/null || true
        _run dnf install -y nodejs npm || true
        check_node && NODE_OK=1
      fi
      _run dnf install -y gcc-c++ make python3 sqlite-devel 2>/dev/null || true
      [ "$GIT_OK" -eq 0 ] && { _run dnf install -y git || true; command -v git >/dev/null 2>&1 && GIT_OK=1; }
      ;;
    pacman)
      if [ "$NODE_OK" -eq 0 ]; then
        _run pacman -S --noconfirm nodejs npm || true
        check_node && NODE_OK=1
      fi
      _run pacman -S --noconfirm base-devel python sqlite || true
      [ "$GIT_OK" -eq 0 ] && { _run pacman -S --noconfirm git || true; command -v git >/dev/null 2>&1 && GIT_OK=1; }
      ;;
    brew)
      if [ "$NODE_OK" -eq 0 ]; then
        _run brew install node@20 2>/dev/null || _run brew install node || true
        check_node && NODE_OK=1
      fi
      [ "$GIT_OK" -eq 0 ] && { _run brew install git || true; command -v git >/dev/null 2>&1 && GIT_OK=1; }
      ;;
    pkg)
      if [ "$NODE_OK" -eq 0 ]; then
        _run pkg install -y nodejs-lts 2>/dev/null || _run pkg install -y nodejs || true
        check_node && NODE_OK=1
      fi
      # Termux build tools for better-sqlite3
      _run pkg install -y clang make python python-pip 2>/dev/null || true
      [ "$GIT_OK" -eq 0 ] && { _run pkg install -y git || true; command -v git >/dev/null 2>&1 && GIT_OK=1; }
      ;;
  esac
fi

# ── Report requirements status ──────────────────────────────────────────────
REQUIREMENTS_MET=1
if [ "$NODE_OK" -eq 1 ]; then
  _ok "Node.js $(node --version 2>/dev/null)"
else
  _err "Node.js 20+ not found"
  REQUIREMENTS_MET=0
fi
if [ "$NPM_OK" -eq 1 ]; then
  _ok "npm $(npm --version 2>/dev/null)"
else
  _err "npm not found (usually ships with Node)"
  REQUIREMENTS_MET=0
fi
if [ "$GIT_OK" -eq 1 ]; then
  _ok "git $(git --version 2>/dev/null | awk '{print $3}')"
else
  _warn "git not found (needed for auto-update)"
fi

if [ "$REQUIREMENTS_MET" -eq 0 ]; then
  echo
  _err "Missing required dependencies. Re-run with --install-deps to auto-install:"
  echo "  bash install.sh --install-deps"
  exit 1
fi

# ─── Step 2: npm install (runtime/server) ───────────────────────────────────
_log ""
_h "[2/4] Installing Node dependencies (runtime/server)"

# Ensure build tools exist on the platform before npm install
# This handles the Termux-Ubuntu proot case where better-sqlite3 fails to
# compile because build-essential / python3 / libsqlite3-dev are absent.
_ensure_build_tools() {
  local missing=""
  command -v python3 >/dev/null 2>&1 || missing="python3 $missing"
  command -v make    >/dev/null 2>&1 || missing="make $missing"
  # gcc OR clang
  { command -v gcc >/dev/null 2>&1 || command -v clang >/dev/null 2>&1; } || missing="gcc $missing"

  if [ -n "$missing" ]; then
    _warn "Build tools missing ($missing) — better-sqlite3 may fail to compile."
    _warn "Re-run with --install-deps to auto-install them."
  fi
}

if [ "$DRY" -eq 0 ]; then
  _ensure_build_tools

  cd "$SERVER_DIR"

  # Attempt 1: plain npm install
  if npm install --loglevel warn 2>&1; then
    _ok "npm install succeeded"
  else
    # Attempt 2: force build from source (works around missing prebuilds)
    _warn "Standard install failed. Retrying with --build-from-source…"
    if npm install --build-from-source --loglevel warn 2>&1; then
      _ok "npm install --build-from-source succeeded"
    else
      # Attempt 3: skip native binaries entirely (fallback — runtime will warn if SQLite unavailable)
      _warn "Build-from-source also failed. Attempting with --ignore-scripts…"
      if npm install --ignore-scripts --loglevel warn 2>&1; then
        _warn "Installed with --ignore-scripts. Native modules may not work."
        _warn "On Ubuntu/proot: sudo apt install build-essential python3 libsqlite3-dev then re-run."
        _warn "On Termux: pkg install clang make python then re-run."
      else
        _err "npm install failed. See above for details."
        _err "Common fixes:"
        _err "  Ubuntu / proot-Ubuntu : apt install build-essential python3 libsqlite3-dev"
        _err "  Termux (native)       : pkg install clang make python"
        _err "  Any platform          : bash install.sh --install-deps"
        exit 1
      fi
    fi
  fi

  cd "$REPO_ROOT"
else
  _log "  [dry] npm install in $SERVER_DIR"
fi

# ─── Step 3: Run scripts/install.sh for full setup ──────────────────────────
_log ""
_h "[3/4] Running full setup (scripts/install.sh)"

FULL_INSTALL_ARGS=()
[ "$DRY"          -eq 1 ] && FULL_INSTALL_ARGS+=("--dry-run")
[ "$QUIET"        -eq 1 ] && FULL_INSTALL_ARGS+=("--quiet")
[ "$FORCE"        -eq 1 ] && FULL_INSTALL_ARGS+=("--force")
[ "$INSTALL_DEPS" -eq 1 ] && FULL_INSTALL_ARGS+=("--install-deps")

if _run bash "$REPO_ROOT/scripts/install.sh" "${FULL_INSTALL_ARGS[@]}" "$@"; then
  true
else
  _warn "scripts/install.sh exited non-zero — continuing anyway"
fi

# ─── Step 4: Install the `tritium-os` command ────────────────────────────────
_log ""
_h "[4/4] Installing the ${CYAN}tritium-os${RESET}${BOLD} command"

WRAPPER_CONTENT="#!/usr/bin/env bash
# tritium-os — Tritium OS CLI wrapper (auto-generated by install.sh)
exec node \"$CLI_SCRIPT\" \"\$@\"
"

# Determine install directory (in order of preference)
_find_bin_dir() {
  if [ "$IS_TERMUX" -eq 1 ] && [ -d "${PREFIX:-}/bin" ]; then
    echo "${PREFIX}/bin"
  elif [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    echo "/usr/local/bin"
  elif [ -d "$HOME/.local/bin" ]; then
    echo "$HOME/.local/bin"
  else
    mkdir -p "$HOME/.local/bin"
    echo "$HOME/.local/bin"
  fi
}

BIN_DIR="$(_find_bin_dir)"
WRAPPER_PATH="$BIN_DIR/tritium-os"

if [ "$DRY" -eq 1 ]; then
  _log "  [dry] would write $WRAPPER_PATH"
else
  if [ -f "$WRAPPER_PATH" ] && [ "$FORCE" -eq 0 ]; then
    # Only overwrite if content differs
    existing_ref="$(grep 'exec node' "$WRAPPER_PATH" 2>/dev/null | grep -o '"[^"]*"' | head -1 || true)"
    new_ref="\"$CLI_SCRIPT\""
    if [ "$existing_ref" = "$new_ref" ]; then
      _ok "tritium-os already installed at $WRAPPER_PATH (unchanged)"
    else
      cp "$WRAPPER_PATH" "$WRAPPER_PATH.bak" 2>/dev/null || true
      printf '%s' "$WRAPPER_CONTENT" > "$WRAPPER_PATH"
      chmod +x "$WRAPPER_PATH"
      _ok "Updated: $WRAPPER_PATH"
    fi
  else
    printf '%s' "$WRAPPER_CONTENT" > "$WRAPPER_PATH"
    chmod +x "$WRAPPER_PATH"
    _ok "Installed: $WRAPPER_PATH"
  fi

  # Check if the bin dir is in PATH
  case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *)
      _warn "$BIN_DIR is not in your PATH."
      echo
      echo "  Add it to your shell profile (e.g. ~/.bashrc, ~/.zshrc):"
      printf '    \033[1mexport PATH="%s:$PATH"\033[0m\n' "$BIN_DIR"
      echo "  Then reload: source ~/.bashrc  (or open a new terminal)"
      echo
      ;;
  esac
fi

# ─── Summary ────────────────────────────────────────────────────────────────
if [ "$QUIET" -eq 0 ]; then
  echo
  echo "┌────────────────────────────────────────────────┐"
  printf "│  \033[1;32mTritium OS installation complete!\033[0m"
  printf "                │\n"
  echo "│                                                │"
  printf "│  Start the runtime:  \033[36mtritium-os serve\033[0m          │\n"
  printf "│  Check health:       \033[36mtritium-os status\033[0m         │\n"
  printf "│  Open dashboard:     \033[36mtritium-os open\033[0m           │\n"
  printf "│  Update:             \033[36mtritium-os update\033[0m         │\n"
  printf "│  Help:               \033[36mtritium-os --help\033[0m         │\n"
  echo "└────────────────────────────────────────────────┘"
  echo
fi
