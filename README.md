# yt-cli

**A friendly terminal app for downloading YouTube videos, playlists, and audio — no flags to memorize.**

Videos · Playlists · MP3 audio · Subtitles · Thumbnails · VLC streaming · Batch downloads

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-97CA00?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Windows%20%7C%20Linux%20%7C%20macOS-informational?style=flat-square)](#requirements)
[![No telemetry](https://img.shields.io/badge/telemetry-none-brightgreen?style=flat-square)](#privacy)

## What is this?

`yt-cli` (installed as `ytdownloader` / `ytcli`) is **one command that
wraps yt-dlp behind plain-English menus**. yt-dlp is the engine that does
the actual downloading — powerful, but its interface is dozens of flags
and format selectors that assume you already know the tool. yt-cli hides
that complexity: you pick a number, answer simple questions (resolution?
bitrate? which playlist range?), and it hands your choices to yt-dlp
internally, using FFmpeg to merge video/audio or extract MP3 when needed.

From the menu you can download a single video (with a details preview —
title, channel, duration, formats, file size — before you commit), whole
playlists with filters (skip Shorts, filter by duration, keywords, upload
date), audio-only MP3s at your chosen bitrate, subtitles or thumbnails on
their own, batch downloads from text/CSV/JSON files, search YouTube
without opening a browser, stream straight into VLC without downloading
anything, and review a persistent download history.

**Who is it for?** Anyone who downloads videos or audio regularly and
wants it simple: students saving lectures, people archiving playlists, or
anyone who prefers a terminal over ad-filled websites.

**Who is it NOT for?** Anyone looking to rip copyrighted content they
have no rights to — you are responsible for what you download (see
[Legal](#legal)). Nothing here bypasses YouTube's own protections; it
just makes lawful downloading pleasant.

## How it works (the mental model)

1. You run `ytdownloader` from any terminal — a menu appears.
2. You pick a number for what you want (video, playlist, audio,
   subtitles, batch, search, watch, history, settings).
3. The tool asks plain-English questions and shows a preview before
   anything downloads — nothing happens without your confirmation.
4. Results land in your chosen output folder and are recorded in a local
   history file, so re-running a playlist never re-downloads what you
   already have (duplicates are skipped by design).

Power users get a second gear: **every core action is also a direct
command** for scripting (`download`, `batch`, `search`, `watch`,
`history`), and the Settings menu exposes the advanced knobs (cookies,
proxy, rate limiting, filename templates) without memorizing flags.

## Requirements

- **Python 3.11+**
- **FFmpeg** on your `PATH` — merges video/audio, extracts MP3, embeds
  thumbnails/subtitles. The app refuses to start a job that needs it and
  tells you exactly what's missing instead of crashing.
- **VLC** — only for the "Watch in VLC" streaming feature. Everything
  else works without it.

| FFmpeg | Command |
|---|---|
| Windows | `winget install Gyan.FFmpeg` |
| macOS | `brew install ffmpeg` |
| Linux (Debian/Ubuntu) | `sudo apt install ffmpeg` |

| VLC (optional) | Command |
|---|---|
| Windows | `winget install VideoLAN.VLC` |
| macOS | `brew install --cask vlc` |
| Linux (Debian/Ubuntu) | `sudo apt install vlc` |

Confirm with `ffmpeg -version`. Works on **Windows, Linux, and macOS**.

## Install

**Step 1 — Clone:**

```bash
git clone https://github.com/JoelDlima/yt-cli.git
cd yt-cli
```

**Step 2 — Run the installer** (creates a virtual environment, installs
dependencies, puts `ytdownloader`/`ytcli` on your PATH so you can run them
from any folder). Safe to re-run after `git pull`:

```bat
install.bat
```

```bash
chmod +x install.sh
./install.sh
```

**Step 3 — Open a fresh terminal** (PATH changes only apply to new
sessions) and run:

```bash
ytdownloader
# or the shorter alias — same tool:
ytcli
```

Prefer to manage the venv yourself? `python -m venv .venv`, activate it,
then `pip install -e .` (extras: `pip install -e ".[extra]"` for clipboard
detection and disk checks, `".[dev]"` for the test suite). With this path
you must activate the venv in each new terminal.

## First run (walkthrough)

Launch from any terminal — you never need to `cd` into the repo again:

![Launching ytcli](docs/images/01-cli-command.jpeg)

Pick a number from the main menu. At any prompt, `back` goes back a step,
`cancel` aborts, `help` explains, and `Ctrl+C` interrupts safely.

![Main menu](docs/images/02-main-menu.jpeg)

Enter a URL — or just search by name and pick from a results table:

![Search results](docs/images/03-search-results.jpeg)

Choose download options (format, resolution/bitrate, subtitles):

![Download options](docs/images/04-download-options.jpeg)

Done — saved to your output folder and recorded in history:

![Download complete](docs/images/05-download-complete.jpeg)

## Scripting (no menu needed)

```bash
# Download a single video at 1080p
ytdownloader download "https://youtu.be/VIDEO_ID" --resolution 1080p

# Extract audio as MP3 at 192 kbps
ytdownloader download "https://youtu.be/VIDEO_ID" --audio-only --bitrate 192

# Preview details only, download nothing
ytdownloader download "https://youtu.be/VIDEO_ID" --dry-run

# Batch: every URL in a file (txt/csv/json - links found automatically,
# extra columns and duplicates handled)
ytdownloader batch urls.txt --resolution 720p
cat urls.txt | ytdownloader batch -

# Search and stream
ytdownloader search "python tutorial" --max-results 5
ytdownloader watch "https://youtu.be/VIDEO_ID"
ytdownloader watch "big buck bunny 4k" --resolution 720p

# History
ytdownloader history
ytdownloader history --export history.csv
```

`ytdownloader --help` or `ytdownloader <command> --help` lists every flag.
Both binary names accept identical commands.

## Settings

Stored in your home directory (`~/.ytdownloader/`), never inside the repo:

| File | Purpose |
|---|---|
| `config.json` | Output folder, quality defaults, concurrency, retries, theme, overwrite/skip, filename templates, cookies, proxy, rate limits, subtitle language |
| `history.json` | Download history |
| `download_archive.txt` | Duplicate prevention (safe playlist resumes) |
| `logs/ytdownloader.log` | Rotating debug/error logs |

Edit from the in-app Settings menu or directly in `config.json`.
Filename templates are yt-dlp style (`%(title)s.%(ext)s` → `My Video.mp4`);
bad characters are sanitized and collisions become `(1)`, `(2)`, ….
Optional env overrides live in `.env` (see `.env.example`) — the Settings
menu takes precedence over them.

## Troubleshooting

- **"FFmpeg required but not found"** — install it (table above) and
  confirm `ffmpeg -version` works in your terminal.
- **"VLC required but not found"** — only affects Watch-in-VLC; install it
  or use downloads instead.
- **Private / age-restricted / deleted video** — reported plainly; age
  gates may need a cookie file in Settings.
- **Rate limited (HTTP 429)** — lower concurrent downloads, add a sleep
  interval, or wait before retrying.
- **Skipped unexpectedly** — check `skip_existing` and the archive file;
  skips are by design so interrupted playlists resume safely.
- **Low disk space** — the app checks before large downloads and asks
  before proceeding.
- **Command not found after install** — open a brand-new terminal window.

## Uninstall

```bat
uninstall.bat
```

```bash
chmod +x uninstall.sh
./uninstall.sh
```

Removes the virtual environment and PATH entry. You'll be asked whether to
also delete app data (`~/.ytdownloader` — settings, history, logs); keep it
if you plan to reinstall. The cloned repo folder itself is left alone —
delete it manually if done with the source.

## Legal

Personal, lawful use only. **You are responsible for what you download** —
only content you own, have permission for, or that is licensed for it
(Creative Commons, public domain). Respect creators and YouTube's Terms of
Service. Not affiliated with YouTube, Google, VideoLAN/VLC, or yt-dlp.

## Privacy

No telemetry. Settings, history, and files stay on your machine in
`~/.ytdownloader`. Nothing is sent anywhere by this software itself.

## Roadmap

Queue management with pause/resume, scheduled downloads, plugin hooks,
shell autocomplete, webhook notifications on batch completion.

Contributions welcome: run `pytest -q` first, keep code type-hinted and
documented like the existing modules.

Built on [yt-dlp](https://github.com/yt-dlp/yt-dlp),
[Rich](https://github.com/Textualize/rich),
[Typer](https://typer.tiangolo.com/), and
[Pydantic](https://docs.pydantic.dev/).

## License

MIT. See [LICENSE](LICENSE).
