# Запуск Telegram-бота на Windows (вне Docker) — использует VPN/сеть ПК, а не контейнера.
# Перед запуском: docker compose up  (без профиля docker-bot)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$envFile = Join-Path $Root ".env"
if (-not (Test-Path $envFile)) {
    Write-Error "Нет файла .env в корне проекта. Скопируйте .env.example"
}

Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    $pair = $_ -split '=', 2
    if ($pair.Count -eq 2) {
        $name = $pair[0].Trim()
        $value = $pair[1].Trim()
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

$env:API_BASE_URL = "http://localhost:8000"

if (-not $env:TELEGRAM_BOT_TOKEN) {
    Write-Error "TELEGRAM_BOT_TOKEN не задан в .env"
}
if (-not $env:INTERNAL_BOT_SECRET) {
    Write-Error "INTERNAL_BOT_SECRET не задан в .env"
}

Write-Host "API: $env:API_BASE_URL"
if ($env:TELEGRAM_PROXY_URL) {
    Write-Host "Proxy: $env:TELEGRAM_PROXY_URL"
}

$venvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    & $venvPython -m bot.main
} else {
    python -m bot.main
}
