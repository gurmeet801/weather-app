$ErrorActionPreference = "Stop"

[CmdletBinding()]
param(
    [string]$Url,
    [int]$TimeoutSeconds = 10
)

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

if (-not $Url) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $repoRoot = Split-Path -Parent $scriptDir
    $envFile = Join-Path $repoRoot ".env"
    $port = if ($env:WEATHER_APP_PORT) { $env:WEATHER_APP_PORT } else { Get-EnvValueFromFile -Path $envFile -Name "WEATHER_APP_PORT" }
    if (-not $port) {
        $port = "4200"
    }
    $Url = "http://localhost:$port/warm"
}

try {
    if ([Net.SecurityProtocolType]::Tls12) {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    }
} catch {
    # Ignore TLS setting failures.
}

try {
    $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec $TimeoutSeconds -Headers @{
        "User-Agent" = "WeatherAppWarmPing/1.0"
    }
    if ($response.StatusCode) {
        Write-Host "Ping ok ($($response.StatusCode))"
    } else {
        Write-Host "Ping ok"
    }
} catch {
    Write-Host "Ping failed: $($_.Exception.Message)"
}
