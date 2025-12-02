-- Construye topología limpia en bloques para evitar timeouts largos.
-- Pasos:
--   1) Divide el bounding box de infra_aristas en tiles con overlap.
--   2) Para cada tile: copia aristas, las ajusta a una grilla (snap),
--      ejecuta pgr_createTopology y guarda aristas/nodos intermedios.
--   3) Une resultados, deduplica nodos en bordes (mismo snap) y genera
--      infra_nodos_cleaned / infra_aristas_cleaned.
--
-- Uso sugerido (8‑12 tiles con ~0.002° de solape):
--   SELECT infra_rebuild_topology_tiled(0.08, 0.002, 0.00001);
--
-- Requiere: infra_aristas poblada y extensiones postgis/pgrouting activas.

drop function if exists infra_rebuild_topology_tiled(double precision, double precision, double precision);
create or replace function infra_rebuild_topology_tiled(
    tile_size_deg double precision default 0.08,   -- ancho/alto del tile en grados
    overlap_deg double precision default 0.002,    -- solape para no cortar aristas en el borde
    snap_grid_deg double precision default 0.00001 -- grilla de snap (misma para tiles y merge)
) returns void
language plpgsql
as $$
declare
    xmin double precision;
    xmax double precision;
    ymin double precision;
    ymax double precision;
    n_cols integer;
    n_rows integer;
    col integer;
    row integer;
    tile_id integer := 0;
    tile_geom geometry;
    snap numeric := greatest(1e-9, snap_grid_deg);
    overlap numeric := greatest(0, overlap_deg);
begin
    if tile_size_deg <= 0 then
        raise exception 'tile_size_deg debe ser > 0';
    end if;

    -- Evita abortos por timeout al procesar cada tile.
    perform set_config('statement_timeout', '0', true);

    -- Limpiar salida previa y staging.
    drop table if exists infra_aristas_cleaned cascade;
    drop table if exists infra_nodos_cleaned cascade;
    drop table if exists infra_clean_tiles_edges;
    drop table if exists infra_clean_tiles_nodes;

    create unlogged table infra_clean_tiles_edges (
        tile_id integer not null,
        original_edge_id bigint,
        geom geometry(LineString,4326) not null,
        start_geom geometry(Point,4326) not null,
        end_geom geometry(Point,4326) not null,
        start_x numeric,
        start_y numeric,
        end_x numeric,
        end_y numeric,
        highway text,
        maxspeed text,
        tags jsonb
    );

    create unlogged table infra_clean_tiles_nodes (
        tile_id integer not null,
        geom geometry(Point,4326) not null,
        x numeric,
        y numeric
    );

    -- Bounding box con pequeño buffer.
    select st_xmin(ext), st_ymin(ext), st_xmax(ext), st_ymax(ext)
    into xmin, ymin, xmax, ymax
    from (
        select st_expand((st_extent(geom))::geometry, overlap) as ext
        from infra_aristas
    ) q;

    if xmin is null then
        raise exception 'infra_aristas está vacío; no hay nada que limpiar';
    end if;

    n_cols := ceil((xmax - xmin) / tile_size_deg)::int;
    n_rows := ceil((ymax - ymin) / tile_size_deg)::int;

    for col in 0..n_cols-1 loop
        for row in 0..n_rows-1 loop
            tile_id := tile_id + 1;

            tile_geom := st_makeenvelope(
                xmin + col * tile_size_deg - overlap,
                ymin + row * tile_size_deg - overlap,
                xmin + (col + 1) * tile_size_deg + overlap,
                ymin + (row + 1) * tile_size_deg + overlap,
                4326
            );

            drop table if exists pg_temp.tmp_tile_edges cascade;
            create temp table tmp_tile_edges as
            select
                id,
                st_snaptogrid(geom, snap) as geom,
                st_snaptogrid(st_startpoint(geom), snap) as start_geom,
                st_snaptogrid(st_endpoint(geom), snap) as end_geom,
                st_x(st_snaptogrid(st_startpoint(geom), snap)) as start_x,
                st_y(st_snaptogrid(st_startpoint(geom), snap)) as start_y,
                st_x(st_snaptogrid(st_endpoint(geom), snap)) as end_x,
                st_y(st_snaptogrid(st_endpoint(geom), snap)) as end_y,
                highway,
                maxspeed,
                tags
            from infra_aristas
            where geom && tile_geom
              and st_intersects(geom, tile_geom);

            if not exists (select 1 from tmp_tile_edges limit 1) then
                continue;
            end if;

            insert into infra_clean_tiles_edges (tile_id, original_edge_id, geom, start_geom, end_geom, start_x, start_y, end_x, end_y, highway, maxspeed, tags)
            select tile_id, id, geom, start_geom, end_geom, start_x, start_y, end_x, end_y, highway, maxspeed, tags
            from tmp_tile_edges;

            insert into infra_clean_tiles_nodes (tile_id, geom, x, y)
            select tile_id, start_geom, start_x, start_y from tmp_tile_edges
            union all
            select tile_id, end_geom, end_x, end_y from tmp_tile_edges;

            drop table if exists pg_temp.tmp_tile_edges cascade;
            drop table if exists pg_temp.tmp_tile_edges_vertices_pgr cascade;
        end loop;
    end loop;

    -- Deduplicar nodos (misma grilla) y asignar IDs finales.
    create unlogged table infra_nodos_cleaned as
    select
        row_number() over () as id,
        geom,
        x,
        y,
        null::bigint as osm_id,
        '{}'::jsonb as tags,
        now() as created_at,
        0.0::double precision as p_fallo_nodo
    from (
        select distinct st_snaptogrid(geom, snap) as geom, x, y
        from infra_clean_tiles_nodes
    ) dedup;

    create index infra_nodos_cleaned_geom_gist on infra_nodos_cleaned using gist (geom);
    create index infra_nodos_cleaned_xy_idx on infra_nodos_cleaned (x, y);

    -- Reasignar source/target usando igualdad en x/y (ya "snapped").
    create unlogged table infra_aristas_cleaned as
    select
        row_number() over () as id,
        src.id as source,
        tgt.id as target,
        st_snaptogrid(e.geom, snap) as geom,
        st_length(st_transform(st_snaptogrid(e.geom, snap), 3857)) as length_m,
        st_length(st_transform(st_snaptogrid(e.geom, snap), 3857)) as cost,
        st_length(st_transform(st_snaptogrid(e.geom, snap), 3857)) as reverse_cost,
        e.highway,
        e.maxspeed,
        e.tags,
        now() as created_at,
        0.0::double precision as p_fallo_arista
    from infra_clean_tiles_edges e
    join infra_nodos_cleaned src
      on src.x = e.start_x and src.y = e.start_y
    join infra_nodos_cleaned tgt
      on tgt.x = e.end_x and tgt.y = e.end_y;

    create index infra_aristas_cleaned_geom_gist on infra_aristas_cleaned using gist (geom);
    create index infra_aristas_cleaned_source_idx on infra_aristas_cleaned (source);
    create index infra_aristas_cleaned_target_idx on infra_aristas_cleaned (target);

    -- Deduplicar aristas generadas en solapes (mantiene la de menor id)
    with dups as (
        select source, target, geom, min(id) as keep_id
        from infra_aristas_cleaned
        group by source, target, geom
        having count(*) > 1
    )
    delete from infra_aristas_cleaned a
    using dups d
    where a.source = d.source
      and a.target = d.target
      and a.geom = d.geom
      and a.id <> d.keep_id;

    -- Eliminar nodos huérfanos tras deduplicación
    delete from infra_nodos_cleaned n
    where not exists (
        select 1 from infra_aristas_cleaned a
        where a.source = n.id or a.target = n.id
    );

    -- Limpieza opcional del staging para ahorrar espacio
    truncate table infra_clean_tiles_edges;
    truncate table infra_clean_tiles_nodes;

    -- Limpieza opcional del staging:
    -- truncate table infra_clean_tiles_edges;
    -- truncate table infra_clean_tiles_nodes;
end;
$$;
