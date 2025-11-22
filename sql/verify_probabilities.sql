-- Verification Queries for Probability Calculations
-- Run these in Supabase SQL Editor to check if calculations are working

-- ============================================================
-- 1. Check if columns exist and have non-zero values
-- ============================================================

SELECT 
  'Nodes' as entity_type,
  COUNT(*) as total_count,
  COUNT(*) FILTER (WHERE p_fallo_nodo > 0) as with_probability,
  COUNT(*) FILTER (WHERE p_fallo_nodo = 0) as zero_probability,
  ROUND(AVG(p_fallo_nodo)::numeric, 6) as avg_probability,
  ROUND(MIN(p_fallo_nodo)::numeric, 6) as min_probability,
  ROUND(MAX(p_fallo_nodo)::numeric, 6) as max_probability
FROM infra_nodos

UNION ALL

SELECT 
  'Edges' as entity_type,
  COUNT(*) as total_count,
  COUNT(*) FILTER (WHERE p_fallo_arista > 0) as with_probability,
  COUNT(*) FILTER (WHERE p_fallo_arista = 0) as zero_probability,
  ROUND(AVG(p_fallo_arista)::numeric, 6) as avg_probability,
  ROUND(MIN(p_fallo_arista)::numeric, 6) as min_probability,
  ROUND(MAX(p_fallo_arista)::numeric, 6) as max_probability
FROM infra_aristas;

-- ============================================================
-- 2. Check specific sector (e.g., Las Condes)
-- ============================================================

SELECT 
  'Las Condes Nodes' as description,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE p_fallo_nodo > 0) as with_prob,
  ROUND(AVG(p_fallo_nodo)::numeric, 4) as avg_prob
FROM infra_nodos
WHERE ST_Intersects(geom, ST_MakeEnvelope(-70.58, -33.42, -70.52, -33.38, 4326));

-- ============================================================
-- 3. Sample some actual values to see the range
-- ============================================================

SELECT 
  id,
  ROUND(p_fallo_nodo::numeric, 4) as probability,
  ST_AsText(geom) as location
FROM infra_nodos
WHERE p_fallo_nodo > 0
ORDER BY p_fallo_nodo DESC
LIMIT 10;

-- ============================================================
-- 4. Check distribution of probabilities
-- ============================================================

SELECT 
  risk_category,
  node_count,
  ROUND(100.0 * node_count / SUM(node_count) OVER (), 2) as percentage
FROM (
  SELECT 
    CASE 
      WHEN p_fallo_nodo = 0 THEN '0 (no risk)'
      WHEN p_fallo_nodo <= 0.1 THEN '0.01-0.10 (very low)'
      WHEN p_fallo_nodo <= 0.3 THEN '0.11-0.30 (low)'
      WHEN p_fallo_nodo <= 0.5 THEN '0.31-0.50 (medium)'
      WHEN p_fallo_nodo <= 0.7 THEN '0.51-0.70 (high)'
      ELSE '0.71-1.00 (very high)'
    END as risk_category,
    COUNT(*) as node_count
  FROM infra_nodos
  GROUP BY 
    CASE 
      WHEN p_fallo_nodo = 0 THEN '0 (no risk)'
      WHEN p_fallo_nodo <= 0.1 THEN '0.01-0.10 (very low)'
      WHEN p_fallo_nodo <= 0.3 THEN '0.11-0.30 (low)'
      WHEN p_fallo_nodo <= 0.5 THEN '0.31-0.50 (medium)'
      WHEN p_fallo_nodo <= 0.7 THEN '0.51-0.70 (high)'
      ELSE '0.71-1.00 (very high)'
    END
) subq
ORDER BY 
  CASE risk_category
    WHEN '0 (no risk)' THEN 1
    WHEN '0.01-0.10 (very low)' THEN 2
    WHEN '0.11-0.30 (low)' THEN 3
    WHEN '0.31-0.50 (medium)' THEN 4
    WHEN '0.51-0.70 (high)' THEN 5
    ELSE 6
  END;

-- ============================================================
-- 5. Check nodes near known amenazas (should have higher prob)
-- ============================================================

-- Find nodes near inundaciones (should have probability > 0)
SELECT 
  n.id,
  ROUND(n.p_fallo_nodo::numeric, 4) as probability,
  ROUND(MIN(ST_Distance(
    ST_Transform(n.geom, 3857),
    ST_Transform(i.geom, 3857)
  ))::numeric, 0) as distance_to_nearest_inundacion_m
FROM infra_nodos n
CROSS JOIN amenaza_inundaciones_hist i
WHERE ST_DWithin(
  ST_Transform(n.geom, 3857),
  ST_Transform(i.geom, 3857),
  500  -- Within 500m
)
GROUP BY n.id, n.p_fallo_nodo
ORDER BY n.p_fallo_nodo DESC
LIMIT 10;

-- ============================================================
-- 6. Verify the exponential decay formula is working
-- ============================================================

-- Nodes at different distances should have decreasing probabilities
-- This checks if closer nodes have higher probabilities
SELECT 
  CASE 
    WHEN dist < 100 THEN '0-100m'
    WHEN dist < 300 THEN '100-300m'
    WHEN dist < 500 THEN '300-500m'
    WHEN dist < 1000 THEN '500-1000m'
    ELSE '1000m+'
  END as distance_range,
  COUNT(*) as node_count,
  ROUND(AVG(prob)::numeric, 4) as avg_probability
FROM (
  SELECT 
    n.id,
    n.p_fallo_nodo as prob,
    MIN(ST_Distance(
      ST_Transform(n.geom, 3857),
      ST_Transform(i.geom, 3857)
    )) as dist
  FROM infra_nodos n
  CROSS JOIN amenaza_inundaciones_hist i
  WHERE n.p_fallo_nodo > 0
  GROUP BY n.id, n.p_fallo_nodo
) subq
GROUP BY 
  CASE 
    WHEN dist < 100 THEN '0-100m'
    WHEN dist < 300 THEN '100-300m'
    WHEN dist < 500 THEN '300-500m'
    WHEN dist < 1000 THEN '500-1000m'
    ELSE '1000m+'
  END
ORDER BY MIN(dist);
