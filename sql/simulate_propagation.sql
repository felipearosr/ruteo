-- Function to simulate failure propagation (Water-like effect)
-- Returns JSON summary

CREATE OR REPLACE FUNCTION simulate_propagation(
    p_min_probability double precision,
    p_propagation_probability double precision,
    p_seed double precision, -- Expected -1.0 to 1.0
    p_max_steps int DEFAULT 10
)
RETURNS json
LANGUAGE plpgsql
AS $$
DECLARE
    v_simulation_id uuid;
    v_step int := 0;
    v_newly_failed_count int;
    v_total_failed_nodes int;
    v_total_failed_edges int;
    v_initial_seeds int;
BEGIN
    -- Set seed if provided to ensure reproducibility within this transaction
    IF p_seed IS NOT NULL THEN
        PERFORM setseed(p_seed);
    END IF;

    v_simulation_id := gen_random_uuid();

    -- 1. Initial Seeds (Nodes)
    -- Select nodes that fail based on their intrinsic probability
    WITH seeds AS (
        SELECT id, p_fallo_nodo, random() as rnd
        FROM infra_nodos
        WHERE p_fallo_nodo > p_min_probability
    ),
    failed_seeds AS (
        SELECT id, p_fallo_nodo, rnd
        FROM seeds
        WHERE rnd < p_fallo_nodo
    )
    INSERT INTO sim_fallas_activas (simulation_id, entity_type, entity_id, p_fallo, random_value, is_failed, created_at)
    SELECT v_simulation_id, 'nodo', id, p_fallo_nodo, rnd, true, now()
    FROM failed_seeds;

    GET DIAGNOSTICS v_initial_seeds = ROW_COUNT;

    -- 2. Propagation Loop (BFS)
    LOOP
        v_step := v_step + 1;
        IF v_step > p_max_steps THEN
            EXIT;
        END IF;

        -- Find neighbors of currently failed nodes that are NOT yet failed
        -- We look for nodes connected via edges to any node currently failed in this simulation
        WITH newly_failed AS (
            SELECT DISTINCT n.id
            FROM sim_fallas_activas sfa -- currently failed nodes (from previous steps)
            JOIN infra_aristas a ON (sfa.entity_id = a.source OR sfa.entity_id = a.target)
            JOIN infra_nodos n ON (n.id = CASE WHEN sfa.entity_id = a.source THEN a.target ELSE a.source END)
            LEFT JOIN sim_fallas_activas existing ON (existing.simulation_id = v_simulation_id AND existing.entity_type = 'nodo' AND existing.entity_id = n.id)
            WHERE sfa.simulation_id = v_simulation_id
              AND sfa.entity_type = 'nodo'
              AND existing.id IS NULL -- not already failed in this simulation
              AND random() < p_propagation_probability -- Apply propagation probability
        )
        INSERT INTO sim_fallas_activas (simulation_id, entity_type, entity_id, p_fallo, random_value, is_failed, created_at)
        SELECT v_simulation_id, 'nodo', id, p_propagation_probability, 0.0, true, now()
        FROM newly_failed;

        GET DIAGNOSTICS v_newly_failed_count = ROW_COUNT;

        -- If no new nodes failed, stop propagation
        IF v_newly_failed_count = 0 THEN
            EXIT;
        END IF;
    END LOOP;

    -- 3. Fail Edges connecting two failed nodes
    -- If both endpoints of an edge are failed, the edge itself should fail
    INSERT INTO sim_fallas_activas (simulation_id, entity_type, entity_id, p_fallo, random_value, is_failed, created_at)
    SELECT DISTINCT v_simulation_id, 'arista', a.id, 1.0, 0.0, true, now()
    FROM infra_aristas a
    JOIN sim_fallas_activas n1 ON (n1.simulation_id = v_simulation_id AND n1.entity_type = 'nodo' AND n1.entity_id = a.source)
    JOIN sim_fallas_activas n2 ON (n2.simulation_id = v_simulation_id AND n2.entity_type = 'nodo' AND n2.entity_id = a.target)
    LEFT JOIN sim_fallas_activas existing ON (existing.simulation_id = v_simulation_id AND existing.entity_type = 'arista' AND existing.entity_id = a.id)
    WHERE existing.id IS NULL;

    -- 4. Fail Independent Edges (optional, based on intrinsic probability)
    -- We can include this to maintain original behavior for edges that fail on their own
    INSERT INTO sim_fallas_activas (simulation_id, entity_type, entity_id, p_fallo, random_value, is_failed, created_at)
    SELECT v_simulation_id, 'arista', id, p_fallo_arista, random(), true, now()
    FROM infra_aristas
    WHERE p_fallo_arista > p_min_probability
      AND random() < p_fallo_arista
      AND id NOT IN (SELECT entity_id FROM sim_fallas_activas WHERE simulation_id = v_simulation_id AND entity_type = 'arista');

    -- Calculate statistics
    SELECT count(*) INTO v_total_failed_nodes FROM sim_fallas_activas WHERE simulation_id = v_simulation_id AND entity_type = 'nodo';
    SELECT count(*) INTO v_total_failed_edges FROM sim_fallas_activas WHERE simulation_id = v_simulation_id AND entity_type = 'arista';

    RETURN json_build_object(
        'simulation_id', v_simulation_id,
        'initial_seeds', v_initial_seeds,
        'propagated_nodes', v_total_failed_nodes - v_initial_seeds,
        'total_nodes_failed', v_total_failed_nodes,
        'total_edges_failed', v_total_failed_edges,
        'steps', v_step
    );
END;
$$;
