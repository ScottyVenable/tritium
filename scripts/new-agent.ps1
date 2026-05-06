# Scaffold a new Tritium agent (PowerShell).
#   .\new-agent.ps1 -Name <name> -Role "<role description>"
param(
  [Parameter(Mandatory)] [string] $Name,
  [Parameter(Mandatory)] [string] $Role
)

$ErrorActionPreference = 'Stop'
if ($Name -notmatch '^[a-z][a-z0-9-]{1,30}$') {
  Write-Error "name must match ^[a-z][a-z0-9-]{1,30}$"; exit 1
}
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Resolve-Path (Join-Path $here '..')
$agentdir = Join-Path $root "agents\$Name"
if (Test-Path $agentdir) { Write-Error "agent '$Name' already exists"; exit 2 }

$Display = $Name.Substring(0,1).ToUpper() + $Name.Substring(1)

New-Item -ItemType Directory -Force -Path `
  "$agentdir\memory\repo", "$agentdir\memory\session", "$agentdir\memory\personal", `
  "$agentdir\portfolio", "$agentdir\prompts" | Out-Null

@"
---
name: $Display
role: $Role
voice: TODO
emoji_policy: none
---

# $Display — $Role

TODO — fill in voice, posture, allowed/disallowed, coordination, non-negotiables.

— $Display
"@ | Out-File -Encoding utf8 "$agentdir\agent.md"

@"
# $Display — Memory
See team\TEAM.md for memory conventions.
— $Display
"@ | Out-File -Encoding utf8 "$agentdir\MEMORY.md"

@"
# $Display — Portfolio
On task completion, classify each file as keep | promote | drop.
— $Display
"@ | Out-File -Encoding utf8 "$agentdir\PORTFOLIO.md"

@"
# System prompt — $Display
You are **$Display**, a member of the Tritium multi-agent crew.
Read your role definition from agents\$Name\agent.md.
At every checkpoint, run: tritium inbox check --agent $Name
— $Display
"@ | Out-File -Encoding utf8 "$agentdir\prompts\system.md"

# Copy prompt into adapters that have per-agent prompts.
foreach ($adapter in @('claude-cli','gemini-cli')) {
  $d = Join-Path $root "adapters\$adapter\agents"
  if (Test-Path $d) {
    Copy-Item "$agentdir\agent.md" (Join-Path $d "$Name.md") -Force
    Write-Host "  registered in adapters/$adapter/"
  }
}

# Copilot-local uses Display-cased file names.
$copilotLocal = Join-Path $root "adapters\github-copilot-local\.github\agents"
if (Test-Path $copilotLocal) {
  Copy-Item "$agentdir\agent.md" (Join-Path $copilotLocal "$Display.agent.md") -Force
  Write-Host "  registered in adapters/github-copilot-local/"
}

Write-Host "[tritium] new agent '$Name' scaffolded at $agentdir"
Write-Host "Manual follow-ups: edit agent.md, update team\TEAM.md handoff matrix, tune SETTINGS.example.jsonc."
