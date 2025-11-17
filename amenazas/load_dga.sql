-- Loader SQL para amenazas DGA
-- Asume que el archivo dga_estaciones.json está cargado en una tabla temporal staging_dga_json

create temp table if not exists staging_dga_json (doc jsonb);

-- Insertar en amenaza_dga desde el JSON
insert into amenaza_dga (geom, station_id, parameter, last_update, properties)
select
    ST_SetSRID(ST_MakePoint((item->>'lon')::float, (item->>'lat')::float), 4326) as geom,
    item->>'station_id' as station_id,
    item->'parameter' as parameter,
    (item->>'last_update')::timestamptz as last_update,
    item as properties
from (
    select jsonb_array_elements(doc) as item
    from staging_dga_json
) sub;

drop table if exists staging_dga_json;
