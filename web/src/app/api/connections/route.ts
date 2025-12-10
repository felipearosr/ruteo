import { NextResponse } from 'next/server';
import { pool } from '@/lib/db';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const bboxParam = searchParams.get('bbox'); // south,west,north,east
  const limitParam = searchParams.get('limit');

  if (!bboxParam) {
    return NextResponse.json({ error: 'bbox requerido: south,west,north,east' }, { status: 400 });
  }

  const parts = bboxParam.split(',').map(parseFloat);
  if (parts.length !== 4 || parts.some((v) => Number.isNaN(v))) {
    return NextResponse.json({ error: 'bbox inválido' }, { status: 400 });
  }

  const [south, west, north, east] = parts;
  const limit = Math.min(Math.max(parseInt(limitParam || '1500', 10), 1), 3000);

  try {
    const result = await pool.query(
      `
      SELECT id,
             source,
             target,
             ST_AsGeoJSON(geom)::json as geom
      FROM infra_aristas_cleaned
      WHERE geom && ST_MakeEnvelope($1, $2, $3, $4, 4326)
        AND COALESCE(highway, '') NOT IN ('footway','pedestrian','cycleway','path','steps','track','bridleway')
      LIMIT $5
      `,
      [west, south, east, north, limit]
    );

    return NextResponse.json({
      connections: result.rows.map((r) => ({
        id: Number(r.id),
        source: Number(r.source),
        target: Number(r.target),
        geom: r.geom
      }))
    });
  } catch (err) {
    console.error('Error fetching connections bbox', err);
    return NextResponse.json(
      { error: 'Error al obtener conexiones' },
      { status: 500 }
    );
  }
}
