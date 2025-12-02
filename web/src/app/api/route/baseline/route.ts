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
import { resolveConnectedNodes } from '@/lib/connectedNodes';

const { Pool } = pg;

// Crear pool de conexiones para PostgreSQL directo
const pool = new Pool({
  host: process.env.SUPABASE_DB_HOST || 'aws-1-us-east-1.pooler.supabase.com',
  port: parseInt(process.env.SUPABASE_DB_PORT || '6543'),
  database: process.env.SUPABASE_DB_NAME || 'postgres',
  user: process.env.SUPABASE_DB_USER || 'postgres.eqjzlgbjgwbnvqzbomsn',
  password: process.env.SUPABASE_DB_PASSWORD,
  ssl: { rejectUnauthorized: false }
});

type AristaTable = 'infra_aristas_cleaned' | 'infra_aristas';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  // Obtener parámetros de origen y destino
  const source = parseInt(searchParams.get('source') || '1');
  const target = parseInt(searchParams.get('target') || '100');
  const avoidFloodZones = searchParams.get('avoid_flood_zones') === 'true';

  // Medir tiempo de inicio
  const startTime = performance.now();
  let client;

  const runForTable = async (table: AristaTable, usedSource: number, usedTarget: number) => {
    const floodFilter = avoidFloodZones ? " AND coalesce(p_fallo_arista, 0) < 0.3" : "";

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
         length_m as reverse_cost 
        FROM ${table} WHERE length_m IS NOT NULL AND length_m > 0${floodFilter}',
        $1::BIGINT,
        $2::BIGINT,
        true
      ) r
      JOIN ${table} a ON r.edge = a.id;
    `;

    const result = await client!.query(query, [usedSource, usedTarget]);
    return result.rows?.[0]?.route || { type: 'FeatureCollection', features: [] };
  };

  try {
    client = await pool.connect();

    const nodeResolution = await resolveConnectedNodes(source, target, client);
    const usedSource = nodeResolution.adjustedSource;
    const usedTarget = nodeResolution.adjustedTarget;

    const tables: AristaTable[] = ['infra_aristas_cleaned', 'infra_aristas'];
    let routeData: any = { type: 'FeatureCollection', features: [] };
    let usedTable: AristaTable = tables[0];

    for (let i = 0; i < tables.length; i++) {
      usedTable = tables[i];
      routeData = await runForTable(usedTable, usedSource, usedTarget);
      if (routeData.features?.length) break;
    }

    const endTime = performance.now();
    const computationTime = endTime - startTime;

    const features = routeData.features || [];
    let totalDistance = 0;
    let totalRisk = 0;
    for (const feature of features) {
      totalDistance += feature.properties.length_m || 0;
      totalRisk += feature.properties.p_fallo || 0;
    }

    if (!features.length) {
      return NextResponse.json({
        route: routeData,
        metrics: {
          distance_m: 0,
          computation_time_ms: computationTime,
          risk_score: 0,
          num_segments: 0,
          method: 'baseline',
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
        risk_score: totalRisk,
        num_segments: features.length,
        method: 'baseline',
        source_table: usedTable
      },
      node_adjustments: nodeResolution
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
        error: 'Error calculando ruta: ' + (err instanceof Error ? err.message : String(err)),
        node_adjustments: { error: 'resolution_failed' }
      },
      { status: 500 }
    );
  } finally {
    if (client) client.release();
  }
}
