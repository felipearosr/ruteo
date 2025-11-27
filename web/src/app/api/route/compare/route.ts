/**
 * API route para comparar las 4 rutas simultáneamente
 *
 * Ejecuta las 4 técnicas de ruteo y retorna todas las rutas con métricas
 * para comparación visual y analítica.
 * 
 * Endpoint: GET /api/route/compare
 * Query params:
 *   - source: nodo origen (requerido)
 *   - target: nodo destino (requerido)
 *   - k: factor de penalización Dijkstra resiliente (default: 5.0)
 *   - risk_weight: peso A* (default: 3.0)
 *   - max_risk: restricción de riesgo (opcional)
 *   - max_distance: restricción de distancia (opcional)
 *   - simulation_id: ID de simulación activa (opcional)
 *   - lambda_risk: factor de riesgo para GUROBI (default: 5.0)
 */
import { NextResponse } from 'next/server';
import pg from 'pg';

const { Pool } = pg;

// Pool compartido para evitar crear conexiones por ruta
const pool = new Pool({
  host: process.env.SUPABASE_DB_HOST,
  port: parseInt(process.env.SUPABASE_DB_PORT || '6543'),
  database: process.env.SUPABASE_DB_NAME || 'postgres',
  user: process.env.SUPABASE_DB_USER,
  password: process.env.SUPABASE_DB_PASSWORD,
  ssl: { rejectUnauthorized: false }
});

async function runBaseline(source: number, target: number, maxDistance: number | null, avoidFlood: boolean) {
  const floodFilter = avoidFlood ? ' AND coalesce(p_fallo_arista, 0) < 0.3' : '';
  const startTime = performance.now();

  const query = `
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
              'p_fallo', 0.0,
              'highway', a.highway
            )
          ) ORDER BY r.seq
        ), '[]'::json)
      ) as route
    FROM pgr_dijkstra(
      'SELECT id, source, target, length_m as cost, 
       CASE 
         WHEN tags->>''oneway'' = ''yes'' THEN -1
         WHEN tags->>''oneway'' = ''-1'' THEN length_m
         ELSE length_m
       END as reverse_cost 
       FROM infra_aristas WHERE length_m IS NOT NULL AND length_m > 0${floodFilter}',
      $1::BIGINT,
      $2::BIGINT,
      true
    ) r
    JOIN infra_aristas a ON r.edge = a.id
    ${maxDistance !== null ? 'WHERE a.length_m <= $3' : ''}
  `;

  const params: (number | bigint)[] = [source, target];
  if (maxDistance !== null) params.push(maxDistance);

  const result = await pool.query(query, params);
  const endTime = performance.now();

  const routeData = result.rows?.[0]?.route || { type: 'FeatureCollection', features: [] };
  const features = routeData.features || [];

  let totalDistance = 0;
  for (const feature of features) {
    totalDistance += feature.properties.length_m || 0;
  }

  return {
    route: routeData,
    metrics: {
      distance_m: totalDistance,
      computation_time_ms: endTime - startTime,
      risk_score: 0,
      num_segments: features.length,
      method: 'baseline'
    }
  };
}

async function runResilient(source: number, target: number, k: number, maxRisk: number | null, maxDistance: number | null, avoidFlood: boolean) {
  const client = await pool.connect();
  const startTime = performance.now();

  try {
    await client.query('BEGIN');

    let edgesQuery = `
      SELECT 
        a.id, 
        a.source, 
        a.target, 
        a.length_m * (1.0 + ${k} * coalesce(a.p_fallo_arista, 0.0)) as cost,
        CASE 
          WHEN a.tags->>'oneway' = 'yes' THEN -1
          WHEN a.tags->>'oneway' = '-1' THEN a.length_m * (1.0 + ${k} * coalesce(a.p_fallo_arista, 0.0))
          ELSE a.length_m * (1.0 + ${k} * coalesce(a.p_fallo_arista, 0.0))
        END as reverse_cost
      FROM infra_aristas a
      WHERE a.length_m IS NOT NULL
    `;

    if (maxRisk !== null) {
      edgesQuery += ` AND a.p_fallo_arista <= ${maxRisk}`;
    }
    if (maxDistance !== null) {
      edgesQuery += ` AND length_m <= ${maxDistance}`;
    }
    if (avoidFlood) {
      edgesQuery += ` AND coalesce(a.p_fallo_arista, 0) < 0.3`;
    }

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

    const routeData = result.rows?.[0]?.route || { type: 'FeatureCollection', features: [] };
    const features = routeData.features || [];

    let totalDistance = 0;
    let totalRisk = 0;
    for (const feature of features) {
      totalDistance += feature.properties.length_m || 0;
      totalRisk += feature.properties.p_fallo || 0;
    }

    const endTime = performance.now();

    return {
      route: routeData,
      metrics: {
        distance_m: totalDistance,
        computation_time_ms: endTime - startTime,
        risk_score: totalRisk,
        num_segments: features.length,
        method: 'resilient',
        parameters: { k, max_risk: maxRisk, max_distance: maxDistance }
      }
    };
  } catch (error) {
    try { await client.query('ROLLBACK'); } catch { /* ignore */ }
    throw error;
  } finally {
    client.release();
  }
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  const source = searchParams.get('source');
  const target = searchParams.get('target');

  if (!source || !target) {
    return NextResponse.json(
      { error: 'Se requieren parámetros source y target' },
      { status: 400 }
    );
  }

  const k = searchParams.get('k') || '5.0';

  const riskWeight = searchParams.get('risk_weight') || '3.0';
  const maxRisk = searchParams.get('max_risk');
  const maxDistance = searchParams.get('max_distance');
  const simulationId = searchParams.get('simulation_id');
  const lambdaRisk = searchParams.get('lambda_risk') || '5.0';
  const maxTime = searchParams.get('max_time_min');
  const avoidFlood = searchParams.get('avoid_flood_zones') === 'true';
  const sourceNum = parseInt(source, 10);
  const targetNum = parseInt(target, 10);
  const kNum = parseFloat(k);
  const riskWeightNum = parseFloat(riskWeight);
  const lambdaRiskNum = parseFloat(lambdaRisk);
  const maxRiskNum = maxRisk ? parseFloat(maxRisk) : null;
  const maxDistanceNum = maxDistance ? parseFloat(maxDistance) : null;
  const maxTimeNum = maxTime ? parseFloat(maxTime) : null;

  const startTime = performance.now();

  try {
    const baseUrl = new URL(request.url).origin;

    const sharedParams = new URLSearchParams({
      source: sourceNum.toString(),
      target: targetNum.toString(),
      ...(maxRiskNum !== null && { max_risk: maxRiskNum.toString() }),
      ...(maxDistanceNum !== null && { max_distance: maxDistanceNum.toString() }),
      ...(maxTimeNum !== null && { max_time_min: maxTimeNum.toString() }),
      ...(avoidFlood && { avoid_flood_zones: 'true' }),
      ...(simulationId && { simulation_id: simulationId })
    });

    const [baselineResult, resilientResult, astarResult, gurobiResult] = await Promise.all([
      runBaseline(sourceNum, targetNum, maxDistanceNum, avoidFlood).catch((err) => ({
        route: { type: 'FeatureCollection', features: [] },
        metrics: { distance_m: 0, computation_time_ms: 0, risk_score: 0, num_segments: 0, method: 'baseline', error: true },
        error: err instanceof Error ? err.message : String(err)
      })),
      runResilient(sourceNum, targetNum, kNum, maxRiskNum, maxDistanceNum, avoidFlood).catch((err) => ({
        route: { type: 'FeatureCollection', features: [] },
        metrics: { distance_m: 0, computation_time_ms: 0, risk_score: 0, num_segments: 0, method: 'resilient', error: true },
        error: err instanceof Error ? err.message : String(err)
      })),
      fetch(`${baseUrl}/api/route/metaheuristic?${sharedParams.toString()}&risk_weight=${riskWeightNum}`)
        .then(r => r.json())
        .catch((err) => ({
          route: { type: 'FeatureCollection', features: [] },
          metrics: { distance_m: 0, computation_time_ms: 0, risk_score: 0, num_segments: 0, method: 'astar', error: true },
          error: err instanceof Error ? err.message : String(err)
        })),
      fetch(`${baseUrl}/api/route/optimize?${sharedParams.toString()}&lambda_risk=${lambdaRiskNum}`)
        .then(r => r.json())
        .catch((err) => ({
          route: { type: 'FeatureCollection', features: [] },
          metrics: { distance_m: 0, computation_time_ms: 0, risk_score: 0, num_segments: 0, method: 'gurobi', error: true },
          error: err instanceof Error ? err.message : String(err)
        }))
    ]);

    const totalTime = performance.now() - startTime;

    const results = {
      baseline: baselineResult,
      resilient: resilientResult,
      astar: astarResult,
      gurobi: gurobiResult,
      comparison: {
        total_time_ms: totalTime,
        parameters: {
          source: sourceNum,
          target: targetNum,
          k: kNum,
          risk_weight: riskWeightNum,
          max_risk: maxRiskNum,
          max_distance: maxDistanceNum,
          max_time_min: maxTimeNum,
          simulation_id: simulationId,
          lambda_risk: lambdaRiskNum,
          avoid_flood_zones: avoidFlood
        },
        summary: {
          shortest_distance: Math.min(
            baselineResult?.metrics?.distance_m || Infinity,
            resilientResult?.metrics?.distance_m || Infinity,
            astarResult?.metrics?.distance_m || Infinity,
            gurobiResult?.metrics?.distance_m || Infinity
          ),
          lowest_risk: Math.min(
            baselineResult?.metrics?.risk_score || Infinity,
            resilientResult?.metrics?.risk_score || Infinity,
            astarResult?.metrics?.risk_score || Infinity,
            gurobiResult?.metrics?.risk_score || Infinity
          ),
          fastest_computation: Math.min(
            baselineResult?.metrics?.computation_time_ms || Infinity,
            resilientResult?.metrics?.computation_time_ms || Infinity,
            astarResult?.metrics?.computation_time_ms || Infinity,
            gurobiResult?.metrics?.computation_time_ms || Infinity
          )
        }
      }
    };

    return NextResponse.json(results);
  } catch (err) {
    const totalTime = performance.now() - startTime;
    console.error('Error en comparación de rutas:', err);
    return NextResponse.json(
      {
        error: 'Error al comparar rutas: ' + (err instanceof Error ? err.message : String(err)),
        comparison: {
          total_time_ms: totalTime,
          success: false
        }
      },
      { status: 500 }
    );
  }
}
