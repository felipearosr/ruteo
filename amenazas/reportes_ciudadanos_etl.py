"""
ETL para amenazas de reportes ciudadanos.

Genera un archivo JSON con puntos reportados por ciudadanos (p. ej. desde redes sociales o una app).
Por ahora crea datos de ejemplo para demostrar la estructura.

Salida:
  - amenazas/reportes_ciudadanos.json

Uso:
  python amenazas/reportes_ciudadanos_etl.py
"""
import os
import json
from datetime import datetime, timedelta


def generate_sample_data():
    # Generar datos de ejemplo de reportes ciudadanos
    now = datetime.utcnow()
    samples = [
        {
            "lon": -70.65,
            "lat": -33.45,
            "reported_at": (now - timedelta(hours=3)).isoformat() + 'Z',
            "reporter": "@usuario1",
            "description": "Inundación en calle principal",
            "media": {"images": ["http://example.com/img1.jpg"]}
        },
        {
            "lon": -70.66,
            "lat": -33.46,
            "reported_at": (now - timedelta(hours=1)).isoformat() + 'Z',
            "reporter": "@usuario2",
            "description": "Tráfico bloqueado por agua",
            "media": {"images": []}
        },
    ]
    return samples


def main():
    data = generate_sample_data()
    outdir = os.path.join(os.path.dirname(__file__), '.')
    outpath = os.path.join(outdir, 'reportes_ciudadanos.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Archivo generado: {outpath} ({len(data)} registros)")


if __name__ == '__main__':
    main()
