CREATE TABLE IF NOT EXISTS sim_fallas_activas (
    id bigserial primary key,
    simulation_id uuid not null,
    entity_type text not null check (entity_type in ('nodo', 'arista')),
    entity_id bigint not null,
    p_fallo double precision not null,
    random_value double precision not null,
    is_failed boolean not null,
    created_at timestamptz default now()
);

CREATE INDEX IF NOT EXISTS sim_fallas_activas_sim_id_idx ON sim_fallas_activas (simulation_id);
CREATE INDEX IF NOT EXISTS sim_fallas_activas_entity_idx ON sim_fallas_activas (entity_type, entity_id);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='infra_nodos' AND column_name='p_fallo_nodo') THEN
        ALTER TABLE infra_nodos ADD COLUMN p_fallo_nodo double precision default 0.0;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='infra_aristas' AND column_name='p_fallo_arista') THEN
        ALTER TABLE infra_aristas ADD COLUMN p_fallo_arista double precision default 0.0;
    END IF;
END $$;
