/**
 * API route para calcular rutas usando pgr_dijkstra en Supabase.
 * 
 * Endpoint: GET /api/route
 * Query params (opcionales): ?from=1&to=2
 * 
 * Retorna un GeoJSON de la ruta calculada.
 */
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  // Por ahora retornamos un stub (datos de ejemplo)
  // En producción, aquí se conectaría a Supabase y ejecutaría pgr_dijkstra
  const routeData = {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [
            [-70.65, -33.45],
            [-70.64, -33.46]
          ]
        },
        properties: {
          cost: 100,
          distance: 150
        }
      }
    ]
  };

  return NextResponse.json(routeData);
}
