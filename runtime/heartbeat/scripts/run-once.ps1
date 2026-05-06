param(
  [string]$Agent,
  [string]$Action,
  [switch]$DryRun
)
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
  $args = @("-m","tritium_bridge","--tick")
  if ($Agent)  { $args += @("--agent",$Agent) }
  if ($Action) { $args += @("--action",$Action) }
  if ($DryRun) { $args += "--dry-run" }
  python @args
} finally {
  Pop-Location
}
