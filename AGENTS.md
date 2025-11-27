# Repository Guidelines

## Project Structure & Module Organization
- `web/`: Next.js 14 app router (`src/app` pages, `src/components` UI, `src/lib` helpers) with Tailwind + shadcn/ui.
- `sql/`: Core schema (`schema.sql`), propagation routines, and sectorized loaders; document any DB change.
- `amenazas/`, `infraestructura/`, `metadata/`: ETL scripts and loaders for threats, network, and contextual layers; orchestrated by `main.py`.
- `optimization/`, `model/`, `docs/`, `assets/`: Algorithm experiments, model artifacts, documentation, and static assets.
- Root Python utilities (`load_to_supabase*.py`, `verify_propagation.py`) read Supabase/postgres vars from `.env`.

## Build, Test, and Development Commands
- Backend/ETL: `pip install -r requirements.txt`, then `python main.py` for the full ETL; `python load_to_supabase.py` pushes generated outputs.
- Web install: `cd web && npm install` (npm is canonical; keep `package-lock.json`).
- Web dev: `cd web && npm run dev` at http://localhost:3000.
- Web build: `cd web && npm run build`; serve prod with `npm start`.
- Lint: `cd web && npm run lint` (Next.js/ESLint). No formal Python lint—follow PEP 8.
- Containers: `docker compose -f docker/docker-compose.yml up` to run services; stop with `down`.

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indent, type hints when useful. `snake_case` for functions/vars; keep ETL steps small and logged.
- TypeScript/React: Functional components with hooks; `PascalCase` components, `camelCase` props/state; helpers in `src/lib`. Keep Tailwind classes grouped by purpose.
- SQL: lower_snake_case identifiers (e.g., `infra_nodos`, `p_fallo`), add brief comments for non-obvious transforms.
- Env/config: derive from `.env.example` and `web/.env.local.example`; never commit secrets.

## Testing Guidelines
- Frontend gate: `npm run lint` must pass. For UI/logic changes, exercise flows in `web/src/app/page.tsx` (routing, threat toggles) and attach screenshots for map/UI tweaks.
- API smoke: with the dev server running, `python verify_propagation.py` hits `/api/simulate-failures` to confirm propagation responds.
- ETL validation: ensure `main.py` finishes cleanly and loader outputs match expected row counts before loading to Supabase.

## Commit & Pull Request Guidelines
- Commits: short, imperative subjects with a type when helpful (`feat: add resilient cost slider`, `fix: handle one-way edges`, `chore: update threats loader`). Keep scope narrow.
- PRs: include a summary, affected areas (ETL, SQL, web UI), testing performed (`npm run lint`, manual flows), linked issue/task, and screenshots or before/after notes for UI changes. Mention any required env or data refresh steps.
