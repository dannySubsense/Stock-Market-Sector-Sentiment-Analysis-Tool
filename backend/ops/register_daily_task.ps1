# backend/ops/register_daily_task.ps1
param(
  [string]$Time = "04:00",                 # local time
  [string]$Days = "MON,TUE,WED,THU,FRI"    # weekdays
)
$script = Resolve-Path (Join-Path $PSScriptRoot "run_daily_1d.ps1")
$cmd = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$script`""
schtasks /Create /TN "SMSA 1D Daily" /TR "$cmd" /SC WEEKLY /D $Days /ST $Time /RL LIMITED
