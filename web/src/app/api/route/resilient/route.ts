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
import { pool } from '@/lib/db';
import { resolveConnectedNodes } from '@/lib/connectedNodes';

type AristaTable = 'infra_aristas_cleaned' | 'infra_aristas';

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
  let nodeResolution;

  try {
    client = await pool.connect();

    nodeResolution = await resolveConnectedNodes(source, target, client);
    const usedSource = nodeResolution.adjustedSource;
    const usedTarget = nodeResolution.adjustedTarget;

    // 1. Pre-cálculos con tablas temporales
    await client.query('BEGIN');

    let penaltyJoin = '';
    let penaltyCost = '0.0';
    let trafficJoin = '';
    let trafficCost = '1.0'; // Factor multiplicativo base (1.0 = sin tráfico)

    // A. Penalización por Fallas (Simulación)
    if (simulationId) {
      // Simple penalty: edges directly marked as failed or connected to failed nodes
      const createFailureTempTable = `
        CREATE TEMP TABLE temp_edge_penalties ON COMMIT DROP AS
        SELECT DISTINCT edge_id, 1.0 as penalty FROM (
          -- Edges directly marked as failed
          SELECT entity_id as edge_id
          FROM sim_fallas_activas
          WHERE simulation_id = $1 AND is_failed = true AND entity_type = 'arista'
          UNION
          -- Edges connected to failed nodes
          SELECT a.id as edge_id
          FROM sim_fallas_activas s
          JOIN infra_aristas_cleaned a ON (a.source = s.entity_id OR a.target = s.entity_id)
          WHERE s.simulation_id = $1 AND s.is_failed = true AND s.entity_type = 'nodo'
        ) sub
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
      FROM infra_aristas_cleaned a
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

    const runForTable = async (table: AristaTable) => {
      let edgesQuery = `
        SELECT 
          a.id, 
          a.source, 
          a.target, 
          a.length_m * ${trafficCost} * ${heuristicTrafficSql} * (1.0 + ${k} * (a.p_fallo_arista + ${penaltyCost})) as cost,
          a.length_m * ${trafficCost} * ${heuristicTrafficSql} * (1.0 + ${k} * (a.p_fallo_arista + ${penaltyCost})) as reverse_cost
        FROM ${table} a
        ${penaltyJoin}
        ${trafficJoin}
        WHERE a.length_m IS NOT NULL
      `;

      if (maxRisk !== null) {
        edgesQuery += ` AND a.p_fallo_arista <= ${maxRisk}`;
      }
      if (maxDistance !== null) {
        edgesQuery += ` AND length_m <= ${maxDistance}`;
      }
      if (avoidFloodZones) {
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
        JOIN ${table} a ON r.edge = a.id;
      `;

      const result = await client!.query(query, [usedSource, usedTarget]);
      return result.rows?.[0]?.route || { type: 'FeatureCollection', features: [] };
    };

    const tables: AristaTable[] = ['infra_aristas_cleaned', 'infra_aristas'];
    let routeData: any = { type: 'FeatureCollection', features: [] };
    let usedTable: AristaTable = tables[0];

    for (let i = 0; i < tables.length; i++) {
      usedTable = tables[i];
      routeData = await runForTable(usedTable);
      if (routeData.features?.length) break;
    }

    await client.query('COMMIT');

    const endTime = performance.now();
    const computationTime = endTime - startTime;

    const features = routeData.features || [];
    let totalDistance = 0;
    let weightedRisk = 0;
    let totalAdjustedCost = 0;

    for (const feature of features) {
      const length = feature.properties.length_m || 0;
      const pFallo = feature.properties.p_fallo || 0;
      totalDistance += length;
      weightedRisk += pFallo * length;
      totalAdjustedCost += feature.properties.adjusted_cost || 0;
    }
    // Promedio ponderado por distancia (0-1)
    const avgRisk = totalDistance > 0 ? weightedRisk / totalDistance : 0;

    if (!features.length) {
      return NextResponse.json({
        route: routeData,
        metrics: {
          distance_m: 0,
          computation_time_ms: computationTime,
          risk_score: 0,
          num_segments: 0,
          method: 'resilient',
          parameters: { k, max_risk: maxRisk, max_distance: maxDistance },
          source_table: usedTable
        },
        error: 'No se encontró ruta entre los nodos especificados.',
        node_adjustments: nodeResolution
      });
    }

    return NextResponse.json({
      route: routeData,
      metrics: {
        distance_m: totalDistance,
        computation_time_ms: computationTime,
        risk_score: avgRisk,
        adjusted_cost: totalAdjustedCost,
        num_segments: features.length,
        method: 'resilient',
        parameters: { k, max_risk: maxRisk, max_distance: maxDistance },
        source_table: usedTable
      },
      node_adjustments: nodeResolution
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
        error: 'Error calculando ruta resiliente: ' + (err instanceof Error ? err.message : String(err)),
        node_adjustments: nodeResolution
      },
      { status: 500 }
    );
  } finally {
    if (client) client.release();
  }
}
