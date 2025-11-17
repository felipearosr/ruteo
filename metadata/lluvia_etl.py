"""
ETL para metadata de lluvia / precipitación.

Genera un archivo JSON con puntos de medición de precipitación.
Por ahora crea datos de ejemplo para demostrar la estructura.

Salida:
  - metadata/lluvia.json

Uso:
  python metadata/lluvia_etl.py
"""
import os
import json
from datetime import datetime, timedelta


def generate_sample_data():
    # Generar unos pocos puntos de ejemplo con precipitación
    now = datetime.utcnow()
    samples = [
        {
            "lon": -70.65,
            "lat": -33.45,
            "precip_mm": 12.5,
            "observed_at": (now - timedelta(hours=1)).isoformat() + 'Z',
            "source": "Estación Meteo A"
        },
        {
            "lon": -70.66,
            "lat": -33.46,
            "precip_mm": 15.0,
            "observed_at": (now - timedelta(hours=2)).isoformat() + 'Z',
            "source": "Estación Meteo B"
        },
    ]
    return samples


def main():
    data = generate_sample_data()
    outdir = os.path.join(os.path.dirname(__file__), '.')
    outpath = os.path.join(outdir, 'lluvia.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Archivo generado: {outpath} ({len(data)} registros)")


if __name__ == '__main__':
    main()
