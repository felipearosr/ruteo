# Sector-Based Probability Calculation

## Overview

The probability calculation has been split into manageable sectors to avoid timeouts and make progress trackable.

## Execution Order

Run these SQL files **in order** in your Supabase SQL Editor:

### Step 1: Setup (Run Once)
```sql
sql/step1_add_columns.sql
```
- Adds `p_fallo_nodo` and `p_fallo_arista` columns
- Creates indexes
- **Time**: ~5 seconds

### Step 2: Calculate by Sector (Run Each)

#### 2a. Las Condes
```sql
sql/step2a_las_condes.sql
```
- Bounding box: -70.58 to -70.52 (lon), -33.42 to -33.38 (lat)
- **Time**: ~2-5 minutes

#### 2b. Lo Barnechea
```sql
sql/step2b_lo_barnechea.sql
```
- Bounding box: -70.52 to -70.46 (lon), -33.38 to -33.32 (lat)
- **Time**: ~2-5 minutes

#### 2c. Providencia
```sql
sql/step2c_providencia.sql
```
- Bounding box: -70.62 to -70.58 (lon), -33.44 to -33.41 (lat)
- **Time**: ~2-5 minutes

#### 2d. Vitacura
```sql
sql/step2d_vitacura.sql
```
- Bounding box: -70.58 to -70.54 (lon), -33.40 to -33.36 (lat)
- **Time**: ~2-5 minutes

#### 2e. Santiago Centro
```sql
sql/step2e_santiago_centro.sql
```
- Bounding box: -70.66 to -70.63 (lon), -33.46 to -33.43 (lat)
- **Time**: ~2-5 minutes

#### 2f. Ñuñoa
```sql
sql/step2f_nunoa.sql
```
- Bounding box: -70.62 to -70.58 (lon), -33.47 to -33.44 (lat)
- **Time**: ~2-5 minutes

#### 2g. La Reina
```sql
sql/step2g_la_reina.sql
```
- Bounding box: -70.58 to -70.54 (lon), -33.46 to -33.42 (lat)
- **Time**: ~2-5 minutes

#### 2h. Peñalolén
```sql
sql/step2h_penalolen.sql
```
- Bounding box: -70.58 to -70.52 (lon), -33.50 to -33.46 (lat)
- **Time**: ~2-5 minutes

#### 2i. Macul & La Florida
```sql
sql/step2i_macul_florida.sql
```
- Bounding box: -70.62 to -70.56 (lon), -33.52 to -33.48 (lat)
- **Time**: ~2-5 minutes

#### 2j. Recoleta & Independencia
```sql
sql/step2j_recoleta_independencia.sql
```
- Bounding box: -70.66 to -70.62 (lon), -33.42 to -33.38 (lat)
- **Time**: ~2-5 minutes

#### 2k. Maipú
```sql
sql/step2k_maipu.sql
```
- Bounding box: -70.78 to -70.72 (lon), -33.54 to -33.48 (lat)
- **Time**: ~2-5 minutes

#### 2l. Pudahuel
```sql
sql/step2l_pudahuel.sql
```
- Bounding box: -70.80 to -70.72 (lon), -33.48 to -33.40 (lat)
- **Time**: ~2-5 minutes

#### 2m. Estación Central & Cerrillos
```sql
sql/step2m_estacion_central_cerrillos.sql
```
- Bounding box: -70.72 to -70.66 (lon), -33.52 to -33.46 (lat)
- **Time**: ~2-5 minutes

#### 2n. San Miguel & La Cisterna
```sql
sql/step2n_san_miguel_cisterna.sql
```
- Bounding box: -70.68 to -70.62 (lon), -33.52 to -33.48 (lat)
- **Time**: ~2-5 minutes

#### 2o. Quilicura & Huechuraba
```sql
sql/step2o_quilicura_huechuraba.sql
```
- Bounding box: -70.74 to -70.64 (lon), -33.38 to -33.32 (lat)
- **Time**: ~2-5 minutes

#### 2p. La Granja & San Ramón
```sql
sql/step2p_la_granja_san_ramon.sql
```
- Bounding box: -70.66 to -70.60 (lon), -33.56 to -33.52 (lat)
- **Time**: ~2-5 minutes

## Progress Tracking

After each sector completes, you can check overall progress:

```sql
SELECT 
  COUNT(*) as total_nodes,
  COUNT(*) FILTER (WHERE p_fallo_nodo > 0) as nodes_calculated,
  ROUND(100.0 * COUNT(*) FILTER (WHERE p_fallo_nodo > 0) / COUNT(*), 1) as percent_complete
FROM infra_nodos;
```

## Testing

After completing any sector, test simulate-failures:

```bash
curl -X POST http://localhost:3000/api/simulate-failures \
  -H "Content-Type: application/json" \
  -d '{"min_probability": 0.01}'
```

The feature will work with whatever sectors you've completed so far!

## Adding More Sectors

To cover more areas, create additional scripts with different bounding boxes. Use this template and adjust coordinates:

```sql
WHERE ST_Intersects(n.geom, ST_MakeEnvelope(lon_min, lat_min, lon_max, lat_max, 4326))
```

