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
      SELECT id, ST_Y(geom)::double precision as lat, ST_X(geom)::double precision as lon
      FROM infra_nodos_cleaned
      WHERE geom && ST_MakeEnvelope($1, $2, $3, $4, 4326)
      ORDER BY id
      LIMIT $5
      `,
      [west, south, east, north, limit]
    );

    return NextResponse.json({
      nodes: result.rows.map((r) => ({
        id: Number(r.id),
        lat: Number(r.lat),
        lon: Number(r.lon)
      }))
    });
  } catch (err) {
    console.error('Error fetching nodes bbox', err);
    return NextResponse.json(
      { error: 'Error al obtener nodos' },
      { status: 500 }
    );
  }
}
