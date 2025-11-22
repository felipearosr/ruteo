-- Step 2a: Calculate probabilities for Las Condes
-- Bounding box: approximately -70.58 to -70.52 (lon), -33.42 to -33.38 (lat)
-- ============================================================

-- Nodes in Las Condes
UPDATE infra_nodos n
SET p_fallo_nodo = LEAST(1.0, GREATEST(0.0,
  0.4 * COALESCE((
    SELECT EXP(-MIN(ST_Distance(ST_Transform(n.geom, 3857), ST_Transform(i.geom, 3857))) / 500.0)
    FROM amenaza_inundaciones_hist i
    WHERE ST_DWithin(ST_Transform(n.geom, 3857), ST_Transform(i.geom, 3857), 2000)
  ), 0.0) +
  0.3 * COALESCE((
    SELECT EXP(-MIN(ST_Distance(ST_Transform(n.geom, 3857), ST_Transform(d.geom, 3857))) / 1000.0)
    FROM amenaza_dga d
    WHERE ST_DWithin(ST_Transform(n.geom, 3857), ST_Transform(d.geom, 3857), 3000)
  ), 0.0) +
  0.2 * COALESCE((
    SELECT EXP(-MIN(ST_Distance(ST_Transform(n.geom, 3857), ST_Transform(r.geom, 3857))) / 200.0)
    FROM amenaza_reportes_ciudadanos r
    WHERE ST_DWithin(ST_Transform(n.geom, 3857), ST_Transform(r.geom, 3857), 1000)
  ), 0.0) +
  0.1 * COALESCE((
    SELECT LEAST(1.0, AVG(precip_mm) / 50.0)
    FROM meta_lluvia m
    WHERE ST_DWithin(ST_Transform(n.geom, 3857), ST_Transform(m.geom, 3857), 1000)
  ), 0.0)
))
WHERE ST_Intersects(n.geom, ST_MakeEnvelope(-70.58, -33.42, -70.52, -33.38, 4326));

-- Edges in Las Condes
UPDATE infra_aristas a
SET p_fallo_arista = LEAST(1.0, GREATEST(0.0,
  0.4 * COALESCE((
    SELECT EXP(-MIN(ST_Distance(ST_Transform(ST_LineInterpolatePoint(a.geom, 0.5), 3857), ST_Transform(i.geom, 3857))) / 500.0)
    FROM amenaza_inundaciones_hist i
    WHERE ST_DWithin(ST_Transform(ST_LineInterpolatePoint(a.geom, 0.5), 3857), ST_Transform(i.geom, 3857), 2000)
  ), 0.0) +
  0.3 * COALESCE((
    SELECT EXP(-MIN(ST_Distance(ST_Transform(ST_LineInterpolatePoint(a.geom, 0.5), 3857), ST_Transform(d.geom, 3857))) / 1000.0)
    FROM amenaza_dga d
    WHERE ST_DWithin(ST_Transform(ST_LineInterpolatePoint(a.geom, 0.5), 3857), ST_Transform(d.geom, 3857), 3000)
  ), 0.0) +
  0.2 * COALESCE((
    SELECT EXP(-MIN(ST_Distance(ST_Transform(ST_LineInterpolatePoint(a.geom, 0.5), 3857), ST_Transform(r.geom, 3857))) / 200.0)
    FROM amenaza_reportes_ciudadanos r
    WHERE ST_DWithin(ST_Transform(ST_LineInterpolatePoint(a.geom, 0.5), 3857), ST_Transform(r.geom, 3857), 1000)
  ), 0.0) +
  0.1 * COALESCE((
    SELECT LEAST(1.0, AVG(precip_mm) / 50.0)
    FROM meta_lluvia m
    WHERE ST_DWithin(ST_Transform(ST_LineInterpolatePoint(a.geom, 0.5), 3857), ST_Transform(m.geom, 3857), 1000)
  ), 0.0)
))
WHERE ST_Intersects(a.geom, ST_MakeEnvelope(-70.58, -33.42, -70.52, -33.38, 4326));

-- Show progress
SELECT 
  'Las Condes' as sector,
  COUNT(*) FILTER (WHERE p_fallo_nodo > 0) as nodes_with_prob,
  COUNT(*) FILTER (WHERE p_fallo_arista > 0) as edges_with_prob
FROM infra_nodos n, infra_aristas a
WHERE ST_Intersects(n.geom, ST_MakeEnvelope(-70.58, -33.42, -70.52, -33.38, 4326))
  AND ST_Intersects(a.geom, ST_MakeEnvelope(-70.58, -33.42, -70.52, -33.38, 4326));
