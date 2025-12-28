$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
Set-Location $repoRoot

$envFile = Join-Path $repoRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            return
        }
        if ($line.StartsWith("export ")) {
            $line = $line.Substring(7).Trim()
        }
        $parts = $line -split "=", 2
        if ($parts.Length -ne 2) {
            return
        }
        $name = $parts[0].Trim()
        $value = $parts[1].Trim()
        if (
            ($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))
        ) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        if (-not [System.Environment]::GetEnvironmentVariable($name)) {
            [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

$port = if ($env:PORT) { $env:PORT } else { "4200" }

python -m waitress --listen=0.0.0.0:$port app:app
