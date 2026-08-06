#!/usr/bin/env bash
# YouTube Downloader CLI - Linux/macOS uninstaller.
# Removes the virtual environment and the PATH entry added by install.sh.
# Optionally removes persistent app data (settings, history, logs).
#
# Usage: ./uninstall.sh   (run from the repository root, or from anywhere)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$REPO_ROOT/.venv"
VENV_BIN="$VENV_DIR/bin"
APP_DATA_DIR="$HOME/.ytdownloader"

step() { echo -e "\n==> $1"; }
ok()   { echo "    $1"; }
warn() { echo "    $1"; }

# 1. Remove the PATH entry from shell profile files
step "Removing ytdownloader from your PATH"
REMOVED_ANY=0
for PROFILE_FILE in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$PROFILE_FILE" ] && grep -qF "$VENV_BIN" "$PROFILE_FILE"; then
        # Remove the marker comment line and the export line that follows it.
        TMP_FILE="$(mktemp)"
        awk -v marker="# Added by ytdownloader install.sh" -v venvbin="$VENV_BIN" '
            $0 == marker { skip_next=1; next }
            skip_next && index($0, venvbin) { skip_next=0; next }
            { print }
        ' "$PROFILE_FILE" > "$TMP_FILE"
        mv "$TMP_FILE" "$PROFILE_FILE"
        ok "Removed PATH entry from $PROFILE_FILE"
        REMOVED_ANY=1
    fi
done
if [ "$REMOVED_ANY" -eq 0 ]; then
    ok "No PATH entries found to remove"
fi

# 2. Remove the virtual environment
step "Removing virtual environment"
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    ok "Removed $VENV_DIR"
else
    ok "No virtual environment found at $VENV_DIR"
fi

# 3. Optionally remove persistent app data (settings, history, logs, archive)
step "Application data"
if [ -d "$APP_DATA_DIR" ]; then
    warn "Found application data at $APP_DATA_DIR (settings, history, logs, download archive)."
    read -r -p "    Delete this data too? [y/N] " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -rf "$APP_DATA_DIR"
        ok "Removed $APP_DATA_DIR"
    else
        ok "Kept $APP_DATA_DIR"
    fi
else
    ok "No application data found at $APP_DATA_DIR"
fi

echo ""
echo "Uninstall complete."
echo "The cloned repository folder itself was not deleted; remove it manually if you no longer need the source code:"
echo "  $REPO_ROOT"
echo "Open a new terminal window (or re-source your shell profile) for the PATH change to take effect."
