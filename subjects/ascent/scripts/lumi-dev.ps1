# tiger's development launcher: pull the latest master, install dependencies if they changed, then run the app.
# Usage: double-click "启动 Lumi（开发版）.cmd" in the repo root, or run this script in PowerShell.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

# Node 24 only honours HTTPS_PROXY when this is set (this computer goes through a local proxy).
$env:NODE_USE_ENV_PROXY = "1"

$lockBefore = (Get-FileHash pnpm-lock.yaml).Hash
Write-Host "拉取最新代码..." -ForegroundColor Magenta
git pull --ff-only
if ($LASTEXITCODE -ne 0) { Write-Warning "拉取失败（可能没联网或本地有改动），用当前代码继续运行。" }

if (-not (Test-Path node_modules) -or (Get-FileHash pnpm-lock.yaml).Hash -ne $lockBefore) {
  Write-Host "依赖有变化，安装中..." -ForegroundColor Magenta
  pnpm install
}

Write-Host "编译并启动拾阶..." -ForegroundColor Magenta
pnpm tauri dev
