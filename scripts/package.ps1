# Build the Tritium pre-release zip + SHA-256 checksum.
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Resolve-Path (Join-Path $here '..')
Set-Location $root

$pkgJson = Get-Content (Join-Path $root 'runtime\server\package.json') -Raw | ConvertFrom-Json
$version = if ($pkgJson.version) { $pkgJson.version } else { '0.1.0' }

$dist = Join-Path $root 'dist'
New-Item -ItemType Directory -Path $dist -Force | Out-Null
$out = Join-Path $dist "tritium-v$version.zip"
if (Test-Path $out) { Remove-Item $out }

# Build a temp staging directory to control exclusions, then zip.
$staging = Join-Path $env:TEMP "tritium-stage-$([Guid]::NewGuid())"
$pkgName = Split-Path $root -Leaf
$copyTarget = Join-Path $staging $pkgName
robocopy $root $copyTarget /MIR `
  /XD dist node_modules .tritium .tritium-verify `
  /XF *.bak | Out-Null

Compress-Archive -Path $copyTarget -DestinationPath $out
Remove-Item -Recurse -Force $staging

$hash = (Get-FileHash $out -Algorithm SHA256).Hash.ToLower()
"$hash  $(Split-Path $out -Leaf)" | Out-File "$out.sha256" -Encoding ascii

Get-Item $out, "$out.sha256" | Format-Table Name, Length
