#!/usr/bin/env bash
# CodeWalker — one-command installer
#
# Usage (run from any directory — it works on any repo):
#   curl -fsSL https://raw.githubusercontent.com/xdun1698/codewalker-cursor/main/scripts/install.sh | bash
#
# Or, if you already have the repo cloned:
#   bash ~/Codewalker/scripts/install.sh
#
# Options (environment variables):
#   CW_REPO_DIR   Path to an existing clone (skips clone/pull). Default: ~/Codewalker
#   CW_SKIP_BUILD Set to 1 to skip npm compile + vsce package (use pre-built .vsix if present)
#   CW_MODE       "vsix"   — installs the .vsix into Cursor (default)
#                 "link"   — symlinks repo into ~/.cursor/plugins/local/ instead
#                 "both"   — does both
#   CW_GAMEPLAN   Set to 1 to initialize .codewalker-gameplan.json in $PWD
#
# The script does NOT require root and does NOT write outside ~/Codewalker and ~/.cursor/.

set -euo pipefail

# ─── colour helpers ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}[codewalker]${NC} $*"; }
success() { echo -e "${GREEN}[codewalker]${NC} $*"; }
warn()    { echo -e "${YELLOW}[codewalker]${NC} $*"; }
die()     { echo -e "${RED}[codewalker] ERROR:${NC} $*" >&2; exit 1; }

# ─── config ──────────────────────────────────────────────────────────────────
CW_REPO_DIR="${CW_REPO_DIR:-$HOME/Codewalker}"
CW_SKIP_BUILD="${CW_SKIP_BUILD:-0}"
CW_MODE="${CW_MODE:-vsix}"
CW_GAMEPLAN="${CW_GAMEPLAN:-0}"
CW_REMOTE="${CW_REMOTE:-https://github.com/xdun1698/codewalker-cursor.git}"
TARGET_DIR="${PWD}"

# ─── prereq checks ───────────────────────────────────────────────────────────
info "Checking prerequisites…"

need() {
  command -v "$1" &>/dev/null || die "'$1' not found. $2"
}

need git  "Install git: https://git-scm.com/downloads"
need node "Install Node.js >= 18: https://nodejs.org"
need npm  "npm is bundled with Node.js"

PYTHON_BIN=""
for py in python3 python3.12 python3.11 python; do
  if command -v "$py" &>/dev/null && "$py" --version 2>&1 | grep -qE '^Python 3\.'; then
    PYTHON_BIN="$py"
    break
  fi
done
[[ -z "$PYTHON_BIN" ]] && warn "Python 3 not found — skill scripts will fall back to HTTP mode."

# ─── cursor cli detection ─────────────────────────────────────────────────────
CURSOR_BIN=""
for bin in cursor "cursor-nightly" "/Applications/Cursor.app/Contents/MacOS/Cursor"; do
  if command -v "$bin" &>/dev/null 2>&1; then
    CURSOR_BIN="$bin"
    break
  fi
done
[[ -z "$CURSOR_BIN" ]] && warn "cursor CLI not found — will print manual VSIX install instructions."

# ─── clone / update repo ─────────────────────────────────────────────────────
info "Resolving CodeWalker source at: $CW_REPO_DIR"
if [[ -d "$CW_REPO_DIR/.git" ]]; then
  info "Repo found — pulling latest…"
  git -C "$CW_REPO_DIR" pull --ff-only --quiet || warn "git pull failed (local changes?); continuing with current state."
else
  info "Cloning CodeWalker into $CW_REPO_DIR …"
  git clone --depth 1 "$CW_REMOTE" "$CW_REPO_DIR"
fi

# ─── build ───────────────────────────────────────────────────────────────────
if [[ "$CW_SKIP_BUILD" == "1" ]]; then
  info "Skipping build (CW_SKIP_BUILD=1)."
else
  info "Installing npm dependencies…"
  npm --prefix "$CW_REPO_DIR" install --silent

  info "Compiling TypeScript…"
  npm --prefix "$CW_REPO_DIR" run compile

  # vsce may or may not be globally installed; prefer local devDependency
  VSCE_BIN="$(npm --prefix "$CW_REPO_DIR" bin)/vsce"
  if [[ ! -x "$VSCE_BIN" ]]; then
    need npx "npx is bundled with npm >= 5"
    VSCE_BIN="npx --prefix $CW_REPO_DIR @vscode/vsce"
  fi

  info "Packaging VSIX…"
  # --no-dependencies: skip marketplace git check for local builds
  (cd "$CW_REPO_DIR" && eval "$VSCE_BIN" package --no-dependencies --out codewalker-latest.vsix) \
    || die "vsce package failed. Run 'npm run compile' in $CW_REPO_DIR to diagnose."
fi

# Locate the most-recently-built VSIX
VSIX_PATH="$(ls -t "$CW_REPO_DIR"/codewalker*.vsix 2>/dev/null | head -1)"

# ─── install mode: vsix ──────────────────────────────────────────────────────
install_vsix() {
  if [[ -z "$VSIX_PATH" ]]; then
    warn "No .vsix file found in $CW_REPO_DIR — skipping VSIX install."
    return
  fi

  if [[ -n "$CURSOR_BIN" ]]; then
    info "Installing VSIX via cursor CLI: $VSIX_PATH"
    "$CURSOR_BIN" --install-extension "$VSIX_PATH" && success "Extension installed in Cursor." || {
      warn "cursor CLI install failed. Manual steps below."
      _manual_vsix_instructions
    }
  else
    _manual_vsix_instructions
  fi
}

_manual_vsix_instructions() {
  echo ""
  echo -e "${YELLOW}  Manual VSIX install:${NC}"
  echo "  1. Open Cursor"
  echo "  2. Press Cmd+Shift+P → 'Extensions: Install from VSIX…'"
  echo "  3. Select: $VSIX_PATH"
  echo ""
}

# ─── install mode: link (Cursor local plugin) ─────────────────────────────────
install_link() {
  local plugins_dir="$HOME/.cursor/plugins/local"
  local link_target="$plugins_dir/codewalker"
  mkdir -p "$plugins_dir"

  if [[ -L "$link_target" ]]; then
    info "Symlink already exists at $link_target — updating target."
    rm "$link_target"
  elif [[ -e "$link_target" ]]; then
    warn "$link_target exists but is not a symlink. Remove it manually, then re-run."
    return
  fi

  ln -s "$CW_REPO_DIR" "$link_target"
  success "Symlinked $CW_REPO_DIR → $link_target"
  info "Reload Cursor (Cmd+Shift+P → Developer: Reload Window) to pick up the plugin."
}

# ─── run install mode ────────────────────────────────────────────────────────
case "$CW_MODE" in
  vsix)        install_vsix ;;
  link)        install_link ;;
  both)        install_vsix; install_link ;;
  *)           die "Unknown CW_MODE='$CW_MODE'. Use vsix, link, or both." ;;
esac

# ─── optional: init .codewalker-gameplan.json in target repo ─────────────────
if [[ "$CW_GAMEPLAN" == "1" && "$TARGET_DIR" != "$CW_REPO_DIR" ]]; then
  GAMEPLAN_FILE="$TARGET_DIR/.codewalker-gameplan.json"
  if [[ -f "$GAMEPLAN_FILE" ]]; then
    info ".codewalker-gameplan.json already exists — skipping."
  else
    info "Initializing .codewalker-gameplan.json in $TARGET_DIR …"
    REPO_NAME="$(basename "$TARGET_DIR")"
    cat > "$GAMEPLAN_FILE" <<JSON
{
  "project": "$REPO_NAME",
  "goals": [],
  "context": "CodeWalker analysis target. Run 'CodeWalker: Run Full Analysis' in Cursor to populate token waste, security, and repo map tabs.",
  "generatedBy": "CodeWalker install.sh",
  "version": "1"
}
JSON
    success "Created $GAMEPLAN_FILE"
    warn "Add .codewalker-gameplan.json to .gitignore if you don't want to commit it."
  fi
fi

# ─── done ────────────────────────────────────────────────────────────────────
echo ""
success "CodeWalker install complete!"
echo ""
echo "  What CodeWalker does on ANY repo:"
echo "  • Token Waste  — BPE-accurate token cost per file; shows which files drain your AI context budget"
echo "  • Security     — OWASP Top 10 + secrets scanner with heatmap overlay"
echo "  • Repo Map     — Interactive dependency graph + git timeline"
echo "  • Game Plan    — AI-powered goal tracker, persisted in .codewalker-gameplan.json"
echo ""
echo "  Quick start:"
echo "  1. Open any repo in Cursor"
echo "  2. Click the CodeWalker icon in the activity bar (or Cmd+Shift+K)"
echo "  3. Run 'CodeWalker: Run Full Analysis' from the command palette"
echo ""
if [[ -n "$PYTHON_BIN" ]]; then
  echo "  Python detected ($PYTHON_BIN) — skills run locally (no server needed)."
else
  echo "  No Python 3 detected — skills will use HTTP fallback (requires Insight server)."
fi
echo ""
echo "  Docs: https://github.com/xdun1698/codewalker-cursor"
echo "  Support: support@nxgentechsolutions.com"
