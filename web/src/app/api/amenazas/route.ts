import { NextRequest, NextResponse } from 'next/server';
import { pool } from '@/lib/db';

// GET /api/amenazas - Obtener todas las amenazas
// Query params: type = 'rios' | 'pasos_bajo_nivel' | 'reportes' | 'dga' | 'all'
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const type = searchParams.get('type') || 'all';

  try {
    const results: Record<string, unknown[]> = {};

    // Cargar rios (zonas de riesgo)
    if (type === 'all' || type === 'rios') {
      const riosResult = await pool.query('SELECT * FROM get_rios_geojson()');
      results.rios = riosResult.rows;
    }

    // Cargar pasos bajo nivel
    if (type === 'all' || type === 'pasos_bajo_nivel') {
      const pasosResult = await pool.query('SELECT * FROM get_pasos_bajo_nivel_geojson()');
      results.pasos_bajo_nivel = pasosResult.rows;
    }

    // Cargar reportes ciudadanos
    if (type === 'all' || type === 'reportes') {
      const reportesResult = await pool.query('SELECT * FROM get_reportes_geojson()');
      results.reportes = reportesResult.rows;
    }

    // Cargar estaciones DGA
    if (type === 'all' || type === 'dga') {
      const dgaResult = await pool.query('SELECT * FROM get_dga_geojson()');
      results.dga = dgaResult.rows;
    }

    return NextResponse.json({
      success: true,
      data: results,
      counts: {
        rios: results.rios?.length || 0,
        pasos_bajo_nivel: results.pasos_bajo_nivel?.length || 0,
        reportes: results.reportes?.length || 0,
        dga: results.dga?.length || 0,
      }
    });

  } catch (error) {
    console.error('Error loading amenazas:', error);
    return NextResponse.json(
      { success: false, error: String(error) },
      { status: 500 }
    );
  }
}
