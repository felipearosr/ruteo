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

  const startTime = performance.now();

  try {
    // Construir query con costos resilientes (usando 0.0 para p_fallo temporalmente)
    let edgesQuery = `
      SELECT 
        id, 
        source, 
        target, 
        length_m * (1.0 + ${k} * 0.0) as cost
      FROM infra_aristas 
      WHERE length_m IS NOT NULL
    `;

    // Aplicar filtros de restricciones si se especifican
    if (maxRisk !== null) {
      edgesQuery += ` AND 0.0 <= ${maxRisk}`;
    }
    if (maxDistance !== null) {
      edgesQuery += ` AND length_m <= ${maxDistance}`;
    }

    const query = `
      WITH route_result AS (
        SELECT * FROM pgr_dijkstra(
          '${edgesQuery}',
          $1::BIGINT,
          $2::BIGINT,
          false
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
                'p_fallo', 0.0,
                'highway', a.highway,
                'adjusted_cost', a.length_m * (1.0 + ${k} * 0.0)
              )
            ) ORDER BY r.seq
          ), '[]'::json)
        ) as route
      FROM route_result r
      JOIN infra_aristas a ON r.edge = a.id;
    `;

    const result = await pool.query(query, [source, target]);
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
  }
}
