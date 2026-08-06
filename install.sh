#!/usr/bin/env bash
# YouTube Downloader CLI - Linux/macOS installer.
# Creates a virtual environment, installs the package, and adds the
# `ytdownloader` / `ytcli` commands to your PATH via your shell profile.
#
# Usage: ./install.sh   (run from the repository root, or from anywhere)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$REPO_ROOT/.venv"
VENV_BIN="$VENV_DIR/bin"

step() { echo -e "\n==> $1"; }
ok()   { echo "    $1"; }
warn() { echo "    $1"; }

# 1. Locate a usable Python interpreter (3.11+)
step "Checking for Python 3.11+"
PYTHON_CMD=""
for candidate in python3.12 python3.11 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        version="$("$candidate" --version 2>&1 | awk '{print $2}')"
        major="$(echo "$version" | cut -d. -f1)"
        minor="$(echo "$version" | cut -d. -f2)"
        if [ "$major" -eq 3 ] && [ "$minor" -ge 11 ]; then
            PYTHON_CMD="$candidate"
            break
        fi
    fi
done
if [ -z "$PYTHON_CMD" ]; then
    echo "Python 3.11 or later was not found on PATH."
    echo "Install it via your package manager (e.g. 'brew install python@3.12' or 'sudo apt install python3.12') and re-run this script."
    exit 1
fi
ok "Using '$PYTHON_CMD'"

# 2. Create the virtual environment if it does not already exist
step "Setting up virtual environment"
if [ -x "$VENV_BIN/python" ]; then
    ok "Virtual environment already exists at $VENV_DIR"
else
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    ok "Created virtual environment at $VENV_DIR"
fi

# 3. Install the package in editable mode
step "Installing dependencies (this may take a minute)"
"$VENV_BIN/python" -m pip install --upgrade pip --quiet
"$VENV_BIN/python" -m pip install -e "$REPO_ROOT" --quiet
ok "Package installed"

# 4. Add the venv's bin directory to PATH via the shell profile
step "Adding ytdownloader to your PATH"
PROFILE_FILE="$HOME/.bashrc"
if [ -n "${ZSH_VERSION:-}" ] || [ "$(basename "${SHELL:-}")" = "zsh" ]; then
    PROFILE_FILE="$HOME/.zshrc"
fi

PATH_LINE="export PATH=\"$VENV_BIN:\$PATH\""
if [ -f "$PROFILE_FILE" ] && grep -qF "$VENV_BIN" "$PROFILE_FILE"; then
    ok "Already present in $PROFILE_FILE"
else
    {
        echo ""
        echo "# Added by ytdownloader install.sh"
        echo "$PATH_LINE"
    } >> "$PROFILE_FILE"
    ok "Added $VENV_BIN to PATH via $PROFILE_FILE"
    warn "Run 'source $PROFILE_FILE' or open a new terminal for this to take effect."
fi

# 5. Check for FFmpeg (required for MP4 merging and MP3 extraction)
step "Checking for FFmpeg"
if command -v ffmpeg >/dev/null 2>&1; then
    ok "FFmpeg found"
else
    warn "FFmpeg was not found on PATH."
    warn "macOS: brew install ffmpeg"
    warn "Debian/Ubuntu: sudo apt install ffmpeg"
    warn "The app will still install, but video/audio conversion will fail until FFmpeg is available."
fi

# 6. Check for VLC (required only for the "Watch in VLC" streaming feature)
step "Checking for VLC"
if command -v vlc >/dev/null 2>&1; then
    ok "VLC found"
else
    warn "VLC was not found."
    warn "macOS: brew install --cask vlc"
    warn "Debian/Ubuntu: sudo apt install vlc"
    warn "The app will still install, but the 'Watch in VLC' feature will fail until VLC is available."
fi

echo ""
echo "Setup complete."
echo "Run 'source $PROFILE_FILE' (or open a new terminal), then run 'ytdownloader' or 'ytcli' from any directory."
