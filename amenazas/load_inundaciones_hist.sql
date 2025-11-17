-- Loader SQL para amenazas de inundaciones históricas
-- Asume que el archivo inundaciones_hist.json está cargado en una tabla temporal staging_inundaciones_hist_json

create temp table if not exists staging_inundaciones_hist_json (doc jsonb);

-- Insertar en amenaza_inundaciones_hist desde el JSON
insert into amenaza_inundaciones_hist (geom, source, event_date, severity, properties)
select
    ST_SetSRID(ST_GeomFromGeoJSON(item->'geometry'), 4326) as geom,
    item->>'source' as source,
    daterange(
        (item->'event_date'->>'lower')::date,
        (item->'event_date'->>'upper')::date,
        '[]'
    ) as event_date,
    item->>'severity' as severity,
    item as properties
from (
    select jsonb_array_elements(doc) as item
    from staging_inundaciones_hist_json
) sub;

drop table if exists staging_inundaciones_hist_json;
