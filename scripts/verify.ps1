$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Resolve-Path (Join-Path $here '..')
Set-Location (Join-Path $root 'runtime\server')
if (-not (Test-Path 'node_modules')) {
  npm install --no-audit --no-fund
}
node src/verify.js
