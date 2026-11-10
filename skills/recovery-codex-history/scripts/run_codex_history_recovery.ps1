[CmdletBinding()]
param(
    [ValidateSet("Status", "Backup", "Sync", "Full", "Gui", "Restore", "Update")]
    [string]$Action = "Full",

    [string]$ToolDir = "",

    [string]$BackupDir = "D:\CodexHistoryBackups",

    [switch]$SkipUpdate
)

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/GODGOD126/codex-history-sync-tool.git"
$CodexDir = Join-Path $env:USERPROFILE ".codex"
$PatchedBackendDir = Join-Path $PSScriptRoot ".generated"

if ([string]::IsNullOrWhiteSpace($ToolDir)) {
    $ToolDir = Join-Path $env:USERPROFILE ".codex-history-sync-tool"
}

$BackupDir = [System.IO.Path]::GetFullPath($BackupDir)

function Assert-Command {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        throw "Required command not found: $Name"
    }
}

function Invoke-External {
    param(
        [string]$Exe,
        [string[]]$ArgumentList,
        [string]$Step
    )

    Write-Host ""
    Write-Host "[$Step] $Exe $($ArgumentList -join ' ')"
    & $Exe @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed with exit code ${LASTEXITCODE}: $Step"
    }
}

function Ensure-ToolRepo {
    Assert-Command "git"

    $parent = Split-Path -Parent $ToolDir
    if (-not (Test-Path -Path $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }

    $gitDir = Join-Path $ToolDir ".git"
    if (-not (Test-Path -Path $gitDir)) {
        Invoke-External -Exe "git" -ArgumentList @("clone", $RepoUrl, $ToolDir) -Step "clone-helper-repo"
    } elseif (-not $SkipUpdate) {
        Invoke-External -Exe "git" -ArgumentList @("-C", $ToolDir, "pull", "--ff-only") -Step "update-helper-repo"
    }
}

function Ensure-BackupDir {
    if (-not (Test-Path -LiteralPath $BackupDir)) {
        New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
    }
}

function Get-BackendScript {
    $source = Join-Path $ToolDir "sync_backend.py"
    if (-not (Test-Path -Path $source)) {
        throw "sync_backend.py not found under $ToolDir"
    }

    if (-not (Test-Path -LiteralPath $PatchedBackendDir)) {
        New-Item -ItemType Directory -Force -Path $PatchedBackendDir | Out-Null
    }

    $target = Join-Path $PatchedBackendDir "sync_backend_d_backup.py"
    $sourceLiteral = ConvertTo-Json -Compress $source
    $backupLiteral = ConvertTo-Json -Compress $BackupDir
    $wrapper = @"
from __future__ import annotations

import importlib.util
import pathlib
import sys

SOURCE = pathlib.Path($sourceLiteral)
BACKUP_DIR = pathlib.Path($backupLiteral)

spec = importlib.util.spec_from_file_location("codex_history_sync_backend", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Could not load backend: {SOURCE}")

backend = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = backend
spec.loader.exec_module(backend)

_original_resolve_paths = backend.resolve_paths


def resolve_paths(codex_home):
    paths = _original_resolve_paths(codex_home)
    paths.backup_dir = BACKUP_DIR
    return paths


backend.resolve_paths = resolve_paths

raise SystemExit(backend.main())
"@
    Set-Content -LiteralPath $target -Value $wrapper -Encoding ASCII
    return $target
}

function Invoke-Backend {
    param([ValidateSet("status", "backup", "sync", "restore")][string]$Command)

    Assert-Command "py"
    $script = Get-BackendScript

    Push-Location $ToolDir
    try {
        Invoke-External -Exe "py" -ArgumentList @("-3", $script, "--json", $Command) -Step $Command
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path -Path $CodexDir)) {
    throw "Local Codex data directory not found: $CodexDir"
}

Write-Host "Codex data dir: $CodexDir"
Write-Host "Helper repo dir: $ToolDir"
Write-Host "Backup dir: $BackupDir"
Write-Host "Requested action: $Action"

Ensure-ToolRepo
Ensure-BackupDir

switch ($Action) {
    "Status" {
        Invoke-Backend -Command "status"
    }
    "Backup" {
        Invoke-Backend -Command "backup"
    }
    "Sync" {
        Invoke-Backend -Command "status"
        Invoke-Backend -Command "backup"
        Invoke-Backend -Command "sync"
    }
    "Full" {
        Invoke-Backend -Command "status"
        Invoke-Backend -Command "backup"
        Invoke-Backend -Command "sync"
    }
    "Gui" {
        $launcher = Join-Path $ToolDir "launch_ui.ps1"
        if (-not (Test-Path -Path $launcher)) {
            throw "launch_ui.ps1 not found under $ToolDir"
        }
        Invoke-External -Exe "powershell" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $launcher) -Step "launch-gui"
    }
    "Restore" {
        Invoke-Backend -Command "backup"
        Invoke-Backend -Command "restore"
    }
    "Update" {
        Write-Host "Helper repository is present and updated."
    }
}

Write-Host ""
Write-Host "Done. Restart Codex Desktop. If history is still hidden, open the original project folder for the old conversation."
