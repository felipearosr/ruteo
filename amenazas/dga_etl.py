"""
ETL para amenazas DGA (estaciones de monitoreo de la Dirección General de Aguas, Chile).

Consulta la API o archivo GeoJSON de estaciones DGA, filtra por bounding box,
y genera un archivo JSON con los puntos de estaciones.

Por ahora crea datos de ejemplo para demostrar la estructura.

Salida:
  - amenazas/dga_estaciones.json

Uso:
  python amenazas/dga_etl.py
"""
import os
import json


def generate_sample_data():
    # Generar datos de ejemplo de estaciones DGA
    samples = [
        {
            "lon": -70.65,
            "lat": -33.45,
            "station_id": "DGA-001",
            "parameter": {"type": "caudal", "unit": "m3/s"},
            "last_update": "2025-11-16T20:00:00Z"
        },
        {
            "lon": -70.66,
            "lat": -33.46,
            "station_id": "DGA-002",
            "parameter": {"type": "nivel", "unit": "m"},
            "last_update": "2025-11-16T19:30:00Z"
        },
    ]
    return samples


def main():
    data = generate_sample_data()
    outdir = os.path.join(os.path.dirname(__file__), '.')
    outpath = os.path.join(outdir, 'dga_estaciones.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Archivo generado: {outpath} ({len(data)} registros)")


if __name__ == '__main__':
    main()
