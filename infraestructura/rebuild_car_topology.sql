-- Reconstruye la topología limpia SOLO para vías transitables por vehículos.
-- Excluye footways, cycleways, pasos peatonales, etc.
-- Usa un snap más agresivo para conectar segmentos cercanos.
--
-- Uso:
--   SELECT infra_rebuild_car_topology(0.0001);
--   -- O con tolerancia personalizada:
--   SELECT infra_rebuild_car_topology(0.0002);

drop function if exists infra_rebuild_car_topology(double precision);
create or replace function infra_rebuild_car_topology(
    snap_tolerance double precision default 0.0001  -- ~11 metros en el ecuador
) returns table(
    total_nodes bigint,
    total_edges bigint,
    num_components bigint,
    largest_component_size bigint
)
language plpgsql
as $$
declare
    snap_val numeric := greatest(1e-9, snap_tolerance);
    comp_count bigint;
    largest_comp bigint;
begin
    raise notice 'Iniciando reconstrucción de topología para vehículos...';
    raise notice 'Tolerancia de snap: % grados (~% metros)', snap_val, round(snap_val * 111000);

    -- Desactivar timeout
    perform set_config('statement_timeout', '0', true);

    -- Limpiar tablas anteriores
    drop table if exists infra_aristas_cleaned cascade;
    drop table if exists infra_nodos_cleaned cascade;

    raise notice 'Filtrando y preparando aristas para vehículos...';

    -- Crear tabla temporal con aristas válidas para vehículos
    create temp table tmp_car_edges as
    select
        id as original_id,
        st_snaptogrid(geom, snap_val) as geom,
        st_snaptogrid(st_startpoint(geom), snap_val) as start_pt,
        st_snaptogrid(st_endpoint(geom), snap_val) as end_pt,
        highway,
        maxspeed,
        tags,
        length_m,
        p_fallo_arista
    from infra_aristas
    where highway IN (
        -- Carreteras principales
        'motorway', 'motorway_link',
        'trunk', 'trunk_link',
        'primary', 'primary_link',
        'secondary', 'secondary_link',
        'tertiary', 'tertiary_link',
        -- Calles urbanas
        'residential',
        'living_street',
        'unclassified',
        'service',
        -- Otros transitables por vehículos
        'track',       -- caminos rurales (algunos requieren 4x4)
        'busway'       -- carriles de bus (generalmente transitables)
    )
    -- Filtrar geometrías degeneradas
    and st_numpoints(geom) >= 2
    and st_length(st_transform(geom, 3857)) > 0.5;  -- min 0.5 metros

    raise notice 'Aristas filtradas: %', (select count(*) from tmp_car_edges);

    -- Crear tabla de nodos únicos directamente
    raise notice 'Extrayendo nodos únicos...';

    create table infra_nodos_cleaned as
    select
        row_number() over (order by y, x) as id,
        geom,
        x,
        y,
        null::bigint as osm_id,
        '{}'::jsonb as tags,
        now() as created_at,
        0.0::double precision as p_fallo_nodo
    from (
        select distinct
            pt as geom,
            st_x(pt) as x,
            st_y(pt) as y
        from (
            select start_pt as pt from tmp_car_edges
            union
            select end_pt as pt from tmp_car_edges
        ) pts
        where pt is not null
    ) dedup;

    create index infra_nodos_cleaned_xy_idx on infra_nodos_cleaned (x, y);

    raise notice 'Nodos creados: %', (select count(*) from infra_nodos_cleaned);

    -- Crear aristas con referencias a nodos
    raise notice 'Creando aristas con referencias a nodos...';

    create table infra_aristas_cleaned as
    select
        row_number() over () as id,
        src.id as source,
        tgt.id as target,
        e.geom,
        coalesce(e.length_m, st_length(st_transform(e.geom, 3857))) as length_m,
        coalesce(e.length_m, st_length(st_transform(e.geom, 3857))) as cost,
        coalesce(e.length_m, st_length(st_transform(e.geom, 3857))) as reverse_cost,
        e.highway,
        e.maxspeed,
        e.tags,
        now() as created_at,
        coalesce(e.p_fallo_arista, 0.1) as p_fallo_arista
    from tmp_car_edges e
    join infra_nodos_cleaned src
        on src.x = st_x(e.start_pt) and src.y = st_y(e.start_pt)
    join infra_nodos_cleaned tgt
        on tgt.x = st_x(e.end_pt) and tgt.y = st_y(e.end_pt)
    where src.id <> tgt.id;  -- evitar loops

    raise notice 'Aristas creadas: %', (select count(*) from infra_aristas_cleaned);

    -- Eliminar duplicados (misma source, target)
    raise notice 'Eliminando aristas duplicadas...';

    with dups as (
        select source, target, min(id) as keep_id
        from infra_aristas_cleaned
        group by source, target
        having count(*) > 1
    )
    delete from infra_aristas_cleaned a
    using dups d
    where a.source = d.source
      and a.target = d.target
      and a.id <> d.keep_id;

    -- Eliminar nodos huérfanos
    raise notice 'Eliminando nodos huérfanos...';

    delete from infra_nodos_cleaned n
    where not exists (
        select 1 from infra_aristas_cleaned a
        where a.source = n.id or a.target = n.id
    );

    -- Crear índices finales
    raise notice 'Creando índices...';

    create index if not exists infra_nodos_cleaned_geom_gist on infra_nodos_cleaned using gist (geom);
    create index if not exists infra_aristas_cleaned_geom_gist on infra_aristas_cleaned using gist (geom);
    create index if not exists infra_aristas_cleaned_source_idx on infra_aristas_cleaned (source);
    create index if not exists infra_aristas_cleaned_target_idx on infra_aristas_cleaned (target);

    -- Calcular estadísticas de componentes
    raise notice 'Calculando componentes conectados...';

    select count(distinct component), max(cnt)
    into comp_count, largest_comp
    from (
        select component, count(*) as cnt
        from pgr_connectedComponents(
            'SELECT id, source, target, cost FROM infra_aristas_cleaned WHERE cost > 0'
        )
        group by component
    ) sub;

    -- Limpiar temporales
    drop table if exists tmp_car_edges;

    raise notice '===========================================';
    raise notice 'Reconstrucción completada!';
    raise notice 'Nodos finales: %', (select count(*) from infra_nodos_cleaned);
    raise notice 'Aristas finales: %', (select count(*) from infra_aristas_cleaned);
    raise notice 'Componentes conectados: %', comp_count;
    raise notice 'Nodos en componente más grande: %', largest_comp;
    raise notice '===========================================';

    return query
    select
        (select count(*) from infra_nodos_cleaned)::bigint,
        (select count(*) from infra_aristas_cleaned)::bigint,
        comp_count,
        largest_comp;
end;
$$;

-- Función auxiliar para encontrar el nodo más cercano SOLO en el componente principal
drop function if exists find_nearest_car_node(double precision, double precision);
create or replace function find_nearest_car_node(lat double precision, lon double precision)
returns table (
    node_id bigint,
    distance_m double precision,
    node_lat double precision,
    node_lon double precision
) as $$
begin
    return query
    select
        n.id,
        st_distance(
            n.geom::geography,
            st_setsrid(st_makepoint(lon, lat), 4326)::geography
        ) as distance_m,
        st_y(n.geom),
        st_x(n.geom)
    from infra_nodos_cleaned n
    where exists (
        select 1 from infra_aristas_cleaned a
        where (a.source = n.id or a.target = n.id)
    )
    order by n.geom <-> st_setsrid(st_makepoint(lon, lat), 4326)
    limit 1;
end;
$$ language plpgsql stable;
