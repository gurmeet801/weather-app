# Install-WeatherApp.ps1
# Creates Windows Task Scheduler task for the Weather App
# Run as Administrator
#
# Usage:
#   .\scripts\Install-WeatherApp.ps1                       # Install for current user (prompt for password)
#   .\scripts\Install-WeatherApp.ps1 -UserName "DOMAIN\\user"
#   .\scripts\Install-WeatherApp.ps1 -Force                # Force reinstall

[CmdletBinding()]
param(
    [string]$UserName,
    [string]$Password,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$TaskName = "WeatherApp"
$StartScript = Join-Path $ProjectRoot "scripts\start.ps1"

if (-not $UserName) {
    $UserName = (whoami)
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Install Weather App Startup Task" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Check if start script exists
if (-not (Test-Path $StartScript)) {
    Write-Host "ERROR: Start script not found: $StartScript" -ForegroundColor Red
    exit 1
}

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    Write-Host "WARNING: 'python' was not found in PATH. Ensure Python or a venv is available for scripts\\start.ps1." -ForegroundColor Yellow
    Write-Host ""
}

# Check for existing task
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

# Create the scheduled task action - run PowerShell with the start script
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$StartScript`"" `
    -WorkingDirectory $ProjectRoot

# Trigger: At logon for the specified user
$trigger = New-ScheduledTaskTrigger -AtLogon -User $UserName

# Settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -MultipleInstances IgnoreNew

# Register the task
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
        -Description "Starts the Weather App (Flask/Waitress) at user logon." `
        -ErrorAction Stop | Out-Null

    Write-Host "Task '$TaskName' created successfully" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor White
    Write-Host "  Script:         $StartScript" -ForegroundColor Gray
    Write-Host "  Working Dir:    $ProjectRoot" -ForegroundColor Gray
    Write-Host "  Trigger:        At logon for user $UserName" -ForegroundColor Gray
    Write-Host ""

    # Ask to start the task now
    $startNow = Read-Host "Start the app now? (y/N)"
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
