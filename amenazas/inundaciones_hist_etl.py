"""
ETL para amenazas de inundaciones históricas.

Genera un archivo JSON con polígonos de zonas que han presentado inundaciones históricas.
Por ahora crea datos de ejemplo para demostrar la estructura.

Salida:
  - amenazas/inundaciones_hist.json

Uso:
  python amenazas/inundaciones_hist_etl.py
"""
import os
import json


def generate_sample_data():
    # Generar datos de ejemplo de zonas de inundación histórica
    samples = [
        {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-70.65, -33.45],
                    [-70.64, -33.45],
                    [-70.64, -33.46],
                    [-70.65, -33.46],
                    [-70.65, -33.45]
                ]]
            },
            "source": "Registro municipal",
            "event_date": {"lower": "2023-06-15", "upper": "2023-06-20"},
            "severity": "alta"
        },
    ]
    return samples


def main():
    data = generate_sample_data()
    outdir = os.path.join(os.path.dirname(__file__), '.')
    outpath = os.path.join(outdir, 'inundaciones_hist.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Archivo generado: {outpath} ({len(data)} registros)")


if __name__ == '__main__':
    main()
