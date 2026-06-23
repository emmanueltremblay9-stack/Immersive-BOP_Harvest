param(
    [string]$ModsDir = "C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT LaB\minecraft\mods"
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

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-FileSha512 {
    param([string]$Path)

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA512).Hash.ToLowerInvariant()
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
    return [ordered]@{
        modId = $ModId
        expectedVersion = $ExpectedVersion
        installedJar = $matches[0].path
        installedSize = $matches[0].size
        installedSha256 = $matches[0].sha256
        installedMetadata = $metadata
        remainingJarsForMod = $matches.Count
    }
}

$props = Read-GradleProperties -Path (Join-Path $ProjectRoot "gradle.properties")
$resolvedModsDir = Resolve-Path -LiteralPath $ModsDir

$modId = $props["mod_id"]
$modVersion = $props["mod_version"]
$modName = $props["mod_name"]
$sourceJar = Select-ProjectJar -Directory $BuildLibsDir -ModId $modId -Version $modVersion

$downloadedDependencies = @(
    [ordered]@{
        modId = "biomesoplenty"
        expectedVersion = $props["biomesoplenty_version"]
        fileName = "BiomesOPlenty-neoforge-$($props["minecraft_version"])-$($props["biomesoplenty_version"]).jar"
        url = "https://cdn.modrinth.com/data/HXF82T3G/versions/8vIRXPpR/BiomesOPlenty-neoforge-1.21.1-21.1.0.13.jar"
        expectedSha512 = "a238c6dbeccf9bb8f7144601e8f8fd7973d76c60344b50670141e76f49f886f6f89487eb81749dfca7c36166831924052106884a9f8dc18893261476a34d4b32"
    },
    [ordered]@{
        modId = "glitchcore"
        expectedVersion = $props["glitchcore_version"]
        fileName = "GlitchCore-neoforge-$($props["minecraft_version"])-$($props["glitchcore_version"]).jar"
        url = "https://cdn.modrinth.com/data/s3dmwKy5/versions/S2TfWrZR/GlitchCore-neoforge-1.21.1-2.1.0.2.jar"
        expectedSha512 = "7a009ed163d03536fdfaee7b37cb1ec3073204dffcb06a683369aa88da8dbc3780b0ac69d466bb32a3ad9394c97b698d0fda676e1b4dd4edfc50ac5aa2283c32"
    },
    [ordered]@{
        modId = "terrablender"
        expectedVersion = $props["terrablender_version"]
        fileName = "TerraBlender-neoforge-$($props["minecraft_version"])-$($props["terrablender_version"]).jar"
        url = "https://cdn.modrinth.com/data/kkmrDlKT/versions/6e8GCrLb/TerraBlender-neoforge-1.21.1-4.1.0.8.jar"
        expectedSha512 = "9d4b2a1be5139c0fb2fad92ed21805b17d9e83b6ea48e637e018bb14063c1823a206390755dbfe8d025c20fd62ac11cdd84db53ddb956dabaeda01bff57bac50"
    }
)

$dependencyResults = @()
if (-not (Test-Path -LiteralPath $RuntimeDepsDir)) {
    New-Item -ItemType Directory -Path $RuntimeDepsDir | Out-Null
}
foreach ($dependency in $downloadedDependencies) {
    $dependencySourceJar = Join-Path $RuntimeDepsDir $dependency.fileName
    if (-not (Test-Path -LiteralPath $dependencySourceJar)) {
        Write-Host "DOWNLOADING: $($dependency.fileName)"
        Invoke-WebRequest -Uri $dependency.url -OutFile $dependencySourceJar
    }

    $sha512 = Get-FileSha512 -Path $dependencySourceJar
    if ($sha512 -ne $dependency.expectedSha512) {
        throw "SHA-512 mismatch for $($dependency.fileName)."
    }

    $installResult = Install-VerifiedJar `
        -SourceJar $dependencySourceJar `
        -TargetDirectory $resolvedModsDir.Path `
        -ModId $dependency.modId `
        -ExpectedVersion $dependency.expectedVersion `
        -AllowFileJarVersionPlaceholder
    Assert-InstallResult -Result $installResult

    $installResult["sourceSha512"] = $sha512
    $installResult["expectedSha512"] = $dependency.expectedSha512
    $installResult["sha512Match"] = ($sha512 -eq $dependency.expectedSha512)
    $dependencyResults += $installResult
}

$previousProjectJars = @(Find-JarsByPrimaryModId -Directory $resolvedModsDir.Path -ModId $modId)
$projectInstall = Install-VerifiedJar `
    -SourceJar $sourceJar `
    -TargetDirectory $resolvedModsDir.Path `
    -ModId $modId `
    -ExpectedVersion $modVersion
Assert-InstallResult -Result $projectInstall
$projectInstall["resourceCounts"] = Get-ResourceCounts -JarPath $projectInstall.installedJar

$existingDependencyResults = @()
$existingDependencyResults += Verify-ExistingDependency -Directory $resolvedModsDir.Path -ModId "farmersdelight" -ExpectedVersion $props["farmersdelight_version"]
$existingDependencyResults += Verify-ExistingDependency -Directory $resolvedModsDir.Path -ModId "immersiveengineering" -ExpectedVersion $props["immersiveengineering_version"]

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
    copiedRuntimeDependencies = $dependencyResults
    existingRuntimeDependencies = $existingDependencyResults
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
