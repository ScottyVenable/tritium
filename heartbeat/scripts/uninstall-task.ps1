param([string]$TaskName = "TritiumBridge")
schtasks /Delete /TN $TaskName /F
