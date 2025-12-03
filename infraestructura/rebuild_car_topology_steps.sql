-- Reconstruye topología en pasos separados para evitar timeouts de Supabase
-- Ejecutar cada paso por separado

-- ==================== PASO 1: Limpiar y crear aristas filtradas ====================
-- Tiempo estimado: ~30 segundos

drop table if exists infra_aristas_cleaned cascade;
drop table if exists infra_nodos_cleaned cascade;

create table infra_aristas_temp as
select
    id as original_id,
    st_snaptogrid(geom, 0.0001) as geom,
    st_snaptogrid(st_startpoint(geom), 0.0001) as start_pt,
    st_snaptogrid(st_endpoint(geom), 0.0001) as end_pt,
    highway,
    maxspeed,
    tags,
    length_m,
    p_fallo_arista
from infra_aristas
where highway IN (
    'motorway', 'motorway_link',
    'trunk', 'trunk_link',
    'primary', 'primary_link',
    'secondary', 'secondary_link',
    'tertiary', 'tertiary_link',
    'residential',
    'living_street',
    'unclassified',
    'service',
    'track',
    'busway'
)
and st_numpoints(geom) >= 2
and st_length(st_transform(geom, 3857)) > 0.5;

select 'Paso 1 completado. Aristas filtradas: ' || count(*) from infra_aristas_temp;
