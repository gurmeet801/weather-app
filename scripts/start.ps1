$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
Set-Location $repoRoot

$env:WEATHER_GOV_USER_AGENT = "weather-app (gsinghjk@gmail.com)"

$env:FLASK_DEBUG = "0"

$port = if ($env:PORT) { $env:PORT } else { "4200" }

python -m waitress --listen=0.0.0.0:$port app:app
