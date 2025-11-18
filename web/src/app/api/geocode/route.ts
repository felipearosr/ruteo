/**
 * API Endpoint: Geocodificación con Nominatim
 * 
 * Convierte direcciones textuales a coordenadas geográficas.
 * 
 * GET /api/geocode?q=Av.+Providencia+1234
 * 
 * Respuesta:
 * {
 *   "success": true,
 *   "results": [
 *     {
 *       "display_name": "Av. Providencia 1234, Santiago, Chile",
 *       "lat": -33.4372,
 *       "lon": -70.6298,
 *       "address": {
 *         "road": "Avenida Providencia",
 *         "house_number": "1234",
 *         "city": "Santiago",
 *         "country": "Chile"
 *       }
 *     }
 *   ]
 * }
 */

import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Obtener query parameter
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.get('q');

    if (!query || query.trim().length === 0) {
      return NextResponse.json(
        { success: false, error: 'Query parameter "q" is required' },
        { status: 400 }
      );
    }

    // Validar longitud mínima (evitar queries inútiles)
    if (query.trim().length < 3) {
      return NextResponse.json(
        { success: false, error: 'Query must be at least 3 characters long' },
        { status: 400 }
      );
    }

    // Llamar a Nominatim API (OpenStreetMap)
    const nominatimUrl = new URL('https://nominatim.openstreetmap.org/search');
    nominatimUrl.searchParams.append('q', query);
    nominatimUrl.searchParams.append('format', 'json');
    nominatimUrl.searchParams.append('addressdetails', '1');
    nominatimUrl.searchParams.append('limit', '5'); // Máximo 5 resultados
    nominatimUrl.searchParams.append('countrycodes', 'cl'); // Solo Chile
    
    // Bias hacia Santiago (coordenadas centrales)
    nominatimUrl.searchParams.append('viewbox', '-70.9,-33.2,-70.4,-33.7');
    nominatimUrl.searchParams.append('bounded', '1');

    console.log(`[Geocode] Llamando a Nominatim: ${query}`);

    const response = await fetch(nominatimUrl.toString(), {
      headers: {
        'User-Agent': 'RuteoResilienteApp/1.0 (https://github.com/felipearosr/ruteo)',
        'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8'
      }
    });

    if (!response.ok) {
      console.error(`[Geocode] Error de Nominatim: ${response.status}`);
      return NextResponse.json(
        { 
          success: false, 
          error: `Nominatim API error: ${response.status}` 
        },
        { status: response.status }
      );
    }

    const data = await response.json();

    // Filtrar y formatear resultados
    const results = data.map((item: any) => ({
      display_name: item.display_name,
      lat: parseFloat(item.lat),
      lon: parseFloat(item.lon),
      address: {
        road: item.address?.road || item.address?.street || '',
        house_number: item.address?.house_number || '',
        suburb: item.address?.suburb || item.address?.neighbourhood || '',
        city: item.address?.city || item.address?.town || item.address?.municipality || 'Santiago',
        region: item.address?.state || 'Región Metropolitana',
        country: item.address?.country || 'Chile',
        postcode: item.address?.postcode || ''
      },
      importance: item.importance || 0,
      type: item.type || 'unknown',
      osm_type: item.osm_type || 'unknown',
      osm_id: item.osm_id || 0
    }));

    // Ordenar por importancia (Nominatim ya lo hace, pero por si acaso)
    results.sort((a: any, b: any) => b.importance - a.importance);

    console.log(`[Geocode] Encontrados ${results.length} resultados para: ${query}`);

    return NextResponse.json({
      success: true,
      query: query,
      count: results.length,
      results: results
    });

  } catch (error: any) {
    console.error('[Geocode] Error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error.message || 'Internal server error',
        details: process.env.NODE_ENV === 'development' ? error.stack : undefined
      },
      { status: 500 }
    );
  }
}
