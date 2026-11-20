# Contributing to yt-cli

Thank you for your interest in contributing to **yt-cli** (`ytdownloader` / `ytcli`)!

## Getting Started

1. **Fork** the repository on GitHub and clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/yt-cli.git
   cd yt-cli
   ```
2. **Create a virtual environment** (Python 3.11+ required) and install the package with optional and development dependencies:
   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate

   pip install -e ".[extra,dev]"
   ```
3. **Create a feature branch** off `main`:
   ```bash
   git checkout -b fix/short-description
   ```

## Coding & Testing Guidelines

- **Run tests before opening a PR:**
  ```bash
  pytest -q
  ```
- **Type hints & docstrings:** Keep new and modified functions type-hinted (`from __future__ import annotations`) and documented consistently with existing modules under `src/ytdownloader/`.
- **Keep PRs focused:** One logical change (bug fix, documentation update, or test addition) per pull request makes review faster and easier.
- **Discuss larger changes first:** If you plan to add a new dependency or a major feature from the roadmap, open an issue first to align on the design.

## Opening a Pull Request

1. Verify `git diff` only includes your intended changes.
2. Push your branch to your fork and open a Pull Request against `main`.
3. Include a brief summary of what changed, why, and how you tested it.
