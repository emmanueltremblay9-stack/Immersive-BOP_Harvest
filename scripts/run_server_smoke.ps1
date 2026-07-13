[CmdletBinding()]
param(
    [ValidateRange(30, 600)]
    [int]$ReadyTimeoutSeconds = 180
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$proofDir = Join-Path $projectRoot "build\server-smoke"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$versionLine = Select-String -LiteralPath (Join-Path $projectRoot "gradle.properties") -Pattern '^mod_version=' | Select-Object -First 1
if ($null -eq $versionLine) {
    throw "mod_version is missing from gradle.properties"
}
$modVersion = ($versionLine.Line -split '=', 2)[1].Trim()
$safeVersion = $modVersion -replace '[^A-Za-z0-9._-]', '_'
$stdoutPath = Join-Path $proofDir "runServer-$safeVersion-$timestamp.out.log"
$stderrPath = Join-Path $proofDir "runServer-$safeVersion-$timestamp.err.log"
$minecraftLog = Join-Path $projectRoot "run\logs\latest.log"

New-Item -ItemType Directory -Force -Path $proofDir | Out-Null

$startTime = Get-Date
$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = "$env:SystemRoot\System32\cmd.exe"
$startInfo.Arguments = '/d /s /c ".\gradlew.bat --no-daemon runServer --stacktrace"'
$startInfo.WorkingDirectory = $projectRoot
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true

$process = [System.Diagnostics.Process]::new()
$process.StartInfo = $startInfo
if (-not $process.Start()) {
    throw "Failed to start Gradle runServer"
}

$stdoutTask = $process.StandardOutput.ReadToEndAsync()
$stderrTask = $process.StandardError.ReadToEndAsync()
$ready = $false
$deadline = $startTime.AddSeconds($ReadyTimeoutSeconds)

while ((Get-Date) -lt $deadline -and -not $process.HasExited) {
    if (Test-Path -LiteralPath $minecraftLog) {
        $logFile = Get-Item -LiteralPath $minecraftLog
        if ($logFile.LastWriteTime -ge $startTime) {
            $ready = [bool](Select-String -LiteralPath $minecraftLog -Pattern "Done \(" -Quiet)
            if ($ready) {
                break
            }
        }
    }
    Start-Sleep -Milliseconds 500
}

$forcedTermination = $false
if ($ready -and -not $process.HasExited) {
    Start-Sleep -Seconds 2
    & "$env:SystemRoot\System32\taskkill.exe" /PID $process.Id /T /F | Out-Null
    $forcedTermination = $true
    $process.WaitForExit()
}

if (-not $ready -and -not $process.HasExited) {
    & "$env:SystemRoot\System32\taskkill.exe" /PID $process.Id /T /F | Out-Null
    $forcedTermination = $true
    $process.WaitForExit()
}

$stdout = $stdoutTask.GetAwaiter().GetResult()
$stderr = $stderrTask.GetAwaiter().GetResult()
[System.IO.File]::WriteAllText($stdoutPath, $stdout, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText($stderrPath, $stderr, [System.Text.UTF8Encoding]::new($false))

if (-not $ready) {
    Write-Error "SERVER SMOKE: ready marker was not observed within $ReadyTimeoutSeconds seconds. Logs: $stdoutPath / $stderrPath"
    exit 1
}
if ($process.ExitCode -ne 0 -and -not $forcedTermination) {
    Write-Error "SERVER SMOKE: Gradle exited with $($process.ExitCode). Logs: $stdoutPath / $stderrPath"
    exit $process.ExitCode
}

Write-Output "SERVER SMOKE: PASSED"
Write-Output "READY MARKER: Done ("
Write-Output "SHUTDOWN MODE: $(if ($forcedTermination) { 'bounded process-tree termination after ready marker' } else { 'process exited normally' })"
Write-Output "GRADLE PROCESS EXIT: $($process.ExitCode)"
Write-Output "STDOUT: $stdoutPath"
Write-Output "STDERR: $stderrPath"
exit 0
