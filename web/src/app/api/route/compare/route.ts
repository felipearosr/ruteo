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
 *   - k: factor de penalización Dijkstra resiliente (default: 15.0)
 *   - risk_weight: peso A* (default: 10.0)
 *   - max_risk: restricción de riesgo (opcional)
 *   - max_distance: restricción de distancia (opcional)
 *   - simulation_id: ID de simulación activa (opcional)
 *   - lambda_risk: factor de riesgo para GUROBI (default: 5.0)
 */
import { NextResponse } from 'next/server';
import pg from 'pg';
import { pool } from '@/lib/db';
import { resolveConnectedNodes } from '@/lib/connectedNodes';

const DEFAULT_TIMEOUT_MS = parseInt(process.env.COMPARE_ROUTE_TIMEOUT_MS || '60000', 10);

const FLOOD_BUFFER_METERS = 150;
const EXCLUDED_HIGHWAYS = [
  'footway',
  'pedestrian',
  'cycleway',
  'path',
  'steps',
  'track',
  'bridleway'
];

const EXCLUDED_HIGHWAYS_LIST = EXCLUDED_HIGHWAYS.map((h) => `'${h}'`).join(', ');
const HIGHWAY_FILTER_CORE = `coalesce(highway, '') NOT IN (${EXCLUDED_HIGHWAYS_LIST})`;
const highwayFilterAliasA = ` AND coalesce(a.highway, '') NOT IN (${EXCLUDED_HIGHWAYS_LIST})`;
const highwayFilterExpression = ` AND ${HIGHWAY_FILTER_CORE}`;

// Velocidades por tipo de via (km/h)
const HIGHWAY_SPEEDS: Record<string, number> = {
  motorway: 80,
  motorway_link: 60,
  trunk: 80,
  trunk_link: 60,
  primary: 60,
  primary_link: 50,
  secondary: 60,
  secondary_link: 50,
  tertiary: 50,
  tertiary_link: 40,
  residential: 40,
  living_street: 20,
  unclassified: 40,
  service: 30,
  default: 50
};

// Calcula tiempo de viaje en minutos basado en distancia y tipo de via
function calculateTravelTime(features: any[]): number {
  let totalTimeMinutes = 0;
  for (const feature of features) {
    const lengthM = feature.properties?.length_m || 0;
    const highway = feature.properties?.highway || 'default';
    const speedKmh = HIGHWAY_SPEEDS[highway] || HIGHWAY_SPEEDS.default;
    // tiempo = distancia / velocidad, convertir m a km y horas a minutos
    const timeMinutes = (lengthM / 1000) / speedKmh * 60;
    totalTimeMinutes += timeMinutes;
  }
  return totalTimeMinutes;
}

async function fetchFloodBlockedEdgeIds(client: pg.PoolClient, simulationId: string, radiusMeters = FLOOD_BUFFER_METERS) {
  if (!simulationId) {
    return [];
  }

  const query = `
    WITH failed_nodes AS (
      SELECT n.geom
      FROM sim_fallas_activas s
      JOIN infra_nodos_cleaned n ON s.entity_type = 'nodo' AND s.entity_id = n.id
      WHERE s.simulation_id = $1 AND s.is_failed = true AND n.geom IS NOT NULL
    ),
    failed_edges AS (
      SELECT a.geom
      FROM sim_fallas_activas s
      JOIN infra_aristas a ON s.entity_type = 'arista' AND s.entity_id = a.id
      WHERE s.simulation_id = $1 AND s.is_failed = true AND a.geom IS NOT NULL
    ),
    failed_geoms AS (
      SELECT geom FROM failed_nodes
      UNION ALL
      SELECT geom FROM failed_edges
    ),
    failure_buffer AS (
      SELECT ST_Union(ST_Buffer(geom::geography, $2)::geometry) AS geom
      FROM failed_geoms
    ),
    candidate_edges AS (
      SELECT id, geom FROM infra_aristas_cleaned WHERE geom IS NOT NULL AND ${HIGHWAY_FILTER_CORE}
      UNION ALL
      SELECT id, geom FROM infra_aristas WHERE geom IS NOT NULL AND ${HIGHWAY_FILTER_CORE}
    )
    SELECT DISTINCT ce.id AS edge_id
    FROM candidate_edges ce
    JOIN failure_buffer fb ON fb.geom IS NOT NULL
    WHERE ST_Intersects(ce.geom, fb.geom)
  `;

  const result = await client.query(query, [simulationId, radiusMeters]);
  const ids = result.rows
    .map((row) => Number(row.edge_id))
    .filter((id) => !Number.isNaN(id));

  return Array.from(new Set(ids));
}

async function runBaselineForTable(
  tableName: 'infra_aristas_cleaned' | 'infra_aristas',
  source: number,
  target: number
) {
  // Baseline: ruta mas corta pura, sin considerar riesgo, inundaciones, ni restricciones
  const startTime = performance.now();

  let edgesSubquery = `
    SELECT id, source, target, length_m as cost,
           length_m as reverse_cost
    FROM ${tableName}
    WHERE length_m IS NOT NULL AND length_m > 0
  `;
  edgesSubquery += highwayFilterExpression;

  const safeEdgesSubquery = edgesSubquery.replace(/'/g, "''");

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
              'p_fallo', COALESCE(a.p_fallo_arista, 0.0),
              'highway', a.highway
            )
          ) ORDER BY r.seq
        ), '[]'::json)
      ) as route
    FROM pgr_dijkstra(
        '${safeEdgesSubquery}',
      $1::BIGINT,
      $2::BIGINT,
      true
    ) r
    JOIN ${tableName} a ON r.edge = a.id
  `;

  const params: (number | bigint)[] = [source, target];

  const result = await pool.query(query, params);
  const endTime = performance.now();

  const routeData = result.rows?.[0]?.route || { type: 'FeatureCollection', features: [] };
  const features = routeData.features || [];

  let totalDistance = 0;
  let weightedRisk = 0;
  for (const feature of features) {
    const length = feature.properties.length_m || 0;
    const pFallo = feature.properties.p_fallo || 0;
    totalDistance += length;
    weightedRisk += pFallo * length;
  }
  // Promedio ponderado por distancia (0-1)
  const avgRisk = totalDistance > 0 ? weightedRisk / totalDistance : 0;
  const travelTimeMin = calculateTravelTime(features);

  return {
    route: routeData,
    metrics: {
      distance_m: totalDistance,
      travel_time_min: travelTimeMin,
      computation_time_ms: endTime - startTime,
      risk_score: avgRisk,
      num_segments: features.length,
      method: 'baseline',
      source_table: tableName
    }
  };
}

async function runBaseline(source: number, target: number) {
  // Baseline: ruta mas corta pura, sin considerar riesgo, simulaciones ni restricciones
  const tables: ('infra_aristas_cleaned' | 'infra_aristas')[] = ['infra_aristas_cleaned', 'infra_aristas'];
  for (let i = 0; i < tables.length; i++) {
    const tableName = tables[i];
    const result = await runBaselineForTable(tableName, source, target);
    if (result.metrics.num_segments > 0 || i === tables.length - 1) {
      if (result.metrics.num_segments === 0 && i < tables.length - 1) {
        console.warn(`[baseline] Sin segmentos usando ${tableName}, probando tabla alternativa`);
      }
      return result;
    }
  }
  return fallbackResult('baseline', 'Sin ruta'); // improbable
}

async function runResilientForTable(
  tableName: 'infra_aristas_cleaned' | 'infra_aristas',
  source: number,
  target: number,
  k: number,
  maxRisk: number | null,
  maxDistance: number | null,
  avoidFlood: boolean,
  blockedEdgeIds: number[],
  simulationId: string | null
) {
  const client = await pool.connect();
  const startTime = performance.now();

  try {
    await client.query('BEGIN');

    // Create temp table with graduated penalties based on proximity to simulation failures
    let penaltyJoin = '';
    let penaltyCost = '0.0';

    if (simulationId) {
      // Simple penalty: edges directly marked as failed in simulation get high penalty
      // Also penalize edges connected to failed nodes
      const createPenaltyTable = `
        CREATE TEMP TABLE temp_sim_penalties ON COMMIT DROP AS
        SELECT DISTINCT edge_id, 1.0 as sim_penalty FROM (
          -- Edges directly marked as failed
          SELECT entity_id as edge_id
          FROM sim_fallas_activas
          WHERE simulation_id = $1 AND is_failed = true AND entity_type = 'arista'
          UNION
          -- Edges connected to failed nodes
          SELECT a.id as edge_id
          FROM sim_fallas_activas s
          JOIN ${tableName} a ON (a.source = s.entity_id OR a.target = s.entity_id)
          WHERE s.simulation_id = $1 AND s.is_failed = true AND s.entity_type = 'nodo'
        ) sub
      `;

      await client.query(createPenaltyTable, [simulationId]);
      penaltyJoin = `LEFT JOIN temp_sim_penalties sp ON a.id = sp.edge_id`;
      penaltyCost = `COALESCE(sp.sim_penalty, 0.0)`;
    }

    // Cost formula: length * (1 + k * (base_risk + simulation_penalty))
    // This makes edges near failures much more expensive without blocking them entirely
    let edgesQuery = `
      SELECT
        a.id,
        a.source,
        a.target,
        a.length_m * (1.0 + ${k} * (coalesce(a.p_fallo_arista, 0.0) + ${penaltyCost})) as cost,
        a.length_m * (1.0 + ${k} * (coalesce(a.p_fallo_arista, 0.0) + ${penaltyCost})) as reverse_cost
      FROM ${tableName} a
      ${penaltyJoin}
      WHERE a.length_m IS NOT NULL
    `;
    edgesQuery += highwayFilterAliasA;

    if (maxRisk !== null) {
      edgesQuery += ` AND a.p_fallo_arista <= ${maxRisk}`;
    }
    if (maxDistance !== null) {
      edgesQuery += ` AND length_m <= ${maxDistance}`;
    }
    if (avoidFlood) {
      edgesQuery += ` AND coalesce(a.p_fallo_arista, 0) < 0.3`;
    }
    // Note: we no longer use blockedEdgeIds for resilient - graduated penalties instead

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
      JOIN ${tableName} a ON r.edge = a.id;
    `;

    const result = await client.query(query, [source, target]);
    await client.query('COMMIT');

    const routeData = result.rows?.[0]?.route || { type: 'FeatureCollection', features: [] };
    const features = routeData.features || [];

    let totalDistance = 0;
    let weightedRisk = 0;
    for (const feature of features) {
      const length = feature.properties.length_m || 0;
      const pFallo = feature.properties.p_fallo || 0;
      totalDistance += length;
      weightedRisk += pFallo * length;
    }
    // Promedio ponderado por distancia (0-1)
    const avgRisk = totalDistance > 0 ? weightedRisk / totalDistance : 0;
    const travelTimeMin = calculateTravelTime(features);

    const endTime = performance.now();

    return {
      route: routeData,
      metrics: {
        distance_m: totalDistance,
        travel_time_min: travelTimeMin,
        computation_time_ms: endTime - startTime,
        risk_score: avgRisk,
        num_segments: features.length,
        method: 'resilient',
        parameters: { k, max_risk: maxRisk, max_distance: maxDistance },
        source_table: tableName
      }
    };
  } catch (error) {
    try { await client.query('ROLLBACK'); } catch { /* ignore */ }
    throw error;
  } finally {
    client.release();
  }
}

async function runResilient(
  source: number,
  target: number,
  k: number,
  maxRisk: number | null,
  maxDistance: number | null,
  avoidFlood: boolean,
  blockedEdgeIds: number[],
  simulationId: string | null
) {
  const tables: ('infra_aristas_cleaned' | 'infra_aristas')[] = ['infra_aristas_cleaned', 'infra_aristas'];
  for (let i = 0; i < tables.length; i++) {
    const tableName = tables[i];
    const result = await runResilientForTable(tableName, source, target, k, maxRisk, maxDistance, avoidFlood, blockedEdgeIds, simulationId);
    if (result.metrics.num_segments > 0 || i === tables.length - 1) {
      if (result.metrics.num_segments === 0 && i < tables.length - 1) {
        console.warn(`[resilient] Sin segmentos usando ${tableName}, probando tabla alternativa`);
      }
      return result;
    }
  }
  return fallbackResult('resilient', 'Sin ruta'); // fallback de seguridad
}

function fallbackResult(method: string, message: string) {
  return {
    route: { type: 'FeatureCollection', features: [] },
    metrics: {
      distance_m: 0,
      travel_time_min: 0,
      computation_time_ms: 0,
      risk_score: 0,
      num_segments: 0,
      method,
      error: true
    },
    error: message
  };
}

function withTimeout<T>(promise: Promise<T>, method: string, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<T | ReturnType<typeof fallbackResult>> {
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      resolve(fallbackResult(method, `${method} timeout after ${timeoutMs}ms`));
    }, timeoutMs);

    promise
      .then((res) => {
        clearTimeout(timer);
        resolve(res);
      })
      .catch((err) => {
        clearTimeout(timer);
        resolve(fallbackResult(method, err instanceof Error ? err.message : String(err)));
      });
  });
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

  const k = searchParams.get('k') || '15.0';

  const riskWeight = searchParams.get('risk_weight') || '10.0';
  const maxRisk = searchParams.get('max_risk');
  const maxDistance = searchParams.get('max_distance');
  const simulationId = searchParams.get('simulation_id');
  const lambdaRisk = searchParams.get('lambda_risk') || '5.0';
  const maxTime = searchParams.get('max_time_min');
  const avoidFlood = searchParams.get('avoid_flood_zones') === 'true';
  const bboxMarginParam = searchParams.get('bbox_margin') || process.env.CPLEX_BBOX_MARGIN || process.env.NEXT_PUBLIC_CPLEX_BBOX_MARGIN || undefined;
  const sourceNum = parseInt(source, 10);
  const targetNum = parseInt(target, 10);
  const kNum = parseFloat(k);
  const riskWeightNum = parseFloat(riskWeight);
  const lambdaRiskNum = parseFloat(lambdaRisk);
  const maxRiskNum = maxRisk ? parseFloat(maxRisk) : null;
  const maxDistanceNum = maxDistance ? parseFloat(maxDistance) : null;
  const maxTimeNum = maxTime ? parseFloat(maxTime) : null;
  const bboxMarginNum = bboxMarginParam !== undefined ? parseFloat(bboxMarginParam) : undefined;

  const startTime = performance.now();
  const client = await pool.connect();

  try {
    const nodeResolution = await resolveConnectedNodes(sourceNum, targetNum, client);
    const usedSource = nodeResolution.adjustedSource;
    const usedTarget = nodeResolution.adjustedTarget;

    let blockedEdgeIds: number[] = [];
    if (avoidFlood && simulationId) {
      blockedEdgeIds = await fetchFloodBlockedEdgeIds(client, simulationId);
    }

    const baseUrl = new URL(request.url).origin;

    const sharedParams = new URLSearchParams({
      source: usedSource.toString(),
      target: usedTarget.toString(),
      ...(maxRiskNum !== null && { max_risk: maxRiskNum.toString() }),
      ...(maxDistanceNum !== null && { max_distance: maxDistanceNum.toString() }),
      ...(maxTimeNum !== null && { max_time_min: maxTimeNum.toString() }),
      ...(avoidFlood && { avoid_flood_zones: 'true' }),
      ...(bboxMarginNum !== undefined && !Number.isNaN(bboxMarginNum) && { bbox_margin: bboxMarginNum.toString() }),
      ...(simulationId && { simulation_id: simulationId })
    });

    const [baselineResult, resilientResult, astarResult, cplexResult] = await Promise.all([
      withTimeout(
        runBaseline(usedSource, usedTarget),
        'baseline'
      ),
      withTimeout(
        runResilient(usedSource, usedTarget, kNum, maxRiskNum, maxDistanceNum, avoidFlood, blockedEdgeIds, simulationId),
        'resilient'
      ),
      withTimeout(
        fetch(`${baseUrl}/api/route/metaheuristic?${sharedParams.toString()}&risk_weight=${riskWeightNum}`).then(r => r.json()),
        'astar'
      ),
      withTimeout(
        fetch(`${baseUrl}/api/route/optimize?${sharedParams.toString()}&lambda_risk=${lambdaRiskNum}`).then(r => r.json()),
        'cplex'
      )
    ]);

    const totalTime = performance.now() - startTime;

    const results = {
      baseline: baselineResult,
      resilient: resilientResult,
      astar: astarResult,
      cplex: cplexResult,
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
          avoid_flood_zones: avoidFlood,
          bbox_margin: bboxMarginNum,
          requested_source: sourceNum,
          requested_target: targetNum,
          resolved_source: usedSource,
          resolved_target: usedTarget
        },
        summary: {
          shortest_distance: Math.min(
            baselineResult?.metrics?.distance_m || Infinity,
            resilientResult?.metrics?.distance_m || Infinity,
            astarResult?.metrics?.distance_m || Infinity,
            cplexResult?.metrics?.distance_m || Infinity
          ),
          shortest_travel_time: Math.min(
            baselineResult?.metrics?.travel_time_min || Infinity,
            resilientResult?.metrics?.travel_time_min || Infinity,
            astarResult?.metrics?.travel_time_min || Infinity,
            cplexResult?.metrics?.travel_time_min || Infinity
          ),
          lowest_risk: Math.min(
            baselineResult?.metrics?.risk_score || Infinity,
            resilientResult?.metrics?.risk_score || Infinity,
            astarResult?.metrics?.risk_score || Infinity,
            cplexResult?.metrics?.risk_score || Infinity
          ),
          fastest_computation: Math.min(
            baselineResult?.metrics?.computation_time_ms || Infinity,
            resilientResult?.metrics?.computation_time_ms || Infinity,
            astarResult?.metrics?.computation_time_ms || Infinity,
            cplexResult?.metrics?.computation_time_ms || Infinity
          )
        }
      },
      node_adjustments: nodeResolution
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
  } finally {
    client.release();
  }
}
