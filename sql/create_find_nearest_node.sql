-- Eliminar función existente si existe
DROP FUNCTION IF EXISTS find_nearest_node(DOUBLE PRECISION, DOUBLE PRECISION);

-- Función para encontrar el nodo más cercano a unas coordenadas
CREATE OR REPLACE FUNCTION find_nearest_node(p_lat DOUBLE PRECISION, p_lon DOUBLE PRECISION)
RETURNS TABLE (
  node_id INTEGER,
  distance_m DOUBLE PRECISION,
  node_lat DOUBLE PRECISION,
  node_lon DOUBLE PRECISION
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    n.id::INTEGER,
    ST_Distance(
      n.geom::geography,
      ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography
    )::DOUBLE PRECISION,
    ST_Y(n.geom)::DOUBLE PRECISION,
    ST_X(n.geom)::DOUBLE PRECISION
  FROM infra_nodos n
  WHERE EXISTS (
    SELECT 1
    FROM infra_aristas a
    WHERE a.source = n.id OR a.target = n.id
  ) -- Filtra nodos aislados
  ORDER BY n.geom <-> ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)
  LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE;

-- Comentario
COMMENT ON FUNCTION find_nearest_node(DOUBLE PRECISION, DOUBLE PRECISION) IS 
'Encuentra el nodo de infraestructura más cercano a unas coordenadas lat/lon';
