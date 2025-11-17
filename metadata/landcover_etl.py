"""
ETL para metadata de landcover (cobertura de suelo).

Genera un archivo JSON con geometrías (puntos o polígonos) clasificados por tipo de cobertura.
Por ahora crea datos de ejemplo para demostrar la estructura.

Salida:
  - metadata/landcover.json

Uso:
  python metadata/landcover_etl.py
"""
import os
import json


def generate_sample_data():
    # Generar unos pocos registros de ejemplo con landcover
    samples = [
        {
            "geometry": {
                "type": "Point",
                "coordinates": [-70.65, -33.45]
            },
            "class": "urban",
            "confidence": 0.95,
            "source": "Sentinel-2"
        },
        {
            "geometry": {
                "type": "Point",
                "coordinates": [-70.66, -33.46]
            },
            "class": "vegetation",
            "confidence": 0.88,
            "source": "Sentinel-2"
        },
    ]
    return samples


def main():
    data = generate_sample_data()
    outdir = os.path.join(os.path.dirname(__file__), '.')
    outpath = os.path.join(outdir, 'landcover.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Archivo generado: {outpath} ({len(data)} registros)")


if __name__ == '__main__':
    main()
