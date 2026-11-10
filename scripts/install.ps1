#Requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$Destination = (Join-Path $env:USERPROFILE '.claude\skills'),
    [string[]]$Name = @(),
    [switch]$IncludeVariants
)

$ErrorActionPreference = 'Stop'
$Name = @($Name | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$catalogPath = Join-Path $repoRoot '_meta\codex-export.json'
$catalog = Get-Content -LiteralPath $catalogPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($catalog.schemaVersion -ne 1) { throw 'Unsupported catalog schema.' }
$targetRoot = [IO.Path]::GetFullPath($Destination).TrimEnd('\', '/')
$runId = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfff') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$statePath = Join-Path $targetRoot '.cloud-skills-state.json'
$state = @{ schemaVersion = 1; repository = 'lyyyyyyyc/my-claude-only-skills'; installed = @{} }
$lockHandle = $null

function Get-SafeChild([string]$Root, [string]$Relative) {
    if ([IO.Path]::IsPathRooted($Relative) -or ($Relative -split '[/\\]') -contains '..') {
        throw "Unsafe relative path: $Relative"
    }
    $full = [IO.Path]::GetFullPath((Join-Path $Root $Relative))
    if (-not $full.StartsWith($Root.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes root: $Relative"
    }
    return $full
}

function Assert-NoLinks([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Use a physical directory instead of a link: $Path"
    }
    if ($item.PSIsContainer) {
        $pending = New-Object 'Collections.Generic.Stack[string]'
        $pending.Push($Path)
        while ($pending.Count -gt 0) {
            foreach ($child in Get-ChildItem -LiteralPath $pending.Pop() -Force) {
                if (($child.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                    throw "Directory contains a link: $($child.FullName)"
                }
                if ($child.PSIsContainer) { $pending.Push($child.FullName) }
            }
        }
    }
}

function Get-TreeFiles([string]$Root) {
    Assert-NoLinks $Root
    $result = @{}
    foreach ($file in Get-ChildItem -LiteralPath $Root -Recurse -File -Force) {
        $relative = $file.FullName.Substring($Root.TrimEnd('\', '/').Length + 1).Replace('\', '/')
        $hasher = [Security.Cryptography.SHA256]::Create()
        $stream = [IO.File]::OpenRead($file.FullName)
        try {
            $result[$relative] = [BitConverter]::ToString($hasher.ComputeHash($stream)).Replace('-', '').ToLowerInvariant()
        } finally {
            $stream.Dispose()
            $hasher.Dispose()
        }
    }
    return $result
}

function Test-SameFiles([hashtable]$Actual, [hashtable]$Expected) {
    if ($Actual.Count -ne $Expected.Count) { return $false }
    foreach ($key in $Expected.Keys) {
        if (-not $Actual.ContainsKey($key) -or $Actual[$key] -ne $Expected[$key]) { return $false }
    }
    return $true
}

$selected = @($catalog.skills | Where-Object { $_.default -or $IncludeVariants })
if ($Name.Count -gt 0) {
    foreach ($requested in $Name) {
        if ($requested -notin $selected.name) { throw "Unknown or disabled skill name: $requested. Use -IncludeVariants for variants." }
    }
    $selected = @($selected | Where-Object { $_.name -in $Name })
}
if ($selected.Count -eq 0) { throw 'No skills selected.' }

$counts = @{ installed = 0; updated = 0; unchanged = 0; skipped = 0; planned = 0 }
try {
    if (-not $WhatIfPreference) {
        [IO.Directory]::CreateDirectory($targetRoot) | Out-Null
        Assert-NoLinks $targetRoot
        $lockPath = Join-Path $targetRoot '.cloud-skills-install.lock'
        $lockHandle = [IO.File]::Open($lockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    }
    if (Test-Path -LiteralPath $statePath) {
        $old = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($old.schemaVersion -ne 1 -or $old.repository -ne $state.repository -or -not $old.installed) {
            throw 'Invalid install state. Preserve it and investigate before updating.'
        }
        foreach ($property in $old.installed.PSObject.Properties) {
            $files = @{}
            foreach ($file in $property.Value.files.PSObject.Properties) { $files[$file.Name] = [string]$file.Value }
            $state.installed[$property.Name] = @{ files = $files }
        }
    }
    foreach ($skill in $selected) {
        if ($skill.name -notmatch '^[a-z0-9]+(-[a-z0-9]+)*$' -or $skill.name.Length -gt 64) {
            throw "Invalid skill name: $($skill.name)"
        }
        $expectedPath = $(if ($skill.default) { 'skills/' } else { 'variants/' }) + $skill.name
        if ($skill.path -cne $expectedPath) { throw "Invalid catalog path: $($skill.path)" }
        $source = Get-SafeChild $repoRoot $skill.path
        $target = Get-SafeChild $targetRoot $skill.name
        $expected = @{}
        foreach ($file in $skill.exportFiles) {
            $null = Get-SafeChild $source $file.path
            if ($expected.ContainsKey($file.path)) { throw "Duplicate catalog file: $($file.path)" }
            $expected[$file.path] = [string]$file.sha256
        }
        if (-not $expected.ContainsKey('SKILL.md')) { throw "Incomplete catalog: $($skill.name)" }
        if (-not (Test-SameFiles (Get-TreeFiles $source) $expected)) {
            throw "Source integrity check failed: $($skill.name). Fetch the complete repository again."
        }
        $exists = Test-Path -LiteralPath $target
        if ($exists) {
            $actual = Get-TreeFiles $target
            if (Test-SameFiles $actual $expected) {
                $state.installed[$skill.name] = @{ files = $expected }
                $counts.unchanged++
                continue
            }
            if (-not $state.installed.ContainsKey($skill.name) -or
                -not (Test-SameFiles $actual $state.installed[$skill.name].files)) {
                Write-Warning "Skipped $($skill.name): existing skill is unmanaged or locally edited."
                $counts.skipped++
                continue
            }
        }
        if (-not $PSCmdlet.ShouldProcess($target, 'Install verified Claude Code skill')) {
            $counts.planned++
            continue
        }
        $stagingRelative = '.cloud-skills-staging/' + $runId + '/' + $skill.name
        $staging = Get-SafeChild $targetRoot $stagingRelative
        [IO.Directory]::CreateDirectory($staging) | Out-Null
        foreach ($file in $skill.exportFiles) {
            $inputPath = Get-SafeChild $source $file.path
            $outputPath = Get-SafeChild $staging $file.path
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($outputPath)) | Out-Null
            Copy-Item -LiteralPath $inputPath -Destination $outputPath
        }
        if (-not (Test-SameFiles (Get-TreeFiles $staging) $expected)) { throw "Staged copy failed integrity: $($skill.name)" }
        if ($exists) {
            $backup = Get-SafeChild $targetRoot ('.cloud-skills-backups/' + $runId + '/' + $skill.name)
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($backup)) | Out-Null
            Move-Item -LiteralPath $target -Destination $backup
        }
        try {
            Move-Item -LiteralPath $staging -Destination $target
        } catch {
            if ($exists -and -not (Test-Path -LiteralPath $target)) {
                Move-Item -LiteralPath $backup -Destination $target
            }
            throw
        }
        $state.installed[$skill.name] = @{ files = $expected }
        if ($exists) { $counts.updated++ } else { $counts.installed++ }
        # Save after each skill so an interrupted install can resume safely.
        $temporaryState = Get-SafeChild $targetRoot ('.cloud-skills-state.' + $runId + '.tmp')
        $json = $state | ConvertTo-Json -Depth 20
        [IO.File]::WriteAllText($temporaryState, $json, (New-Object Text.UTF8Encoding($false)))
        Move-Item -LiteralPath $temporaryState -Destination $statePath -Force
    }
    Write-Output ("Installed={0} Updated={1} Unchanged={2} Skipped={3} Planned={4}" -f
        $counts.installed, $counts.updated, $counts.unchanged, $counts.skipped, $counts.planned)
    Write-Output "Skill directory: $targetRoot"
} finally {
    if ($lockHandle) { $lockHandle.Dispose() }
}
