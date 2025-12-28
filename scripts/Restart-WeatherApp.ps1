$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$taskName = "WeatherApp"

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

$envFile = Join-Path $repoRoot ".env"
$port = if ($env:PORT) { $env:PORT } else { Get-EnvValueFromFile -Path $envFile -Name "PORT" }
if (-not $port) {
    $port = "4200"
}

$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Host "ERROR: Scheduled task '$taskName' not found." -ForegroundColor Red
    exit 1
}

Write-Host "Stopping scheduled task '$taskName'..." -ForegroundColor Yellow
Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

$pids = @()

try {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        $pids += $connections | Select-Object -ExpandProperty OwningProcess
    }
} catch {
    # Ignore if Get-NetTCPConnection is unavailable.
}

$pythonMatches = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object {
        $_.CommandLine -and
        $_.CommandLine -like "*waitress*" -and
        $_.CommandLine -like "*$port*"
    }
if ($pythonMatches) {
    $pids += $pythonMatches | Select-Object -ExpandProperty ProcessId
}

$pids = $pids | Sort-Object -Unique

if ($pids.Count -gt 0) {
    Write-Host "Stopping process id(s): $($pids -join ', ')" -ForegroundColor Yellow
    foreach ($pid in $pids) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "No running Weather App process found on port $port." -ForegroundColor Gray
}

Write-Host "Starting scheduled task '$taskName'..." -ForegroundColor Yellow
Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
Write-Host "Weather App restarted." -ForegroundColor Green
