"""
ETL para obtener rios y cursos de agua de OpenStreetMap.

Descarga geometrias de rios principales de Santiago para crear
zonas de riesgo de inundacion basadas en buffers.

Rios principales:
- Rio Mapocho
- Rio Maipo
- Zanjon de la Aguada
- Estero Lampa
- Estero Colina
- Canal San Carlos

Salida:
  - amenazas/rios_santiago.json

Uso:
  python amenazas/rios_etl.py
"""
import os
import json
import requests
from typing import List, Dict, Any

# Bounding box de Santiago
SANTIAGO_BBOX = {
    "south": -33.65,
    "north": -33.25,
    "west": -70.85,
    "east": -70.45
}

# Query Overpass para rios y cursos de agua
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def get_overpass_query() -> str:
    """Genera query Overpass para rios de Santiago."""
    bbox = f"{SANTIAGO_BBOX['south']},{SANTIAGO_BBOX['west']},{SANTIAGO_BBOX['north']},{SANTIAGO_BBOX['east']}"

    query = f"""
    [out:json][timeout:120];
    (
      // Rios principales
      way["waterway"="river"]({bbox});
      relation["waterway"="river"]({bbox});

      // Canales importantes
      way["waterway"="canal"]({bbox});

      // Esteros y arroyos
      way["waterway"="stream"]({bbox});

      // Zanjon de la Aguada y similares
      way["waterway"="drain"]["name"]({bbox});
    );
    out body geom;
    """
    return query


def fetch_waterways() -> Dict[str, Any]:
    """Descarga datos de cursos de agua desde Overpass."""
    print("Descargando cursos de agua de OpenStreetMap...")

    query = get_overpass_query()

    try:
        response = requests.post(
            OVERPASS_URL,
            data={'data': query},
            timeout=180
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar datos: {e}")
        return None


def parse_way_geometry(element: Dict) -> List[List[float]]:
    """Extrae coordenadas de un way."""
    if 'geometry' not in element:
        return []

    coords = []
    for node in element['geometry']:
        coords.append([node['lon'], node['lat']])

    return coords


def process_waterways(data: Dict) -> List[Dict]:
    """Procesa los datos de Overpass y extrae rios."""
    if not data or 'elements' not in data:
        return []

    waterways = []

    for element in data['elements']:
        if element['type'] != 'way':
            continue

        coords = parse_way_geometry(element)
        if len(coords) < 2:
            continue

        tags = element.get('tags', {})
        name = tags.get('name', 'Sin nombre')
        waterway_type = tags.get('waterway', 'unknown')

        # Determinar severidad basada en tipo y nombre
        severity = 'media'
        if 'mapocho' in name.lower() or 'maipo' in name.lower():
            severity = 'muy_alta'
        elif 'zanjon' in name.lower() or waterway_type == 'river':
            severity = 'alta'
        elif waterway_type == 'canal':
            severity = 'media'
        elif waterway_type == 'stream':
            severity = 'baja'

        # Buffer en metros segun severidad
        buffer_m = {
            'muy_alta': 150,
            'alta': 100,
            'media': 75,
            'baja': 50
        }.get(severity, 75)

        waterways.append({
            'osm_id': element['id'],
            'name': name,
            'type': waterway_type,
            'severity': severity,
            'buffer_m': buffer_m,
            'geometry': {
                'type': 'LineString',
                'coordinates': coords
            },
            'tags': tags
        })

    return waterways


def main():
    data = fetch_waterways()

    if not data:
        print("No se pudieron obtener datos. Usando datos de respaldo...")
        # Crear datos minimos de respaldo
        waterways = create_fallback_data()
    else:
        waterways = process_waterways(data)

    print(f"Cursos de agua procesados: {len(waterways)}")

    # Filtrar los mas importantes (con nombre)
    named_waterways = [w for w in waterways if w['name'] != 'Sin nombre']
    print(f"Cursos de agua con nombre: {len(named_waterways)}")

    # Guardar todos
    outdir = os.path.dirname(__file__)
    outpath = os.path.join(outdir, 'rios_santiago.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(waterways, f, ensure_ascii=False, indent=2)

    print(f"Archivo generado: {outpath}")

    # Resumen por tipo
    tipos = {}
    for w in waterways:
        t = w['type']
        tipos[t] = tipos.get(t, 0) + 1

    print("\nResumen por tipo:")
    for t, c in sorted(tipos.items()):
        print(f"  {t}: {c}")

    # Resumen por severidad
    severidades = {}
    for w in waterways:
        s = w['severity']
        severidades[s] = severidades.get(s, 0) + 1

    print("\nResumen por severidad:")
    for s, c in sorted(severidades.items()):
        print(f"  {s}: {c}")


def create_fallback_data() -> List[Dict]:
    """Crea datos de respaldo con rios principales conocidos."""
    # Coordenadas aproximadas de rios principales de Santiago
    return [
        {
            'osm_id': 1,
            'name': 'Rio Mapocho',
            'type': 'river',
            'severity': 'muy_alta',
            'buffer_m': 150,
            'geometry': {
                'type': 'LineString',
                'coordinates': [
                    [-70.45, -33.42], [-70.50, -33.43], [-70.55, -33.43],
                    [-70.60, -33.43], [-70.65, -33.44], [-70.70, -33.44],
                    [-70.75, -33.45], [-70.80, -33.46]
                ]
            },
            'tags': {'name': 'Rio Mapocho', 'waterway': 'river'}
        },
        {
            'osm_id': 2,
            'name': 'Zanjon de la Aguada',
            'type': 'drain',
            'severity': 'alta',
            'buffer_m': 100,
            'geometry': {
                'type': 'LineString',
                'coordinates': [
                    [-70.55, -33.48], [-70.60, -33.49], [-70.65, -33.49],
                    [-70.70, -33.50], [-70.75, -33.51]
                ]
            },
            'tags': {'name': 'Zanjon de la Aguada', 'waterway': 'drain'}
        },
        {
            'osm_id': 3,
            'name': 'Canal San Carlos',
            'type': 'canal',
            'severity': 'media',
            'buffer_m': 75,
            'geometry': {
                'type': 'LineString',
                'coordinates': [
                    [-70.52, -33.44], [-70.55, -33.45], [-70.58, -33.46],
                    [-70.60, -33.47]
                ]
            },
            'tags': {'name': 'Canal San Carlos', 'waterway': 'canal'}
        }
    ]


if __name__ == '__main__':
    main()
