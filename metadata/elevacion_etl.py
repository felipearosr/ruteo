"""
ETL para metadata de elevación.

Genera un archivo JSON con puntos de elevación obtenidos de una fuente simulada (o API externa).
Por ahora crea datos de ejemplo para demostrar la estructura.

Salida:
  - metadata/elevacion.json

Uso:
  python metadata/elevacion_etl.py
"""
import os
import json


def generate_sample_data():
    # Generar unos pocos puntos de ejemplo con elevación
    # En producción, estos datos provendrían de una API (p. ej. SRTM, Google Elevation API)
    samples = [
        {"lon": -70.65, "lat": -33.45, "elev_m": 520.0, "source": "SRTM"},
        {"lon": -70.66, "lat": -33.46, "elev_m": 530.5, "source": "SRTM"},
        {"lon": -70.64, "lat": -33.44, "elev_m": 515.0, "source": "SRTM"},
    ]
    return samples


def main():
    data = generate_sample_data()
    outdir = os.path.join(os.path.dirname(__file__), '.')
    outpath = os.path.join(outdir, 'elevacion.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Archivo generado: {outpath} ({len(data)} registros)")


if __name__ == '__main__':
    main()
