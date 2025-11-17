-- Esquema de la base de datos para Supabase con PostGIS y pgRouting
-- Generado siguiendo las reglas en copilot-instructions.md
-- Comentarios y nombres de objetos en español

-- Habilitar extensiones necesarias
create extension if not exists postgis;
create extension if not exists pgrouting;

-- Usaremos SRID 4326 (WGS84) para todas las geometrías de entrada/salida

-- Tabla de nodos de infraestructura (puntos)
-- Cada nodo representa una intersección o vértice de la red vial
create table if not exists infra_nodos (
    id bigserial primary key,
    -- geometría puntual en WGS84
    geom geometry(Point,4326) not null,
    -- campos de metadatos opcionales
    osm_id bigint,
    tags jsonb,
    created_at timestamptz default now()
);

-- Índice espacial para nodos
create index if not exists infra_nodos_geom_gist on infra_nodos using gist (geom);

-- Tabla de aristas (edges) para pgrouting
-- Debe contener columnas "source" y "target" que referencian infra_nodos(id)
create table if not exists infra_aristas (
    id bigserial primary key,
    -- columnas para pgrouting
    source bigint not null,
    target bigint not null,
    -- geometría de la arista (LineString) en WGS84
    geom geometry(LineString,4326) not null,
    -- longitud en metros (se puede calcular al cargar usando ST_Length(ST_Transform(...)))
    length_m double precision,
    -- costo para ruteo (por defecto igual a length_m, pero puede incluir penalizaciones)
    cost double precision,
    -- costo inverso (para ruteo dirigido)
    reverse_cost double precision,
    -- atributos adicionales
    highway text,
    maxspeed text,
    tags jsonb,
    created_at timestamptz default now(),
    -- asegurar integridad referencial básica
    constraint fk_infra_aristas_source foreign key (source) references infra_nodos(id) on delete cascade,
    constraint fk_infra_aristas_target foreign key (target) references infra_nodos(id) on delete cascade
);

-- Índice espacial para aristas
create index if not exists infra_aristas_geom_gist on infra_aristas using gist (geom);

-- Índice para source/target para acelerar pgrouting
create index if not exists infra_aristas_source_idx on infra_aristas (source);
create index if not exists infra_aristas_target_idx on infra_aristas (target);

-- Tablas de metadata

-- Elevación (puede ser puntos o celdas de una malla)
create table if not exists meta_elevacion (
    id bigserial primary key,
    geom geometry(Point,4326) not null,
    elev_m double precision not null,
    source text,
    ts timestamptz,
    properties jsonb
);
create index if not exists meta_elevacion_geom_gist on meta_elevacion using gist (geom);

-- Lluvia / precipitación (sensor o rejilla temporal)
create table if not exists meta_lluvia (
    id bigserial primary key,
    geom geometry(Point,4326) not null,
    precip_mm double precision,
    observed_at timestamptz,
    source text,
    properties jsonb
);
create index if not exists meta_lluvia_geom_gist on meta_lluvia using gist (geom);

-- Landcover (clases de cobertura de suelo)
create table if not exists meta_landcover (
    id bigserial primary key,
    geom geometry(Geometry,4326) not null,
    class text,
    confidence double precision,
    source text,
    properties jsonb
);
create index if not exists meta_landcover_geom_gist on meta_landcover using gist (geom);

-- Tablas de amenazas

-- Estaciones DGA (ejemplo: puntos con lecturas o ubicación)
create table if not exists amenaza_dga (
    id bigserial primary key,
    geom geometry(Point,4326) not null,
    station_id text,
    parameter jsonb,
    last_update timestamptz,
    properties jsonb
);
create index if not exists amenaza_dga_geom_gist on amenaza_dga using gist (geom);

-- Inundaciones históricas (polígonos o multi-polígonos)
create table if not exists amenaza_inundaciones_hist (
    id bigserial primary key,
    geom geometry(Geometry,4326) not null,
    source text,
    event_date daterange,
    severity text,
    properties jsonb
);
create index if not exists amenaza_inundaciones_hist_geom_gist on amenaza_inundaciones_hist using gist (geom);

-- Reportes ciudadanos (puntos con texto, imágenes, etc.)
create table if not exists amenaza_reportes_ciudadanos (
    id bigserial primary key,
    geom geometry(Point,4326) not null,
    reported_at timestamptz,
    reporter text,
    description text,
    media jsonb,
    properties jsonb
);
create index if not exists amenaza_reportes_ciudadanos_geom_gist on amenaza_reportes_ciudadanos using gist (geom);

-- Vista/función de ejemplo para calcular longitud y costos en infra_aristas
-- Esta función solo añade/updatea los campos length_m y cost basados en geom
create or replace function infra_calcular_longitudes_costs() returns void as $$
begin
    update infra_aristas
    set
        length_m = ST_Length(ST_Transform(geom,3857)),
        cost = ST_Length(ST_Transform(geom,3857)),
        reverse_cost = ST_Length(ST_Transform(geom,3857))
    where length_m is null or cost is null;
end;
$$ language plpgsql;

-- Nota: Para usar pgrouting, se recomienda poblar las columnas source/target usando
-- pgr_createTopology o calculando la topología externamente y cargando los ids.
