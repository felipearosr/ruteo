-- Loader SQL para metadata de landcover
-- Asume que el archivo landcover.json está cargado en una tabla temporal staging_landcover_json

create temp table if not exists staging_landcover_json (doc jsonb);

-- Insertar en meta_landcover desde el JSON
insert into meta_landcover (geom, class, confidence, source, properties)
select
    ST_SetSRID(ST_GeomFromGeoJSON(item->'geometry'), 4326) as geom,
    item->>'class' as class,
    (item->>'confidence')::float as confidence,
    item->>'source' as source,
    item as properties
from (
    select jsonb_array_elements(doc) as item
    from staging_landcover_json
) sub;

drop table if exists staging_landcover_json;
