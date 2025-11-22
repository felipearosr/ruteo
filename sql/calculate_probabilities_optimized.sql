-- Optimized SQL-based probability calculation
-- This is MUCH faster than the Python script (minutes instead of hours)

-- Step 1: Calculate probabilities for nodes
-- Uses spatial joins and exponential decay function

UPDATE infra_nodos n
SET p_fallo_nodo = LEAST(1.0, GREATEST(0.0,
  -- Inundaciones (40% weight, 500m radius)
  0.4 * COALESCE((
    SELECT EXP(-MIN(ST_Distance(
      ST_Transform(n.geom, 3857),
      ST_Transform(i.geom, 3857)
    )) / 500.0)
    FROM amenaza_inundaciones_hist i
    WHERE ST_DWithin(
      ST_Transform(n.geom, 3857),
      ST_Transform(i.geom, 3857),
      2000  -- Only check within 2km for performance
    )
  ), 0.0) +
  
  -- DGA stations (30% weight, 1000m radius)
  0.3 * COALESCE((
    SELECT EXP(-MIN(ST_Distance(
      ST_Transform(n.geom, 3857),
      ST_Transform(d.geom, 3857)
    )) / 1000.0)
    FROM amenaza_dga d
    WHERE ST_DWithin(
      ST_Transform(n.geom, 3857),
      ST_Transform(d.geom, 3857),
      3000  -- Only check within 3km for performance
    )
  ), 0.0) +
  
  -- Reportes ciudadanos (20% weight, 200m radius)
  0.2 * COALESCE((
    SELECT EXP(-MIN(ST_Distance(
      ST_Transform(n.geom, 3857),
      ST_Transform(r.geom, 3857)
    )) / 200.0)
    FROM amenaza_reportes_ciudadanos r
    WHERE ST_DWithin(
      ST_Transform(n.geom, 3857),
      ST_Transform(r.geom, 3857),
      1000  -- Only check within 1km for performance
    )
  ), 0.0) +
  
  -- Lluvia (10% weight, normalized to 50mm)
  0.1 * COALESCE((
    SELECT LEAST(1.0, AVG(precip_mm) / 50.0)
    FROM meta_lluvia m
    WHERE ST_DWithin(
      ST_Transform(n.geom, 3857),
      ST_Transform(m.geom, 3857),
      1000
    )
  ), 0.0)
));

-- Step 2: Calculate probabilities for edges
-- Uses midpoint of LineString

UPDATE infra_aristas a
SET p_fallo_arista = LEAST(1.0, GREATEST(0.0,
  -- Inundaciones (40% weight, 500m radius)
  0.4 * COALESCE((
    SELECT EXP(-MIN(ST_Distance(
      ST_Transform(ST_LineInterpolatePoint(a.geom, 0.5), 3857),
      ST_Transform(i.geom, 3857)
    )) / 500.0)
    FROM amenaza_inundaciones_hist i
    WHERE ST_DWithin(
      ST_Transform(ST_LineInterpolatePoint(a.geom, 0.5), 3857),
      ST_Transform(i.geom, 3857),
      2000
    )
  ), 0.0) +
  
  -- DGA stations (30% weight, 1000m radius)
  0.3 * COALESCE((
    SELECT EXP(-MIN(ST_Distance(
      ST_Transform(ST_LineInterpolatePoint(a.geom, 0.5), 3857),
      ST_Transform(d.geom, 3857)
    )) / 1000.0)
    FROM amenaza_dga d
    WHERE ST_DWithin(
      ST_Transform(ST_LineInterpolatePoint(a.geom, 0.5), 3857),
      ST_Transform(d.geom, 3857),
      3000
    )
  ), 0.0) +
  
  -- Reportes ciudadanos (20% weight, 200m radius)
  0.2 * COALESCE((
    SELECT EXP(-MIN(ST_Distance(
      ST_Transform(ST_LineInterpolatePoint(a.geom, 0.5), 3857),
      ST_Transform(r.geom, 3857)
    )) / 200.0)
    FROM amenaza_reportes_ciudadanos r
    WHERE ST_DWithin(
      ST_Transform(ST_LineInterpolatePoint(a.geom, 0.5), 3857),
      ST_Transform(r.geom, 3857),
      1000
    )
  ), 0.0) +
  
  -- Lluvia (10% weight, normalized to 50mm)
  0.1 * COALESCE((
    SELECT LEAST(1.0, AVG(precip_mm) / 50.0)
    FROM meta_lluvia m
    WHERE ST_DWithin(
      ST_Transform(ST_LineInterpolatePoint(a.geom, 0.5), 3857),
      ST_Transform(m.geom, 3857),
      1000
    )
  ), 0.0)
));

-- Step 3: Show statistics
SELECT 
  'Nodes' as entity_type,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE p_fallo_nodo > 0) as with_probability,
  ROUND(AVG(p_fallo_nodo)::numeric, 4) as avg_probability,
  ROUND(MAX(p_fallo_nodo)::numeric, 4) as max_probability
FROM infra_nodos

UNION ALL

SELECT 
  'Edges' as entity_type,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE p_fallo_arista > 0) as with_probability,
  ROUND(AVG(p_fallo_arista)::numeric, 4) as avg_probability,
  ROUND(MAX(p_fallo_arista)::numeric, 4) as max_probability
FROM infra_aristas;
