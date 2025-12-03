# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a resilient urban routing system for flood-prone areas (Phase 3). The project compares 4 routing algorithms considering dynamic failure probabilities based on real threats.

## Common Development Commands

### Frontend Development (Next.js)
```bash
cd web
npm install              # Install dependencies
npm run dev             # Start development server (http://localhost:3000)
npm run build           # Build for production
npm run lint            # Lint the codebase
```

### Backend/ETL Development (Python)
```bash
pip install -r requirements.txt    # Install Python dependencies
python main.py                     # Run complete ETL process
python load_to_supabase.py        # Load generated data to Supabase
```

### Database Operations
```bash
# Apply schema (requires PostgreSQL connection)
psql "postgresql://postgres:PASSWORD@HOST:5432/DATABASE" -f sql/schema.sql

# Calculate probabilities after loading data
psql "postgresql://postgres:PASSWORD@HOST:5432/DATABASE" -f sql/setup_and_calculate_probabilities.sql
```

### Docker Operations
```bash
# Build and run with Docker Compose
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up
docker compose -f docker/docker-compose.yml down
```

## Architecture Overview

### Tech Stack
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui, Leaflet
- **Backend**: PostgreSQL 15+ with PostGIS 3.3+ and pgRouting 3.4+
- **Database**: Supabase (managed PostgreSQL)
- **Optimization**: CPLEX/docplex for MILP optimization
- **Languages**: TypeScript (frontend), Python (ETL/algorithms), SQL (database)

### Core Components

1. **ETL Pipeline** (`main.py` orchestrates):
   - Infrastructure extraction from OpenStreetMap (`infraestructura/osm_infra_etl.py`)
   - Metadata processing (elevation, rainfall, landcover in `metadata/`)
   - Threat data processing (floods, DGA stations, citizen reports in `amenazas/`)
   - Probability calculations (`model/actualizar_probabilidades.py`)

2. **Routing Algorithms** (`optimization/`):
   - Baseline: Classic Dijkstra (shortest path)
   - Resilient: Dijkstra with risk-adjusted costs
   - CPLEX: MILP optimization (global optimal)
   - A*: Metaheuristic with risk heuristic

3. **API Endpoints** (`web/src/app/api/`):
   - `/api/route/baseline` - Classic Dijkstra routing
   - `/api/route/resilient` - Risk-aware Dijkstra
   - `/api/route/optimize` - CPLEX MILP optimization
   - `/api/route/metaheuristic` - A* algorithm
   - `/api/route/compare` - Runs all 4 algorithms simultaneously
   - `/api/geocode` - Address geocoding with Nominatim
   - `/api/simulate-failures` - Dynamic failure simulation

4. **Database Schema**:
   - `infra_nodos` (42,534 nodes) and `infra_aristas` (89,021 edges)
   - Metadata tables: `meta_elevacion`, `meta_lluvia`, `meta_landcover`
   - Threat tables: `amenaza_dga`, `amenaza_inundaciones_hist`, `amenaza_reportes_ciudadanos`
   - `sim_fallas_activas` for failure simulation state

### Key Implementation Details

- **Spanish Comments**: The codebase uses Spanish for comments and documentation (per copilot-instructions.md)
- **No Emojis in Code**: Avoid using emojis in code, comments, or commits
- **Environment Variables**: All credentials must use environment variables (see `.env.example`)
- **Database Connection**: Always use Supabase pooler port (6543) instead of direct port (5432)
- **Highway Filtering**: Excludes footways, pedestrian paths, cycleways from routing
- **Flood Buffer**: 150-meter buffer around flood zones for risk calculation
- **Timeout Configuration**: API routes have configurable timeouts (default 60s for compare)

### Routing Algorithm Parameters
- `k`: Penalization factor for resilient Dijkstra (default: 5.0)
- `lambda_risk`: Risk factor for CPLEX optimization (default: 5.0)
- `risk_weight`: Weight for A* heuristic (default: 3.0)
- `max_risk`: Optional risk constraint (0.0-1.0)
- `max_distance`: Optional distance constraint in meters

### Important Files to Know
- `sql/schema.sql` - Complete database schema
- `web/src/app/page.tsx` - Main UI component
- `optimization/cplex_model.py` - MILP optimization implementation
- `web/src/app/api/route/compare/route.ts` - Main routing comparison endpoint
- `.env.example` - Environment variable template