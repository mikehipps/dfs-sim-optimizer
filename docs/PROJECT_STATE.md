# DFS Sim Optimizer — Project State

## What’s built (backend)
- FastAPI service with:
  - Inputs: `POST /slates/{slate_id}/projections(.csv)`, `POST /slates/{slate_id}/ownership(.csv)`, `GET /slates/{slate_id}/inputs`
  - Sampler test: `GET /slates/{slate_id}/sample-lineup?salary_cap=&min_stack=`
  - Runs: `POST /runs` (fields: slate_id, pool_size, salary_cap, min_stack, n_sims, field_size, corr_sigma), `GET /runs`, `GET /runs/{id}`, `GET /runs/{id}/lineups`, `GET /runs/{id}/metrics`, `GET /runs/{id}/simstats`
  - Exports: `GET /exports/{id}/fd-stub?n=`, `GET /exports/{id}/top-by-sim?n=`
- Pool builder: contest-legal MLB roster (FD-style), min stack, salary cap, dedupe.
- Metrics: proj summary + lineup table with value/z/rank.
- Simulator: per-lineup outcomes with `n_sims`, `field_size`, correlation σ; returns mean/stdev/top50/top10/top1.
- Artifacts under `app/runs/`:  
  - `<id>.json` (run record), `<id>_pool.json`, `<id>_metrics.json`, `<id>_simstats.json`, CSV exports.

## What’s built (frontend)
- `/` Home: knobs = slate, pool size, salary cap, min stack, n sims, field size, corr σ; progress bar + CSV export link.
- `/runs`: recent runs; load **Lineups**, **Metrics**, **Simstats**; **Top-by-Sim (N)** download.

## How to run
- Backend: `uvicorn app.main:app --reload` → http://127.0.0.1:8000/docs
- Frontend: `npm run dev` in `web` → http://localhost:3000

## Known limitations (next up)
- No `site` selector (FD vs DK roster); exports are stubs except top-by-sim CSV.
- No matchup data → `avoid_hvp` placeholder.
- No UI filters/exposures/pruning yet.
