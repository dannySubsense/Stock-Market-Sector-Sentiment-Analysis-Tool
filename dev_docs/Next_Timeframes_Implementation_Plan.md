### Purpose
Single handoff document to continue work in a new chat. Summarizes what we changed, the current behavior, and a precise, sequential plan to add the remaining timeframes (3-day, 1-week, 30-minute) without breaking the sector-first architecture.

### What We Changed This Session
- Backend dev server
  - Updated root `package.json` to launch uvicorn with `--app-dir backend` and `-k` for process-tree cleanup.
  - Added `dev:clean` script to kill any listener on port 8000.
- CORS/Frontend
  - `backend/main.py`: allow origins `http://localhost:3000` and `http://127.0.0.1:3000`.
  - `frontend/components/SectorGrid.tsx`: introduced `API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'` for configurable backend URL; rewired initial fetch and recompute POST to use `API_BASE`.

### Current Behavior Snapshot
- Initial load: UI calls `GET /api/sectors/1day/` to read the latest persisted 1D batch from DB. No external fetch occurs.
- Refresh: UI `POST /api/sectors/1day/recompute` schedules background fetch + 1D pipeline; UI polls for a new batch timestamp, then refetches the 1D data.
- Weighted toggle: UI `GET /api/sectors/1day/?calc=weighted` computes on-the-fly from DB (no persistence, no external fetch).

### Dev Commands (PowerShell)
- Start: `npm run dev` (use `npm run dev:clean` first if needed)
- Lint/Format: `npm run lint`, `npm run format`
- Tests (Python): `cd backend; python -m pytest -k <one_test>`

### Branching Strategy (One-at-a-time)
- Each timeframe is implemented on its own branch and merged independently:
  - `feat/timeframe-3day`
  - `feat/timeframe-1week`
  - `feat/timeframe-30min`
  - Use Conventional Commits; prefer “Squash and merge.”

### SDD Alignment Requirements (Keep These Invariant)
- Preserve sector-first flow: Sector Grid → Multi-Timeframe Analysis → Stock Rankings.
- Maintain 11 FMP sectors + 1 theme slot on the UI; top 3 bullish/bearish per sector.
- Support timeframes: 30min, 1D, 3D, 1W; extend hours capability and 30-minute refresh cycles.
- Keep modular layering: `services/`, `mcp/`, `agents/`, `components/`.

### Operational constants and conventions (make-or-break details)
- Recompute API
  - Enabled: `enable_recompute_api = True`
  - Auth header: `X-Admin-Token: <ADMIN_RECOMPUTE_TOKEN>`
  - Backend reads token from environment `ADMIN_RECOMPUTE_TOKEN`; frontend optionally from `NEXT_PUBLIC_ADMIN_RECOMPUTE_TOKEN`.
- Cooldown policy (hard/soft + boundary scheduling)
  - 30min:
    - Hard cooldown: 10 minutes (600s). Requests within 10 minutes of last complete batch return 429.
    - Soft window: 30 minutes cadence aligned to clock (:00, :30). If last run < 30 minutes but ≥ 10 minutes and no job is running, accept and run now; else schedule for next boundary and return 202 with ETA.
  - 1day:
    - Hard cooldown: 15 minutes (900s).
    - Soft window: 60 minutes during market hours. If <60m but ≥15m, accept and run now; else 202 schedule at next 15‑minute bucket. End-of-day finalize after close.
  - 3day:
    - Hard cooldown: 2 hours (7200s).
    - Soft window: 6 hours. If <6h but ≥2h, accept; else 202 schedule next 6h bucket.
  - 1week:
    - Hard cooldown: 6 hours (21600s).
    - Soft window: 24 hours. If <24h but ≥6h, accept; else 202 schedule next 24h bucket.
- Staleness thresholds (for `metadata.is_stale` and `age_minutes` guidance):
  - 30min: 60 minutes
  - 1day: 60 minutes
  - 3day: 24 hours
  - 1week: 72 hours
- Table retention policies (TimescaleDB):
  - `sector_sentiment_30m`: keep 7 days; compress after 2 days
  - `sector_sentiment_1d`: keep 90 days; compress after 7 days
  - `sector_sentiment_3d`: keep 180 days; compress after 14 days
  - `sector_sentiment_1w`: keep 365 days; compress after 30 days
- SQL migration naming (one file per timeframe):
  - `backend/database/migrations/2025MMDD_add_sector_sentiment_3d.sql`
  - `backend/database/migrations/2025MMDD_add_sector_sentiment_1w.sql`
  - `backend/database/migrations/2025MMDD_add_sector_sentiment_30m.sql`
  - Each migration includes table creation, indexes, hypertable, retention, compression.
- Endpoint naming (exact):
  - 3D: `GET /api/sectors/3day/`, `POST /api/sectors/3day/recompute`
  - 1W: `GET /api/sectors/1week/`, `POST /api/sectors/1week/recompute`
  - 30M: `GET /api/sectors/30min/`, `POST /api/sectors/30min/recompute`
- Frontend environment:
  - Ensure `API_BASE` is used in all requests, including the polling helper; avoid hardcoded localhost.

### Recompute API behavior (detailed)
- Request: `POST /api/sectors/{timeframe}/recompute[?force=true]`
  - Requires `X-Admin-Token` header if configured.
  - `force=true` bypasses the soft window and boundary scheduling (runs immediately) but NEVER bypasses the hard cooldown or an already-running job.
- Responses:
  - 202 Accepted (scheduled or accepted):
    - `{ status: "accepted", timeframe, scheduled_for_iso, eta_minutes, mode: "immediate"|"scheduled" }`
  - 409 Conflict (job already running):
    - `{ status: "running", started_at_iso, timeframe }`
  - 429 Too Many Requests (within hard cooldown):
    - `{ status: "cooldown", retry_after_seconds, last_batch_iso, timeframe }`

### Data Model and Tables (New)
Mirror the 1D persisted batch shape for each timeframe. Create new tables:
- `sector_sentiment_3d`
- `sector_sentiment_1w`
- `sector_sentiment_30m` (TimescaleDB hypertable recommended)

Common columns (align with 1D):
- `id`, `batch_id` (text/uuid), `timestamp` (timestamptz), `timeframe` (enum/text), `sector` (text),
- `sentiment_score` (numeric), `sentiment_normalized` (numeric), `color_classification` (text),
- `trading_signal` (text), `stock_count` (int), `created_at` (timestamptz default now())

Add an SQL migration file per timeframe under `backend/database/` (e.g., `phase_timeframes_extension.sql`).

### Services and Pipelines (New)
- Create Pydantic/SQLAlchemy models mirroring the 1D model:
  - `backend/models/sector_sentiment_3d.py`
  - `backend/models/sector_sentiment_1w.py`
  - `backend/models/sector_sentiment_30m.py`
- Create pipelines (follow `services/sma_1d_pipeline.py` patterns):
  - `backend/services/sma_3d_pipeline.py`
  - `backend/services/sma_1w_pipeline.py`
  - `backend/services/sma_30m_pipeline.py`
- Reuse `SectorDataService`, `SectorFilters`, and calculator strategy. For 30m, ensure intraday aggregation is efficient and rate-limited; consider Timescale continuous aggregates if needed.

### API: Endpoints Per Timeframe
Add to `backend/api/routes/sectors.py` with parity to 1D:
- `GET /api/sectors/3day/` and `POST /api/sectors/3day/recompute`
- `GET /api/sectors/1week/` and `POST /api/sectors/1week/recompute`
- `GET /api/sectors/30min/` and `POST /api/sectors/30min/recompute`

Rules:
- `GET` returns the latest complete persisted batch; `?calc=simple|weighted` may preview computed (non-persisted) results if appropriate.
- `POST .../recompute` schedules a background coroutine to fetch prices (batch), compute, and persist to its timeframe table, with cooldown via `DataFreshnessService`.
- Extend `DataFreshnessService` if needed to support timeframe-specific staleness thresholds (e.g., 30m stricter).
  - Implement per-timeframe cooldown using constants above. Return 429 on violation.
  - Implement boundary scheduling and `force=true` behavior as defined above. Include detailed 202/409/429 payloads.

### Frontend: Multi-Timeframe Wiring (Incremental)
- Keep the grid. Update the `timeframe_scores` per card using three extra API reads:
  - `1D` already populated from `/api/sectors/1day/`.
  - `3D`: `GET /api/sectors/3day/`, map normalized score to `timeframe_scores['3day']`.
  - `1W`: `GET /api/sectors/1week/`, map to `timeframe_scores['1week']`.
  - `30M`: `GET /api/sectors/30min/`, map to `timeframe_scores['30min']`.
- Only after each API exists and is green. Maintain `API_BASE` usage everywhere. Change the current poller’s hardcoded URL to use `API_BASE`.

### Testing Gates (Per Timeframe)
- Unit tests co-located near services/calculators.
- Integration tests under `backend/tests/integration/` validating:
  - Batch persistence shape and integrity checks for the timeframe.
  - Freshness service staleness and cooldown behavior.
  - API `GET` returns 11 sectors with metadata; `POST /recompute` enforces token/cooldown.
  - For 30m: verify that recompute within 30 minutes returns 429; verify `is_stale` toggles after threshold passes.
  - Force flag: `force=true` runs immediately when outside hard cooldown and no job running; still 429 if inside hard cooldown; still 409 if job running.
- Run: `black --check`, `flake8`/`ruff`, `mypy`, `pytest` — all green before merging.

### Risks & Mitigations
- Orphan listeners: addressed by `concurrently -k` and `dev:clean`.
- Intraday load (30m): implement strict cooldowns, use batch endpoints to upstream APIs, consider Timescale continuous aggregates for rollups.
- Staleness confusion: surface `metadata.is_stale`, `age_minutes`, and warnings consistently across all timeframes.

### Step-by-Step Plan (Do Not Parallelize)
1) Branch: `git checkout -b feat/timeframe-3day`
2) DB: add migration for `sector_sentiment_3d`; run locally.
3) Models/Services: add 3D models and `sma_3d_pipeline.py` (reuse 1D logic with 3D horizon).
4) API: add `GET /api/sectors/3day/` and `POST /api/sectors/3day/recompute` with freshness + cooldown.
5) Frontend: read 3D endpoint and fill `timeframe_scores['3day']`.
6) Tests: unit + integration; ensure all gates pass.
7) PR: squash-merge.

Next:
8) Repeat for 1W on branch `feat/timeframe-1week`.
9) Repeat for 30M on branch `feat/timeframe-30min` (tighter cooldowns; consider WebSocket later).

### Definition of Done (Per Timeframe)
- New table created and populated by pipeline.
- `GET` and `POST /recompute` endpoints implemented with freshness/cooldown and security.
- Frontend displays the timeframe dot with correct normalized score.
- Gates green: format, lint, type-check, tests.

### Quick Start for the Next Chat
- Paste this file’s “Step-by-Step Plan” and say: “Start with 3-day timeframe (step 1).”
- Provide your DB is up and credentials are set (see `credentials.yml`).
- I will implement step 2 (migration + model stubs) with TDD and proceed sequentially.


