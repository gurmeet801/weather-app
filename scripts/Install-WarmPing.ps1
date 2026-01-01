#
# Install-WarmPing.ps1
# Creates Windows Task Scheduler task to keep the Weather app warm.
# Run as Administrator
#
# Usage:
#   .\scripts\Install-WarmPing.ps1
#   .\scripts\Install-WarmPing.ps1 -IntervalMinutes 15
#   .\scripts\Install-WarmPing.ps1 -UserName "DOMAIN\\user"
#   .\scripts\Install-WarmPing.ps1 -Force

[CmdletBinding()]
param(
    [int]$IntervalMinutes = 15,
    [string]$UserName,
    [string]$Password,
    [string]$TaskName = "WeatherAppWarmPing",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$PingScript = Join-Path $ProjectRoot "scripts\warm-ping.ps1"
function Get-EnvValueFromFile {
    param(
        [string]$Path,
        [string]$Name
    )

    if (-not (Test-Path $Path)) {
        return $null
    }

    foreach ($line in Get-Content $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }
        if ($trimmed.StartsWith("export ")) {
            $trimmed = $trimmed.Substring(7).Trim()
        }
        $parts = $trimmed -split "=", 2
        if ($parts.Length -ne 2) {
            continue
        }
        $key = $parts[0].Trim()
        $value = $parts[1].Trim()
        if (
            ($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))
        ) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        if ($key -ieq $Name) {
            return $value
        }
    }

    return $null
}

if (-not (Test-Path $PingScript)) {
    Write-Host "ERROR: Ping script not found: $PingScript" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Install Weather App Warm Ping Task" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

if ($IntervalMinutes -lt 1) {
    Write-Host "ERROR: IntervalMinutes must be at least 1." -ForegroundColor Red
    exit 1
}

if (-not $UserName) {
    $UserName = (whoami)
}

$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    if (-not $Force) {
        Write-Host "Task '$TaskName' already exists (state: $($existingTask.State))." -ForegroundColor Yellow
        Write-Host "Use -Force to reinstall." -ForegroundColor Yellow
        exit 0
    }
    Write-Host "Removing existing task (force reinstall)..." -ForegroundColor Yellow
    if ($existingTask.State -eq "Running") {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    }
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$startTime = (Get-Date).AddMinutes(1)
$envFile = Join-Path $ProjectRoot ".env"
$port = if ($env:PORT) { $env:PORT } else { Get-EnvValueFromFile -Path $envFile -Name "PORT" }
if (-not $port) {
    $port = "4200"
}
$url = "http://localhost:$port/warm"

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$PingScript`"" `
    -WorkingDirectory $ProjectRoot

$trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At $startTime `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -RepetitionDuration (New-TimeSpan -Days 1)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -MultipleInstances IgnoreNew

try {
    if (-not $Password) {
        $Password = Read-Host -Prompt "Enter password for $UserName"
    }

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -RunLevel Highest `
        -User $UserName `
        -Password $Password `
        -Description "Pings the Weather App /warm endpoint every $IntervalMinutes minutes." `
        -ErrorAction Stop | Out-Null

    Write-Host "Task '$TaskName' created successfully" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor White
    Write-Host "  Url:            $url" -ForegroundColor Gray
    Write-Host "  Interval:       $IntervalMinutes minutes" -ForegroundColor Gray
    Write-Host "  Script:         $PingScript" -ForegroundColor Gray
    Write-Host "  Trigger:        Every $IntervalMinutes minutes" -ForegroundColor Gray
    Write-Host ""

    $startNow = Read-Host "Start the task now? (y/N)"
    if ($startNow -eq 'y' -or $startNow -eq 'Y') {
        Write-Host "Starting task..." -ForegroundColor Yellow
        Start-ScheduledTask -TaskName $TaskName -ErrorAction Stop
        Write-Host "Task started" -ForegroundColor Green
    }
} catch {
    Write-Host "ERROR: Failed to create task: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Management commands:" -ForegroundColor White
Write-Host "  Start:   Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  Stop:    Stop-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  Status:  Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  Remove:  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Gray
Write-Host ""
