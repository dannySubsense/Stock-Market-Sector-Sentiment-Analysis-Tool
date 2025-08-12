Operational helpers for the 1D production pipeline (FMP-based).

Scripts
- Step 1: run_step1_populate_universe.py
- Step 2: populate_stock_prices_1d.py
- Step 3/4: run_sma_1d_once.py (writes sector_sentiment_1d and sector_gappers_1d)
- Verify: verify_stock_prices_1d.py
- Orchestrator: run_daily_1d.ps1 (runs Step 123/4 and logs to ./logs)
- Scheduler helper: register_daily_task.ps1 (creates a weekday 4:00 AM task)

Notes
- UniverseBuilder does NOT truncate stock_universe; it upserts and maintains is_active.
- To fully reset tables, use clean_*.py in backend/ (or empty_all_tables.py) manually.

Usage (from project root)
- python backend/ops/run_step1_populate_universe.py
- python backend/ops/populate_stock_prices_1d.py
- python backend/ops/run_sma_1d_once.py
- python backend/ops/verify_stock_prices_1d.py

Scheduling (Windows)
- powershell -NoProfile -ExecutionPolicy Bypass -File backend/ops/register_daily_task.ps1 -Time 04:00 -Days MON,TUE,WED,THU,FRI
