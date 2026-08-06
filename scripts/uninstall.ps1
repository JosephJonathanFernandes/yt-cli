#Requires -Version 5.0
<#
    .SYNOPSIS
        Removes everything install.ps1 set up: the virtual environment,
        the PATH entry, and (optionally) persistent app data such as
        settings, history, and logs.

    .NOTES
        Invoked by uninstall.bat. Safe to re-run.
#>

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvDir = Join-Path $RepoRoot ".venv"
$VenvScripts = Join-Path $VenvDir "Scripts"
$AppDataDir = Join-Path $env:USERPROFILE ".ytdownloader"

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

# 1. Remove the venv's Scripts directory from the current user's PATH
Write-Step "Removing ytdownloader from your PATH"
$currentUserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentUserPath) {
    $pathEntries = $currentUserPath.Split(";") | Where-Object { $_ -ne "" -and $_ -ne $VenvScripts }
    $newPath = ($pathEntries -join ";")
    if ($newPath -ne $currentUserPath) {
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Ok "Removed $VenvScripts from your user PATH"
    } else {
        Write-Ok "Was not present in your user PATH"
    }
} else {
    Write-Ok "No user PATH entries to clean up"
}

# 2. Remove the virtual environment
Write-Step "Removing virtual environment"
if (Test-Path $VenvDir) {
    Remove-Item -Recurse -Force $VenvDir
    Write-Ok "Removed $VenvDir"
} else {
    Write-Ok "No virtual environment found at $VenvDir"
}

# 3. Optionally remove persistent app data (settings, history, logs, archive)
Write-Step "Application data"
if (Test-Path $AppDataDir) {
    Write-Warn "Found application data at $AppDataDir (settings, history, logs, download archive)."
    $response = Read-Host "    Delete this data too? [y/N]"
    if ($response -match "^[Yy]") {
        Remove-Item -Recurse -Force $AppDataDir
        Write-Ok "Removed $AppDataDir"
    } else {
        Write-Ok "Kept $AppDataDir"
    }
} else {
    Write-Ok "No application data found at $AppDataDir"
}

Write-Host ""
Write-Host "Uninstall complete." -ForegroundColor Green
Write-Host "The cloned repository folder itself was not deleted; remove it manually if you no longer need the source code:" -ForegroundColor Green
Write-Host "  $RepoRoot" -ForegroundColor Green
Write-Host "Open a new terminal window for the PATH change to take effect." -ForegroundColor Green
