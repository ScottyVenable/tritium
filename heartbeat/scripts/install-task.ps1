# Registers the Windows scheduled task `TritiumBridge`.
# First run = 5 minutes from now, then every 30 minutes.
param(
  [string]$TaskName = "TritiumBridge",
  [int]$IntervalMinutes = 30
)

$ErrorActionPreference = "Continue"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonExe) { throw "python.exe not found on PATH" }

$startTime = (Get-Date).AddMinutes(5)
$startTimeStr = $startTime.ToString("HH:mm")

$tr = "`"$pythonExe`""
$args = "-m tritium_bridge --tick"

# Remove existing
schtasks /Query /TN $TaskName 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
  schtasks /Delete /TN $TaskName /F | Out-Null
}

schtasks /Create `
  /TN $TaskName `
  /TR "$tr $args" `
  /SC MINUTE `
  /MO $IntervalMinutes `
  /ST $startTimeStr `
  /RL LIMITED `
  /F `
  /SD (Get-Date).ToString("MM/dd/yyyy")

# Set the working directory via a brief XML edit so the task runs from the repo root.
$xmlPath = Join-Path $env:TEMP "$TaskName.xml"
schtasks /Query /TN $TaskName /XML | Out-File -Encoding Unicode $xmlPath
[xml]$x = Get-Content $xmlPath
$ns = New-Object Xml.XmlNamespaceManager($x.NameTable)
$ns.AddNamespace("t", "http://schemas.microsoft.com/windows/2004/02/mit/task")
$exec = $x.SelectSingleNode("//t:Actions/t:Exec", $ns)
$wd = $x.CreateElement("WorkingDirectory", $ns.LookupNamespace("t"))
$wd.InnerText = $repoRoot
$exec.AppendChild($wd) | Out-Null
$x.Save($xmlPath)
schtasks /Delete /TN $TaskName /F | Out-Null
schtasks /Create /TN $TaskName /XML $xmlPath /F | Out-Null

Write-Host "Registered scheduled task '$TaskName'."
Write-Host "First run: $startTime"
Write-Host "Interval : every $IntervalMinutes minutes"
schtasks /Query /TN $TaskName /V /FO LIST | Select-String -Pattern "TaskName|Next Run|Status|Last Run|Working"
