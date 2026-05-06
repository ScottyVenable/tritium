# Install a Tritium adapter into a target repo (PowerShell).
#
#   .\install.ps1 -Target <path> -Adapter <name>

param(
  [Parameter(Mandatory)] [string] $Target,
  [Parameter(Mandatory)] [string] $Adapter
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Resolve-Path (Join-Path $here '..')
$src  = Join-Path $root "adapters\$Adapter"

if (-not (Test-Path $src)) {
  Write-Error "unknown adapter '$Adapter' (looked in $src)"
  exit 2
}

$Target = (Resolve-Path $Target).Path
Write-Host "[tritium] installing $Adapter into $Target"

Get-ChildItem -Path $src -Recurse -File | ForEach-Object {
  $rel = $_.FullName.Substring($src.Length + 1)
  if ($rel -eq 'README.md') { return }
  $dest = Join-Path $Target $rel
  $destDir = Split-Path -Parent $dest
  if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir | Out-Null }
  if (Test-Path $dest) {
    Copy-Item -Force $dest "$dest.bak"
    Write-Host "  preserved $rel  ->  $rel.bak"
  }
  Copy-Item $_.FullName $dest -Force
  Write-Host "  installed $rel"
}
Write-Host "[tritium] done."
