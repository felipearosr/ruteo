# Instrucciones para crear find_nearest_node en Supabase

## Opción 1: Desde Supabase Dashboard (Recomendado)

1. Ve a https://supabase.com/dashboard
2. Selecciona tu proyecto
3. Ve a "SQL Editor"
4. Pega este SQL:

```sql
CREATE OR REPLACE FUNCTION find_nearest_node(lat DOUBLE PRECISION, lon DOUBLE PRECISION)
RETURNS TABLE (
  id INTEGER,
  distance_m DOUBLE PRECISION,
  lat DOUBLE PRECISION,
  lon DOUBLE PRECISION
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    n.id,
    ST_Distance(
      n.geom::geography,
      ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography
    ) AS distance_m,
    ST_Y(n.geom) AS lat,
    ST_X(n.geom) AS lon
  FROM infra_nodos n
  ORDER BY n.geom <-> ST_SetSRID(ST_MakePoint(lon, lat), 4326)
  LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE;
```

5. Click en "Run"

## Opción 2: Desde psql (Terminal)

```bash
psql "postgresql://postgres:[TU-PASSWORD]@db.eqjzlgbjgwbnvqzbomsn.supabase.co:5432/postgres" -f sql/create_find_nearest_node.sql
```

Reemplaza [TU-PASSWORD] con tu contraseña de Supabase.

## Verificar que funciona

```sql
-- Test rápido (coordenadas de Santiago centro)
SELECT * FROM find_nearest_node(-33.4489, -70.6693);
```

Debería retornar algo como:
```
 id   | distance_m | lat       | lon
------+------------+-----------+---------
 1234 | 42.5       | -33.44891 | -70.66932
```
