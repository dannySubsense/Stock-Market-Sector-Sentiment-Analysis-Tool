# backend/ops/run_daily_1d.ps1
$ErrorActionPreference = "Stop"
# Resolve project root from this script location
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$python = "python"   # or set to full path/venv python
$logDir = Join-Path $root "logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$log = Join-Path $logDir ("daily_1d_{0}.log" -f (Get-Date -Format yyyyMMdd))
Set-Location $root

# Step 1: Universe (does not truncate; upserts + maintains is_active)
& $python "backend/ops/run_step1_populate_universe.py" *>&1 | Tee-Object -FilePath $log -Append
Start-Sleep -Seconds 120
# Step 2: Prices (FMP batch)
& $python "backend/ops/populate_stock_prices_1d.py" *>&1 | Tee-Object -FilePath $log -Append
Start-Sleep -Seconds 60
# Step 3/4: SMA 1D pipeline (sentiment + gappers)
& $python "backend/ops/run_sma_1d_once.py" *>&1 | Tee-Object -FilePath $log -Append
