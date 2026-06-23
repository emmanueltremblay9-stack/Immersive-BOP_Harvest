param(
    [string]$ModsDir = "C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT play\minecraft\mods"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Add-Type -AssemblyName System.IO.Compression.FileSystem

$ProjectRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$BuildLibsDir = Join-Path $ProjectRoot "build\libs"
$RuntimeDepsDir = Join-Path $ProjectRoot "build\runtime-deps"
$ReportPath = Join-Path $ProjectRoot "build\install-report.json"

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
        $key = $trimmed.Substring(0, $index).Trim()
        $value = $trimmed.Substring($index + 1).Trim()
        $props[$key] = $value
    }
    return $props
}

function Get-FileSha256 {
    param([string]$Path)

    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $hasher = [System.Security.Cryptography.SHA256]::Create()
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

function Get-FileSha512 {
    param([string]$Path)

    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $hasher = [System.Security.Cryptography.SHA512]::Create()
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

function Get-JarEntries {
    param([string]$JarPath)

    $archive = [System.IO.Compression.ZipFile]::OpenRead($JarPath)
    try {
        return @($archive.Entries | ForEach-Object { $_.FullName })
    } finally {
        $archive.Dispose()
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
    $dependencies = @()
    foreach ($dependencyBlockMatch in [regex]::Matches($toml, "(?ms)^\s*\[\[dependencies\.[^\]]+\]\]\s*(?<block>.*?)(?=^\s*\[\[|\z)")) {
        $dependencyBlock = $dependencyBlockMatch.Groups["block"].Value
        $dependencyModId = Get-TomlValue -Block $dependencyBlock -Name "modId"
        if ($dependencyModId) {
            $dependencies += [ordered]@{
                modId = $dependencyModId
                type = Get-TomlValue -Block $dependencyBlock -Name "type"
                versionRange = Get-TomlValue -Block $dependencyBlock -Name "versionRange"
                ordering = Get-TomlValue -Block $dependencyBlock -Name "ordering"
                side = Get-TomlValue -Block $dependencyBlock -Name "side"
            }
        }
    }

    return [ordered]@{
        modId = Get-TomlValue -Block $modBlock -Name "modId"
        version = Get-TomlValue -Block $modBlock -Name "version"
        displayName = Get-TomlValue -Block $modBlock -Name "displayName"
        dependencies = $dependencies
    }
}

function Find-JarsByPrimaryModId {
    param(
        [string]$Directory,
        [string]$ModId
    )

    if (-not (Test-Path -LiteralPath $Directory)) {
        return @()
    }

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
                    sha256 = Get-FileSha256 -Path $jar.FullName
                }
            }
        } catch {
            continue
        }
    }
    return @($matches)
}

function Test-VersionMatch {
    param(
        $Info,
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

function Select-ProjectJar {
    param(
        [string]$Directory,
        [string]$ModId,
        [string]$Version
    )

    $jars = Get-ChildItem -LiteralPath $Directory -File -Filter "*.jar" |
        Where-Object { $_.Name -notmatch "(?i)(sources|javadoc|dev|plain|test|api)" }

    foreach ($jar in $jars) {
        $info = Get-JarModInfo -JarPath $jar.FullName
        if ($null -ne $info -and $info.modId -eq $ModId -and $info.version -eq $Version) {
            return $jar.FullName
        }
    }

    throw "No production jar in $Directory matched mod id '$ModId' and version '$Version'."
}

function Install-VerifiedJar {
    param(
        [string]$SourceJar,
        [string]$TargetDirectory,
        [string]$ModId,
        [string]$ExpectedVersion,
        [switch]$AllowFileJarVersionPlaceholder
    )

    $sourceInfo = Get-JarModInfo -JarPath $SourceJar
    if ($null -eq $sourceInfo) {
        throw "Source jar has no NeoForge metadata: $SourceJar"
    }
    if ($sourceInfo.modId -ne $ModId) {
        throw "Source jar primary mod id '$($sourceInfo.modId)' did not match '$ModId': $SourceJar"
    }
    $versionMatches = $sourceInfo.version -eq $ExpectedVersion
    $versionPlaceholderMatches = $AllowFileJarVersionPlaceholder -and $sourceInfo.version -eq '${file.jarVersion}'
    if ($ExpectedVersion -and -not $versionMatches -and -not $versionPlaceholderMatches) {
        throw "Source jar version '$($sourceInfo.version)' did not match '$ExpectedVersion': $SourceJar"
    }

    $oldJars = @(Find-JarsByPrimaryModId -Directory $TargetDirectory -ModId $ModId)
    foreach ($oldJar in $oldJars) {
        Remove-Item -LiteralPath $oldJar.path -Force
    }

    $targetJar = Join-Path $TargetDirectory (Split-Path -Leaf $SourceJar)
    Copy-Item -LiteralPath $SourceJar -Destination $targetJar -Force

    $sourceFile = Get-Item -LiteralPath $SourceJar
    $targetFile = Get-Item -LiteralPath $targetJar
    $sourceSha256 = Get-FileSha256 -Path $SourceJar
    $targetSha256 = Get-FileSha256 -Path $targetJar
    $remainingJars = @(Find-JarsByPrimaryModId -Directory $TargetDirectory -ModId $ModId)
    $targetInfo = Get-JarModInfo -JarPath $targetJar

    return [ordered]@{
        modId = $ModId
        expectedVersion = $ExpectedVersion
        sourceJar = $sourceFile.FullName
        installedJar = $targetFile.FullName
        sourceSize = $sourceFile.Length
        installedSize = $targetFile.Length
        sourceSha256 = $sourceSha256
        installedSha256 = $targetSha256
        hashMatch = ($sourceSha256 -eq $targetSha256)
        deletedOldJars = $oldJars
        remainingJarsForMod = $remainingJars.Count
        remainingJars = $remainingJars
        installedMetadata = $targetInfo
    }
}

function Assert-InstallResult {
    param($Result)

    if (-not $Result.hashMatch) {
        throw "Installed hash mismatch for $($Result.modId)."
    }
    if ($Result.remainingJarsForMod -ne 1) {
        throw "Expected exactly one installed jar for $($Result.modId); found $($Result.remainingJarsForMod)."
    }
}

function Get-ResourceCounts {
    param([string]$JarPath)

    $entries = @(Get-JarEntries -JarPath $JarPath)
    return [ordered]@{
        cuttingRecipes = @($entries | Where-Object { $_ -like "data/immersive_bop_harvest/recipe/cutting/*.json" }).Count
        sawmillRecipes = @($entries | Where-Object { $_ -like "data/immersive_bop_harvest/recipe/sawmill/*.json" }).Count
        directHarvestModifiers = @($entries | Where-Object { $_ -like "data/immersive_bop_harvest/loot_modifiers/direct_harvest/*.json" }).Count
        directHarvestLootTables = @($entries | Where-Object { $_ -like "data/immersive_bop_harvest/loot_table/direct_harvest/*.json" }).Count
        cItemTags = @($entries | Where-Object { $_.StartsWith("data/c/tags/item/") -and $_.EndsWith(".json") }).Count
        globalLootModifierIndex = $entries.Contains("data/neoforge/loot_modifiers/global_loot_modifiers.json")
    }
}

function Verify-ExistingDependency {
    param(
        [string]$Directory,
        [string]$ModId,
        [string]$ExpectedVersion
    )

    $matches = @(Find-JarsByPrimaryModId -Directory $Directory -ModId $ModId)
    if ($matches.Count -ne 1) {
        throw "Expected exactly one installed dependency jar for $ModId; found $($matches.Count)."
    }
    $metadata = Get-JarModInfo -JarPath $matches[0].path
    if (-not (Test-VersionMatch -Info $metadata -JarName $matches[0].name -ExpectedVersion $ExpectedVersion)) {
        throw "Installed dependency $ModId version '$($metadata.version)' did not match expected '$ExpectedVersion'."
    }
    return [ordered]@{
        modId = $ModId
        expectedVersion = $ExpectedVersion
        installedJar = $matches[0].path
        installedSize = $matches[0].size
        installedSha256 = $matches[0].sha256
        installedMetadata = $metadata
        remainingJarsForMod = $matches.Count
        copiedFromRuntimeDeps = $false
    }
}

function Find-RuntimeDependencySource {
    param(
        [string]$Directory,
        [string]$ModId,
        [string]$ExpectedVersion
    )

    $matches = @(Find-JarsByPrimaryModId -Directory $Directory -ModId $ModId | Where-Object {
        $metadata = Get-JarModInfo -JarPath $_.path
        Test-VersionMatch -Info $metadata -JarName $_.name -ExpectedVersion $ExpectedVersion
    })
    if ($matches.Count -ne 1) {
        $found = @(Find-JarsByPrimaryModId -Directory $Directory -ModId $ModId | ForEach-Object { "$($_.name)@$($_.version)" })
        throw "Expected exactly one runtime dependency source jar for $ModId $ExpectedVersion; found $($matches.Count). Candidates: $($found -join ', ')"
    }
    return $matches[0].path
}

function Ensure-DependencyInstalled {
    param(
        [string]$TargetDirectory,
        [string]$RuntimeDepsDirectory,
        [string]$ModId,
        [string]$ExpectedVersion
    )

    try {
        return Verify-ExistingDependency -Directory $TargetDirectory -ModId $ModId -ExpectedVersion $ExpectedVersion
    } catch {
        $sourceJar = Find-RuntimeDependencySource -Directory $RuntimeDepsDirectory -ModId $ModId -ExpectedVersion $ExpectedVersion
        $result = Install-VerifiedJar `
            -SourceJar $sourceJar `
            -TargetDirectory $TargetDirectory `
            -ModId $ModId `
            -ExpectedVersion $ExpectedVersion `
            -AllowFileJarVersionPlaceholder
        Assert-InstallResult -Result $result
        $result["copiedFromRuntimeDeps"] = $true
        return $result
    }
}

$props = Read-GradleProperties -Path (Join-Path $ProjectRoot "gradle.properties")
$resolvedModsDir = Resolve-Path -LiteralPath $ModsDir

$modId = $props["mod_id"]
$modVersion = $props["mod_version"]
$modName = $props["mod_name"]
$sourceJar = Select-ProjectJar -Directory $BuildLibsDir -ModId $modId -Version $modVersion

if (-not (Test-Path -LiteralPath $RuntimeDepsDir)) {
    New-Item -ItemType Directory -Path $RuntimeDepsDir | Out-Null
}

$runtimeDependencies = @(
    [ordered]@{ modId = "biomesoplenty"; expectedVersion = $props["biomesoplenty_version"] },
    [ordered]@{ modId = "glitchcore"; expectedVersion = $props["glitchcore_version"] },
    [ordered]@{ modId = "terrablender"; expectedVersion = $props["terrablender_version"] },
    [ordered]@{ modId = "farmersdelight"; expectedVersion = $props["farmersdelight_version"] },
    [ordered]@{ modId = "immersiveengineering"; expectedVersion = $props["immersiveengineering_version"] }
)

$dependencyResults = @()
foreach ($dependency in $runtimeDependencies) {
    $dependencyResults += Ensure-DependencyInstalled `
        -TargetDirectory $resolvedModsDir.Path `
        -RuntimeDepsDirectory $RuntimeDepsDir `
        -ModId $dependency.modId `
        -ExpectedVersion $dependency.expectedVersion
}

$previousProjectJars = @(Find-JarsByPrimaryModId -Directory $resolvedModsDir.Path -ModId $modId)
$projectInstall = Install-VerifiedJar `
    -SourceJar $sourceJar `
    -TargetDirectory $resolvedModsDir.Path `
    -ModId $modId `
    -ExpectedVersion $modVersion
Assert-InstallResult -Result $projectInstall
$projectInstall["resourceCounts"] = Get-ResourceCounts -JarPath $projectInstall.installedJar

$report = [ordered]@{
    generatedAt = (Get-Date).ToString("o")
    projectRoot = $ProjectRoot.Path
    targetModsDir = $resolvedModsDir.Path
    loader = "NeoForge"
    minecraftVersion = $props["minecraft_version"]
    neoForgeVersion = $props["neo_version"]
    previousVersion = if ($previousProjectJars.Count -gt 0) { $previousProjectJars[0].version } else { $null }
    newVersion = $modVersion
    modId = $modId
    modName = $modName
    projectJar = $projectInstall
    runtimeDependencies = $dependencyResults
    copiedRuntimeDependencies = @($dependencyResults | Where-Object { $_.copiedFromRuntimeDeps })
    existingRuntimeDependencies = @($dependencyResults | Where-Object { -not $_.copiedFromRuntimeDeps })
    liveClientSmokeTested = $false
    safeToLaunchMinecraft = $true
}

$reportDir = Split-Path -Parent $ReportPath
if (-not (Test-Path -LiteralPath $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir | Out-Null
}

$report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
Write-Host "INSTALL REPORT: $ReportPath"
Write-Host "INSTALLED: $($projectInstall.installedJar)"
Write-Host "SHA256: $($projectInstall.installedSha256)"
Write-Host "REMAINING MOD JARS: $($projectInstall.remainingJarsForMod)"
