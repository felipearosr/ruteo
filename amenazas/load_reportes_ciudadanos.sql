-- Loader SQL para amenazas de reportes ciudadanos
-- Asume que el archivo reportes_ciudadanos.json está cargado en una tabla temporal staging_reportes_ciudadanos_json

create temp table if not exists staging_reportes_ciudadanos_json (doc jsonb);

-- Insertar en amenaza_reportes_ciudadanos desde el JSON
insert into amenaza_reportes_ciudadanos (geom, reported_at, reporter, description, media, properties)
select
    ST_SetSRID(ST_MakePoint((item->>'lon')::float, (item->>'lat')::float), 4326) as geom,
    (item->>'reported_at')::timestamptz as reported_at,
    item->>'reporter' as reporter,
    item->>'description' as description,
    item->'media' as media,
    item as properties
from (
    select jsonb_array_elements(doc) as item
    from staging_reportes_ciudadanos_json
) sub;

drop table if exists staging_reportes_ciudadanos_json;
