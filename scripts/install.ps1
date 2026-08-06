#Requires -Version 5.0
<#
    .SYNOPSIS
        Sets up the YouTube Downloader CLI: creates a virtual environment,
        installs the package, and adds it to the current user's PATH so
        `ytdownloader` / `ytcli` can be launched from any directory.

    .NOTES
        Invoked by install.bat. Safe to re-run; it skips steps that are
        already complete.
#>

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvDir = Join-Path $RepoRoot ".venv"
$VenvScripts = Join-Path $VenvDir "Scripts"

function Write-Step($message) {
    Write-Host ""
    Write-Host "==> $message" -ForegroundColor Cyan
}

function Write-Ok($message) {
    Write-Host "    $message" -ForegroundColor Green
}

function Write-Warn($message) {
    Write-Host "    $message" -ForegroundColor Yellow
}

# 1. Locate a usable Python interpreter (3.11+)
Write-Step "Checking for Python 3.11+"
$pythonCmd = $null
foreach ($candidate in @("py", "python", "python3")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $versionOutput = & $candidate --version 2>&1
        if ($versionOutput -match "Python 3\.(\d+)") {
            if ([int]$Matches[1] -ge 11) {
                $pythonCmd = $candidate
                break
            }
        }
    }
}
if (-not $pythonCmd) {
    Write-Host "Python 3.11 or later was not found on PATH." -ForegroundColor Red
    Write-Host "Install it from https://www.python.org/downloads/ and re-run this script." -ForegroundColor Red
    exit 1
}
Write-Ok "Using '$pythonCmd'"

# 2. Create the virtual environment if it does not already exist
Write-Step "Setting up virtual environment"
if (Test-Path (Join-Path $VenvScripts "python.exe")) {
    Write-Ok "Virtual environment already exists at $VenvDir"
} else {
    & $pythonCmd -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create the virtual environment." -ForegroundColor Red
        exit 1
    }
    Write-Ok "Created virtual environment at $VenvDir"
}

$VenvPython = Join-Path $VenvScripts "python.exe"

# 3. Install the package in editable mode
Write-Step "Installing dependencies (this may take a minute)"
& $VenvPython -m pip install --upgrade pip --quiet
& $VenvPython -m pip install -e $RepoRoot --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "Dependency installation failed. See output above for details." -ForegroundColor Red
    exit 1
}
Write-Ok "Package installed"

# 4. Add the venv's Scripts directory to the current user's PATH
Write-Step "Adding ytdownloader to your PATH"
$currentUserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$pathEntries = @()
if ($currentUserPath) {
    $pathEntries = $currentUserPath.Split(";") | Where-Object { $_ -ne "" }
}
if ($pathEntries -contains $VenvScripts) {
    Write-Ok "Already present in your user PATH"
} else {
    $newPath = if ($currentUserPath) { "$currentUserPath;$VenvScripts" } else { $VenvScripts }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Ok "Added $VenvScripts to your user PATH"
    Write-Warn "Open a NEW terminal window for this change to take effect."
}

# 5. Check for FFmpeg (required for MP4 merging and MP3 extraction)
Write-Step "Checking for FFmpeg"
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Write-Ok "FFmpeg found"
} else {
    Write-Warn "FFmpeg was not found on PATH."
    Write-Warn "Install it with: winget install Gyan.FFmpeg"
    Write-Warn "The app will still install, but video/audio conversion will fail until FFmpeg is available."
}

# 6. Check for VLC (required only for the "Watch in VLC" streaming feature)
Write-Step "Checking for VLC"
$vlcFound = $false
if (Get-Command vlc -ErrorAction SilentlyContinue) {
    $vlcFound = $true
} else {
    foreach ($candidate in @(
        "$env:ProgramFiles\VideoLAN\VLC\vlc.exe",
        "${env:ProgramFiles(x86)}\VideoLAN\VLC\vlc.exe"
    )) {
        if (Test-Path $candidate) {
            $vlcFound = $true
            break
        }
    }
}
if ($vlcFound) {
    Write-Ok "VLC found"
} else {
    Write-Warn "VLC was not found."
    Write-Warn "Install it with: winget install VideoLAN.VLC"
    Write-Warn "The app will still install, but the 'Watch in VLC' feature will fail until VLC is available."
}

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Open a new terminal window and run 'ytdownloader' or 'ytcli' from any directory." -ForegroundColor Green
