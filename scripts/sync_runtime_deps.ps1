param(
    [string]$SourceModsDir = "C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT play\minecraft\mods",
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Add-Type -AssemblyName System.IO.Compression.FileSystem

$ProjectRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$BuildRoot = Join-Path $ProjectRoot "build"
if ($OutputDir.Length -eq 0) {
    $OutputDir = Join-Path $BuildRoot "runtime-deps"
}

function Read-GradleProperties {
    param([string]$Path)

    $props = @{}
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if ($trimmed.Length -eq 0 -or $trimmed.StartsWith("#")) {
            continue
        }
        $index = $trimmed.IndexOf("=")
        if ($index -lt 1) {
            continue
        }
        $props[$trimmed.Substring(0, $index).Trim()] = $trimmed.Substring($index + 1).Trim()
    }
    return $props
}

function Get-ZipEntryText {
    param(
        [string]$JarPath,
        [string]$EntryName
    )

    $archive = [System.IO.Compression.ZipFile]::OpenRead($JarPath)
    try {
        $entry = $archive.GetEntry($EntryName)
        if ($null -eq $entry) {
            return $null
        }

        $stream = $entry.Open()
        try {
            $reader = [System.IO.StreamReader]::new($stream)
            try {
                return $reader.ReadToEnd()
            } finally {
                $reader.Dispose()
            }
        } finally {
            $stream.Dispose()
        }
    } finally {
        $archive.Dispose()
    }
}

function Get-FileHashHex {
    param(
        [string]$Path,
        [ValidateSet("SHA256", "SHA512")]
        [string]$Algorithm
    )

    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $hasher = if ($Algorithm -eq "SHA256") {
            [System.Security.Cryptography.SHA256]::Create()
        } else {
            [System.Security.Cryptography.SHA512]::Create()
        }
        try {
            $bytes = $hasher.ComputeHash($stream)
            return ([System.BitConverter]::ToString($bytes) -replace "-", "").ToLowerInvariant()
        } finally {
            $hasher.Dispose()
        }
    } finally {
        $stream.Dispose()
    }
}

function Get-TomlValue {
    param(
        [string]$Block,
        [string]$Name
    )

    $match = [regex]::Match($Block, "(?m)^\s*$([regex]::Escape($Name))\s*=\s*`"?(?<value>[^`"\r\n]+)`"?\s*$")
    if ($match.Success) {
        return $match.Groups["value"].Value.Trim()
    }
    return $null
}

function Get-JarModInfo {
    param([string]$JarPath)

    $toml = Get-ZipEntryText -JarPath $JarPath -EntryName "META-INF/neoforge.mods.toml"
    if ($null -eq $toml) {
        return $null
    }

    $modBlockMatch = [regex]::Match($toml, "(?ms)^\s*\[\[mods\]\]\s*(?<block>.*?)(?=^\s*\[\[|\z)")
    if (-not $modBlockMatch.Success) {
        return $null
    }

    $modBlock = $modBlockMatch.Groups["block"].Value
    return [ordered]@{
        modId = Get-TomlValue -Block $modBlock -Name "modId"
        version = Get-TomlValue -Block $modBlock -Name "version"
        displayName = Get-TomlValue -Block $modBlock -Name "displayName"
    }
}

function Test-VersionMatch {
    param(
        [object]$Info,
        [string]$JarName,
        [string]$ExpectedVersion
    )

    if ($Info.version -eq $ExpectedVersion) {
        return $true
    }
    if ($Info.version -eq '${file.jarVersion}' -and $JarName.Contains($ExpectedVersion)) {
        return $true
    }
    return $false
}

function Find-JarsByModId {
    param(
        [string]$Directory,
        [string]$ModId
    )

    $matches = @()
    foreach ($jar in Get-ChildItem -LiteralPath $Directory -File -Filter "*.jar") {
        try {
            $info = Get-JarModInfo -JarPath $jar.FullName
            if ($null -ne $info -and $info.modId -eq $ModId) {
                $matches += [ordered]@{
                    path = $jar.FullName
                    name = $jar.Name
                    version = $info.version
                    displayName = $info.displayName
                    size = $jar.Length
                    sha256 = Get-FileHashHex -Path $jar.FullName -Algorithm SHA256
                    sha512 = Get-FileHashHex -Path $jar.FullName -Algorithm SHA512
                }
            }
        } catch {
            if ($jar.Name -match [regex]::Escape($ModId)) {
                Write-Warning "Could not inspect $($jar.FullName): $($_.Exception.Message)"
            }
            continue
        }
    }
    return @($matches)
}

$resolvedSource = Resolve-Path -LiteralPath $SourceModsDir
$sourceJarCount = @(Get-ChildItem -LiteralPath $resolvedSource.Path -File -Filter "*.jar").Count
Write-Host "SYNC SOURCE: $($resolvedSource.Path)"
Write-Host "SYNC SOURCE JARS: $sourceJarCount"
if (-not (Test-Path -LiteralPath $BuildRoot)) {
    New-Item -ItemType Directory -Path $BuildRoot | Out-Null
}
if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}
$resolvedOutput = Resolve-Path -LiteralPath $OutputDir
$resolvedBuild = Resolve-Path -LiteralPath $BuildRoot
if (-not $resolvedOutput.Path.StartsWith($resolvedBuild.Path, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputDir must stay inside the project build directory: $($resolvedOutput.Path)"
}

$props = Read-GradleProperties -Path (Join-Path $ProjectRoot "gradle.properties")
$required = @(
    [ordered]@{ modId = "biomesoplenty"; expectedVersion = $props["biomesoplenty_version"] },
    [ordered]@{ modId = "glitchcore"; expectedVersion = $props["glitchcore_version"] },
    [ordered]@{ modId = "terrablender"; expectedVersion = $props["terrablender_version"] },
    [ordered]@{ modId = "farmersdelight"; expectedVersion = $props["farmersdelight_version"] },
    [ordered]@{ modId = "immersiveengineering"; expectedVersion = $props["immersiveengineering_version"] }
)

$results = @()
foreach ($dependency in $required) {
    $sourceMatches = @(Find-JarsByModId -Directory $resolvedSource.Path -ModId $dependency.modId | Where-Object {
        Test-VersionMatch -Info $_ -JarName $_.name -ExpectedVersion $dependency.expectedVersion
    })
    if ($sourceMatches.Count -ne 1) {
        $found = @(Find-JarsByModId -Directory $resolvedSource.Path -ModId $dependency.modId | ForEach-Object { "$($_.name)@$($_.version)" })
        throw "Expected exactly one source jar for $($dependency.modId) $($dependency.expectedVersion); found $($sourceMatches.Count). Candidates: $($found -join ', ')"
    }

    $staleCopies = @(Find-JarsByModId -Directory $resolvedOutput.Path -ModId $dependency.modId)
    foreach ($stale in $staleCopies) {
        Remove-Item -LiteralPath $stale.path -Force
    }

    $targetPath = Join-Path $resolvedOutput.Path $sourceMatches[0].name
    Copy-Item -LiteralPath $sourceMatches[0].path -Destination $targetPath -Force
    $targetItem = Get-Item -LiteralPath $targetPath
    $targetSha256 = Get-FileHashHex -Path $targetPath -Algorithm SHA256

    if ($targetSha256 -ne $sourceMatches[0].sha256) {
        throw "SHA-256 mismatch after copying $($dependency.modId)."
    }

    $results += [ordered]@{
        modId = $dependency.modId
        expectedVersion = $dependency.expectedVersion
        sourceJar = $sourceMatches[0].path
        runtimeJar = $targetItem.FullName
        sourceSha256 = $sourceMatches[0].sha256
        runtimeSha256 = $targetSha256
        hashMatch = $true
        removedStaleRuntimeJars = $staleCopies
    }
}

$report = [ordered]@{
    generatedAt = (Get-Date).ToString("o")
    sourceModsDir = $resolvedSource.Path
    outputDir = $resolvedOutput.Path
    dependencies = $results
}
$reportPath = Join-Path $resolvedBuild.Path "runtime-deps-report.json"
$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $reportPath -Encoding UTF8

Write-Host "RUNTIME DEPS REPORT: $reportPath"
foreach ($result in $results) {
    Write-Host "RUNTIME DEP: $($result.modId) $($result.expectedVersion) -> $($result.runtimeJar)"
}
