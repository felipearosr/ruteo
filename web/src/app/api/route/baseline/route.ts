/**
 * API route para Ruta 1: pgr_dijkstra Baseline
 * 
 * Ruta más corta usando solo la distancia como costo (sin considerar riesgo).
 * Sirve como baseline para comparar con las rutas resilientes.
 * 
 * Endpoint: GET /api/route/baseline
 * Query params: ?source=X&target=Y
 */
import { NextResponse } from 'next/server';
import pg from 'pg';

const { Pool } = pg;

// Crear pool de conexiones para PostgreSQL directo
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

  // Obtener parámetros de origen y destino
  const source = parseInt(searchParams.get('source') || '1');
  const target = parseInt(searchParams.get('target') || '100');

  // Medir tiempo de inicio
  const startTime = performance.now();

  try {
    // Consulta SQL con pgr_dijkstra (solo costo = distancia)
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
         FROM infra_aristas WHERE length_m IS NOT NULL AND length_m > 0',
        $1::BIGINT,
        $2::BIGINT,
        true
      ) r
      JOIN infra_aristas a ON r.edge = a.id;
    `;

    const result = await pool.query(query, [source, target]);

    // Medir tiempo de finalización
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
          method: 'baseline'
        },
        error: 'No se encontró ruta entre los nodos especificados.'
      });
    }

    const routeData = result.rows[0].route;

    // Calcular métricas
    let totalDistance = 0;
    let totalRisk = 0;
    const features = routeData.features || [];

    for (const feature of features) {
      totalDistance += feature.properties.length_m || 0;
      totalRisk += feature.properties.p_fallo || 0;
    }

    return NextResponse.json({
      route: routeData,
      metrics: {
        distance_m: totalDistance,
        computation_time_ms: computationTime,
        risk_score: totalRisk,
        num_segments: features.length,
        method: 'baseline'
      }
    });

  } catch (err) {
    const endTime = performance.now();
    const computationTime = endTime - startTime;

    console.error('Error en el endpoint de ruta baseline:', err);
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
          method: 'baseline'
        },
        error: 'Error calculando ruta: ' + (err instanceof Error ? err.message : String(err))
      },
      { status: 500 }
    );
  }
}
