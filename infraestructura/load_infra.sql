-- Loader SQL para infraestructura
-- Asume que el archivo infraestructura.geojson ya está disponible y se puede leer con una función de carga
-- o que se ha copiado/convertido en una tabla staging.
-- 
-- Estrategia:
--   1) Crear una tabla staging temporal para cargar el GeoJSON.
--   2) Insertar nodos únicos en infra_nodos.
--   3) Insertar aristas en infra_aristas, referenciando source/target desde infra_nodos.
--   4) Llamar a la función que calcula longitudes/costos.
--
-- Nota: Este script se ejecuta dentro de Supabase; se puede usar psql para copiar/cargar el JSON.
-- Ejemplo de carga (antes de ejecutar este script):
--   CREATE TEMP TABLE staging_infra_geojson (doc jsonb);
--   COPY staging_infra_geojson (doc) FROM '/path/to/infraestructura.geojson';
-- O desde Supabase dashboard, usar el data importer o un script Python que inserte el JSON.

-- Por simplicidad, este script asume que el GeoJSON ya está cargado en una tabla temporal llamada staging_infra_geojson.

-- Limpiar tablas (solo para desarrollo; en producción no se recomendaría truncar)
-- truncate table infra_aristas cascade;
-- truncate table infra_nodos cascade;

-- Paso 1: Crear una tabla temporal para features
create temp table if not exists staging_features as
select
    (feat->>'id')::bigint as osm_way_id,
    ST_GeomFromGeoJSON(feat->'geometry') as geom,
    feat->'properties' as props
from (
    select jsonb_array_elements((doc->'features')) as feat
    from staging_infra_geojson
) sub
where (feat->'geometry'->>'type') = 'LineString';

-- Paso 2: Extraer nodos únicos de las geometrías y poblar infra_nodos
-- Aquí usamos ST_DumpPoints para obtener los vértices de cada LineString.
-- Agrupamos para evitar duplicados de nodos en la misma ubicación.
insert into infra_nodos (geom, osm_id, tags)
select distinct on (st_x(geom), st_y(geom))
    geom, null::bigint as osm_id, '{}'::jsonb as tags
from (
    select (ST_DumpPoints(geom)).geom as geom
    from staging_features
) pts;

-- Paso 3: Insertar aristas
-- Necesitamos encontrar source/target en infra_nodos usando las coordenadas.
-- Estrategia: para cada LineString, el primer punto es source y el último es target.
insert into infra_aristas (source, target, geom, highway, maxspeed, tags)
select
    src.id as source,
    tgt.id as target,
    sf.geom,
    sf.props->>'highway' as highway,
    sf.props->>'maxspeed' as maxspeed,
    sf.props
from staging_features sf
cross join lateral (
    select id from infra_nodos
    where ST_Equals(geom, ST_PointN(sf.geom, 1))
    limit 1
) src
cross join lateral (
    select id from infra_nodos
    where ST_Equals(geom, ST_PointN(sf.geom, ST_NumPoints(sf.geom)))
    limit 1
) tgt;

-- Paso 4: Calcular longitudes y costos
select infra_calcular_longitudes_costs();

-- Opcional: crear topología con pgr_createTopology si se quiere automatizar source/target
-- (esto requeriría adaptar el insert de aristas o hacerlo luego)

drop table if exists staging_features;
-- drop table if exists staging_infra_geojson;
