-- Loader SQL para metadata de elevación
-- Asume que el archivo elevacion.json está cargado en una tabla temporal staging_elevacion_json

-- Crear tabla staging temporal si no existe
create temp table if not exists staging_elevacion_json (doc jsonb);

-- Ejemplo de carga (ejecutar antes desde psql):
-- \set content `cat metadata/elevacion.json`
-- insert into staging_elevacion_json (doc) values (:'content');

-- Insertar en meta_elevacion desde el JSON
insert into meta_elevacion (geom, elev_m, source, properties)
select
    ST_SetSRID(ST_MakePoint((item->>'lon')::float, (item->>'lat')::float), 4326) as geom,
    (item->>'elev_m')::float as elev_m,
    item->>'source' as source,
    item as properties
from (
    select jsonb_array_elements(doc) as item
    from staging_elevacion_json
) sub;

drop table if exists staging_elevacion_json;
