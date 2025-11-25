-- Create traffic metadata table
CREATE TABLE IF NOT EXISTS meta_trafico (
    id bigserial primary key,
    geom geometry(Polygon, 4326) not null,
    congestion_factor double precision not null default 1.0,
    description text,
    schedule jsonb,
    created_at timestamptz default now()
);

CREATE INDEX IF NOT EXISTS meta_trafico_geom_gist ON meta_trafico USING gist (geom);

-- Clean existing data for fresh insert
TRUNCATE meta_trafico;

-- Insert sample congestion zones

-- 1. Santiago Centro (High Congestion)
INSERT INTO meta_trafico (geom, congestion_factor, description)
VALUES (
    ST_SetSRID(ST_GeomFromText('POLYGON((-70.658 33.435, -70.645 33.435, -70.645 33.445, -70.658 33.445, -70.658 33.435))'), 4326),
    3.0,
    'Zona Santiago Centro - Congestión Alta'
);

-- 2. Providencia (Medium Congestion)
INSERT INTO meta_trafico (geom, congestion_factor, description)
VALUES (
    ST_SetSRID(ST_GeomFromText('POLYGON((-70.620 33.425, -70.605 33.425, -70.605 33.435, -70.620 33.435, -70.620 33.425))'), 4326),
    2.0,
    'Zona Providencia - Congestión Media'
);

-- 3. Vespucio Norte (Extreme Congestion)
INSERT INTO meta_trafico (geom, congestion_factor, description)
VALUES (
    ST_SetSRID(ST_GeomFromText('POLYGON((-70.600 33.380, -70.580 33.380, -70.580 33.400, -70.600 33.400, -70.600 33.380))'), 4326),
    5.0,
    'Nudo Vespucio - Congestión Extrema'
);

-- 4. El Golf / Isidora Goyenechea (High Congestion)
INSERT INTO meta_trafico (geom, congestion_factor, description)
VALUES (
    ST_SetSRID(ST_GeomFromText('POLYGON((-70.600 33.410, -70.590 33.410, -70.590 33.420, -70.600 33.420, -70.600 33.410))'), 4326),
    3.5,
    'Barrio El Golf - Congestión Alta'
);

-- 5. Ciudad Empresarial (Medium Congestion)
INSERT INTO meta_trafico (geom, congestion_factor, description)
VALUES (
    ST_SetSRID(ST_GeomFromText('POLYGON((-70.615 33.390, -70.605 33.390, -70.605 33.400, -70.615 33.400, -70.615 33.390))'), 4326),
    2.5,
    'Ciudad Empresarial - Congestión Media'
);

-- 6. Estación Central / Meiggs (High Congestion)
INSERT INTO meta_trafico (geom, congestion_factor, description)
VALUES (
    ST_SetSRID(ST_GeomFromText('POLYGON((-70.685 33.445, -70.670 33.445, -70.670 33.455, -70.685 33.455, -70.685 33.445))'), 4326),
    4.0,
    'Estación Central - Congestión Alta'
);

-- 7. Plaza Egaña (Medium Congestion)
INSERT INTO meta_trafico (geom, congestion_factor, description)
VALUES (
    ST_SetSRID(ST_GeomFromText('POLYGON((-70.570 33.450, -70.560 33.450, -70.560 33.460, -70.570 33.460, -70.570 33.450))'), 4326),
    2.0,
    'Plaza Egaña - Congestión Media'
);
