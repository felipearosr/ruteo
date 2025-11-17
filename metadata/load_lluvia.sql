-- Loader SQL para metadata de lluvia
-- Asume que el archivo lluvia.json está cargado en una tabla temporal staging_lluvia_json

create temp table if not exists staging_lluvia_json (doc jsonb);

-- Insertar en meta_lluvia desde el JSON
insert into meta_lluvia (geom, precip_mm, observed_at, source, properties)
select
    ST_SetSRID(ST_MakePoint((item->>'lon')::float, (item->>'lat')::float), 4326) as geom,
    (item->>'precip_mm')::float as precip_mm,
    (item->>'observed_at')::timestamptz as observed_at,
    item->>'source' as source,
    item as properties
from (
    select jsonb_array_elements(doc) as item
    from staging_lluvia_json
) sub;

drop table if exists staging_lluvia_json;
