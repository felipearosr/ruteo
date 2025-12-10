import { NextRequest, NextResponse } from 'next/server';
import { pool } from '@/lib/db';

// GET /api/node/nearest?lat=X&lon=Y - Encontrar nodo mas cercano a coordenadas
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const lat = parseFloat(searchParams.get('lat') || '');
  const lon = parseFloat(searchParams.get('lon') || '');

  if (isNaN(lat) || isNaN(lon)) {
    return NextResponse.json(
      { success: false, error: 'lat and lon are required' },
      { status: 400 }
    );
  }

  try {
    const result = await pool.query(
      'SELECT * FROM find_nearest_node($1, $2)',
      [lat, lon]
    );

    if (result.rows.length === 0) {
      return NextResponse.json(
        { success: false, error: 'No node found nearby' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      data: result.rows
    });

  } catch (error) {
    console.error('Error finding nearest node:', error);
    return NextResponse.json(
      { success: false, error: String(error) },
      { status: 500 }
    );
  }
}
