/**
 * API route para Ruta 3: pgr_dijkstra con Costos Ajustados por Riesgo
 * 
 * Usa la función SQL infra_calcular_costo_resiliente para calcular costos
 * que consideran tanto distancia como probabilidad de falla.
 * 
 * Endpoint: GET /api/route/resilient
 * Query params: 
 *   - source: nodo origen
 *   - target: nodo destino
 *   - k: factor de penalización por riesgo (default: 5.0)
 *   - max_risk: riesgo acumulado máximo permitido (opcional)
 *   - max_distance: distancia máxima permitida en metros (opcional)
 */
import { NextResponse } from 'next/server';
import pg from 'pg';

const { Pool } = pg;

const pool = new Pool({
  host: process.env.SUPABASE_DB_HOST || 'aws-1-us-east-1.pooler.supabase.com',
  port: parseInt(process.env.SUPABASE_DB_PORT || '5432'),
  database: process.env.SUPABASE_DB_NAME || 'postgres',
  user: process.env.SUPABASE_DB_USER || 'postgres.eqjzlgbjgwbnvqzbomsn',
  password: process.env.SUPABASE_DB_PASSWORD,
  ssl: { rejectUnauthorized: false }
});

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  const source = parseInt(searchParams.get('source') || '1');
  const target = parseInt(searchParams.get('target') || '100');
  const k = parseFloat(searchParams.get('k') || '5.0');
  const maxRisk = searchParams.get('max_risk') ? parseFloat(searchParams.get('max_risk')!) : null;
  const maxDistance = searchParams.get('max_distance') ? parseFloat(searchParams.get('max_distance')!) : null;
  const simulationId = searchParams.get('simulation_id');
  const avoidFloodZones = searchParams.get('avoid_flood_zones') === 'true';

  const startTime = performance.now();
  let client;

  try {
    client = await pool.connect();

    // 1. Pre-cálculos con tablas temporales
    await client.query('BEGIN');

    let penaltyJoin = '';
    let penaltyCost = '0.0';
    let trafficJoin = '';
    let trafficCost = '1.0'; // Factor multiplicativo base (1.0 = sin tráfico)

    // A. Penalización por Fallas (Simulación)
    if (simulationId) {
      const createFailureTempTable = `
        CREATE TEMP TABLE temp_edge_penalties ON COMMIT DROP AS
        WITH active_failures AS (
          SELECT 
            CASE 
              WHEN entity_type = 'nodo' THEN (SELECT geom FROM infra_nodos WHERE id = entity_id)
              WHEN entity_type = 'arista' THEN (SELECT geom FROM infra_aristas WHERE id = entity_id)
            END as geom_sim
          FROM sim_fallas_activas 
          WHERE simulation_id = $1 AND is_failed = true
        )
        SELECT 
          a.id as edge_id,
          SUM(5.0 / (ST_Distance(a.geom::geography, f.geom_sim::geography) + 1.0)) as penalty
        FROM infra_aristas a
        JOIN active_failures f ON ST_DWithin(a.geom, f.geom_sim, 0.001)
        GROUP BY a.id
      `;

      await client.query(createFailureTempTable, [simulationId]);
      penaltyJoin = `LEFT JOIN temp_edge_penalties p ON a.id = p.edge_id`;
      penaltyCost = `COALESCE(p.penalty, 0.0)`;
    }

    // B. Penalización por Tráfico (Metadata)
    // Calculamos qué aristas están dentro de zonas de congestión
    const createTrafficTempTable = `
      CREATE TEMP TABLE temp_traffic_factors ON COMMIT DROP AS
      SELECT 
        a.id as edge_id,
        MAX(t.congestion_factor) as traffic_factor
      FROM infra_aristas a
      JOIN meta_trafico t ON ST_Intersects(a.geom, t.geom)
      GROUP BY a.id
    `;

    await client.query(createTrafficTempTable);
    trafficJoin = `LEFT JOIN temp_traffic_factors tf ON a.id = tf.edge_id`;
    trafficCost = `COALESCE(tf.traffic_factor, 1.0)`;

    // 2. Construir query para pgr_dijkstra
    // Costo = Longitud * FactorTráfico * FactorHeurístico * (1 + k * (ProbFallo + PenalizaciónProximidad))

    // Heurística: Avenidas principales son más lentas por defecto (simulación de tráfico base)
    const heuristicTrafficSql = `
      CASE 
        WHEN a.highway IN ('motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link') THEN 1.5
        WHEN a.highway IN ('secondary', 'secondary_link') THEN 1.2
        ELSE 1.0
      END
    `;

    let edgesQuery = `
      SELECT 
        a.id, 
        a.source, 
        a.target, 
        a.length_m * ${trafficCost} * ${heuristicTrafficSql} * (1.0 + ${k} * (a.p_fallo_arista + ${penaltyCost})) as cost,
        CASE 
          WHEN a.tags->>'oneway' = 'yes' THEN -1
          WHEN a.tags->>'oneway' = '-1' THEN a.length_m * ${trafficCost} * ${heuristicTrafficSql} * (1.0 + ${k} * (a.p_fallo_arista + ${penaltyCost}))
          ELSE a.length_m * ${trafficCost} * ${heuristicTrafficSql} * (1.0 + ${k} * (a.p_fallo_arista + ${penaltyCost}))
        END as reverse_cost
      FROM infra_aristas a
      ${penaltyJoin}
      ${trafficJoin}
      WHERE a.length_m IS NOT NULL
    `;

    // Aplicar filtros de restricciones
    if (maxRisk !== null) {
      edgesQuery += ` AND a.p_fallo_arista <= ${maxRisk}`;
    }
    if (maxDistance !== null) {
      edgesQuery += ` AND length_m <= ${maxDistance}`;
    }
    if (avoidFloodZones) {
      edgesQuery += ` AND coalesce(a.p_fallo_arista, 0) < 0.3`;
    }

    // Escapar comillas simples para pgr_dijkstra
    const safeEdgesQuery = edgesQuery.replace(/'/g, "''");

    const query = `
      WITH route_result AS (
        SELECT * FROM pgr_dijkstra(
          '${safeEdgesQuery}',
          $1::BIGINT,
          $2::BIGINT,
          true
        )
      )
      SELECT 
        json_build_object(
          'type', 'FeatureCollection',
          'features', COALESCE(json_agg(
            json_build_object(
              'type', 'Feature',
              'geometry', CASE 
                WHEN r.node = a.source THEN ST_AsGeoJSON(a.geom)::json
                ELSE ST_AsGeoJSON(ST_Reverse(a.geom))::json
              END,
              'properties', json_build_object(
                'seq', r.seq,
                'edge_id', r.edge,
                'cost', r.cost,
                'length_m', a.length_m,
                'p_fallo', a.p_fallo_arista,
                'highway', a.highway,
                'adjusted_cost', r.cost
              )
            ) ORDER BY r.seq
          ), '[]'::json)
        ) as route
      FROM route_result r
      JOIN infra_aristas a ON r.edge = a.id;
    `;

    const result = await client.query(query, [source, target]);

    await client.query('COMMIT');

    const endTime = performance.now();
    const computationTime = endTime - startTime;

    if (!result.rows || result.rows.length === 0) {
      return NextResponse.json({
        route: {
          type: 'FeatureCollection',
          features: []
        },
        metrics: {
          distance_m: 0,
          computation_time_ms: computationTime,
          risk_score: 0,
          num_segments: 0,
          method: 'resilient',
          parameters: { k, max_risk: maxRisk, max_distance: maxDistance }
        },
        error: 'No se encontró ruta entre los nodos especificados.'
      });
    }

    const routeData = result.rows[0].route;

    // Calcular métricas
    let totalDistance = 0;
    let totalRisk = 0;
    let totalAdjustedCost = 0;
    const features = routeData.features || [];

    for (const feature of features) {
      totalDistance += feature.properties.length_m || 0;
      totalRisk += feature.properties.p_fallo || 0;
      totalAdjustedCost += feature.properties.adjusted_cost || 0;
    }

    return NextResponse.json({
      route: routeData,
      metrics: {
        distance_m: totalDistance,
        computation_time_ms: computationTime,
        risk_score: totalRisk,
        adjusted_cost: totalAdjustedCost,
        num_segments: features.length,
        method: 'resilient',
        parameters: { k, max_risk: maxRisk, max_distance: maxDistance }
      }
    });

  } catch (err) {
    if (client) {
      try { await client.query('ROLLBACK'); } catch (e) { }
    }

    const endTime = performance.now();
    const computationTime = endTime - startTime;

    console.error('Error en el endpoint de ruta resiliente:', err);
    return NextResponse.json(
      {
        route: {
          type: 'FeatureCollection',
          features: []
        },
        metrics: {
          distance_m: 0,
          computation_time_ms: computationTime,
          risk_score: 0,
          num_segments: 0,
          method: 'resilient',
          parameters: { k, max_risk: maxRisk, max_distance: maxDistance }
        },
        error: 'Error calculando ruta resiliente: ' + (err instanceof Error ? err.message : String(err))
      },
      { status: 500 }
    );
  } finally {
    if (client) client.release();
  }
}
