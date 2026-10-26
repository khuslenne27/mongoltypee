$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot 'frontend')
if (-not (Test-Path 'node_modules\next\package.json')) {
    npm ci
    if ($LASTEXITCODE -ne 0) { throw 'npm ci failed.' }
}
npm run dev
