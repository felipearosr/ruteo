/**
 * API route para calcular rutas usando pgr_dijkstra en Supabase (topología limpiada).
 * 
 * Endpoint: GET /api/route
 * Query params (opcionales): ?source=1&target=100
 * 
 * Retorna un GeoJSON de la ruta calculada con pgr_dijkstra.
 */
import { NextResponse } from 'next/server';
import pg from 'pg';

const { Pool } = pg;

// Crear pool de conexiones para PostgreSQL directo
const pool = new Pool({
  host: process.env.SUPABASE_DB_HOST,
  port: parseInt(process.env.SUPABASE_DB_PORT || '6543'),
  database: 'postgres',
  user: process.env.SUPABASE_DB_USER,
  password: process.env.SUPABASE_DB_PASSWORD,
  ssl: { rejectUnauthorized: false }
});

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  
  // Obtener parámetros de origen y destino (o usar defaults)
  const source = parseInt(searchParams.get('source') || '1');
  const target = parseInt(searchParams.get('target') || '100');

  try {
    // Consulta SQL con pgr_dijkstra
    const query = `
      SELECT 
        json_build_object(
          'type', 'FeatureCollection',
          'features', COALESCE(json_agg(
            json_build_object(
              'type', 'Feature',
              'geometry', ST_AsGeoJSON(a.geom)::json,
              'properties', json_build_object(
                'seq', r.seq,
                'edge_id', r.edge,
                'cost', r.cost,
                'length_m', a.length_m,
                'highway', a.highway
              )
            ) ORDER BY r.seq
          ), '[]'::json)
        ) as route
      FROM pgr_dijkstra(
        'SELECT id, source, target, cost FROM infra_aristas_cleaned WHERE cost IS NOT NULL',
        $1,
        $2,
        directed := false
      ) r
      JOIN infra_aristas_cleaned a ON r.edge = a.id;
    `;

    const result = await pool.query(query, [source, target]);

    if (!result.rows || result.rows.length === 0) {
      return NextResponse.json({
        type: 'FeatureCollection',
        features: [],
        error: 'No se encontró ruta entre los nodos especificados.'
      });
    }

    return NextResponse.json(result.rows[0].route);

  } catch (err) {
    console.error('Error en el endpoint de ruta:', err);
    return NextResponse.json(
      { 
        type: 'FeatureCollection',
        features: [],
        error: 'Error calculando ruta: ' + (err instanceof Error ? err.message : String(err))
      },
      { status: 500 }
    );
  }
}
